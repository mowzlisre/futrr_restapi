from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import authenticate
from django.db import IntegrityError
import requests
from .models import FutrrUser, Follow, PasswordResetToken, TwoFactorDevice
from django.db.models import Q
from django.utils import timezone
import secrets
import pyotp
from app.s3 import upload_file, generate_presigned_url as s3_presign


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
                    "is_email_verified": user.is_email_verified
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
        user = request.user
        return Response(
            {
                "id": str(user.id),
                "email": user.email,
                "username": user.username,
                "phone": user.phone,
                "avatar": _presign_avatar(user.avatar),
                "bio": user.bio,
                "timezone": user.timezone,
                "notification_email": user.notification_email,
                "notification_push": user.notification_push,
                "is_email_verified": user.is_email_verified,
                "is_phone_verified": user.is_phone_verified,
                "two_factor_enabled": user.two_factor_enabled,
                "capsules_sealed": user.capsules_sealed,
                "capsules_unlocked": user.capsules_unlocked,
                "followers_count": user.followers.count(),
                "following_count": user.following.count(),
                "created_at": user.created_at,
            }
        )

    @staticmethod
    @api_view(["PATCH"])
    @permission_classes([IsAuthenticated])
    def update_me(request):
        user = request.user
        allowed_fields = ["username", "bio", "timezone", "notification_email", "notification_push", "avatar"]
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


def _serialize_user(user, request_user=None, following_ids=None):
    if following_ids is not None:
        is_following = user.id in following_ids
    elif request_user and request_user.id != user.id:
        is_following = Follow.objects.filter(follower=request_user, following=user).exists()
    else:
        is_following = False

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
        from app.models import Capsule
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
        return Response(data)


class FollowView:
    """
    POST   /users/:id/follow/   — follow a user
    DELETE /users/:id/follow/   — unfollow a user
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

        _, created = Follow.objects.get_or_create(follower=request.user, following=target)
        if created:
            # Create in-app notification for the followed user
            from app.models import Notification
            Notification.objects.create(
                user=target,
                notif_type="recipient_added",
                title=f"@{request.user.username} started following you",
                body="",
            )
        return Response({"following": True}, status=status.HTTP_200_OK)

    @staticmethod
    @api_view(["DELETE"])
    @permission_classes([IsAuthenticated])
    def unfollow(request, user_id):
        Follow.objects.filter(follower=request.user, following_id=user_id).delete()
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
