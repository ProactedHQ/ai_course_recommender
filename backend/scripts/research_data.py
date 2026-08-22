
import sys
import os
import django
import json

# Add current directory to path
sys.path.append(os.getcwd())
# Add apps directory to path
sys.path.append(os.path.join(os.getcwd(), 'apps'))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "course_recomeder_backend.settings")
django.setup()

from apps.students.models import Subject
from apps.universities.models import ClusterGroup

def get_data():
    subjects = [
        {
            "code": s.code,
            "name": s.name,
            "category": s.category
        }
        for s in Subject.objects.all()
    ]
    
    clusters = [
        {
            "code": c.code,
            "name": c.name,
            "subject_1": c.subject_1,
            "subject_2": c.subject_2,
            "subject_3": c.subject_3,
            "subject_4": c.subject_4
        }
        for c in ClusterGroup.objects.filter(level__name='DEGREE').order_by('code')
    ]
    
    data = {
        "subjects": subjects,
        "clusters": clusters
    }
    
    with open("research_data.json", "w") as f:
        json.dump(data, f, indent=4)
    
    print(f"Fetched {len(subjects)} subjects and {len(clusters)} clusters.")

if __name__ == "__main__":
    get_data()
