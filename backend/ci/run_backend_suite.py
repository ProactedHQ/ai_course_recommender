"""
CI: run the whole backend test suite (same module discovery as run_tests.py) with APP_ENV=test,
then compare failing tests with ci/known_test_failures.txt.

  - Any failure/error NOT in the known list  -> exit 1 (a regression or a new broken test).
  - The run not completing (import/setup crash) -> exit 1.
  - A known failure that now passes            -> notice only; remove it from the list.

The known list holds pre-existing legacy failures (outdated fixtures/imports) that existed before
the payment/security work. They are tracked, not hidden: every CI run reports them.
"""
import glob
import os
import re
import subprocess
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
KNOWN_FILE = BACKEND / "ci" / "known_test_failures.txt"
RESULT_RE = re.compile(r"^(FAIL|ERROR): \S+ \(([^)]+)\)", re.M)


def load_known():
    lines = KNOWN_FILE.read_text().splitlines()
    return {line.strip() for line in lines if line.strip() and not line.lstrip().startswith("#")}


def summary(text):
    path = os.environ.get("GITHUB_STEP_SUMMARY")
    if path:
        with open(path, "a") as fh:
            fh.write(text + "\n")


def main():
    labels = sorted(p[:-3].replace(os.sep, ".")
                    for p in glob.glob(os.path.join("apps", "*", "tests", "test_*.py"), root_dir=BACKEND))
    env = dict(os.environ, APP_ENV="test")
    proc = subprocess.run([sys.executable, "manage.py", "test", *labels, "--noinput", "-v", "2"],
                          cwd=BACKEND, env=env, capture_output=True, text=True)
    output = proc.stdout + proc.stderr
    print(output)

    ran = re.search(r"^Ran (\d+) tests?", output, re.M)
    if not ran:
        print("::error::The backend test run did not complete (import or setup failure).")
        return 1

    failing = {f"{kind} {test_id}" for kind, test_id in RESULT_RE.findall(output)}
    known = load_known()
    new = sorted(failing - known)
    fixed = sorted(known - failing)
    legacy = sorted(failing & known)

    print("=" * 70)
    print(f"Tests run: {ran.group(1)} | failing: {len(failing)} | known legacy: {len(legacy)} | NEW: {len(new)}")
    for item in legacy:
        print(f"  known legacy failure: {item}")
    for item in fixed:
        print(f"::notice::Known legacy failure now passes - remove from ci/known_test_failures.txt: {item}")
    for item in new:
        print(f"::error::New test failure (not in ci/known_test_failures.txt): {item}")

    summary(f"### Backend test suite\n\nRan **{ran.group(1)}** tests. "
            f"Known legacy failures: **{len(legacy)}**. New failures: **{len(new)}**.\n")
    if new:
        summary("New failures:\n" + "\n".join(f"- `{i}`" for i in new))
    if fixed:
        summary("Legacy failures that now pass (remove from the list):\n" + "\n".join(f"- `{i}`" for i in fixed))
    return 1 if new else 0


if __name__ == "__main__":
    sys.exit(main())
