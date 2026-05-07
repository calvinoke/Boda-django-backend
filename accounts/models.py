from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator

phone_validator = RegexValidator(
    regex=r'^\+256[0-9]{9}$',
    message='Phone number must be in format: +2567XXXXXXXX'
)

class User(AbstractUser):

    ROLE_CHOICES = (
        ('rider', 'Rider'),
        ('admin', 'Admin'),
    )

    email = models.EmailField(unique=True, db_index=True)

    phone_number = models.CharField(
        max_length=15,
        unique=True,
        validators=[phone_validator],
        db_index=True
    )

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='rider',
        db_index=True
    )

    is_verified = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['phone_number']),
            models.Index(fields=['role']),
        ]

    def __str__(self):
        return self.email