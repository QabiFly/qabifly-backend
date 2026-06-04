import logging
import string
import random
from django.contrib.auth import authenticate
from django.utils import timezone
from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

from core.responses import success_response, error_response
from core.email import send_otp_email
from core.security import sanitize_text, get_client_ip
from apps.users.models import User
from apps.users.serializers import UserProfileSerializer

from .models import OTPRecord
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
from .firebase_auth import verify_firebase_phone_token
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


# ── Register ──────────────────────────────────────────────────────────────────

@method_decorator(
    ratelimit(key="ip", rate="10/h", method="POST", block=True),
    name="post"
)
class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user   = serializer.save()
        record = get_or_create_otp(
            user.email, OTPRecord.OTPType.EMAIL_VERIFICATION
        )
        send_otp_email(user.email, record.otp_code, user.full_name or "User")

        return success_response(
            data={"email": user.email},
            message="Registration successful. OTP bheja gaya.",
            status_code=status.HTTP_201_CREATED,
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
            try:
                name = User.objects.get(email=email).full_name or "User"
            except User.DoesNotExist:
                pass

        send_otp_email(email, record.otp_code, name)
        return success_response(message=f"OTP bheja gaya {email} pe.")


@method_decorator(
    ratelimit(key="ip", rate="10/m", method="POST", block=True),
    name="post"
)
class VerifyEmailOTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = VerifyEmailOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email    = serializer.validated_data["email"].lower().strip()
        otp_code = serializer.validated_data["otp_code"]

        ok, msg = verify_otp(email, otp_code, OTPRecord.OTPType.EMAIL_VERIFICATION)
        if not ok:
            return error_response(message=msg, status_code=400)

        try:
            user = User.objects.get(email=email)
            user.is_verified = True
            user.save(update_fields=["is_verified"])
            tokens = get_tokens_for_user(user)
            return success_response(
                data={
                    **tokens,
                    "user":                UserProfileSerializer(user).data,
                    "onboarding_complete": user.onboarding_complete,
                },
                message="Email verified.",
            )
        except User.DoesNotExist:
            return error_response(message="User nahi mila.", status_code=404)


# ── Login — Email + Password ──────────────────────────────────────────────────

@method_decorator(
    ratelimit(key="ip", rate="10/m", method="POST", block=True),
    name="post"
)
class EmailPasswordLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = EmailPasswordLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email    = serializer.validated_data["email"].lower().strip()
        password = serializer.validated_data["password"]
        user     = authenticate(request, username=email, password=password)

        if not user:
            logger.warning(f"Failed login attempt for {email} from {get_client_ip(request)}")
            return error_response(
                message="Email ya password galat hai.",
                status_code=status.HTTP_401_UNAUTHORIZED,
            )
        if not user.is_active:
            return error_response(message="Account deactivate hai.", status_code=403)
        if not user.is_verified:
            record = get_or_create_otp(email, OTPRecord.OTPType.EMAIL_VERIFICATION)
            send_otp_email(email, record.otp_code, user.full_name or "User")
            return error_response(
                message="Email verify nahi hua. OTP bheja gaya.",
                status_code=403,
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


# ── Login — Email OTP ─────────────────────────────────────────────────────────

@method_decorator(
    ratelimit(key="ip", rate="5/m", method="POST", block=True),
    name="post"
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
                message="Is email se koi account nahi hai.",
                status_code=404,
            )

        if not user.is_active:
            return error_response(message="Account deactivate hai.", status_code=403)

        record = get_or_create_otp(email, OTPRecord.OTPType.EMAIL_LOGIN)
        send_otp_email(email, record.otp_code, user.full_name or "User")
        return success_response(message=f"OTP bheja gaya {email} pe.")


@method_decorator(
    ratelimit(key="ip", rate="10/m", method="POST", block=True),
    name="post"
)
class EmailOTPLoginVerifyView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = VerifyEmailOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email    = serializer.validated_data["email"].lower().strip()
        otp_code = serializer.validated_data["otp_code"]

        ok, msg = verify_otp(email, otp_code, OTPRecord.OTPType.EMAIL_LOGIN)
        if not ok:
            return error_response(message=msg, status_code=400)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return error_response(message="User nahi mila.", status_code=404)

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
    ratelimit(key="ip", rate="20/m", method="POST", block=True),
    name="post"
)
class GoogleLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        token = (
            request.data.get("access_token") or
            request.data.get("id_token")
        )
        if not token:
            return error_response(message="Google token required.", status_code=400)

        google_info = verify_google_token(token)
        if not google_info:
            return error_response(
                message="Invalid Google token.",
                status_code=status.HTTP_401_UNAUTHORIZED,
            )

        email = google_info["email"]
        if not email:
            return error_response(message="Google account mein email nahi.", status_code=400)

        google_id = google_info["google_id"]
        name      = sanitize_text(google_info["name"], 150)

        user = User.objects.filter(email=email).first()
        if user:
            if not user.google_id:
                user.google_id     = google_id
                user.auth_provider = User.AuthProvider.GOOGLE
                user.is_verified   = True
                user.save(update_fields=["google_id", "auth_provider", "is_verified"])
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


# ── Firebase Phone Login ──────────────────────────────────────────────────────

@method_decorator(
    ratelimit(key="ip", rate="10/m", method="POST", block=True),
    name="post"
)
class FirebasePhoneLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        id_token = request.data.get("id_token")
        if not id_token:
            return error_response(message="Firebase ID token required.", status_code=400)

        firebase_info = verify_firebase_phone_token(id_token)
        if not firebase_info:
            return error_response(
                message="Invalid Firebase token.",
                status_code=status.HTTP_401_UNAUTHORIZED,
            )

        phone = firebase_info["phone"]
        user  = User.objects.filter(phone=phone).first()

        if user:
            user.is_phone_verified = True
            user.save(update_fields=["is_phone_verified"])
            is_new = False
        else:
            suffix = "".join(random.choices(string.digits, k=6))
            user   = User.objects.create_user(
                email             = f"phone_{phone.replace('+','')}@qabifly.in",
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


# ── Onboarding ────────────────────────────────────────────────────────────────

class StationCodesView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return success_response(data=get_all_station_codes())


class OnboardingView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        if user.onboarding_complete:
            return error_response(message="Onboarding already complete.", status_code=400)

        virtual_name  = sanitize_text(request.data.get("virtual_name", ""), 100)
        village       = sanitize_text(request.data.get("village",      ""), 100)
        district      = sanitize_text(request.data.get("district",     ""), 100)
        state         = sanitize_text(request.data.get("state", "Uttar Pradesh"), 100)
        station_code  = str(request.data.get("station_code", "")).strip().upper()[:5]
        virtual_photo = request.FILES.get("virtual_photo")

        if not virtual_name:
            return error_response(message="Virtual name zaroori hai.", status_code=400)
        if not village:
            return error_response(message="Village zaroori hai.", status_code=400)
        if not district:
            return error_response(message="District zaroori hai.", status_code=400)
        if not station_code:
            return error_response(message="Station code zaroori hai.", status_code=400)

        # Photo validate karo
        if virtual_photo:
            try:
                from core.security import validate_file_upload
                validate_file_upload(
                    virtual_photo,
                    allowed_types=['image/jpeg', 'image/png', 'image/webp'],
                    max_mb=2
                )
            except ValueError as e:
                return error_response(message=str(e), status_code=400)

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

        logger.info(f"Onboarding: {user.email} → {virtual_number}")
        return success_response(
            data=UserProfileSerializer(user).data,
            message=f"Welcome! Aapka virtual number: {virtual_number}",
        )


class UpdateStationCodeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        new_code = str(request.data.get("station_code", "")).strip().upper()[:5]
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
            message=f"Virtual number update: {new_number}",
        )


# ── Phone OTP (Fast2SMS) ──────────────────────────────────────────────────────

@method_decorator(
    ratelimit(key="ip", rate="3/m", method="POST", block=True),
    name="post"
)
class SendPhoneOTPView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = SendPhoneOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone  = serializer.validated_data["phone"]
        record = get_or_create_otp(phone, OTPRecord.OTPType.PHONE_VERIFICATION)
        sent   = send_phone_otp(phone, record.otp_code)
        if not sent:
            return error_response(message="SMS send nahi ho saka.", status_code=503)
        return success_response(message=f"OTP sent to {phone}.")


class VerifyPhoneOTPView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = VerifyPhoneOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone    = serializer.validated_data["phone"]
        otp_code = serializer.validated_data["otp_code"]

        ok, msg = verify_otp(phone, otp_code, OTPRecord.OTPType.PHONE_VERIFICATION)
        if not ok:
            return error_response(message=msg, status_code=400)

        user = request.user
        user.phone             = phone
        user.is_phone_verified = True
        user.save(update_fields=["phone", "is_phone_verified"])
        return success_response(message="Phone verified.")


# ── Password ──────────────────────────────────────────────────────────────────

class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user
        if not user.check_password(serializer.validated_data["old_password"]):
            return error_response(message="Current password galat hai.", status_code=400)
        user.set_password(serializer.validated_data["new_password"])
        user.save(update_fields=["password"])
        return success_response(message="Password change ho gaya.")


@method_decorator(
    ratelimit(key="ip", rate="5/h", method="POST", block=True),
    name="post"
)
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
        return success_response(message="Agar email registered hai toh OTP bheja gaya.")


class ResetPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email    = serializer.validated_data["email"].lower().strip()
        otp_code = serializer.validated_data["otp_code"]
        new_pass = serializer.validated_data["new_password"]

        ok, msg = verify_otp(email, otp_code, OTPRecord.OTPType.PASSWORD_RESET)
        if not ok:
            return error_response(message=msg, status_code=400)

        try:
            user = User.objects.get(email=email)
            user.set_password(new_pass)
            user.save(update_fields=["password"])
            return success_response(message="Password reset. Login karein.")
        except User.DoesNotExist:
            return error_response(message="User nahi mila.", status_code=404)


# ── Logout ────────────────────────────────────────────────────────────────────

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            token = RefreshToken(serializer.validated_data["refresh"])
            token.blacklist()
            return success_response(message="Logout successful.")
        except TokenError:
            return error_response(message="Invalid token.", status_code=400)


class TokenRefreshView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        from rest_framework_simplejwt.serializers import (
            TokenRefreshSerializer as JWTRefresh
        )
        serializer = JWTRefresh(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            return success_response(
                data={"access": serializer.validated_data["access"]},
                message="Token refreshed.",
            )
        except TokenError:
            return error_response(
                message="Token expire ho gaya. Login karein.",
                status_code=401,
            )
