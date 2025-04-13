from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import login, validate_token

urlpatterns = [
    # Login APIs
    path('login/', login, name='login'),
    path('validate-token/', validate_token),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),

    # CRUD APIs of schools

    # CRUD APIs of principals
    
]
