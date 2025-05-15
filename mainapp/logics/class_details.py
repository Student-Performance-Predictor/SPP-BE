from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from ..models import Class, Teacher
from ..serializers import ClassSerializer
from django.shortcuts import get_object_or_404


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_assigned_class(request):
    try:
        teacher = Teacher.objects.get(user=request.user, type="class_teacher")
    except Teacher.DoesNotExist:
        return Response({"error": "You are not a class teacher."}, status=status.HTTP_403_FORBIDDEN)

    if not teacher.class_assigned:
        return Response({"error": "No class assigned to this teacher."}, status=status.HTTP_404_NOT_FOUND)

    class_obj = get_object_or_404(Class, class_number=teacher.class_assigned, school_id=teacher.school_id)

    class_obj.update_total_working_days()
    serializer = ClassSerializer(class_obj)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_assigned_class(request):
    try:
        teacher = Teacher.objects.get(user=request.user, type="class_teacher")
    except Teacher.DoesNotExist:
        return Response({"error": "You are not a class teacher."}, status=status.HTTP_403_FORBIDDEN)

    if not teacher.class_assigned:
        return Response({"error": "No class assigned to this teacher."}, status=status.HTTP_404_NOT_FOUND)

    class_obj = get_object_or_404(Class, class_number=teacher.class_assigned,school_id=teacher.school_id)
    serializer = ClassSerializer(class_obj, data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({"message": "Class Details updated successfully"}, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_class_details(request, class_number):
    teacher = Teacher.objects.get(user=request.user)
    print(teacher)
    class_obj = get_object_or_404(Class, class_number=class_number, school_id=teacher.school_id)
    print(class_obj)

    class_obj.update_total_working_days()
    serializer = ClassSerializer(class_obj)
    return Response(serializer.data, status=status.HTTP_200_OK)
