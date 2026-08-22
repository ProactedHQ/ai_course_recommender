import os
import django
from django.conf import settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "course_recomeder_backend.settings")
django.setup()

from universities.models import Programme, ProgrammeOffering, CutOffPoint, Institution

print(f"Institutions: {Institution.objects.count()}")
print(f"Programmes: {Programme.objects.count()}")
print(f"Offerings: {ProgrammeOffering.objects.count()}")
print(f"CutOffPoints: {CutOffPoint.objects.count()}")
