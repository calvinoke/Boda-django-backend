import logging
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger("accounts.email")


def send_welcome_email(user):
    """
    Send welcome email to new user.
    
    Args:
        user: User object
    
    Returns:
        bool: True if email sent successfully
    """
    try:
        subject = f"Welcome to {settings.EMAIL_SUBJECT_PREFIX} {user.first_name}!"
        
        # HTML email content
        html_content = f"""
        <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background-color: #4CAF50; color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0; }}
                    .content {{ padding: 20px; background-color: #f9f9f9; border: 1px solid #ddd; border-radius: 0 0 5px 5px; }}
                    .details {{ background-color: white; padding: 15px; border-radius: 5px; margin: 15px 0; }}
                    .footer {{ margin-top: 20px; text-align: center; color: #666; font-size: 12px; }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>Welcome {user.first_name}!</h1>
                </div>
                <div class="content">
                    <p>Thank you for registering with us. Your account has been created successfully!</p>
                    
                    <div class="details">
                        <p><strong>Username:</strong> {user.username}</p>
                        <p><strong>Email:</strong> {user.email}</p>
                        <p><strong>Phone:</strong> {user.phone_number}</p>
                        <p><strong>Role:</strong> {user.get_role_display()}</p>
                    </div>
                    
                    <p>You can now log in to your account and start using our services.</p>
                    
                    <p>If you have any questions, feel free to contact our support team.</p>
                    
                    <p>Best regards,<br>Your Team</p>
                </div>
                <div class="footer">
                    <p>&copy; {timezone.now().year} Your Company. All rights reserved.</p>
                </div>
            </body>
        </html>
        """
        
        # Plain text version
        text_content = f"""
        Welcome {user.first_name}!
        
        Thank you for registering with us. Your account has been created successfully!
        
        Username: {user.username}
        Email: {user.email}
        Phone: {user.phone_number}
        Role: {user.get_role_display()}
        
        You can now log in to your account and start using our services.
        
        If you have any questions, feel free to contact our support team.
        
        Best regards,
        Your Team
        """
        
        email = EmailMultiAlternatives(
            subject,
            text_content,
            settings.DEFAULT_FROM_EMAIL,
            [user.email]
        )
        email.attach_alternative(html_content, "text/html")
        email.send()
        
        logger.info(
            f"Welcome email sent to {user.email}",
            extra={
                "user_id": user.id,
                "username": user.username,
                "email": user.email
            }
        )
        return True
        
    except Exception as e:
        logger.error(
            f"Failed to send welcome email to {user.email}: {str(e)}",
            extra={
                "user_id": user.id,
                "error": str(e)
            }
        )
        return False


def send_otp_email(user, otp_code, purpose="verification"):
    """
    Send OTP via email.
    
    Args:
        user: User object
        otp_code (str): OTP code
        purpose (str): Purpose of OTP
    
    Returns:
        bool: True if email sent successfully
    """
    try:
        subject = f"Your OTP Code - {settings.EMAIL_SUBJECT_PREFIX}"
        
        # HTML email content
        html_content = f"""
        <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background-color: #2196F3; color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0; }}
                    .content {{ padding: 20px; background-color: #f9f9f9; border: 1px solid #ddd; border-radius: 0 0 5px 5px; }}
                    .otp-box {{ background-color: white; padding: 20px; text-align: center; border-radius: 5px; margin: 20px 0; }}
                    .otp-code {{ font-size: 36px; font-weight: bold; color: #2196F3; letter-spacing: 5px; }}
                    .footer {{ margin-top: 20px; text-align: center; color: #666; font-size: 12px; }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>Your OTP Code</h1>
                </div>
                <div class="content">
                    <p>Your OTP for <strong>{purpose}</strong> is:</p>
                    
                    <div class="otp-box">
                        <div class="otp-code">{otp_code}</div>
                    </div>
                    
                    <p>This OTP is valid for <strong>5 minutes</strong>.</p>
                    
                    <p>If you didn't request this, please ignore this email.</p>
                    
                    <p>Best regards,<br>Your Team</p>
                </div>
                <div class="footer">
                    <p>This is an automated message. Please do not reply to this email.</p>
                    <p>&copy; {timezone.now().year} Your Company. All rights reserved.</p>
                </div>
            </body>
        </html>
        """
        
        # Plain text version
        text_content = f"""
        Your OTP Code
        
        Your OTP for {purpose} is: {otp_code}
        
        This OTP is valid for 5 minutes.
        
        If you didn't request this, please ignore this email.
        
        Best regards,
        Your Team
        """
        
        email = EmailMultiAlternatives(
            subject,
            text_content,
            settings.DEFAULT_FROM_EMAIL,
            [user.email]
        )
        email.attach_alternative(html_content, "text/html")
        email.send()
        
        logger.info(
            f"OTP email sent to {user.email}",
            extra={
                "user_id": user.id,
                "username": user.username,
                "email": user.email,
                "purpose": purpose
            }
        )
        return True
        
    except Exception as e:
        logger.error(
            f"Failed to send OTP email to {user.email}: {str(e)}",
            extra={
                "user_id": user.id,
                "error": str(e)
            }
        )
        return False


