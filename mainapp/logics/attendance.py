from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status as http_status
from ..models import Attendance, Class, ClassWorkingDay, Student, School
from ..serializers import AttendanceSerializer
from django.utils.dateparse import parse_date
from datetime import date
from django.db import transaction
from django.db import IntegrityError
from ..logics.email import send_email_sync
import datetime, traceback
from rest_framework.test import APIRequestFactory

# Add Attendance (POST API)
@api_view(['POST'])
def add_attendance(request):
    data = request.data
    required_fields = ['school', 'school_id', 'class_number', 'date', 'students']
    
    if not all(field in data for field in required_fields):
        return Response({"message": "Missing required fields"}, status=http_status.HTTP_400_BAD_REQUEST)

    date_obj = parse_date(data['date']) or date.today()
    if date_obj > date.today():
        return Response({"message": "Cannot add attendance for future dates"}, status=http_status.HTTP_400_BAD_REQUEST)

    try:
        class_obj = Class.objects.get(class_number=data['class_number'])
    except Class.DoesNotExist:
        return Response({"message": "Class not found"}, status=http_status.HTTP_404_NOT_FOUND)

    if date_obj < class_obj.start_date:
        return Response({"message": "Attendance can only be added from class start date onwards"}, status=http_status.HTTP_400_BAD_REQUEST)

    data["school"] = School.objects.get(id=data["school_id"]).name
    class_working_day, created = ClassWorkingDay.objects.get_or_create(
        school_id=data['school_id'], class_number=data['class_number'], defaults={'school': data['school'], 'working_days': {}}
    )
    class_working_day.working_days.setdefault(date_obj.isoformat(), False)
    class_working_day.save()

    attendance, created = Attendance.objects.get_or_create(
        school_id=data['school_id'], class_number=data['class_number'], date=date_obj, defaults={'students': []}
    )

    existing_students = {stu['student_id']: stu for stu in attendance.students}
    for student_data in data['students']:
        student_id = student_data.get('student_id')
        if student_id:
            existing_student = existing_students.get(student_id, {})
            existing_student.update(student_data)
            existing_students[student_id] = existing_student

    attendance.students = list(existing_students.values())
    attendance.save()

    return Response({
        "message": "Attendance saved successfully",
        "data": AttendanceSerializer(attendance).data
    }, status=http_status.HTTP_201_CREATED if created else http_status.HTTP_200_OK)


