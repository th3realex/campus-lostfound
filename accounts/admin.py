from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'role', 'student_id', 'is_verified']
    list_filter = ['role', 'is_verified', 'is_active']
    fieldsets = UserAdmin.fieldsets + (
        ('Campus Info', {'fields': ('role', 'student_id', 'phone', 'department', 'profile_picture', 'is_verified')}),
    )
    search_fields = ['username', 'email', 'student_id', 'first_name', 'last_name']
