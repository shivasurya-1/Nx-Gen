from django.urls import path
from .views import ChangePasswordView, RegisterView, LoginView, StudentProfileView

urlpatterns = [
    # path("admin/login/", AdminLoginView.as_view()),
    path('register/', RegisterView.as_view()),
    path('login/', LoginView.as_view()),
    path('change-password/', ChangePasswordView.as_view()),
    path('profile/', StudentProfileView.as_view()),
]
