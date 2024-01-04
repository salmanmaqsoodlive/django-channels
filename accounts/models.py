from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("User must have email address")

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=255, blank=True)
    last_name = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=True)
    date_joined = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = "email"

    def get_full_name(self):
        return f"{self.first_name}{self.last_name}"

    def __str__(self) -> str:
        return self.email


class Chat(models.Model):
    id = models.AutoField(primary_key=True)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now=True)
    sender_id = models.CharField(max_length=100)
    receiver_id = models.CharField(max_length=100)
    voice_note_data = models.TextField(null=True, blank=True)
    file_field = models.FileField(upload_to="media/chat_files/", null=True, blank=True)
    parent = models.ForeignKey(
        "self", on_delete=models.CASCADE, null=True, blank=True, related_name="replies"
    )
    is_read = models.BooleanField(default=False)
    likes = models.ManyToManyField(User, blank=True)

    def __str__(self):
        return self.content


class Group(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name
