from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from accounts.views import register_user, login, chats, get_user_list, read_receipt

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", chats),
    path("register", register_user, name="register"),
    path("login", login, name="login"),
    path("chats/<int:user_id>", chats, name="chats"),
    path("read-receipt", read_receipt, name="read-receipt"),
    path("users", get_user_list, name="get-user-list"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
