from rest_framework import serializers
from .models import School, Teacher, Attendance

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()

class SchoolSerializer(serializers.ModelSerializer):
    class Meta:
        model = School
        fields = '__all__'

class TeacherSerializer(serializers.ModelSerializer):
    date_of_birth = serializers.DateField(input_formats=['%d-%m-%Y'])
    class Meta:
        model = Teacher
        # fields = '__all__'
        exclude = ['user','type']

class StudentAttendanceSerializer(serializers.Serializer):
    name = serializers.CharField()
    student_id = serializers.CharField()
    email = serializers.EmailField()
    phone = serializers.CharField()
    status = serializers.ChoiceField(choices=['present', 'absent', 'not_marked'])
    present_count = serializers.IntegerField(required=False)
    percentage = serializers.FloatField(required=False)

class AttendanceSerializer(serializers.ModelSerializer):
    students = StudentAttendanceSerializer(many=True)

    class Meta:
        model = Attendance
        fields = '__all__'
