#!/usr/bin/env python3
"""
Automated Enrollment Monitor Update
Generates dashboard and pushes to GitHub in one command
"""
import subprocess
import sys
from pathlib import Path

def run_command(command, cwd=None):
    """Run a shell command."""
    try:
        result = subprocess.run(command, shell=True, cwd=cwd, check=True, capture_output=True, text=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Command failed: {command}")
        print(f"Error: {e.stderr}")
        return False

def update_monitor():
    """Update the enrollment monitor dashboard."""
    print("Generating dashboard...")
    success = run_command("python enrollment_monitor.py")
    if not success:
        print("Failed to generate dashboard")
        return False

    print("Pushing to GitHub...")
    success = run_command("python deploy_monitor.py update")
    if not success:
        print("Failed to push to GitHub")
        return False

    print("Monitor updated successfully!")
    return True

def main():
    if len(sys.argv) > 1 and sys.argv[1] == 'setup':
        if len(sys.argv) < 3:
            print("Usage: python update_monitor.py setup <github-repo-url>")
            return
        repo_url = sys.argv[2]
        print("Setting up monitor...")
        success = run_command(f"python deploy_monitor.py setup {repo_url}")
        if success:
            print("Setup completed! Monitor will be available at your CloudFlare Pages URL once deployed.")
        else:
            print("Setup failed")
    else:
        success = update_monitor()
        if not success:
            sys.exit(1)

if __name__ == '__main__':
    main()