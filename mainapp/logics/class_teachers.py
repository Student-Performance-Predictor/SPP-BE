from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from ..serializers import TeacherSerializer
from ..models import Teacher, Class
from ..logics.email import send_email_sync
from django.contrib.auth import get_user_model
User = get_user_model()
import os, datetime

# Get All Teachers
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_all_class_teachers(request):
    teachers = Teacher.objects.filter(type="class_teacher")
    serializer = TeacherSerializer(teachers, many=True)
    return Response(serializer.data)


# Add Teacher
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_class_teacher(request):
    serializer = TeacherSerializer(data=request.data)
    if serializer.is_valid():
        teacher_data = serializer.validated_data
        teacher_data["name"] = teacher_data["name"].title()
        username = teacher_data["name"].lower().replace(" ", "")
        email = teacher_data["email"].lower().strip()
        class_assigned = teacher_data["class_assigned"]
        
        if User.objects.filter(email=email).exists():
            return Response({"error": "User with this email already exists"}, status=status.HTTP_400_BAD_REQUEST)
        
        if class_assigned:
            if Teacher.objects.filter(school=teacher_data["school"], school_id=teacher_data["school_id"], class_assigned=class_assigned, type="class_teacher").exists():
                return Response({"error": f"A class teacher for Class '{class_assigned}' already exists."}, status=status.HTTP_400_BAD_REQUEST)
        
        user = User.objects.create(username=username, email=email)
        
        teacher = Teacher.objects.create(
            user=user,
            name=teacher_data["name"],
            type="class_teacher",
            phone=teacher_data["phone"],
            email=teacher_data["email"],
            date_of_birth=teacher_data["date_of_birth"],
            school=teacher_data["school"],
            school_id=teacher_data["school_id"],
            address=teacher_data["address"],
            city=teacher_data["city"],
            state=teacher_data["state"],
            pincode=teacher_data["pincode"],
            profile_image=teacher_data.get("profile_image"),
            class_assigned=teacher_data.get("class_assigned")  # ⚡ Important
        )

        # After teacher is created and before password is set
        class_assigned = teacher.class_assigned
        if class_assigned:
            Class.objects.get_or_create(
                school = teacher.school,
                school_id = teacher.school_id,
                class_number=class_assigned,
                defaults={
                    'total_working_days': 0,
                    'threshold': 0
                }
            )

        
        year = teacher.date_of_birth.year
        password = f"{teacher.name.title().split(' ')[0]}@{year}{teacher.id}"
        user.set_password(password)
        user.save()

        email_subject = "EduMet Account Login Credentials"
        email_context = {
            'type': 'Class Teacher',
            'name': teacher.name,
            'email': teacher.email,
            'username': username,
            'password': password,
            'school': teacher.school,
            'current_year': datetime.datetime.now().year
        }

        send_email_sync(
            subject=email_subject,
            template_name='emails/welcome_email.html',
            context=email_context,
            recipient_email=email
        )

        return Response({
            "message": "Class Teacher credentials sent to his/her mail address!",
            "data": TeacherSerializer(teacher).data
        }, status=status.HTTP_201_CREATED)

    return Response({
        "message": "Failed to add class teacher.",
        "errors": serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


# View Teacher by Id
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def view_class_teacher(request, pk):
    try:
        teacher = Teacher.objects.get(pk=pk, type="class_teacher")
    except Teacher.DoesNotExist:
        return Response({"error": "Class Teacher not found"}, status=status.HTTP_404_NOT_FOUND)
    
    serializer = TeacherSerializer(teacher)
    return Response(serializer.data)


# Update Teacher by Id
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_class_teacher(request, pk):
    try:
        teacher = Teacher.objects.get(pk=pk, type="class_teacher")
    except Teacher.DoesNotExist:
        return Response({"error": "Class Teacher not found"}, status=status.HTTP_404_NOT_FOUND)
    
    serializer = TeacherSerializer(teacher, data=request.data)
    if serializer.is_valid():
        serializer.save()
        user = teacher.user
        if "name" in serializer.validated_data:
            user.username = serializer.validated_data["name"].lower().replace(" ", "")
        if "email" in serializer.validated_data:
            user.email = serializer.validated_data["email"]
        user.save()
        return Response({"message": "Class Teacher updated successfully!"}, status=status.HTTP_200_OK)

    return Response({
        "message": "Failed to update class teacher.",
        "errors": serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


# Delete Teacher by Id
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_class_teacher(request, pk):
    try:
        teacher = Teacher.objects.get(pk=pk, type="class_teacher")
    except Teacher.DoesNotExist:
        return Response({"error": "Class Teacher not found"}, status=status.HTTP_404_NOT_FOUND)

    # Delete the class associated with this teacher (if any)
    related_class = Class.objects.filter(class_number=teacher.class_assigned).first()
    if related_class:
        related_class.delete()

    # Delete teacher's profile image if exists
    if teacher.profile_image and os.path.isfile(teacher.profile_image.path):
        os.remove(teacher.profile_image.path)

    teacher.user.delete()

    # Send email
    email_subject = "Goodbye from EduMet - Account Has Been Permanently Removed"
    email_context = {
        'name': teacher.name,
        'email': teacher.email,
        'current_year': datetime.datetime.now().year
    }

    send_email_sync(
        subject=email_subject,
        template_name='emails/delete_teacher.html',
        context=email_context,
        recipient_email=teacher.email
    )

    return Response({"message": "Class Teacher deleted successfully"}, status=status.HTTP_200_OK)


# Get Teacher Details from Access Token
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_teacher_from_token(request):
    try:
        teacher = Teacher.objects.get(user=request.user, type="class_teacher")
    except Teacher.DoesNotExist:
        return Response({"error": "Teacher not found or you are not a class teacher."}, status=status.HTTP_404_NOT_FOUND)
    
    serializer = TeacherSerializer(teacher)
    return Response(serializer.data, status=status.HTTP_200_OK)


# Get All Teachers in the Same School
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_class_teachers_by_school(request):
    try:
        # Get the logged-in teacher or admin
        requesting_teacher = Teacher.objects.get(user=request.user)
    except Teacher.DoesNotExist:
        return Response({"error": "You are not registered as a teacher."}, status=status.HTTP_404_NOT_FOUND)

    teachers = Teacher.objects.filter(school_id=requesting_teacher.school_id, type="class_teacher")
    serializer = TeacherSerializer(teachers, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)
