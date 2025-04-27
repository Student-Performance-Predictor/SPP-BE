from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .logics.login import login, validate_token
from .logics.schools import get_all_schools, get_school_names_with_id, add_school, view_school, update_school, delete_school
from .logics.principals import get_all_principals, add_principal, view_principal, update_principal, delete_principal
from .logics.class_teachers import get_all_class_teachers, add_class_teacher, view_class_teacher, update_class_teacher, delete_class_teacher

urlpatterns = [
    # Login APIs
    path('login/', login, name='login'),
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

    # CRUD APIs of class teachers
    path('getAllTeachers/', get_all_class_teachers, name='get_all_principals'),
    path('addTeacher/', add_class_teacher, name='add_principal'),
    path('viewTeacher/<int:pk>/', view_class_teacher, name='view_principal'),
    path('updateTeacher/<int:pk>/', update_class_teacher, name='update_principal'),
    path('deleteTeacher/<int:pk>/', delete_class_teacher, name='delete_principal'),
]
