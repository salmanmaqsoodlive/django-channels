from django.contrib import admin
from accounts.models import User
from .models import Chat, Group

admin.site.register(User)
admin.site.register(Chat)
admin.site.register(Group)
# Register your models here.
