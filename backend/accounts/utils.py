from django.core.mail import send_mail
from django.conf import settings

def send_reset_email(user, token, uid):
    subject = 'Password Reset Request'
    message = f"Please use the following link to reset your password: \
                http://localhost:8000/accounts/reset-password/?token={token}&uid={uid}"
    email_from = settings.EMAIL_HOST_USER
    recipient_list = [user.email]
    send_mail(subject, message, email_from, recipient_list)
