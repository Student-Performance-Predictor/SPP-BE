from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from sppml.predict import predict_single, predict_bulk
from ..models import Student, Teacher
from rest_framework.parsers import MultiPartParser
import pandas as pd
import io


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser])
def predict_bulk_final_grades(request):
    school_id = request.query_params.get("school_id")
    if not school_id:
        return Response({"error": "school_id is required."}, status=status.HTTP_400_BAD_REQUEST)

    if 'file' not in request.FILES:
        return Response({"error": "No file uploaded."}, status=status.HTTP_400_BAD_REQUEST)
    
    csv_file = request.FILES['file']
    
    try:
        # Read the CSV file into a DataFrame
        df = pd.read_csv(io.StringIO(csv_file.read().decode('utf-8')))
        
        # Map the CSV columns to the expected feature names
        column_mapping = {
            'attendance_percentage': 'Attendance_Percentage',
            'parental_education': 'Parental_Education',
            'study_hours': 'Study_Hours_Per_Week',
            'failures': 'Failures',
            'extracurricular': 'Extra_Curricular',
            'participation': 'Participation_Score',
            'rating': 'Teacher_Rating',
            'discipline': 'Discipline_Issues',
            'late_submissions': 'Late_Submissions',
            'prev_grade1': 'Previous_Grade_1',
            'prev_grade2': 'Previous_Grade_2'
        }
        
        # Rename columns and keep only the ones we need
        df = df.rename(columns=column_mapping)
        features = [
            'Attendance_Percentage',
            'Parental_Education',
            'Study_Hours_Per_Week',
            'Failures',
            'Extra_Curricular',
            'Participation_Score',
            'Teacher_Rating',
            'Discipline_Issues',
            'Late_Submissions',
            'Previous_Grade_1',
            'Previous_Grade_2'
        ]
        
        prediction_df = df[features].copy()
        
        # Call the predict_bulk function
        result_df = predict_bulk(prediction_df, from_csv=False)
        
        if result_df.empty:
            return Response({"error": "Bulk prediction failed."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Update final_grade with predicted values instead of creating new column
        df["final_grade"] = result_df["Predicted_Final_Grade"]

        # Save predictions to database
        success_count = 0
        for _, row in df.iterrows():
            try:
                student = Student.objects.get(
                    student_id=row['student_id'],
                    school_id=school_id
                )
                student.final_grade = row['final_grade']
                student.save()
                success_count += 1
            except Student.DoesNotExist:
                continue
        
        # Convert the DataFrame to a list of dictionaries for the response
        response_data = df.to_dict('records')
        
        return Response({
            "message": f"Successfully predicted grades for {success_count}/{len(df)} students",
            "data": response_data
        }, status=status.HTTP_200_OK)
        
    except pd.errors.EmptyDataError:
        return Response({"error": "The CSV file is empty."}, status=status.HTTP_400_BAD_REQUEST)
    except pd.errors.ParserError:
        return Response({"error": "Invalid CSV file format."}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def predict_final_grade(request):
    student_id = request.query_params.get("student_id")

    if not student_id:
        return Response({"error": "student_id is required."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        student = Student.objects.get(student_id=student_id)

        student_data = {
            "Attendance_Percentage": student.attendance_percentage,
            "Parental_Education": student.parental_education,
            "Study_Hours_Per_Week": student.study_hours,
            "Failures": student.failures,
            "Extra_Curricular": student.extracurricular,
            "Participation_Score": student.participation,
            "Teacher_Rating": student.rating,
            "Discipline_Issues": student.discipline,
            "Late_Submissions": student.late_submissions,
            "Previous_Grade_1": student.prev_grade1,
            "Previous_Grade_2": student.prev_grade2
        }
        
        prediction = predict_single(student_data)
        
        if prediction is None:
            return Response({"error": "Prediction failed."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        student.final_grade = prediction
        student.save()

        student_details = {
            "student_id": student.student_id,
            "full_name": student.full_name,
            "attendance_percentage": student.attendance_percentage,
            "parental_education": student.parental_education,
            "study_hours": student.study_hours,
            "failures": student.failures,
            "extracurricular": student.extracurricular,
            "participation": student.participation,
            "rating": student.rating,
            "discipline": student.discipline,
            "late_submissions": student.late_submissions,
            "prev_grade1": student.prev_grade1,
            "prev_grade2": student.prev_grade2,
            "final_grade": student.final_grade
        }

        return Response(student_details, status=status.HTTP_200_OK)

    except Student.DoesNotExist:
        return Response({"error": "Student not found."}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def reset_final_grades(request):
    """
    Resets the final_grade of all students in the given class_number and school_id to 0.
    """
    school_id = request.query_params.get("school_id")
    class_number = request.query_params.get("class_number")

    if not school_id or not class_number:
        return Response(
            {"error": "Both 'school_id' and 'class_number' query parameters are required."},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Bulk update all students of that class to set final_grade = 0
    updated_count = Student.objects.filter(class_assigned=class_number, school_id=school_id).update(final_grade=0)

    return Response(
        {"message": f"Final grades reset to 0 for {updated_count} students."},
        status=status.HTTP_200_OK
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def predict_random_student_grade(request):
    """
    This API takes the student data (attendance, etc.), ensures the user is a teacher,
    and predicts the grade for a random student using the provided data.
    """
    # Ensure the user is a teacher
    user = request.user
    try:
        teacher = Teacher.objects.get(user=user)
    except Teacher.DoesNotExist:
        return Response({"error": "Only teachers can access this API."}, status=status.HTTP_403_FORBIDDEN)
    
    # Get the data from the request
    student_data = {
        "Attendance_Percentage": request.data.get("Attendance_Percentage"),
        "Parental_Education": request.data.get("Parental_Education"),
        "Study_Hours_Per_Week": request.data.get("Study_Hours_Per_Week"),
        "Failures": request.data.get("Failures"),
        "Extra_Curricular": request.data.get("Extra_Curricular"),
        "Participation_Score": request.data.get("Participation_Score"),
        "Teacher_Rating": request.data.get("Teacher_Rating"),
        "Discipline_Issues": request.data.get("Discipline_Issues"),
        "Late_Submissions": request.data.get("Late_Submissions"),
        "Previous_Grade_1": request.data.get("Previous_Grade_1"),
        "Previous_Grade_2": request.data.get("Previous_Grade_2")
    }

    # Predict the grade using the provided data
    prediction = predict_single(student_data)

    # Select a random student (for the sake of this example)
    random_student = Student.objects.filter(school_id=teacher.school_id).order_by("?").first()

    if not random_student:
        return Response({"error": "No students found in the system."}, status=status.HTTP_404_NOT_FOUND)

    # Prepare the response data
    student_details = {
        "attendance_percentage": random_student.attendance_percentage,
        "parental_education": random_student.parental_education,
        "study_hours": random_student.study_hours,
        "failures": random_student.failures,
        "extracurricular": random_student.extracurricular,
        "participation": random_student.participation,
        "rating": random_student.rating,
        "discipline": random_student.discipline,
        "late_submissions": random_student.late_submissions,
        "prev_grade1": random_student.prev_grade1,
        "prev_grade2": random_student.prev_grade2,
        "final_grade": prediction
    }

    return Response({
        "message": "Successfully predicted the grade for a random student.",
        "data": student_details
    }, status=status.HTTP_200_OK)
