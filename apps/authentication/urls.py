from django.urls import path
from .views import (
    RegisterView,
    SendEmailOTPView,
    VerifyEmailOTPView,
    SendPhoneOTPView,
    VerifyPhoneOTPView,
    EmailPasswordLoginView,
    EmailOTPLoginView,
    EmailOTPLoginVerifyView,
    ChangePasswordView,
    ForgotPasswordView,
    ResetPasswordView,
    LogoutView,
    TokenRefreshView,
    # New
    GoogleLoginView,
    FirebasePhoneLoginView,
    StationCodesView,
    OnboardingView,
    UpdateStationCodeView,
)

urlpatterns = [
    # Registration
    path("register/",              RegisterView.as_view(),           name="auth-register"),

    # Email OTP
    path("otp/email/send/",        SendEmailOTPView.as_view(),       name="auth-otp-email-send"),
    path("otp/email/verify/",      VerifyEmailOTPView.as_view(),     name="auth-otp-email-verify"),

    # Phone OTP (optional)
    path("otp/phone/send/",        SendPhoneOTPView.as_view(),       name="auth-otp-phone-send"),
    path("otp/phone/verify/",      VerifyPhoneOTPView.as_view(),     name="auth-otp-phone-verify"),

    # Login
    path("login/",                 EmailPasswordLoginView.as_view(), name="auth-login"),
    path("login/otp/",             EmailOTPLoginView.as_view(),      name="auth-login-otp"),
    path("login/otp/verify/",      EmailOTPLoginVerifyView.as_view(),name="auth-login-otp-verify"),

    # Google Login
    path("google/",                GoogleLoginView.as_view(),        name="auth-google"),
    path("firebase/phone/", FirebasePhoneLoginView.as_view(), name="auth-firebase-phone"),
    # Onboarding
    path("onboarding/",            OnboardingView.as_view(),         name="auth-onboarding"),
    path("station-codes/",         StationCodesView.as_view(),       name="station-codes"),
    path("update-station/",        UpdateStationCodeView.as_view(),  name="update-station"),

    # Password
    path("password/change/",       ChangePasswordView.as_view(),     name="auth-password-change"),
    path("password/forgot/",       ForgotPasswordView.as_view(),     name="auth-password-forgot"),
    path("password/reset/",        ResetPasswordView.as_view(),      name="auth-password-reset"),

    # Token
    path("token/refresh/",         TokenRefreshView.as_view(),       name="auth-token-refresh"),

    # Logout
    path("logout/",                LogoutView.as_view(),             name="auth-logout"),
]
