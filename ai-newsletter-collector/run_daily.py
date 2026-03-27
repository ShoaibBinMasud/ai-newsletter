"""
Daily runner — called by Windows Task Scheduler at 7:00 AM.
Fetches news, ranks with AI, builds email, and sends it.

To set up Windows Task Scheduler:
  1. Open Task Scheduler → Create Basic Task
  2. Trigger: Daily at 7:00 AM
  3. Action: Start a Program
     Program: C:\\path\\to\\python.exe
     Arguments: C:\\Users\\shakt\\Desktop\\ai-newsletter\\ai-newsletter-collector\\run_daily.py --send
  4. (Optional) Start in: C:\\Users\\shakt\\Desktop\\ai-newsletter\\ai-newsletter-collector
"""

import subprocess
import sys
import os

# Make sure we run from the collector directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

def run(script: str, extra_args: list[str] = []):
    result = subprocess.run(
        [sys.executable, script] + extra_args,
        cwd=os.path.dirname(os.path.abspath(__file__)),
    )
    if result.returncode != 0:
        print(f"[!] {script} failed with code {result.returncode}")
        sys.exit(result.returncode)


if __name__ == "__main__":
    send = "--send" in sys.argv

    print("=== Step 1: Collecting news ===")
    run("main.py")

    print("\n=== Step 2: Building + sending email ===")
    run("email_builder.py", ["--send"] if send else [])

    print("\n=== Done ===")
