from django.contrib.auth import authenticate
from ..models import Teacher, EmailOTP
import random, datetime
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from ..serializers import LoginSerializer
from rest_framework import status
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from .email import send_email_background
from django.conf import settings
from cryptography.fernet import InvalidToken

User = get_user_model()

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
            return Response({"error": "Invalid credentials"}, status=401)

        user = authenticate(email=email, password=password)

        if user is None:
            return Response({"error": "Invalid credentials"}, status=401)

        try:
            teacher = Teacher.objects.get(user=user)
        except Teacher.DoesNotExist:
            return Response({"error": "Account is not linked to teacher"}, status=401)

        user_type = teacher.type
        user_id = teacher.id
        mfa_enabled = teacher.mfa_enabled

        if not mfa_enabled:
            refresh = RefreshToken.for_user(user)
            return Response({
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "type": user_type,
                "id": user_id,
                "mfa": False,
                "message": "Login successful"
            }, status=200)

        otp = create_otp_for_user(user)

        context = {"otp": otp, "name": teacher.name, "current_year": timezone.now().year}
        send_email_background(
            subject="Your EduMet Login OTP",
            template_name="emails/otp_email.html",
            context=context,
            recipient_email=email
        )

        return Response({
            "message": f"OTP sent to {email}",
            "mfa": True,
            "email": email,
            "id": user_id,
            "type": user_type
        }, status=200)

    return Response(serializer.errors, status=400)

# OTP Functionality
def generate_otp():
    return str(random.randint(100000, 999999))

def encrypt_otp(otp: str) -> str:
    fernet = settings.FERNET
    return fernet.encrypt(otp.encode()).decode()

def decrypt_otp(encrypted_otp: str) -> str:
    fernet = settings.FERNET
    try:
        return fernet.decrypt(encrypted_otp.encode()).decode()
    except InvalidToken:
        return None

def create_otp_for_user(user):
    otp = generate_otp()
    encrypted = encrypt_otp(otp)
    expiry = timezone.now() + datetime.timedelta(minutes=10)

    EmailOTP.objects.update_or_create(
        user=user,
        defaults={"otp_encrypted": encrypted, "expires_at": expiry}
    )

    return otp

@api_view(["POST"])
def resend_otp(request):
    email = request.data.get("email")

    if not email:
        return Response({"error": "Email is required"}, status=400)

    try:
        user = User.objects.get(email=email)
        teacher = Teacher.objects.get(user=user)
        otp_obj = EmailOTP.objects.get(user=user)
    except:
        return Response({"error": "User not found"}, status=404)

    if not teacher.mfa_enabled:
        return Response({"error": "MFA is not enabled"}, status=400)

    otp_obj.otp = generate_otp()
    otp_obj.expires_at = timezone.now() + datetime.timedelta(minutes=10)
    otp_obj.save()

    context = {"otp": otp_obj.otp, "name": teacher.name, "current_year": timezone.now().year}
    
    send_email_background(
        subject="Your EduMet Login OTP (Resent)",
        template_name="emails/otp_email.html",
        context=context,
        recipient_email=email
    )

    return Response({"message": "OTP resent successfully"})

@api_view(["POST"])
def verify_otp(request):
    email = request.data.get("email")
    otp_entered = request.data.get("otp")

    if not email or not otp_entered:
        return Response({"error": "Email and OTP are required"}, status=400)

    try:
        user = User.objects.get(email=email)
        teacher = Teacher.objects.get(user=user)
        otp_obj = EmailOTP.objects.get(user=user)
    except:
        return Response({"error": "Invalid request"}, status=404)

    if timezone.now() > otp_obj.expires_at:
        return Response({"error": "OTP expired"}, status=400)

    decrypted_otp = decrypt_otp(otp_obj.otp_encrypted)

    if not decrypted_otp or decrypted_otp != otp_entered:
        return Response({"error": "Invalid OTP"}, status=400)

    otp_obj.delete()

    # Issue JWT tokens
    refresh = RefreshToken.for_user(user)

    return Response({
        "message": "OTP verified successfully",
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "type": teacher.type,
        "id": teacher.id,
        "mfa": True
    }, status=200)

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
