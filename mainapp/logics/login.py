from django.contrib.auth import authenticate
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from ..serializers import LoginSerializer
from rest_framework import status
from rest_framework.response import Response
from django.contrib.auth import get_user_model
User = get_user_model()
from ..models import Teacher 

# Login with Email and Password
@api_view(["POST"])
def login(request):
    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid():
        email = serializer.validated_data["email"].lower().strip()
        password = serializer.validated_data["password"]

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)
        
        user = authenticate(email=email, password=password)

        if user is not None:
            try:
                teacher = Teacher.objects.get(user=user)
                user_type = teacher.type
                user_id = teacher.id
            except Teacher.DoesNotExist:
                user_type = "unknown"
                user_id = None

            refresh = RefreshToken.for_user(user)
            return Response({
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "type": user_type,
                "id": user_id
            })
        else:
            return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Validate Token
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def validate_token(request):
    """
    Function-based view to validate JWT token.
    """
    return Response({"valid": True}, status=status.HTTP_200_OK)

@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def update_password(request):
    """
    API to update the password of the logged-in user.
    Expected fields: old_password, new_password, confirm_password
    """
    user = request.user
    data = request.data

    old_password = data.get("old_password")
    new_password = data.get("new_password")
    confirm_password = data.get("confirm_password")

    # Check all fields are provided
    if not old_password or not new_password or not confirm_password:
        return Response(
            {"error": "All fields (old_password, new_password, confirm_password) are required."},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Check old password is correct
    if not user.check_password(old_password):
        return Response(
            {"error": "Old password is incorrect."},
            status=status.HTTP_401_UNAUTHORIZED
        )

    # Check new and confirm passwords match
    if new_password != confirm_password:
        return Response(
            {"error": "New password and confirm password do not match."},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Optional: Check if new password is different from old
    if old_password == new_password:
        return Response(
            {"error": "New password must be different from the old password."},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Optional: Add custom password policy (e.g., min length)
    if len(new_password) < 8:
        return Response(
            {"error": "New password must be at least 8 characters long."},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Update password
    user.set_password(new_password)
    user.save()

    return Response({"message": "Password updated successfully."}, status=status.HTTP_200_OK)
