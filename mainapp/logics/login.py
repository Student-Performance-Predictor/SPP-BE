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
