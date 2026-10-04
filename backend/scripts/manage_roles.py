import os
import sys
import django
import requests
import secrets
from django.core.exceptions import ValidationError

# Add backend to path so we can import django settings
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "course_recomeder_backend.settings")

# Setup Django
try:
    django.setup()
except Exception as e:
    print(f"Error setting up Django: {e}")
    sys.exit(1)

from django.contrib.auth import get_user_model
from django.conf import settings

User = get_user_model()

def get_supabase_client_data():
    """Helper to get Supabase URL and Service Role Key from environment."""
    url = os.environ.get("SUPABASE_URL") or os.environ.get("VITE_SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("VITE_SUPABASE_SERVICE_ROLE_KEY")
    
    if not url or not key:
        print("\n[!] Supabase credentials missing.")
        print("    Ensure SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are in your .env file.")
        return None, None
    # Only an explicit APP_ENV=production run may change users in the production Supabase project.
    from utils.env_safety import points_at_production_supabase
    if settings.APP_ENV != "production" and points_at_production_supabase(url):
        print(f"\n[!] APP_ENV={settings.APP_ENV}: refusing to modify the PRODUCTION Supabase project.")
        return None, None
    return url.rstrip('/'), key

def update_supabase_metadata(email, role_data):
    """
    Updates Supabase user_metadata using the Admin API (Service Role Key required).
    """
    url, key = get_supabase_client_data()
    if not url or not key:
        print("[!] Skipping Supabase sync due to missing credentials.")
        return False

    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json"
    }

    print(f"\n[SUPABASE] Fetching user by email: {email}...")
    try:
        # 1. Get user ID from email
        resp = requests.get(f"{url}/auth/v1/admin/users", headers=headers)
        resp.raise_for_status()
        users = resp.json().get('users', [])
        target_user = next((u for u in users if (u.get('email') or '').lower() == email.lower()), None)

        if not target_user:
            print(f"[!] User not found in Supabase for email: {email}")
            return False

        user_id = target_user['id']
        current_metadata = target_user.get('user_metadata', {})

        # 2. Update metadata
        new_metadata = {
            **current_metadata,
            "is_staff": role_data['is_staff'],
            "is_student": role_data['is_student'],
            "role": "admin" if role_data['is_staff'] else "student"
        }

        print(f"[SUPABASE] Updating metadata for {user_id}...")
        update_resp = requests.put(
            f"{url}/auth/v1/admin/users/{user_id}",
            headers=headers,
            json={"user_metadata": new_metadata}
        )
        update_resp.raise_for_status()
        print("✅ Supabase metadata updated successfully.")
        return True

    except Exception as e:
        print(f"[!] Supabase sync failed: {e}")
        return False

def manage_roles():
    print("=" * 60)
    print("      AI Course Recommender - Unified Role Manager")
    print("=" * 60)

    # 1. Input Email
    email = input("\n📧 Enter user email: ").strip().lower()
    if not email:
        print("Error: Email is required.")
        return

    # 2. Select Role
    print("\nSelect target role:")
    print("  1. Student     (is_student=True, is_staff=False, is_superuser=False)")
    print("  2. Staff/Admin (is_student=False, is_staff=True, is_superuser=False)")
    print("  3. Superuser   (is_student=False, is_staff=True, is_superuser=True)")
    
    choice = input("\nTarget role [1/2/3]: ").strip()
    
    role_data = {
        "is_student": False,
        "is_staff": False,
        "is_superuser": False
    }

    if choice == '1':
        role_data["is_student"] = True
    elif choice == '2':
        role_data["is_staff"] = True
    elif choice == '3':
        role_data["is_staff"] = True
        role_data["is_superuser"] = True
    else:
        print("Invalid choice.")
        return

    print("\n" + "-" * 40)
    print(f"UPDATING {email}:")
    print(f"  is_student:   {role_data['is_student']}")
    print(f"  is_staff:     {role_data['is_staff']}")
    print(f"  is_superuser: {role_data['is_superuser']}")
    print("-" * 40)

    # 3. Update Django
    try:
        user = User.objects.filter(email__iexact=email).first() or User.objects.filter(username__iexact=email).first()
        
        create_new = False
        if not user:
            confirm = input(f"User {email} not found in Django. Create new? (y/n): ").lower()
            if confirm != 'y':
                print("Aborting.")
                return
            create_new = True

        if create_new:
            password = secrets.token_urlsafe(12)
            user = User.objects.create_user(
                username=email,
                email=email,
                password=password,
                **role_data
            )
            print(f"✅ Created new Django user: {email}")
            print(f"🔑 Password: {password}")
        else:
            # Update existing
            user.is_student = role_data["is_student"]
            user.is_staff = role_data["is_staff"]
            user.is_superuser = role_data["is_superuser"]
            
            # Ensure superuser invariant is strictly met
            if user.is_superuser:
                user.is_staff = True
                user.is_student = False
            elif user.is_staff:
                user.is_student = False

            user.save()
            print(f"✅ Updated existing Django user: {email}")

        # 4. Sync to Supabase
        update_supabase_metadata(email, role_data)

    except ValidationError as ve:
        print(f"\n❌ FAILED: Invariant check failed: {ve}")
    except Exception as e:
        print(f"\n❌ FAILED: An unexpected error occurred: {e}")

    print("\n" + "=" * 60)
    print("Done.")

if __name__ == "__main__":
    manage_roles()
