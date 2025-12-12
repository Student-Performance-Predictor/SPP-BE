from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from ..models import Student, Teacher, Attendance, Class
from ..serializers import StudentSerializer
from django.shortcuts import get_object_or_404
from datetime import date
import csv
import io
from django.db import transaction
from django.http import HttpResponse


# Get All Students in the Same School
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_all_students(request):
    try:
        teacher = Teacher.objects.get(user=request.user)
    except Teacher.DoesNotExist:
        return Response({"error": "Teacher not found"}, status=status.HTTP_404_NOT_FOUND)

    students = Student.objects.filter(school_id=teacher.school_id)
    serializer = StudentSerializer(students, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


# Get All Students in a Class (within the teacher's school)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_all_class_students(request, class_number):
    try:
        teacher = Teacher.objects.get(user=request.user)
    except Teacher.DoesNotExist:
        return Response({"error": "Teacher not found"}, status=status.HTTP_404_NOT_FOUND)

    students = Student.objects.filter(school_id=teacher.school_id, class_assigned=class_number)
    serializer = StudentSerializer(students, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


# Add a New Student
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_student(request):
    try:
        teacher = Teacher.objects.get(user=request.user)
    except Teacher.DoesNotExist:
        return Response({"error": "Teacher not found"}, status=status.HTTP_404_NOT_FOUND)

    student_data = request.data.copy()
    student_data["school_id"] = teacher.school_id
    student_data["school"] = teacher.school

    # Serialize student data
    serializer = StudentSerializer(data=student_data)
    if serializer.is_valid():
        student = serializer.save()

        # Get the class and its start date
        try:
            class_obj = Class.objects.get(class_number=student.class_assigned)
        except Class.DoesNotExist:
            return Response({"error": f"Class {student.class_assigned} not found"}, status=status.HTTP_404_NOT_FOUND)

        # Check if today's date is before the class's start date
        today = date.today()
        if today < class_obj.start_date:
            return Response({"message": "Student added successfully."}, status=status.HTTP_201_CREATED)

        # Create or update Attendance record for the new student
        attendance, created = Attendance.objects.get_or_create(
            school=teacher.school,
            school_id=teacher.school_id,
            class_number=student.class_assigned,
            date=today
        )

        # If the attendance record already exists, add the new student if not already present
        if not created:
            if not any(s['student_id'] == student.student_id for s in attendance.students):
                attendance.students.append({
                    "student_id": student.student_id,
                    "name": student.full_name,
                    "email": student.email,
                    "phone": student.phone,
                    "status": "not_marked",
                    "present_count": 0,
                    "percentage": 0.0
                })
                attendance.save()

        return Response({
            "message": "Student added successfully.",
            "data": serializer.data
        }, status=status.HTTP_201_CREATED)

    return Response({
        "message": "Failed to add student.",
        "errors": serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


# View a Student by ID
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def view_student(request, pk):
    student = get_object_or_404(Student, pk=pk)
    serializer = StudentSerializer(student)
    return Response(serializer.data, status=status.HTTP_200_OK)


# Update a Student by ID
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_student(request, pk):
    student = get_object_or_404(Student, pk=pk)
    serializer = StudentSerializer(student, data=request.data)
    print(request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({"message": "Student updated successfully."}, status=status.HTTP_200_OK)
    return Response({
        "message": "Failed to update student.",
        "errors": serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


# Delete a Student by ID
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_student(request, pk):
    student = get_object_or_404(Student, pk=pk)
    attendances = Attendance.objects.filter(
        students__contains=[{'student_id': student.student_id}]
    )
    for attendance in attendances:
        attendance.students = [s for s in attendance.students if s.get('student_id') != student.student_id]
        attendance.save()
    student.delete()
    return Response({"message": "Student deleted successfully."}, status=status.HTTP_200_OK)


# Export Students Data
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def export_students(request):
    try:
        teacher = Teacher.objects.get(user=request.user)
    except Teacher.DoesNotExist:
        return Response({"error": "Teacher not found"}, status=status.HTTP_404_NOT_FOUND)

    students = Student.objects.filter(
        school_id=teacher.school_id,
        class_assigned=teacher.class_assigned
    )

    # Create a CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)

    # Write header
    writer.writerow([
        'full_name', 'student_id', 'email', 'phone', 'class_assigned', 'attendance_percentage',
        'parental_education', 'study_hours', 'failures',
        'extracurricular', 'participation', 'rating', 'discipline',
        'late_submissions', 'prev_grade1', 'prev_grade2', 'final_grade'
    ])

    # Write data
    for student in students:
        writer.writerow([
            student.full_name,
            student.student_id,
            student.email,
            student.phone,
            student.class_assigned,
            student.attendance_percentage,
            student.parental_education,
            student.study_hours,
            student.failures,
            student.extracurricular,
            student.participation,
            student.rating,
            student.discipline,
            student.late_submissions,
            student.prev_grade1,
            student.prev_grade2,
            student.final_grade,
        ])

    fileName = f'students_export_{teacher.school_id}_{teacher.class_assigned}'

    # Prepare response
    output.seek(0)
    response = HttpResponse(
        output,
        content_type='text/csv',
        status=status.HTTP_200_OK
    )
    response['Content-Disposition'] = f'attachment; filename={fileName}.csv'
    return response


# Import Students Data
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def import_students(request):
    try:
        teacher = Teacher.objects.get(user=request.user)
    except Teacher.DoesNotExist:
        return Response({"error": "Teacher not found"}, status=status.HTTP_404_NOT_FOUND)

    if 'file' not in request.FILES:
        return Response({"error": "No file uploaded"}, status=status.HTTP_400_BAD_REQUEST)

    file = request.FILES['file']
    if not file.name.endswith('.csv'):
        return Response({"error": "File must be a CSV"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        # Read the CSV file
        data = file.read().decode('utf-8')
        io_string = io.StringIO(data)
        reader = csv.DictReader(io_string)
        
        results = {
            'success': 0,
            'failed': 0,
            'errors': [],
            'created': [],
            'updated': []
        }

        today = date.today()

        with transaction.atomic():
            for row in reader:
                try:
                    # Prepare student data
                    student_data = {
                        'full_name': row.get('full_name', '').strip(),
                        'student_id': row.get('student_id', '').strip(),
                        'email': row.get('email', '').strip(),
                        'phone': row.get('phone', '').strip(),
                        'class_assigned': row.get('class_assigned', '').strip(),
                        'school': teacher.school,
                        'school_id': teacher.school_id,
                        'attendance_percentage': float(row.get('attendance_percentage',0)),
                        'parental_education': int(row.get('parental_education', 0)),
                        'study_hours': int(row.get('study_hours', 0)),
                        'failures': int(row.get('failures', 0)),
                        'extracurricular': int(row.get('extracurricular', 0)),
                        'participation': int(row.get('participation', 0)),
                        'rating': int(row.get('rating', 0)),
                        'discipline': int(row.get('discipline', 0)),
                        'late_submissions': int(row.get('late_submissions', 0)),
                        'prev_grade1': float(row.get('prev_grade1', 0)),
                        'prev_grade2': float(row.get('prev_grade2', 0)),
                        'final_grade': float(row.get('final_grade', 0)),
                    }

                    # Check if student exists
                    existing_student = Student.objects.filter(student_id=student_data['student_id']).first()
                    
                    if existing_student:
                        # Update existing student
                        serializer = StudentSerializer(existing_student, data=student_data)
                        action = 'updated'
                    else:
                        # Create new student
                        serializer = StudentSerializer(data=student_data)
                        action = 'created'

                    if serializer.is_valid():
                        student = serializer.save()
                        results[action].append(student_data['student_id'])
                        results['success'] += 1

                        # Only process attendance for newly created students
                        if action == 'created':
                            # Get the class and its start date
                            try:
                                class_obj = Class.objects.get(class_number=student.class_assigned)
                            except Class.DoesNotExist:
                                results['errors'].append(f"Class {student.class_assigned} not found for student {student.student_id}")
                                continue

                            # Skip if today is before class start date
                            if today < class_obj.start_date:
                                continue

                            # Create or update Attendance record
                            attendance, created = Attendance.objects.get_or_create(
                                school=teacher.school,
                                school_id=teacher.school_id,
                                class_number=student.class_assigned,
                                date=today
                            )

                            # If attendance exists, add the new student if not present
                            if not created:
                                if not any(s['student_id'] == student.student_id for s in attendance.students):
                                    attendance.students.append({
                                        "student_id": student.student_id,
                                        "name": student.full_name,
                                        "email": student.email,
                                        "phone": student.phone,
                                        "status": "not_marked",
                                        "present_count": 0,
                                        "percentage": 0.0
                                    })
                                    attendance.save()

                    else:
                        results['failed'] += 1
                        results['errors'].append({
                            'student_id': student_data.get('student_id', 'N/A'),
                            'errors': serializer.errors
                        })

                except Exception as e:
                    results['failed'] += 1
                    results['errors'].append({
                        'row': row,
                        'error': str(e)
                    })

        return Response(results, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)