def send_password_reset_email(user, reset_token):
    """
    Send password reset email to user.
    
    Args:
        user: User object
        reset_token (str): Password reset token
    
    Returns:
        bool: True if email sent successfully
    """
    try:
        subject = f"Password Reset Request - {settings.EMAIL_SUBJECT_PREFIX}"
        
        reset_link = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"
        
        # HTML email content
        html_content = f"""
        <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background-color: #f44336; color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0; }}
                    .content {{ padding: 20px; background-color: #f9f9f9; border: 1px solid #ddd; border-radius: 0 0 5px 5px; }}
                    .button {{
                        display: inline-block;
                        padding: 10px 20px;
                        background-color: #f44336;
                        color: white;
                        text-decoration: none;
                        border-radius: 5px;
                        margin: 10px 0;
                    }}
                    .footer {{ margin-top: 20px; text-align: center; color: #666; font-size: 12px; }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>Password Reset Request</h1>
                </div>
                <div class="content">
                    <p>Hello {user.first_name},</p>
                    <p>We received a request to reset your password. Click the button below to reset it:</p>
                    <p><a href="{reset_link}" class="button">Reset Password</a></p>
                    <p>If the button doesn't work, copy and paste this link into your browser:</p>
                    <p>{reset_link}</p>
                    <p>This link will expire in 24 hours.</p>
                    <p>If you didn't request this, please ignore this email.</p>
                    <p>Best regards,<br>Your Team</p>
                </div>
                <div class="footer">
                    <p>&copy; {timezone.now().year} Your Company. All rights reserved.</p>
                </div>
            </body>
        </html>
        """
        
        # Plain text version
        text_content = f"""
        Password Reset Request
        
        Hello {user.first_name},
        
        We received a request to reset your password. Use the link below to reset it:
        
        {reset_link}
        
        This link will expire in 24 hours.
        
        If you didn't request this, please ignore this email.
        
        Best regards,
        Your Team
        """
        
        email = EmailMultiAlternatives(
            subject,
            text_content,
            settings.DEFAULT_FROM_EMAIL,
            [user.email]
        )
        email.attach_alternative(html_content, "text/html")
        email.send()
        
        logger.info(
            f"Password reset email sent to {user.email}",
            extra={
                "user_id": user.id,
                "username": user.username,
                "email": user.email
            }
        )
        return True
        
    except Exception as e:
        logger.error(
            f"Failed to send password reset email to {user.email}: {str(e)}",
            extra={
                "user_id": user.id,
                "error": str(e)
            }
        )
        return False


def send_generic_email(subject, html_content, text_content, to_email, from_email=None):
    """
    Send a generic email with both HTML and plain text versions.
    
    Args:
        subject (str): Email subject
        html_content (str): HTML content
        text_content (str): Plain text content
        to_email (str or list): Recipient email(s)
        from_email (str): Sender email (defaults to DEFAULT_FROM_EMAIL)
    
    Returns:
        bool: True if email sent successfully
    """
    try:
        if from_email is None:
            from_email = settings.DEFAULT_FROM_EMAIL
        
        if isinstance(to_email, str):
            to_email = [to_email]
        
        email = EmailMultiAlternatives(
            subject,
            text_content,
            from_email,
            to_email
        )
        email.attach_alternative(html_content, "text/html")
        email.send()
        
        logger.info(
            f"Generic email sent to {to_email}",
            extra={
                "subject": subject,
                "to_email": to_email
            }
        )
        return True
        
    except Exception as e:
        logger.error(
            f"Failed to send generic email to {to_email}: {str(e)}",
            extra={
                "subject": subject,
                "error": str(e)
            }
        )
        return False