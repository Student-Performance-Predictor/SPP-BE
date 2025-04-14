from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import login, validate_token
from .views import add_school, view_school, update_school, delete_school

urlpatterns = [
    # Login APIs
    path('login/', login, name='login'),
    path('validate-token/', validate_token),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),

    # CRUD APIs of schools
    path('addSchool/', add_school, name='add_school'),
    path('viewSchool/<int:pk>/', view_school, name='view_school'),
    path('updateSchool/<int:pk>/', update_school, name='update_school'),
    path('deleteSchool/<int:pk>/', delete_school, name='delete_school'),

    # CRUD APIs of principals

]
