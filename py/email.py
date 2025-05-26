from flask_mail import Message
from flask import current_app
from app import mail

def send_email(subject: str, recipients: list, body: str):
    """Generic email sending function"""
    msg = Message(subject=subject, recipients=recipients, body=body)
    mail.send(msg)

def send_registration_confirmation(user):
    body = f"""Hello {user.username},

Thank you for registering at My Weather Report!

Your account is now active.
"""
    send_email(
        subject="Welcome to My Weather Report!",
        recipients=[user.email],
        body=body
    )

def send_password_reset(user, reset_link):
    body = f"""Hello {user.username},

You requested a password reset.
Click the link below to set a new password:

{reset_link}

If you didn't request this, just ignore this email.
"""
    send_email(
        subject="Reset your password",
        recipients=[user.email],
        body=body
    )