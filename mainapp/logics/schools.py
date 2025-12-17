from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from ..serializers import SchoolSerializer
from ..models import School
from django.contrib.auth import get_user_model
User = get_user_model()

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
    return Response({"message":"School deleted successfully!"},status=status.HTTP_200_OK)
