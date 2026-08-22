#!/usr/bin/env python
"""Get all subjects from database for subject mapping"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'course_recomeder_backend.settings')
django.setup()

from students.models import Subject

subjects = Subject.objects.all().order_by('code')
print(f'Total subjects: {subjects.count()}')
print('\nAll subjects for mapping:')
for s in subjects:
    print(f"'{s.code}': '{s.name}',  # {s.category}")
