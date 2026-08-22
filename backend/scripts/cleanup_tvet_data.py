import os
import sys
import django
import logging

sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'apps'))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "course_recomeder_backend.settings")
django.setup()

from apps.universities.models import Institution, Programme, ProgrammeLevel, ProgrammeOffering, ProgrammeRequirement, ClusterGroup

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

def cleanup():
    logger.info("🗑️ Starting surgical cleanup of corrupted TVET data...")

    levels_to_clean = ['ARTISAN', 'CERTIFICATE']   # Craft was stored under CERTIFICATE in bad import

    # === COUNTS FIRST (dry-run style) ===
    logger.info("📊 Pre-cleanup counts:")
    print(f"   Offerings:     {ProgrammeOffering.objects.filter(programme__level__name__in=levels_to_clean).count()}")
    print(f"   Requirements:  {ProgrammeRequirement.objects.filter(programme__level__name__in=levels_to_clean).count()}")
    print(f"   Programmes:    {Programme.objects.filter(level__name__in=levels_to_clean).count()}")
    print(f"   ClusterGroups: {ClusterGroup.objects.filter(level__name__in=levels_to_clean).count()}")
    print(f"   TVET Insts:    {Institution.objects.filter(code__startswith='TVET-').count()}")

    confirm = input("\n🚨 Proceed with DELETION? (y/n): ")
    if confirm.lower() != 'y':
        logger.info("Cleanup cancelled.")
        return

    # === ACTUAL DELETE ===
    ProgrammeOffering.objects.filter(programme__level__name__in=levels_to_clean).delete()
    ProgrammeRequirement.objects.filter(programme__level__name__in=levels_to_clean).delete()
    Programme.objects.filter(level__name__in=levels_to_clean).delete()
    ClusterGroup.objects.filter(level__name__in=levels_to_clean).delete()
    Institution.objects.filter(code__startswith="TVET-").delete()

    logger.info("🏆 Cleanup complete. Database is now pristine and ready for the fixed JSON import.")

if __name__ == "__main__":
    cleanup()