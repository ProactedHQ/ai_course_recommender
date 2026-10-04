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
    
    # APP_ENV=test => in-memory SQLite + mock payments + no Redis (see settings.py).
    # It can never reach the production database or PayHero, whatever is in backend/.env.
    env = dict(os.environ, APP_ENV="test")

    # Every apps/*/tests/test_*.py module (labels are explicit because apps/ is a namespace package)
    import glob
    test_targets = sorted(
        path[:-3].replace(os.sep, ".")
        for path in glob.glob(os.path.join("apps", "*", "tests", "test_*.py"))
    )
    print(f"\n[RUNNING] {len(test_targets)} test modules...")

    cmd = [sys.executable, "manage.py", "test"] + test_targets + ["-v", "2", "--noinput"] + sys.argv[1:]
    
    result = subprocess.run(cmd, env=env)

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
