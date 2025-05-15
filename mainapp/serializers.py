from rest_framework import serializers
from .models import School, Teacher, Class, ClassWorkingDay

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

class ClassSerializer(serializers.ModelSerializer):
    class Meta:
        model = Class
        fields = '__all__'

class ClassWorkingDaySerializer(serializers.ModelSerializer):
    class Meta:
        model = ClassWorkingDay
        fields = ['school', 'school_id', 'class_number', 'working_days']

    # SerializerMethodField to dynamically calculate total_working_days
    total_working_days = serializers.SerializerMethodField()

    def get_total_working_days(self, obj):
        # Calculate the total working days based on the `working_days` field
        return sum(1 for day, is_working in obj.working_days.items() if is_working)

class StudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields ='__all__'
