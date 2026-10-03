"""
Monthly prompt quota per subscription tier.

Usage is tracked on CustomUser (prompts_used_in_period, prompt_period_start) and
reset lazily - there is no cron job; every quota check calls sync_subscription_period first.
"""
from datetime import date

from django.db.models import F

# Prompts allowed per calendar month. None means unlimited.
TIER_LIMITS = {
    'explorer': 1,
    'mentor_elite': 5,
    'scholar_vvip': None,
}

def sync_subscription_period(user):
    """
    Checks if the calendar month has changed since prompt_period_start.
    If so, resets the usage and updates the period start date.
    Should be called lazily before any usage checks or API responses.
    """
    today = date.today()
    # Find the 1st day of the current month
    first_of_this_month = today.replace(day=1)

    if user.prompt_period_start < first_of_this_month:
        user.prompt_period_start = first_of_this_month
        user.prompts_used_in_period = 0
        user.save(update_fields=['prompt_period_start', 'prompts_used_in_period'])

    return user

def get_remaining_prompts(user):
    """
    Computes the number of prompts remaining for the current period.
    Returns:
        int: Number of prompts left.
        None: If the tier is unlimited (Scholar VVIP).

    An unrecognised tier gets the Explorer limit rather than being treated as unlimited.
    """
    if user.subscription_tier in TIER_LIMITS:
        limit = TIER_LIMITS[user.subscription_tier]
    else:
        limit = TIER_LIMITS['explorer']
    if limit is None:
        return None

    return max(0, limit - user.prompts_used_in_period)

def refund_prompt(user_id):
    """
    Give back one prompt after a submission that failed before producing results
    (bad payload, no eligible programmes, AI failure). Never goes below zero.
    """
    from apps.users.models import CustomUser
    CustomUser.objects.filter(id=user_id, prompts_used_in_period__gt=0).update(
        prompts_used_in_period=F('prompts_used_in_period') - 1
    )
