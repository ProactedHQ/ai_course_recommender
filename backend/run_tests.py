#!/usr/bin/env python
"""
KeDira Test Runner
==================
Utility to run the comprehensive test suite with clear, emoji-supported logging.
"""
import subprocess
import sys
import os

def run_tests():
    print("\n" + "="*80)
    print("  [OK]  KEDIRA SYSTEM TEST SUITE  [OK]")
    print("="*80)
    
    # Run all tests at once to avoid multiple DB create/delete cycles
    # and use --noinput to avoid the stale DB prompt
    print("\n[RUNNING] All suites: Auth, Payments, Prompts, Admin...")
    
    test_targets = [
        "apps.users.tests.test_auth",
        "apps.users.tests.test_payments",
        "apps.users.tests.test_admin",
        "apps.users.tests.test_prompts",
    ]
    
    cmd = [sys.executable, "manage.py", "test"] + test_targets + ["-v", "2", "--noinput", "--keepdb"]
    
    result = subprocess.run(cmd)

    print("\n" + "="*80)
    if result.returncode == 0:
        print("  [SUCCESS]  ALL TESTS PASSED SUCCESSFULLY!  [SUCCESS]")
    else:
        print("  [ERROR]  SOME TESTS FAILED. CHECK LOGS ABOVE.  [ERROR]")
    print("="*80 + "\n")

if __name__ == "__main__":
    # Ensure current dir is backend
    if not os.path.exists("manage.py"):
        print("Error: run_tests.py must be run from the Django backend root directory.")
        sys.exit(1)
    run_tests()
