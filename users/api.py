from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import authenticate
from django.db import IntegrityError
import requests
from .models import FutrrUser, Follow, FollowRequest, PasswordResetToken, TwoFactorDevice, EmailOTP
from django.db.models import Q
from django.utils import timezone
import secrets
import random
import pyotp
from app.s3 import upload_file, generate_presigned_url as s3_presign
from .emails import send_otp_email, send_welcome_email


class SignUpView:
    """Handle user sign up"""
    
    @staticmethod
    @api_view(['POST'])
    @permission_classes([AllowAny])
    def signup(request):
        """
        Register a new user.
        Expected fields: email, username, password
        """
        try:
            email = request.data.get('email')
            username = request.data.get('username')
            password = request.data.get('password')
            print(f"Received signup data: email={email}, username={username}, password={password}")
            # Validate required fields
            if not all([email, username, password]):
                return Response(
                    {"error": "Email, username, and password are required"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check email format
            if '@' not in email or '.' not in email:
                return Response(
                    {"error": "Invalid email format"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check password length
            if len(password) < 8:
                return Response(
                    {"error": "Password must be at least 8 characters long"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Create user
            user = FutrrUser.objects.create_user(
                email=email,
                username=username,
                password=password
            )
            
            # Generate tokens
            refresh = RefreshToken.for_user(user)
            
            return Response(
                {
                    "message": "User created successfully",
                    "user": {
                        "id": str(user.id),
                        "email": user.email,
                        "username": user.username
                    },
                    "tokens": {
                        "refresh": str(refresh),
                        "access": str(refresh.access_token)
                    }
                },
                status=status.HTTP_201_CREATED
            )
        
        except IntegrityError as e:
            if 'email' in str(e):
                return Response(
                    {"error": "Email already exists"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            elif 'username' in str(e):
                return Response(
                    {"error": "Username already exists"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            return Response(
                {"error": "User creation failed"},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class LoginView:
    """Handle user login"""

    @staticmethod
    @api_view(['POST'])
    @permission_classes([AllowAny])
    def login(request):

        identifier = request.data.get('identifier') 
        password = request.data.get('password')

        if not identifier or not password:
            return Response(
                {"error": "Username/Email and password are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = FutrrUser.objects.filter(
            Q(email__iexact=identifier) | Q(username__iexact=identifier) | Q(phone__iexact=identifier)
        ).first()

        if not user:
            return Response(
                {"error": "Invalid credentials"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if not user.check_password(password):
            return Response(
                {"error": "Invalid credentials"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if not user.is_active:
            return Response(
                {"error": "User account is disabled"},
                status=status.HTTP_403_FORBIDDEN
            )

        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "message": "Login successful",
                "user": {
                    "id": str(user.id),
                    "email": user.email,
                    "username": user.username,
                    "is_email_verified": user.is_email_verified,
                    "isPreboarded": user.isPreboarded,
                },
                "tokens": {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token)
                }
            },
            status=status.HTTP_200_OK
        )

class LogoutView:
    """Handle user logout"""
    
    @staticmethod
    @api_view(['POST'])
    @permission_classes([IsAuthenticated])
    def logout(request):
        """
        Logout user by blacklisting refresh token.
        Expected fields: refresh token in request body
        """
        try:
            refresh_token = request.data.get('refresh')
            
            if not refresh_token:
                return Response(
                    {"error": "Refresh token is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            try:
                token = RefreshToken(refresh_token)
                token.blacklist()
            except Exception as e:
                return Response(
                    {"error": "Invalid token"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            return Response(
                {"message": "Logout successful"},
                status=status.HTTP_200_OK
            )
        
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class OAuthView:
    """Handle OAuth authentication"""
    
    @staticmethod
    @api_view(['POST'])
    @permission_classes([AllowAny])
    def google_oauth(request):
        """
        Authenticate user with Google OAuth token.
        Expected fields: id_token (Google OAuth token)
        """
        try:
            id_token = request.data.get('id_token')
            
            if not id_token:
                return Response(
                    {"error": "Google OAuth token is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Verify token with Google
            google_url = "https://www.googleapis.com/oauth2/v1/tokeninfo"
            params = {"id_token": id_token}
            
            response = requests.get(google_url, params=params)
            
            if response.status_code != 200:
                return Response(
                    {"error": "Invalid Google token"},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            google_data = response.json()
            email = google_data.get('email')
            
            if not email:
                return Response(
                    {"error": "Could not retrieve email from Google"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get or create user
            user, created = FutrrUser.objects.get_or_create(
                email=email,
                defaults={
                    'username': email.split('@')[0],
                    'is_email_verified': True
                }
            )
            
            # Generate tokens
            refresh = RefreshToken.for_user(user)
            
            return Response(
                {
                    "message": "Google OAuth login successful",
                    "user": {
                        "id": str(user.id),
                        "email": user.email,
                        "username": user.username,
                        "created": created
                    },
                    "tokens": {
                        "refresh": str(refresh),
                        "access": str(refresh.access_token)
                    }
                },
                status=status.HTTP_200_OK
            )
        
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @staticmethod
    @api_view(['POST'])
    @permission_classes([AllowAny])
    def github_oauth(request):
        """
        Authenticate user with GitHub OAuth code.
        Expected fields: code (GitHub OAuth authorization code)
        """
        try:
            code = request.data.get('code')
            client_id = request.data.get('client_id')
            client_secret = request.data.get('client_secret')
            
            if not all([code, client_id, client_secret]):
                return Response(
                    {"error": "Code, client_id, and client_secret are required"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Exchange code for access token
            token_url = "https://github.com/login/oauth/access_token"
            token_data = {
                "client_id": client_id,
                "client_secret": client_secret,
                "code": code
            }
            headers = {"Accept": "application/json"}
            
            token_response = requests.post(token_url, data=token_data, headers=headers)
            
            if token_response.status_code != 200:
                return Response(
                    {"error": "Failed to exchange code for token"},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            token_data = token_response.json()
            access_token = token_data.get('access_token')
            
            if not access_token:
                return Response(
                    {"error": "Could not retrieve access token from GitHub"},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            # Get user info from GitHub
            user_url = "https://api.github.com/user"
            user_headers = {
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/vnd.github.v3+json"
            }
            
            user_response = requests.get(user_url, headers=user_headers)
            
            if user_response.status_code != 200:
                return Response(
                    {"error": "Failed to retrieve user info from GitHub"},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            github_user = user_response.json()
            github_email = github_user.get('email') or f"{github_user.get('login')}@github.local"
            github_username = github_user.get('login')
            
            # Get or create user
            user, created = FutrrUser.objects.get_or_create(
                email=github_email,
                defaults={
                    'username': github_username or github_email.split('@')[0],
                    'is_email_verified': True if github_user.get('email') else False
                }
            )
            
            # Generate tokens
            refresh = RefreshToken.for_user(user)
            
            return Response(
                {
                    "message": "GitHub OAuth login successful",
                    "user": {
                        "id": str(user.id),
                        "email": user.email,
                        "username": user.username,
                        "created": created
                    },
                    "tokens": {
                        "refresh": str(refresh),
                        "access": str(refresh.access_token)
                    }
                },
                status=status.HTTP_200_OK
            )
        
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PasswordResetView:
    """Handle password reset requests and password updates"""

    @staticmethod
    @api_view(['POST'])
    @permission_classes([AllowAny])
    def forget_password(request):
        """
        Request password reset token.
        Token will be printed to console (for development).
        Expected fields: email
        """
        try:
            email = request.data.get('email')

            if not email:
                return Response(
                    {"error": "Email is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            try:
                user = FutrrUser.objects.get(email=email)
            except FutrrUser.DoesNotExist:
                # Don't reveal if email exists or not
                return Response(
                    {"message": "If email exists, password reset link has been sent"},
                    status=status.HTTP_200_OK
                )

            # Create password reset token
            reset_token = PasswordResetToken.objects.create(user=user)

            # Print token to console (for development purposes)
            print(f"\n{'='*60}")
            print(f"PASSWORD RESET TOKEN FOR: {user.email}")
            print(f"Token: {reset_token.token}")
            print(f"Expires at: {reset_token.expires_at}")
            print(f"{'='*60}\n")

            return Response(
                {
                    "message": "Password reset token has been created",
                    "token": reset_token.token,  # Include in response for testing
                    "expires_in_minutes": 60
                },
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @staticmethod
    @api_view(['POST'])
    @permission_classes([AllowAny])
    def reset_password(request):
        """
        Reset password using token.
        Expected fields: token, new_password, confirm_password
        """
        try:
            token = request.data.get('token')
            new_password = request.data.get('new_password')
            confirm_password = request.data.get('confirm_password')

            # Validate required fields
            if not all([token, new_password, confirm_password]):
                return Response(
                    {"error": "Token, new_password, and confirm_password are required"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Check password match
            if new_password != confirm_password:
                return Response(
                    {"error": "Passwords do not match"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Check password length
            if len(new_password) < 8:
                return Response(
                    {"error": "Password must be at least 8 characters long"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Validate token
            try:
                reset_token = PasswordResetToken.objects.get(token=token)
            except PasswordResetToken.DoesNotExist:
                return Response(
                    {"error": "Invalid token"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Check if token is valid
            if not reset_token.is_valid():
                return Response(
                    {"error": "Token has expired or already used"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Update password
            user = reset_token.user
            user.set_password(new_password)
            user.save()

            # Mark token as used
            reset_token.is_used = True
            reset_token.save()

            return Response(
                {"message": "Password reset successfully"},
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class TwoFactorView:
    """Handle 2FA device management"""

    @staticmethod
    @api_view(['POST'])
    @permission_classes([IsAuthenticated])
    def add_device(request):
        """
        Add a new 2FA device.
        Expected fields: device_type, device_name
        device_type options: 'totp', 'sms', 'email'
        """
        try:
            device_type = request.data.get('device_type')
            device_name = request.data.get('device_name')

            # Validate required fields
            if not all([device_type, device_name]):
                return Response(
                    {"error": "device_type and device_name are required"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Validate device type
            valid_types = ['totp', 'sms', 'email']
            if device_type not in valid_types:
                return Response(
                    {"error": f"Invalid device_type. Must be one of: {', '.join(valid_types)}"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Check if device with same name exists
            if TwoFactorDevice.objects.filter(user=request.user, device_name=device_name).exists():
                return Response(
                    {"error": "Device with this name already exists"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Create device
            device = TwoFactorDevice.objects.create(
                user=request.user,
                device_type=device_type,
                device_name=device_name
            )

            response_data = {
                "message": "2FA device added successfully",
                "device": {
                    "id": device.id,
                    "device_type": device.device_type,
                    "device_name": device.device_name,
                    "is_verified": device.is_verified
                }
            }

            # For TOTP, generate QR code secret
            if device_type == 'totp':
                totp = pyotp.TOTP(device.secret)
                response_data["device"]["secret"] = device.secret
                response_data["device"]["provisioning_uri"] = totp.provisioning_uri(
                    name=request.user.email,
                    issuer_name='Futrr'
                )
                response_data["message"] = "2FA device added. Scan QR code to verify."

            print(f"\n{'='*60}")
            print(f"2FA Device Created for: {request.user.email}")
            print(f"Device Type: {device_type}")
            print(f"Device Name: {device_name}")
            if device_type == 'totp':
                print(f"Secret: {device.secret}")
            print(f"{'='*60}\n")

            return Response(response_data, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @staticmethod
    @api_view(['POST'])
    @permission_classes([IsAuthenticated])
    def remove_device(request):
        """
        Remove a 2FA device.
        Expected fields: device_id
        """
        try:
            device_id = request.data.get('device_id')

            if not device_id:
                return Response(
                    {"error": "device_id is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            try:
                device = TwoFactorDevice.objects.get(id=device_id, user=request.user)
            except TwoFactorDevice.DoesNotExist:
                return Response(
                    {"error": "Device not found"},
                    status=status.HTTP_404_NOT_FOUND
                )

            device_name = device.device_name
            device.delete()

            # If this was the primary device and user had 2FA enabled, disable it if no other devices
            if not TwoFactorDevice.objects.filter(user=request.user, is_verified=True).exists():
                request.user.two_factor_enabled = False
                request.user.save()

            return Response(
                {"message": f"Device '{device_name}' removed successfully"},
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @staticmethod
    @api_view(['POST'])
    @permission_classes([IsAuthenticated])
    def verify_device(request):
        """
        Verify a 2FA device with OTP code.
        Expected fields: device_id, code
        """
        try:
            device_id = request.data.get('device_id')
            code = request.data.get('code')

            if not all([device_id, code]):
                return Response(
                    {"error": "device_id and code are required"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            try:
                device = TwoFactorDevice.objects.get(id=device_id, user=request.user)
            except TwoFactorDevice.DoesNotExist:
                return Response(
                    {"error": "Device not found"},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Verify code based on device type
            if device.device_type == 'totp':
                totp = pyotp.TOTP(device.secret)
                if not totp.verify(code):
                    return Response(
                        {"error": "Invalid OTP code"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            else:
                # For SMS/Email, code verification would be done through other means
                # For now, we'll just accept it
                pass

            # Mark device as verified
            device.is_verified = True
            device.save()

            # Enable 2FA on user account
            request.user.two_factor_enabled = True
            request.user.save()

            return Response(
                {
                    "message": "2FA device verified successfully",
                    "device": {
                        "id": device.id,
                        "device_name": device.device_name,
                        "device_type": device.device_type,
                        "is_verified": True
                    }
                },
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @staticmethod
    @api_view(['GET'])
    @permission_classes([IsAuthenticated])
    def list_devices(request):
        """List all 2FA devices for the user"""
        try:
            devices = TwoFactorDevice.objects.filter(user=request.user)

            device_list = [
                {
                    "id": device.id,
                    "device_type": device.device_type,
                    "device_name": device.device_name,
                    "is_primary": device.is_primary,
                    "is_verified": device.is_verified,
                    "created_at": device.created_at,
                    "last_used_at": device.last_used_at
                }
                for device in devices
            ]

            return Response(
                {
                    "devices": device_list,
                    "total": devices.count(),
                    "verified_count": devices.filter(is_verified=True).count()
                },
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ChangePasswordView:
    """Handle password change for authenticated users"""

    @staticmethod
    @api_view(['POST'])
    @permission_classes([IsAuthenticated])
    def change_password(request):
        """
        Change password for authenticated user.
        Expected fields: old_password, new_password, confirm_password
        """
        try:
            old_password = request.data.get('old_password')
            new_password = request.data.get('new_password')
            confirm_password = request.data.get('confirm_password')

            # Validate required fields
            if not all([old_password, new_password, confirm_password]):
                return Response(
                    {"error": "old_password, new_password, and confirm_password are required"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Verify old password
            if not request.user.check_password(old_password):
                return Response(
                    {"error": "Old password is incorrect"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Check passwords match
            if new_password != confirm_password:
                return Response(
                    {"error": "Passwords do not match"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Check password length
            if len(new_password) < 8:
                return Response(
                    {"error": "Password must be at least 8 characters long"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Update password
            request.user.set_password(new_password)
            request.user.save()

            return Response(
                {"message": "Password changed successfully"},
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class UserProfileView:
    """GET /users/me/ and PATCH /users/me/"""

    @staticmethod
    @api_view(["GET"])
    @permission_classes([IsAuthenticated])
    def get_me(request):
        from app.models import CapsulePin
        user = request.user
        return Response(
            {
                "id": str(user.id),
                "email": user.email,
                "username": user.username,
                "first_name": user.first_name,
                "isPreboarded": user.isPreboarded,
                "date_of_birth": user.date_of_birth.isoformat() if user.date_of_birth else None,
                "country": user.country,
                "phone": user.phone,
                "avatar": _presign_avatar(user.avatar),
                "bio": user.bio,
                "timezone": user.timezone,
                "notification_email": user.notification_email,
                "notification_push": user.notification_push,
                "is_private": user.is_private,
                "is_email_verified": user.is_email_verified,
                "is_phone_verified": user.is_phone_verified,
                "two_factor_enabled": user.two_factor_enabled,
                "capsules_sealed": user.capsules_sealed,
                "capsules_unlocked": user.capsules_unlocked,
                "followers_count": user.followers.count(),
                "following_count": user.following.count(),
                "pinned_count": CapsulePin.objects.filter(user=user).count(),
                "created_at": user.created_at,
            }
        )

    @staticmethod
    @api_view(["PATCH"])
    @permission_classes([IsAuthenticated])
    def update_me(request):
        user = request.user
        allowed_fields = ["username", "bio", "timezone", "notification_email", "notification_push", "is_private", "avatar"]
        for field in allowed_fields:
            if field in request.data:
                setattr(user, field, request.data[field])
        try:
            user.save()
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"message": "Profile updated"})


class DeleteAccountView:
    """DELETE /auth/delete-account/"""

    @staticmethod
    @api_view(["DELETE"])
    @permission_classes([IsAuthenticated])
    def delete_account(request):
        """
        Permanently delete the authenticated user's account.
        - All capsules they created → BROKEN (via pre_delete signal)
        - Their recipient rows → removed (via pre_delete signal)
        Requires password confirmation.
        """
        password = request.data.get("password")
        if not password:
            return Response(
                {"error": "Password confirmation is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not request.user.check_password(password):
            return Response(
                {"error": "Incorrect password"},
                status=status.HTTP_403_FORBIDDEN,
            )
        request.user.delete()
        return Response({"message": "Account deleted"}, status=status.HTTP_200_OK)


def _serialize_user(user, request_user=None, following_ids=None, pending_ids=None):
    if following_ids is not None:
        is_following = user.id in following_ids
    elif request_user and request_user.id != user.id:
        is_following = Follow.objects.filter(follower=request_user, following=user).exists()
    else:
        is_following = False

    if pending_ids is not None:
        follow_request_pending = user.id in pending_ids
    elif request_user and request_user.id != user.id and not is_following:
        follow_request_pending = FollowRequest.objects.filter(
            from_user=request_user, to_user=user, status=FollowRequest.STATUS_PENDING
        ).exists()
    else:
        follow_request_pending = False

    # Use pre-annotated counts when available (avoids N+1 in list views)
    fc_ann = getattr(user, "followers_count_ann", None)
    followers_count = fc_ann if fc_ann is not None else user.followers.count()
    fg_ann = getattr(user, "following_count_ann", None)
    following_count = fg_ann if fg_ann is not None else user.following.count()

    return {
        "id": str(user.id),
        "username": user.username,
        "avatar": _presign_avatar(user.avatar),
        "bio": user.bio,
        "followers_count": followers_count,
        "following_count": following_count,
        "capsules_sealed": user.capsules_sealed,
        "is_following": is_following,
        "is_private": user.is_private,
        "follow_request_pending": follow_request_pending,
    }


class UserSearchView:
    """
    GET /users/search/?q=<query>
    Search users by username. Returns top 20 matches, excluding the requesting user.
    """

    @staticmethod
    @api_view(["GET"])
    @permission_classes([IsAuthenticated])
    def search(request):
        from django.db.models import Count
        q = request.query_params.get("q", "").strip()
        if not q:
            return Response([])
        users = list(
            FutrrUser.objects.filter(username__icontains=q)
            .exclude(id=request.user.id)
            .annotate(
                followers_count_ann=Count("followers", distinct=True),
                following_count_ann=Count("following", distinct=True),
            )[:20]
        )
        following_ids = set(
            Follow.objects.filter(
                follower=request.user, following_id__in=[u.id for u in users]
            ).values_list("following_id", flat=True)
        )
        return Response([_serialize_user(u, request.user, following_ids=following_ids) for u in users])


class PublicUserProfileView:
    """
    GET /users/:id/  — public profile of any user
    """

    @staticmethod
    @api_view(["GET"])
    @permission_classes([IsAuthenticated])
    def get_user(request, user_id):
        from app.models import Capsule, CapsulePin
        try:
            user = FutrrUser.objects.get(id=user_id)
        except FutrrUser.DoesNotExist:
            return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        data = _serialize_user(user, request.user)
        # Attach public capsules for the profile view
        public_capsules = Capsule.objects.filter(
            created_by=user, is_public=True
        ).order_by("-created_at")[:12]
        data["public_capsules"] = [
            {
                "id": str(c.id),
                "title": c.title,
                "status": c.status,
                "unlock_at": c.unlock_at.isoformat() if c.unlock_at else None,
            }
            for c in public_capsules
        ]
        # Attach pinned capsules for the profile view
        pinned_capsules = Capsule.objects.filter(
            pinned_by__user=user, is_public=True
        ).select_related("created_by").order_by("-pinned_by__created_at")[:12]
        data["pinned_capsules"] = [
            {
                "id": str(c.id),
                "title": c.title,
                "status": c.status,
                "unlock_at": c.unlock_at.isoformat() if c.unlock_at else None,
                "created_by_username": c.created_by.username if c.created_by else None,
            }
            for c in pinned_capsules
        ]
        data["pinned_count"] = CapsulePin.objects.filter(user=user).count()
        return Response(data)


class FollowView:
    """
    POST   /users/:id/follow/   — follow a user (or send request if private)
    DELETE /users/:id/follow/   — unfollow / cancel follow request
    GET    /users/me/followers/  — list my followers
    GET    /users/me/following/  — list users I follow
    """

    @staticmethod
    @api_view(["POST"])
    @permission_classes([IsAuthenticated])
    def follow(request, user_id):
        if str(request.user.id) == str(user_id):
            return Response({"error": "Cannot follow yourself"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            target = FutrrUser.objects.get(id=user_id)
        except FutrrUser.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        # Already following?
        if Follow.objects.filter(follower=request.user, following=target).exists():
            return Response({"following": True}, status=status.HTTP_200_OK)

        if target.is_private:
            # Create or return existing follow request
            _, created = FollowRequest.objects.get_or_create(
                from_user=request.user, to_user=target,
                defaults={"status": FollowRequest.STATUS_PENDING},
            )
            if created:
                from app.models import Notification
                Notification.objects.create(
                    user=target,
                    notif_type="recipient_added",
                    title=f"@{request.user.username} requested to follow you",
                    body="",
                )
            return Response({"following": False, "pending": True}, status=status.HTTP_200_OK)

        _, created = Follow.objects.get_or_create(follower=request.user, following=target)
        if created:
            from app.models import Notification
            Notification.objects.create(
                user=target,
                notif_type="recipient_added",
                title=f"@{request.user.username} started following you",
                body="",
            )
        return Response({"following": True, "pending": False}, status=status.HTTP_200_OK)

    @staticmethod
    @api_view(["DELETE"])
    @permission_classes([IsAuthenticated])
    def unfollow(request, user_id):
        Follow.objects.filter(follower=request.user, following_id=user_id).delete()
        # Also cancel any pending follow request
        FollowRequest.objects.filter(from_user=request.user, to_user_id=user_id).delete()
        return Response({"following": False}, status=status.HTTP_200_OK)

    @staticmethod
    @api_view(["GET"])
    @permission_classes([IsAuthenticated])
    def followers(request):
        from django.db.models import Count
        follower_ids = list(
            Follow.objects.filter(following=request.user).values_list("follower_id", flat=True)
        )
        users = list(
            FutrrUser.objects.filter(id__in=follower_ids)
            .annotate(
                followers_count_ann=Count("followers", distinct=True),
                following_count_ann=Count("following", distinct=True),
            )
        )
        # Which of these followers does request.user also follow back?
        following_ids = set(
            Follow.objects.filter(
                follower=request.user, following_id__in=follower_ids
            ).values_list("following_id", flat=True)
        )
        return Response([_serialize_user(u, request.user, following_ids=following_ids) for u in users])

    @staticmethod
    @api_view(["GET"])
    @permission_classes([IsAuthenticated])
    def following(request):
        from django.db.models import Count
        following_id_list = list(
            Follow.objects.filter(follower=request.user).values_list("following_id", flat=True)
        )
        users = list(
            FutrrUser.objects.filter(id__in=following_id_list)
            .annotate(
                followers_count_ann=Count("followers", distinct=True),
                following_count_ann=Count("following", distinct=True),
            )
        )
        # All these users are followed by request.user
        following_ids = set(following_id_list)
        return Response([_serialize_user(u, request.user, following_ids=following_ids) for u in users])


class FollowRequestView:
    """
    GET    /users/me/follow-requests/         — list pending requests I received
    POST   /users/follow-requests/:id/accept/ — accept a request
    DELETE /users/follow-requests/:id/reject/ — reject / cancel a request
    """

    @staticmethod
    @api_view(["GET"])
    @permission_classes([IsAuthenticated])
    def list_requests(request):
        reqs = FollowRequest.objects.filter(
            to_user=request.user, status=FollowRequest.STATUS_PENDING
        ).select_related("from_user").order_by("-created_at")
        data = [
            {
                "id": r.id,
                "from_user": {
                    "id": str(r.from_user.id),
                    "username": r.from_user.username,
                    "avatar": _presign_avatar(r.from_user.avatar),
                    "bio": r.from_user.bio,
                },
                "created_at": r.created_at,
            }
            for r in reqs
        ]
        return Response(data, status=status.HTTP_200_OK)

    @staticmethod
    @api_view(["POST"])
    @permission_classes([IsAuthenticated])
    def accept_request(request, request_id):
        try:
            req = FollowRequest.objects.get(
                id=request_id, to_user=request.user, status=FollowRequest.STATUS_PENDING
            )
        except FollowRequest.DoesNotExist:
            return Response({"error": "Request not found"}, status=status.HTTP_404_NOT_FOUND)

        Follow.objects.get_or_create(follower=req.from_user, following=request.user)
        req.delete()

        from app.models import Notification
        Notification.objects.create(
            user=req.from_user,
            notif_type="recipient_added",
            title=f"@{request.user.username} accepted your follow request",
            body="",
        )
        return Response({"accepted": True}, status=status.HTTP_200_OK)

    @staticmethod
    @api_view(["DELETE"])
    @permission_classes([IsAuthenticated])
    def reject_request(request, request_id):
        FollowRequest.objects.filter(id=request_id, to_user=request.user).delete()
        return Response({"rejected": True}, status=status.HTTP_200_OK)


class EmailOTPView:
    """OTP-based email verification for registration."""

    @staticmethod
    @api_view(["POST"])
    @permission_classes([AllowAny])
    def send_otp(request):
        email = request.data.get("email", "").strip().lower()
        if not email or "@" not in email or "." not in email:
            return Response({"error": "Valid email address required"}, status=status.HTTP_400_BAD_REQUEST)

        # Invalidate any existing unused OTPs for this email
        EmailOTP.objects.filter(email=email, is_used=False).update(is_used=True)

        otp = f"{random.randint(100000, 999999)}"
        record = EmailOTP.objects.create(email=email, otp=otp)

        try:
            send_otp_email(email, otp)
        except Exception as e:
            print(f"[OTP EMAIL FAILED] {email}: {e}")

        return Response({"message": "Verification code sent"}, status=status.HTTP_200_OK)

    @staticmethod
    @api_view(["POST"])
    @permission_classes([AllowAny])
    def verify_otp(request):
        email = request.data.get("email", "").strip().lower()
        otp = request.data.get("otp", "").strip()

        if not email or not otp:
            return Response({"error": "Email and code are required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            record = EmailOTP.objects.filter(
                email=email, otp=otp, is_used=False
            ).latest("created_at")
        except EmailOTP.DoesNotExist:
            return Response({"error": "Invalid or expired code"}, status=status.HTTP_400_BAD_REQUEST)

        if not record.is_valid():
            return Response(
                {"error": "Code has expired. Please request a new one."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        token = secrets.token_urlsafe(32)
        record.session_token = token
        record.is_used = True
        record.save(update_fields=["session_token", "is_used"])

        return Response({"verified": True, "session_token": token}, status=status.HTTP_200_OK)


class RegistrationView:
    """Complete registration after email verification."""

    @staticmethod
    @api_view(["GET"])
    @permission_classes([AllowAny])
    def check_username(request):
        import re
        username = request.query_params.get("username", "").strip()
        if not username:
            return Response({"error": "Username required"}, status=status.HTTP_400_BAD_REQUEST)
        if len(username) < 3:
            return Response({"available": False, "reason": "Must be at least 3 characters"})
        if len(username) > 30:
            return Response({"available": False, "reason": "Must be 30 characters or fewer"})
        if not re.match(r'^[a-zA-Z0-9_.]+$', username):
            return Response({"available": False, "reason": "Only letters, numbers, _ and . allowed"})
        available = not FutrrUser.objects.filter(username__iexact=username).exists()
        return Response({"available": available})

    @staticmethod
    @api_view(["POST"])
    @permission_classes([AllowAny])
    def complete_registration(request):
        email = request.data.get("email", "").strip().lower()
        session_token = request.data.get("session_token", "").strip()
        username = request.data.get("username", "").strip()
        password = request.data.get("password", "")

        if not all([email, session_token, username, password]):
            return Response({"error": "All fields are required"}, status=status.HTTP_400_BAD_REQUEST)

        # Validate session token proves email was verified
        try:
            EmailOTP.objects.get(email=email, session_token=session_token, is_used=True)
        except EmailOTP.DoesNotExist:
            return Response(
                {"error": "Email verification expired. Please start over."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if len(password) < 8:
            return Response({"error": "Password must be at least 8 characters"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = FutrrUser.objects.create_user(
                email=email,
                username=username,
                password=password,
                is_email_verified=True,
            )
        except IntegrityError as e:
            err = str(e).lower()
            if "email" in err:
                return Response({"error": "Email already registered"}, status=status.HTTP_400_BAD_REQUEST)
            if "username" in err:
                return Response({"error": "Username already taken"}, status=status.HTTP_400_BAD_REQUEST)
            return Response({"error": "Registration failed"}, status=status.HTTP_400_BAD_REQUEST)

        print(f"[WELCOME EMAIL] Attempting to send to {user.email} ({user.username})")
        try:
            send_welcome_email(user.email, user.username)
            print(f"[WELCOME EMAIL] Sent successfully to {user.email}")
        except Exception as e:
            import traceback
            print(f"[WELCOME EMAIL FAILED] {user.email}: {e}")
            traceback.print_exc()

        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "message": "Account created",
                "user": {
                    "id": str(user.id),
                    "email": user.email,
                    "username": user.username,
                    "isPreboarded": user.isPreboarded,
                    "is_email_verified": user.is_email_verified,
                },
                "tokens": {
                    "access": str(refresh.access_token),
                    "refresh": str(refresh),
                },
            },
            status=status.HTTP_201_CREATED,
        )


class PreboardingView:
    """Complete profile preboarding (steps 4-6 of onboarding)."""

    @staticmethod
    @api_view(["PATCH"])
    @permission_classes([IsAuthenticated])
    def complete(request):
        from datetime import date as date_type

        user = request.user
        first_name = request.data.get("first_name", "").strip()
        date_of_birth = request.data.get("date_of_birth")
        country = request.data.get("country", "").strip()
        tz = request.data.get("timezone", "UTC").strip()
        notification_push = request.data.get("notification_push", True)

        if not first_name:
            return Response({"error": "Name is required"}, status=status.HTTP_400_BAD_REQUEST)
        if not date_of_birth:
            return Response({"error": "Date of birth is required"}, status=status.HTTP_400_BAD_REQUEST)
        if not country:
            return Response({"error": "Country is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            dob = date_type.fromisoformat(date_of_birth)
            today = date_type.today()
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            if age < 18:
                return Response(
                    {"error": "You must be at least 18 years old to use Futrr"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        except ValueError:
            return Response({"error": "Invalid date format. Use YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)

        user.first_name = first_name
        user.date_of_birth = dob
        user.country = country
        user.timezone = tz
        user.notification_push = bool(notification_push)
        user.isPreboarded = True
        user.save(update_fields=["first_name", "date_of_birth", "country", "timezone", "notification_push", "isPreboarded"])

        return Response({"isPreboarded": True, "message": "Welcome to Futrr!"}, status=status.HTTP_200_OK)


# ---------------------------------------------------------------------------
# Avatar helpers
# ---------------------------------------------------------------------------

def _presign_avatar(avatar_value: str | None) -> str | None:
    """
    If avatar_value is an S3 key (starts with 'user_avatars/'), return a
    presigned URL.  Otherwise return as-is (OAuth URLs, None, etc.).
    """
    if avatar_value and avatar_value.startswith("user_avatars/"):
        return s3_presign(avatar_value, expiry_seconds=3600)
    return avatar_value


class AvatarUploadView:
    """POST /users/me/avatar/ — upload a new profile avatar image"""

    @staticmethod
    @api_view(["POST"])
    @permission_classes([IsAuthenticated])
    def upload(request):
        file = request.FILES.get("avatar")
        if not file:
            return Response({"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST)

        allowed_types = {"image/jpeg", "image/png", "image/webp"}
        content_type = file.content_type or "image/jpeg"
        if content_type not in allowed_types:
            return Response(
                {"error": "Only JPEG, PNG, and WebP images are supported"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        ext = content_type.split("/")[-1].replace("jpeg", "jpg")
        s3_key = f"user_avatars/{request.user.id}/avatar.{ext}"

        upload_file(s3_key, file, content_type)

        request.user.avatar = s3_key
        request.user.save(update_fields=["avatar"])

        presigned_url = _presign_avatar(s3_key)
        return Response({"avatar": presigned_url}, status=status.HTTP_200_OK)
