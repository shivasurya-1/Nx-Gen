from django.urls import path
from .views import (
    ChangePasswordView,
    RegisterView,
    LoginView,
    StudentProfileView,
    ForgotPasswordRequestView,
    ForgotPasswordVerifyOTPView,
    ForgotPasswordResetView
)

urlpatterns = [
    # path("admin/login/", AdminLoginView.as_view()),
    path('register/', RegisterView.as_view()),
    path('login/', LoginView.as_view()),
    path('change-password/', ChangePasswordView.as_view()),
    path('profile/', StudentProfileView.as_view()),
    
    # Password Reset Endpoints
    path('forgot-password/', ForgotPasswordRequestView.as_view()),
    path('forgot-password/verify-otp/', ForgotPasswordVerifyOTPView.as_view()),
    path('forgot-password/reset/', ForgotPasswordResetView.as_view()),
    
    # Alternative endpoints (for frontend compatibility)
    path('auth/forgot-password/', ForgotPasswordRequestView.as_view()),
    path('auth/forgot-password/verify-otp/', ForgotPasswordVerifyOTPView.as_view()),
    path('auth/forgot-password/reset/', ForgotPasswordResetView.as_view()),
    path('auth/password-reset/request-otp/', ForgotPasswordRequestView.as_view()),
    path('auth/password-reset/verify-otp/', ForgotPasswordVerifyOTPView.as_view()),
    path('auth/password-reset/confirm/', ForgotPasswordResetView.as_view()),
    path('auth/request-password-reset/', ForgotPasswordRequestView.as_view()),
    path('auth/verify-reset-otp/', ForgotPasswordVerifyOTPView.as_view()),
    path('auth/reset-password/', ForgotPasswordResetView.as_view()),
]
