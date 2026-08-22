from datetime import date
from django.utils import timezone
from django.db import transaction

# Tier limits constant
TIER_LIMITS = {
    'explorer': 1,
    'mentor_elite': 5,
    'scholar_vvip': None, # None means Unlimited
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
    """
    limit = TIER_LIMITS.get(user.subscription_tier)
    if limit is None:
        return None
    
    return max(0, limit - user.prompts_used_in_period)
