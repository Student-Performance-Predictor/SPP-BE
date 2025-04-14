from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import LoginSerializer, SchoolSerializer
from .models import Teacher, School

@api_view(["POST"])
def login(request):
    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid():
        username = serializer.validated_data["username"]
        password = serializer.validated_data["password"]

        user = authenticate(username=username, password=password)

        if user is not None:
            try:
                teacher = Teacher.objects.get(user=user)
                user_type = teacher.type
            except Teacher.DoesNotExist:
                user_type = "unknown"

            refresh = RefreshToken.for_user(user)
            return Response({
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "type": user_type
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

# Add School
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def add_school(request):
    serializer = SchoolSerializer(data=request.data)
    print(request)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data,status=status.HTTP_201_CREATED)
    return Response(serializer.data,status=status.HTTP_400_BAD_REQUEST)

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
    return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST) 

# Delete School by Id
@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_school(request, pk):
    try:
        school = School.objects.get(pk=pk)
    except School.DoesNotExist:
        return Response({"error":"School not found"},status=status.HTTP_404_NOT_FOUND)
    school.delete()
    return Response({"message":"School Deleted Successfully"},status=status.HTTP_204_NO_CONTENT) 