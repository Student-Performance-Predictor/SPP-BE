from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .logics.login import login, validate_token, update_password
from .logics.schools import get_all_schools, get_school_names_with_id, add_school, view_school, update_school, delete_school
from .logics.principals import get_all_principals, add_principal, view_principal, update_principal, delete_principal, get_principal_from_token
from .logics.class_teachers import get_all_class_teachers, add_class_teacher, view_class_teacher, update_class_teacher, delete_class_teacher, get_teacher_from_token, get_class_teachers_by_school
from .logics.students import get_all_class_students, get_all_students, add_student, view_student, update_student, delete_student, export_students, import_students
from .logics.class_details import get_assigned_class, update_assigned_class, get_class_details
from .logics.attendance import get_attendance, add_attendance, update_class_attendance, send_attendance_alert
from .logics.predict import predict_final_grade, predict_bulk_final_grades, reset_final_grades, predict_random_student_grade

urlpatterns = [
    # Login APIs
    path('login/', login, name='login'),
    path('updatePassword/', update_password, name='update_password'),
    path('validate-token/', validate_token),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),

    # CRUD APIs of schools
    path('getAllSchools/', get_all_schools, name='get_all_schools'),
    path('getSchoolNames/', get_school_names_with_id, name='get_school_names_with_id'),
    path('addSchool/', add_school, name='add_school'),
    path('viewSchool/<int:pk>/', view_school, name='view_school'),
    path('updateSchool/<int:pk>/', update_school, name='update_school'),
    path('deleteSchool/<int:pk>/', delete_school, name='delete_school'),

    # CRUD APIs of principals
    path('getAllPrincipals/', get_all_principals, name='get_all_principals'),
    path('addPrincipal/', add_principal, name='add_principal'),
    path('viewPrincipal/<int:pk>/', view_principal, name='view_principal'),
    path('updatePrincipal/<int:pk>/', update_principal, name='update_principal'),
    path('deletePrincipal/<int:pk>/', delete_principal, name='delete_principal'),
    path('principal/me/', get_principal_from_token, name='get_principal_from_token'),

    # CRUD APIs of class teachers
    path('getAllTeachers/', get_all_class_teachers, name='get_all_principals'),
    path('addTeacher/', add_class_teacher, name='add_principal'),
    path('viewTeacher/<int:pk>/', view_class_teacher, name='view_principal'),
    path('updateTeacher/<int:pk>/', update_class_teacher, name='update_principal'),
    path('deleteTeacher/<int:pk>/', delete_class_teacher, name='delete_principal'),
    path('teacher/me/', get_teacher_from_token, name='get_teacher_from_token'),
    path('getAllSchoolTeachers/', get_class_teachers_by_school, name='get_class_teachers_by_school'),

    # CRUD APIs of students
    path('getAllStudents/', get_all_students, name='get_all_students'),
    path('getAllClassStudents/<str:class_number>/', get_all_class_students, name='get_all_class_students'),
    path('addStudent/', add_student, name='add_student'),
    path('viewStudent/<int:pk>/', view_student, name='view_student'),
    path('updateStudent/<int:pk>/', update_student, name='update_student'),
    path('deleteStudent/<int:pk>/', delete_student, name='delete_student'),
    path('exportStudents/', export_students, name='export-students'),
    path('importStudents/', import_students, name='import-students'),

    # Class Details APIs
    path('classAssigned/', get_assigned_class, name='get_assigned_class'),
    path('classDetails/<str:class_number>/', get_class_details, name='get_class_details'),
    path('updateClass/', update_assigned_class, name='update_assigned_class'),

    # Attendance APIs
    path('attendance/', get_attendance, name='get_attendance'),
    path('addAttendance/', add_attendance, name='add_attendance'),
    path('updateClassAttendance/', update_class_attendance, name='update_class_attendance'),
    path('send-alert/', send_attendance_alert, name='send_attendance_alert'),

    # Predict Final Grade API
    path('predictStudent/', predict_final_grade, name='predict_final_grade'),
    path("predictRandom/", predict_random_student_grade, name="predict_random_student_grade"),
    path("predictStduentBulk/", predict_bulk_final_grades, name="predict_bulk_final_grades"),
    path("resetFinalGrades/", reset_final_grades, name="reset_final_grades"),
]
