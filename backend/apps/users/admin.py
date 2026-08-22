from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    # Added custom fields to the admin display
    list_display = ['username', 'email', 'is_student', 'is_institution_admin', 'is_staff']
    
    # Added custom fields to the edit form
    fieldsets = UserAdmin.fieldsets + (
        ('Role Info', {'fields': ('is_student', 'is_institution_admin', 'phone_number')}),
    )

admin.site.register(CustomUser, CustomUserAdmin)