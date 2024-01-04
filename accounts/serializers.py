from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate
from .models import Chat


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    def create(self, validated_data):
        user = get_user_model().objects.create_user(
            email=validated_data["email"],
            password=validated_data["password"],
            first_name=validated_data.get("first_name", ""),
            last_name=validated_data.get("last_name", ""),
        )

        return user

    class Meta:
        model = get_user_model()
        fields = ["email", "password", "first_name", "last_name"]
        extra_kwargs = {"password": {"write_only": True}}


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    id = serializers.CharField(max_length=15, read_only=True)
    password = serializers.CharField(max_length=255, write_only=True)

    def validate(self, data):
        email = data.get("email", None)
        password = data.get("password", None)

        if email is None:
            raise serializers.ValidationError("An email address is required for login")

        if password is None:
            raise serializers.ValidationError("Passowrd is required for login")

        user = authenticate(username=email, password=password)

        if user is None:
            raise serializers.ValidationError("Invalid email or password")

        if not user.is_active:
            raise serializers.ValidationError("User is inactive")

        return {"email": user.email, "id": user.id}


class UserGetSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ["email", "first_name", "last_name", "id"]
        extra_kwargs = {"id": {"read_only": True}}


class ChatsSerializer(serializers.ModelSerializer):
    replies = serializers.SerializerMethodField()
    like_count = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    likes = UserGetSerializer(many=True, read_only=True)
    file_field = serializers.FileField(allow_null=True, required=False)

    class Meta:
        model = Chat
        fields = [
            "id",
            "content",
            "created_at",
            "sender_id",
            "receiver_id",
            "voice_note_data",
            "parent_id",
            "replies",
            "is_read",
            "file_field",
            "likes",
            "like_count",
            "is_liked",
        ]

    def get_replies(self, obj):
        # Serialize replies recursively
        serializer = self.__class__(obj.replies.all(), many=True)
        return serializer.data

    def get_like_count(self, obj):
        return len(obj.likes.all())

    def get_is_liked(self, obj):
        if len(obj.likes.all()):
            return True

        return False
