from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import login, validate_token
from .views import get_all_schools, get_school_names_with_id, add_school, view_school, update_school, delete_school
from .views import add_principal, view_principal, update_principal, delete_principal

urlpatterns = [
    # Login APIs
    path('login/', login, name='login'),
    path('validate-token/', validate_token),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),

    # CRUD APIs of schools
    path('getAllSchools/', get_all_schools, name='get_all_schools'),
    path('getSchoolsNames/', get_school_names_with_id, name='get_school_names_with_id'),
    path('addSchool/', add_school, name='add_school'),
    path('viewSchool/<int:pk>/', view_school, name='view_school'),
    path('updateSchool/<int:pk>/', update_school, name='update_school'),
    path('deleteSchool/<int:pk>/', delete_school, name='delete_school'),

    # CRUD APIs of principals
    path('addPrincipal/', add_principal, name='add_principal'),
    path('viewPrincipal/<int:pk>/', view_principal, name='view_principal'),
    path('updatePrincipal/<int:pk>/', update_principal, name='update_principal'),
    path('deletePrincipal/<int:pk>/', delete_principal, name='delete_principal'),

]