# Update Class Attendance (PUT API)
@api_view(['PUT'])
def update_class_attendance(request):
    data = request.data
    school = data.get("school")
    school_id = data.get("school_id")
    class_number = data.get("class_number")
    date_str = data.get("date")
    students = data.get("students")

    if not all([school, school_id, class_number, date_str, students]):
        return Response(
            {"message": "school, school_id, class_number, date, and students are required"},
            status=http_status.HTTP_400_BAD_REQUEST
        )

    date_obj = parse_date(date_str)
    if not date_obj or date_obj > date.today():
        return Response(
            {"message": "Invalid or future date"},
            status=http_status.HTTP_400_BAD_REQUEST
        )

    try:
        class_obj = Class.objects.get(class_number=class_number)
    except Class.DoesNotExist:
        return Response(
            {"message": "Class not found"},
            status=http_status.HTTP_404_NOT_FOUND
        )

    if date_obj < class_obj.start_date:
        return Response(
            {"message": f"Attendance can only be updated from {class_obj.start_date} onwards"},
            status=http_status.HTTP_400_BAD_REQUEST
        )

    max_retries = 3
    retry_count = 0

    while retry_count < max_retries:
        try:
            with transaction.atomic():
                # Attempt to retrieve existing attendance with a lock
                attendance = Attendance.objects.select_for_update().filter(
                    school_id=school_id,
                    class_number=class_number,
                    date=date_obj
                ).first()

                if not attendance:
                    # Create new attendance record if it doesn't exist
                    attendance = Attendance.objects.create(
                        school_id=school_id,
                        class_number=class_number,
                        date=date_obj,
                        students=[]
                    )

                # Map existing students by student_id
                existing_students = {stu['student_id']: stu for stu in attendance.students}
                updated_students = []
                all_students_marked = True

                for student in students:
                    student_id = student.get("student_id")
                    new_status = student.get("status")

                    if not student_id or not new_status:
                        return Response(
                            {"message": "student_id and status are required for each student"},
                            status=http_status.HTTP_400_BAD_REQUEST
                        )

                    if new_status not in ['present', 'absent', 'not_marked']:
                        return Response(
                            {"message": "Invalid status"},
                            status=http_status.HTTP_400_BAD_REQUEST
                        )

                    student_data = existing_students.get(student_id, {
                        "student_id": student_id,
                        "name": student.get("name", ""),
                        "email": student.get("email", ""),
                        "phone": student.get("phone", ""),
                        "status": new_status,
                        "present_count": 0,
                        "percentage": 0.0
                    })

                    student_data['status'] = new_status

                    if new_status == 'not_marked':
                        all_students_marked = False

                    updated_students.append(student_data)

                attendance.students = updated_students
                attendance.save()

                # Update ClassWorkingDay
                class_working_day, _ = ClassWorkingDay.objects.get_or_create(
                    school_id=school_id,
                    class_number=class_number,
                    defaults={'working_days': {}}
                )
                class_working_day.working_days[date_obj.isoformat()] = all_students_marked
                class_working_day.save()

                # Update total working days count
                class_obj.total_working_days = sum(
                    1 for marked in class_working_day.working_days.values() if marked
                )
                class_obj.save()

                # Recalculate present counts for all students
                all_attendances = Attendance.objects.filter(
                    school_id=school_id,
                    class_number=class_number,
                    date__gte=class_obj.start_date,
                    date__lte=date.today()
                ).order_by('date')

                student_present_counts = {
                    stu.student_id: 0
                    for stu in Student.objects.filter(school_id=school_id, class_assigned=class_number)
                }

                for att in all_attendances:
                    for student in att.students:
                        student_id = student['student_id']
                        if student.get('status') == 'present' and student_id in student_present_counts:
                            student_present_counts[student_id] += 1

                for att in all_attendances:
                    needs_save = False
                    for student in att.students:
                        student_id = student['student_id']
                        current_present_count = student_present_counts.get(student_id, 0)

                        if student.get('present_count', 0) != current_present_count:
                            student['present_count'] = current_present_count
                            student['percentage'] = round(
                                (current_present_count / class_obj.total_working_days) * 100, 2
                            ) if class_obj.total_working_days > 0 else 0.0
                            needs_save = True

                    if needs_save:
                        att.save()

                return Response(
                    {
                        "message": f"Attendance for class {class_number} on {date_obj} updated successfully",
                        "data": AttendanceSerializer(attendance).data
                    },
                    status=http_status.HTTP_200_OK
                )

        except IntegrityError:
            retry_count += 1
            if retry_count >= max_retries:
                return Response(
                    {"message": "Failed to update attendance after multiple attempts. Please try again."},
                    status=http_status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            continue
        except Exception as e:
            # Log the full traceback for debugging
            print("Exception occurred in update_class_attendance:")
            print(traceback.format_exc())
            return Response(
                {"message": f"An error occurred: {str(e)}"},
                status=http_status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    return Response(
        {"message": "Unexpected error occurred"},
        status=http_status.HTTP_500_INTERNAL_SERVER_ERROR
    )


@api_view(['GET'])
def get_attendance(request):
    class_number = request.GET.get('class_number')
    school_id = request.GET.get('school_id')
    date_str = request.GET.get('date')

    if not all([class_number, school_id, date_str]):
        return Response({"message": "school_id, class_number, and date are required"}, 
                      status=http_status.HTTP_400_BAD_REQUEST)

    date_obj = parse_date(date_str)
    if not date_obj:
        return Response({"message": "Invalid date format. Use YYYY-MM-DD."}, 
                      status=http_status.HTTP_400_BAD_REQUEST)

    try:
        attendance = Attendance.objects.get(class_number=class_number, school_id=school_id, date=date_obj)
        
        # Get student IDs already in attendance
        existing_ids = {student['student_id'] for student in attendance.students}

        # Get all current students of that class
        all_students = Student.objects.filter(school_id=school_id, class_assigned=class_number)

        new_students_added = False
        for student in all_students:
            if student.student_id not in existing_ids:
                attendance.students.append({
                    "student_id": student.student_id,
                    "name": student.full_name,
                    "email": student.email,
                    "phone": student.phone,
                    "status": "not_marked",
                    "present_count": 0,
                    "percentage": 0.0
                })
                new_students_added = True

        if new_students_added:
            attendance.save()

    except Attendance.DoesNotExist:
        # Instead of modifying request.data, create a new dictionary
        attendance_data = {
            "school": School.objects.get(id=school_id).name,
            "school_id": school_id,
            "class_number": class_number,
            "date": date_str,
            "students": [
                {
                    "student_id": student.student_id,
                    "name": student.full_name,
                    "email": student.email,
                    "phone": student.phone,
                    "status": "not_marked",
                    "present_count": 0,
                    "percentage": 0.0
                }
                for student in Student.objects.filter(school_id=school_id, class_assigned=class_number)
            ]
        }
        
        factory = APIRequestFactory()
        new_request = factory.post('/attendance/', attendance_data, format='json')
        new_request.user = request.user
        new_request.auth = request.auth
        
        return add_attendance(new_request)

    serializer = AttendanceSerializer(attendance)
    return Response(serializer.data, status=http_status.HTTP_200_OK)


@api_view(['POST'])
def send_attendance_alert(request):
    student_id = request.data.get("student_id")
    present_count = request.data.get("present_count")
    percentage = request.data.get("percentage")

    if not student_id or percentage is None or present_count is None:
        return Response({"message": "student_id, present_count, and percentage are required"}, status=http_status.HTTP_400_BAD_REQUEST)

    try:
        student = Student.objects.get(student_id=student_id)
    except Student.DoesNotExist:
        return Response({"message": "Student not found"}, status=http_status.HTTP_404_NOT_FOUND)

    try:
        class_obj = Class.objects.get(class_number=student.class_assigned, school_id=student.school_id)
        total_working_days = class_obj.total_working_days
    except Class.DoesNotExist:
        total_working_days = 0  # fallback

    email_subject = "📉 Low Attendance Alert from EduMet"
    email_context = {
        'name': student.full_name,
        'student_id': student.student_id,
        'present_count': present_count,
        'total_working_days': total_working_days,
        'percentage': percentage,
        'current_year': datetime.datetime.now().year
    }

    send_email_sync(
        subject=email_subject,
        template_name='emails/low_attendance_alert.html',
        context=email_context,
        recipient_email=student.email
    )

    return Response({"message": f"Low attendance alert sent to {student.email}"}, status=http_status.HTTP_200_OK)
