#!/usr/bin/env python3
"""
GitHub Deployment Script for Enrollment Monitor
Initializes git repo and pushes dashboard to GitHub
"""
import os
import subprocess
import sys
from pathlib import Path

def run_command(command, cwd=None):
    """Run a shell command and return success."""
    try:
        result = subprocess.run(command, shell=True, cwd=cwd, check=True, capture_output=True, text=True)
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Command failed: {command}")
        print(f"Error: {e.stderr}")
        return False, e.stderr

def setup_github_repo(repo_url, site_dir='monitoring_site'):
    """Setup GitHub repo for the monitoring site."""
    site_path = Path(site_dir)

    if not site_path.exists():
        print(f"Site directory {site_dir} does not exist!")
        return False

    os.chdir(site_path)

    # Initialize git repo if not already
    if not (site_path / '.git').exists():
        print("Initializing git repository...")
        success, _ = run_command("git init")
        if not success:
            return False

        success, _ = run_command("git add .")
        if not success:
            return False

        success, _ = run_command('git commit -m "Initial enrollment monitor dashboard"')
        if not success:
            return False

    # Add remote if not exists
    success, output = run_command("git remote -v")
    if 'origin' not in output:
        print(f"Adding remote origin: {repo_url}")
        success, _ = run_command(f"git remote add origin {repo_url}")
        if not success:
            return False
    else:
        print("Remote origin already exists")

    # Push to GitHub
    print("Pushing to GitHub...")
    success, _ = run_command("git push -u origin main")
    if not success:
        # Try master branch
        success, _ = run_command("git push -u origin master")
        if not success:
            return False

    return True

def update_and_push(site_dir='monitoring_site'):
    """Update the dashboard and push changes."""
    site_path = Path(site_dir)

    if not site_path.exists():
        print(f"Site directory {site_dir} does not exist!")
        return False

    os.chdir(site_path)

    # Add all changes
    success, _ = run_command("git add .")
    if not success:
        return False

    # Check if there are changes
    success, output = run_command("git status --porcelain")
    if not output.strip():
        print("No changes to commit")
        return True

    # Commit changes
    success, _ = run_command('git commit -m "Update enrollment monitor dashboard"')
    if not success:
        return False

    # Push changes
    success, _ = run_command("git push")
    if not success:
        return False

    return True

def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python deploy_monitor.py setup <github-repo-url>")
        print("  python deploy_monitor.py update")
        return

    command = sys.argv[1]

    if command == 'setup':
        if len(sys.argv) < 3:
            print("Please provide GitHub repo URL")
            return
        repo_url = sys.argv[2]
        success = setup_github_repo(repo_url)
        if success:
            print("GitHub repo setup completed successfully!")
        else:
            print("Failed to setup GitHub repo")
    elif command == 'update':
        success = update_and_push()
        if success:
            print("Dashboard updated and pushed successfully!")
        else:
            print("Failed to update and push dashboard")
    else:
        print("Unknown command. Use 'setup' or 'update'")

if __name__ == '__main__':
    main()