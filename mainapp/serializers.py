from rest_framework import serializers
from .models import School, Teacher

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