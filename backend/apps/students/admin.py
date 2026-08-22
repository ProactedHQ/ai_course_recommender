from django.contrib import admin
from .models import StudentProfile, Subject, AcademicResult, StudentAttribute, CareerGoal

admin.site.register(StudentProfile)
admin.site.register(Subject)
admin.site.register(AcademicResult)
admin.site.register(StudentAttribute)
admin.site.register(CareerGoal)