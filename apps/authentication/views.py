import logging
from django.contrib.auth import authenticate
from django.utils import timezone
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from .firebase_auth import verify_firebase_phone_token
from core.responses import success_response, error_response
from core.email import send_otp_email
from apps.users.models import User
from apps.users.serializers import UserProfileSerializer
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator

from .models import OTPRecord, RefreshTokenRecord
from .serializers import (
    RegisterSerializer,
    SendEmailOTPSerializer,
    VerifyEmailOTPSerializer,
    SendPhoneOTPSerializer,
    VerifyPhoneOTPSerializer,
    EmailPasswordLoginSerializer,
    EmailOTPLoginSerializer,
    ChangePasswordSerializer,
    ForgotPasswordSerializer,
    ResetPasswordSerializer,
    LogoutSerializer,
)
from .utils import get_or_create_otp, verify_otp, send_phone_otp
from .google_auth import verify_google_token
from apps.users.virtual_number import (
    generate_virtual_number,
    get_all_station_codes,
)

logger = logging.getLogger("apps")


def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        "access":  str(refresh.access_token),
        "refresh": str(refresh),
    }


# ── Registration ──────────────────────────────────────────────────────────────

class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        record = get_or_create_otp(user.email, OTPRecord.OTPType.EMAIL_VERIFICATION)
        sent   = send_otp_email(user.email, record.otp_code, user.full_name or "User")

        if not sent:
            logger.warning(f"OTP email failed for {user.email}")

        return success_response(
            data={"email": user.email},
            message="Registration successful. Please verify your email.",
            status_code=status.HTTP_201_CREATED,
        )

@method_decorator(
    ratelimit(key="ip", rate="10/m", method="POST", block=True),
    name="post"
)
class FirebasePhoneLoginView(APIView):
    """
    POST /api/v1/auth/firebase/phone/
    
    Flutter Firebase Phone Auth se ID token aata hai.
    Backend verify karta hai → JWT return karta hai.
    
    Body: {"id_token": "firebase-id-token"}
    """
    permission_classes = [AllowAny]

    def post(self, request):
        id_token = request.data.get("id_token")

        if not id_token:
            return error_response(
                message="Firebase ID token required.",
                status_code=400,
            )

        # Firebase se verify karo
        firebase_info = verify_firebase_phone_token(id_token)

        if not firebase_info:
            return error_response(
                message="Invalid Firebase token.",
                status_code=status.HTTP_401_UNAUTHORIZED,
            )

        phone        = firebase_info["phone"]
        firebase_uid = firebase_info["firebase_uid"]

        # User dhundo ya banao
        user = User.objects.filter(phone=phone).first()

        if user:
            # Existing user — update firebase uid
            if not hasattr(user, 'firebase_uid') or not user.firebase_uid:
                user.is_phone_verified = True
                user.save(update_fields=["is_phone_verified"])
            is_new = False
        else:
            # Naya user — auto create
            import random
            import string
            suffix = "".join(random.choices(string.digits, k=6))

            user = User.objects.create_user(
                email             = f"phone_{phone.replace('+', '')}@qabifly.in",
                full_name         = f"User {suffix}",
                phone             = phone,
                role              = User.Role.BUYER,
                is_verified       = True,
                is_phone_verified = True,
            )
            is_new = True

        tokens = get_tokens_for_user(user)

        return success_response(
            data={
                **tokens,
                "user":                UserProfileSerializer(user).data,
                "is_new":             is_new,
                "onboarding_complete": user.onboarding_complete,
            },
            message="Phone login successful.",
        )

# ── Email OTP ─────────────────────────────────────────────────────────────────
@method_decorator(
    ratelimit(key="ip", rate="5/m", method="POST", block=True),
    name="post"
)

class SendEmailOTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = SendEmailOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"].lower().strip()

        user_exists = User.objects.filter(email=email).exists()
        otp_type    = (
            OTPRecord.OTPType.EMAIL_LOGIN
            if user_exists
            else OTPRecord.OTPType.EMAIL_VERIFICATION
        )

        record = get_or_create_otp(email, otp_type)
        name   = "User"
        if user_exists:
            name = User.objects.get(email=email).full_name or "User"

        send_otp_email(email, record.otp_code, name)

        return success_response(
            message=f"OTP sent to {email}."
        )


class VerifyEmailOTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = VerifyEmailOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email    = serializer.validated_data["email"].lower().strip()
        otp_code = serializer.validated_data["otp_code"]

        success, message = verify_otp(
            email, otp_code, OTPRecord.OTPType.EMAIL_VERIFICATION
        )
        if not success:
            return error_response(
                message=message,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user             = User.objects.get(email=email)
            user.is_verified = True
            user.save(update_fields=["is_verified"])
            tokens = get_tokens_for_user(user)
            return success_response(
                data={**tokens, "user": UserProfileSerializer(user).data},
                message="Email verified successfully.",
            )
        except User.DoesNotExist:
            return error_response(
                message="User not found.",
                status_code=status.HTTP_404_NOT_FOUND,
            )


# ── Phone OTP ─────────────────────────────────────────────────────────────────

class SendPhoneOTPView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = SendPhoneOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone = serializer.validated_data["phone"]

        record = get_or_create_otp(phone, OTPRecord.OTPType.PHONE_VERIFICATION)
        sent   = send_phone_otp(phone, record.otp_code)

        if not sent:
            return error_response(
                message="Could not send SMS.",
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        return success_response(message=f"OTP sent to {phone}.")


class VerifyPhoneOTPView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = VerifyPhoneOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone    = serializer.validated_data["phone"]
        otp_code = serializer.validated_data["otp_code"]

        success, message = verify_otp(
            phone, otp_code, OTPRecord.OTPType.PHONE_VERIFICATION
        )
        if not success:
            return error_response(
                message=message,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        user = request.user
        user.phone             = phone
        user.is_phone_verified = True
        user.save(update_fields=["phone", "is_phone_verified"])

        return success_response(message="Phone verified successfully.")


# ── Login ─────────────────────────────────────────────────────────────────────

class EmailPasswordLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = EmailPasswordLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email    = serializer.validated_data["email"].lower().strip()
        password = serializer.validated_data["password"]
        user     = authenticate(request, username=email, password=password)

        if not user:
            return error_response(
                message="Invalid email or password.",
                status_code=status.HTTP_401_UNAUTHORIZED,
            )
        if not user.is_active:
            return error_response(
                message="Account deactivated.",
                status_code=status.HTTP_403_FORBIDDEN,
            )
        if not user.is_verified:
            record = get_or_create_otp(
                email, OTPRecord.OTPType.EMAIL_VERIFICATION
            )
            send_otp_email(email, record.otp_code, user.full_name or "User")
            return error_response(
                message="Email not verified. OTP sent.",
                status_code=status.HTTP_403_FORBIDDEN,
            )

        tokens = get_tokens_for_user(user)
        return success_response(
            data={
                **tokens,
                "user":                UserProfileSerializer(user).data,
                "onboarding_complete": user.onboarding_complete,
            },
            message="Login successful.",
        )


class EmailOTPLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = EmailOTPLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"].lower().strip()

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return error_response(
                message="No account found with this email.",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        if not user.is_active:
            return error_response(
                message="Account deactivated.",
                status_code=status.HTTP_403_FORBIDDEN,
            )

        record = get_or_create_otp(email, OTPRecord.OTPType.EMAIL_LOGIN)
        send_otp_email(email, record.otp_code, user.full_name or "User")

        return success_response(message=f"OTP sent to {email}.")


class EmailOTPLoginVerifyView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = VerifyEmailOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email    = serializer.validated_data["email"].lower().strip()
        otp_code = serializer.validated_data["otp_code"]

        success, message = verify_otp(
            email, otp_code, OTPRecord.OTPType.EMAIL_LOGIN
        )
        if not success:
            return error_response(
                message=message,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return error_response(
                message="User not found.",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        if not user.is_verified:
            user.is_verified = True
            user.save(update_fields=["is_verified"])

        tokens = get_tokens_for_user(user)
        return success_response(
            data={
                **tokens,
                "user":                UserProfileSerializer(user).data,
                "onboarding_complete": user.onboarding_complete,
            },
            message="Login successful.",
        )


# ── Google Login ──────────────────────────────────────────────────────────────
@method_decorator(
    ratelimit(key="ip", rate="5/m", method="POST", block=True),
    name="post"
)

class GoogleLoginView(APIView):
    """
    POST /api/v1/auth/google/
    NextJS:  {"access_token": "..."}
    Flutter: {"id_token": "..."}
    """
    permission_classes = [AllowAny]

    def post(self, request):
        token = (
            request.data.get("access_token") or
            request.data.get("id_token")
        )

        if not token:
            return error_response(
                message="Google token required.",
                status_code=400,
            )

        google_info = verify_google_token(token)
        if not google_info:
            return error_response(
                message="Invalid Google token.",
                status_code=status.HTTP_401_UNAUTHORIZED,
            )

        email     = google_info["email"]
        google_id = google_info["google_id"]
        name      = google_info["name"]

        if not email:
            return error_response(
                message="Google account mein email nahi hai.",
                status_code=400,
            )

        user = User.objects.filter(email=email).first()

        if user:
            if not user.google_id:
                user.google_id     = google_id
                user.auth_provider = User.AuthProvider.GOOGLE
                user.is_verified   = True
                user.save(update_fields=[
                    "google_id", "auth_provider", "is_verified"
                ])
            is_new = False
        else:
            user = User.objects.create_user(
                email         = email,
                full_name     = name,
                google_id     = google_id,
                auth_provider = User.AuthProvider.GOOGLE,
                role          = User.Role.BUYER,
                is_verified   = True,
            )
            is_new = True

        tokens = get_tokens_for_user(user)

        return success_response(
            data={
                **tokens,
                "user":                UserProfileSerializer(user).data,
                "is_new":             is_new,
                "onboarding_complete": user.onboarding_complete,
            },
            message="Google login successful.",
        )


# ── Onboarding ────────────────────────────────────────────────────────────────

class StationCodesView(APIView):
    """GET /api/v1/auth/station-codes/"""
    permission_classes = [AllowAny]

    def get(self, request):
        codes = get_all_station_codes()
        return success_response(data=codes)


class OnboardingView(APIView):
    """POST /api/v1/auth/onboarding/"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user

        if user.onboarding_complete:
            return error_response(
                message="Onboarding already complete.",
                status_code=400,
            )

        virtual_name  = request.data.get("virtual_name",  "").strip()
        village       = request.data.get("village",       "").strip()
        district      = request.data.get("district",      "").strip()
        state         = request.data.get("state", "Uttar Pradesh").strip()
        station_code  = request.data.get("station_code",  "").strip().upper()
        virtual_photo = request.FILES.get("virtual_photo")

        if not virtual_name:
            return error_response(message="Virtual name zaroori hai.", status_code=400)
        if not village:
            return error_response(message="Village zaroori hai.", status_code=400)
        if not district:
            return error_response(message="District zaroori hai.", status_code=400)
        if not station_code:
            return error_response(message="Station code zaroori hai.", status_code=400)

        try:
            virtual_number = generate_virtual_number(station_code)
        except ValueError as e:
            return error_response(message=str(e), status_code=400)

        user.virtual_name        = virtual_name
        user.virtual_number      = virtual_number
        user.station_code        = station_code
        user.village             = village
        user.district            = district
        user.state               = state
        user.city                = village
        user.onboarding_complete = True

        if virtual_photo:
            user.virtual_photo = virtual_photo

        user.save()

        logger.info(f"Onboarding complete: {user.email} → {virtual_number}")

        return success_response(
            data=UserProfileSerializer(user).data,
            message=f"Welcome! Aapka virtual number: {virtual_number}",
        )


class UpdateStationCodeView(APIView):
    """POST /api/v1/auth/update-station/"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        new_code = request.data.get("station_code", "").strip().upper()
        if not new_code:
            return error_response(message="Station code required.", status_code=400)

        user       = request.user
        old_number = user.virtual_number

        try:
            new_number = generate_virtual_number(new_code)
        except ValueError as e:
            return error_response(message=str(e), status_code=400)

        user.station_code   = new_code
        user.virtual_number = new_number
        user.save(update_fields=["station_code", "virtual_number"])

        logger.info(f"Station changed: {user.email} {old_number} → {new_number}")

        return success_response(
            data={"virtual_number": new_number},
            message=f"Virtual number: {new_number}",
        )


# ── Password ──────────────────────────────────────────────────────────────────

class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        if not user.check_password(serializer.validated_data["old_password"]):
            return error_response(
                message="Current password incorrect.",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(serializer.validated_data["new_password"])
        user.save(update_fields=["password"])
        return success_response(message="Password changed.")


class ForgotPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"].lower().strip()

        try:
            user   = User.objects.get(email=email)
            record = get_or_create_otp(email, OTPRecord.OTPType.PASSWORD_RESET)
            send_otp_email(email, record.otp_code, user.full_name or "User")
        except User.DoesNotExist:
            pass

        return success_response(
            message="If registered, reset OTP has been sent."
        )


class ResetPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email        = serializer.validated_data["email"].lower().strip()
        otp_code     = serializer.validated_data["otp_code"]
        new_password = serializer.validated_data["new_password"]

        success, message = verify_otp(
            email, otp_code, OTPRecord.OTPType.PASSWORD_RESET
        )
        if not success:
            return error_response(
                message=message,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = User.objects.get(email=email)
            user.set_password(new_password)
            user.save(update_fields=["password"])
            return success_response(message="Password reset. Please login.")
        except User.DoesNotExist:
            return error_response(message="User not found.", status_code=404)


# ── Logout ────────────────────────────────────────────────────────────────────

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            token = RefreshToken(serializer.validated_data["refresh"])
            token.blacklist()
            return success_response(message="Logged out.")
        except TokenError:
            return error_response(
                message="Invalid token.",
                status_code=status.HTTP_400_BAD_REQUEST,
            )


class TokenRefreshView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        from rest_framework_simplejwt.serializers import (
            TokenRefreshSerializer as JWTRefreshSerializer,
        )
        serializer = JWTRefreshSerializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            return success_response(
                data={"access": serializer.validated_data["access"]},
                message="Token refreshed.",
            )
        except TokenError:
            return error_response(
                message="Refresh token expired. Please login.",
                status_code=status.HTTP_401_UNAUTHORIZED,
            )
