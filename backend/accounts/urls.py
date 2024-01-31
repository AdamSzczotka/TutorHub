from django.urls import path
from .views import UserRegistrationView, UserLoginView,ChangePasswordView, RequestResetPasswordView, ResetPasswordView

urlpatterns = [
    path('register/', UserRegistrationView.as_view(), name='register'),
    path('login/', UserLoginView.as_view(), name='login'),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
    path('request-reset-password/', RequestResetPasswordView.as_view(), name='request-reset-password'),
    path('reset-password/', ResetPasswordView.as_view(), name='reset-password'),
]

# Make sure to include these URLs in your project's main urls.py file.
