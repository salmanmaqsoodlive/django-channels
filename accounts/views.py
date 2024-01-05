from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from .serializers import (
    UserSerializer,
    LoginSerializer,
    ChatsSerializer,
    UserGetSerializer,
)
from accounts.tokenauthentication import JWTAuthentication
from .models import Chat, Group, User
from django.db.models import Q
from rest_framework.permissions import IsAuthenticated


@api_view(["POST"])
def register_user(request):
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()

        return Response(serializer.data, status=201)

    return Response(serializer.errors, status=400)


@api_view(["POST"])
def login(request):
    print("request.headers", request.headers)
    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid():
        token = JWTAuthentication.generate_token(payload=serializer.data)
        return Response(
            {"message": "Login Successful", "token": token, "user": serializer.data},
            status=200,
        )
    return Response(serializer.errors, status=400)


@api_view(["GET"])
def chats(request, user_id):
    group_name = "programmers"  # Replace with the desired group name
    jwt_auth = JWTAuthentication()
    user, _ = jwt_auth.authenticate(request)
    auth_user = User.objects.get(email=user)
    # replies =
    try:
        chats = Chat.objects.filter(
            Q(receiver_id=user_id, sender_id=auth_user.id)
            | Q(receiver_id=auth_user.id, sender_id=user_id),
            parent_id=None,  # Fetch only top-level chats (no parent)
        ).prefetch_related(
            "replies"
        )  # Fetch related replies efficiently
        print(chats)
        serializer = ChatsSerializer(chats, many=True)
        return Response({"data": serializer.data}, status=200)
    except Group.DoesNotExist:
        return Response(
            {"error": f"Group with name '{group_name}' does not exist."}, status=400
        )
    except Exception as e:
        print(str(e))
        return Response({"error": "Error in getting chats"}, status=500)


@api_view(["POST"])
def read_receipt(request):
    try:
        jwt_auth = JWTAuthentication()
        user, _ = jwt_auth.authenticate(request)
        auth_user = User.objects.get(email=user)
        chat_ids = request.data.get("chat_ids", [])
        # Update is_read for multiple chat IDs
        Chat.objects.filter(
            Q(receiver_id=auth_user.id) | Q(sender_id=auth_user.id), id__in=chat_ids
        ).update(is_read=True)

        return Response({"data": "Successful"}, status=200)

    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=404)

    except Exception as e:
        print(str(e))
        return Response({"error": "Error in updating chats"}, status=500)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_user_list(request):
    try:
        user_obj = User.objects.exclude(id=request.user.id)
        serializer = UserGetSerializer(user_obj, many=True)
        return Response(serializer.data, status=200)
    except Exception as e:
        return Response({"error": "Error in getting users list"}, status=400)
