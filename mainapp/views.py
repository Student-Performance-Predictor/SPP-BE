from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import LoginSerializer, SchoolSerializer, TeacherSerializer
from .models import Teacher, School
from django.contrib.auth import get_user_model
User = get_user_model()
import os, datetime
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags

def send_email_sync(subject, template_name, context, recipient_email):
    try:
        html_content = render_to_string(template_name, context)
        text_content = strip_tags(html_content)  # Plain text version of the email body
        email = EmailMultiAlternatives(
            subject,
            text_content,
            'EduMet <noreply@edumet.in>',
            [recipient_email],
        )

        email.attach_alternative(html_content, "text/html")
        email.send()
        
    except Exception as e:
        error_message = f"Email sending failed for {recipient_email}. Error: {e}"
        print(error_message)

@api_view(["POST"])
def login(request):
    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid():
        email = serializer.validated_data["email"].lower().strip()
        password = serializer.validated_data["password"]

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)
        
        user = authenticate(username=user.username, password=password)

        if user is not None:
            try:
                teacher = Teacher.objects.get(user=user)
                user_type = teacher.type
                user_id = teacher.id
            except Teacher.DoesNotExist:
                user_type = "unknown"
                user_id = None

            refresh = RefreshToken.for_user(user)
            return Response({
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "type": user_type,
                "id": user_id
            })
        else:
            return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def validate_token(request):
    """
    Function-based view to validate JWT token.
    """
    return Response({"valid": True}, status=status.HTTP_200_OK)

# Get all schools names
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_school_names_with_id(request):
    schools = School.objects.all().values("id", "name")
    return Response({
        "schools": list(schools)
    }, status=status.HTTP_200_OK)

# Get all Schools
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_all_schools(request):
    schools = School.objects.all()
    serializer = SchoolSerializer(schools, many=True)
    return Response(serializer.data)

# Add School
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def add_school(request):
    serializer = SchoolSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(
            {
                "message":"School added successfully!",
                "data":serializer.data
            },status=status.HTTP_201_CREATED)
    return Response({
        "message": "Failed to add school.",
        "errors": serializer.errors
    },status=status.HTTP_400_BAD_REQUEST)

# View School by Id
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def view_school(request, pk):
    try:
        school = School.objects.get(pk=pk)
    except School.DoesNotExist:
        return Response({"error":"School not found"},status=status.HTTP_404_NOT_FOUND)
    serializer = SchoolSerializer(school)
    return Response(serializer.data)

# Update School by Id
@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def update_school(request, pk):
    try:
        school = School.objects.get(pk=pk)
    except School.DoesNotExist:
        return Response({"error":"School not found"},status=status.HTTP_404_NOT_FOUND)
    serializer = SchoolSerializer(school,data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({"message":"School updated successfully!"},status=status.HTTP_200_OK)
    return Response({
        "message": "Failed to add school.",
        "errors": serializer.errors
    },status=status.HTTP_400_BAD_REQUEST)

# Delete School by Id
@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_school(request, pk):
    try:
        school = School.objects.get(pk=pk)
    except School.DoesNotExist:
        return Response({"error":"School not found"},status=status.HTTP_404_NOT_FOUND)
    school.delete()
    return Response({"message":"School deleted successfully"},status=status.HTTP_204_NO_CONTENT)

# Add Principal
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_principal(request):
    serializer = TeacherSerializer(data=request.data)
    if serializer.is_valid():
        teacher_data = serializer.validated_data
        teacher_data["name"] = teacher_data["name"].title()
        username = teacher_data["name"].lower().replace(" ","")
        email = teacher_data["email"].lower().strip()
        if User.objects.filter(email=email).exists():
            return Response({"error": "User with this email already exists"}, status=status.HTTP_400_BAD_REQUEST)
        
        user = User.objects.create(username=username,email=email)
        teacher = Teacher.objects.create(
            user=user,
            name = teacher_data["name"],
            type = "principal",
            phone_number = teacher_data["phone_number"],
            email = teacher_data["email"],
            date_of_birth = teacher_data["date_of_birth"],
            school = teacher_data["school"],
            address = teacher_data["address"],
            city = teacher_data["city"],
            state = teacher_data["state"],
            pincode = teacher_data["pincode"],
            profile_image = teacher_data.get("profile_image")
        )
        year = teacher.date_of_birth.year
        password = f"{teacher.name.title().split(" ")[0]}@{year}{teacher.id}"
        user.set_password(password)
        user.save()

        email_subject = "EduMet Account Login Credentials"
        email_context = {
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

        return Response(TeacherSerializer(teacher).data,status=status.HTTP_201_CREATED)
    return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)

# View Principal by Id
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def view_principal(request, pk):
    try:
        teacher = Teacher.objects.get(pk=pk,type="principal")
    except Teacher.DoesNotExist:
        return Response({"error":"Principal not found"},status=status.HTTP_404_NOT_FOUND)
    serializer = TeacherSerializer(teacher)
    return Response(serializer.data)

# Update Principal by Id
@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def update_principal(request, pk):
    try:
        teacher = Teacher.objects.get(pk=pk,type="principal")
    except Teacher.DoesNotExist:
        return Response({"error":"Principal not found"},status=status.HTTP_404_NOT_FOUND)
    serializer = TeacherSerializer(teacher,data=request.data)
    if serializer.is_valid():
        serializer.save()
        user = teacher.user
        if "name" in serializer.validated_data:
            user.username = serializer.validated_data["name"].lower().replace(" ","")
        if "email" in serializer.validated_data:
            user.email = serializer.validated_data["email"]
        user.save()
        return Response({"message":"Principal updated successfully!"},status=status.HTTP_200_OK)
    return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)

# Delete Principal by Id
@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_principal(request, pk):
    try:
        teacher = Teacher.objects.get(pk=pk,type="principal")
    except Teacher.DoesNotExist:
        return Response({"error":"Principal not found"},status=status.HTTP_404_NOT_FOUND)
    if teacher.profile_image and os.path.isfile(teacher.profile_image.path):
        os.remove(teacher.profile_image.path)
    teacher.user.delete()
    return Response({"message":"Principal deleted Successfully"},status=status.HTTP_204_NO_CONTENT)
