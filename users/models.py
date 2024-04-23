from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager


class UserManager(BaseUserManager):
    def create_user(self, phone_number, **extra_fields):
        if not phone_number:
            raise ValueError('The Phone Number field must be set')
        user = self.model(phone_number=phone_number, **extra_fields)
        user.save()
        return user


class User(AbstractBaseUser):
    phone_number = models.CharField(
        max_length=17,
        unique=True,
        null=False,
        db_index=True
    )
    invite_code = models.CharField(
        max_length=6,
        unique=True,
        null=False,
        db_index=True
    )
    activated_from = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        related_name='activated_by',
        blank=True,
        null=True
    )

    objects = UserManager()

    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = []
