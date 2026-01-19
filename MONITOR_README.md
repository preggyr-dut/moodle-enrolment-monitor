# Moodle Enrollment Monitor

A monitoring dashboard for Moodle enrollment synchronization that displays sync status, metrics, and recent activity on a public website.

## Features

- Real-time enrollment sync metrics
- Success/error counts
- Recent processing activity
- Responsive Bootstrap UI
- Automatic deployment to CloudFlare Pages

## Setup Instructions

### 1. Create GitHub Repository

1. Go to [GitHub.com](https://github.com) and create a new repository
2. Name it something like `moodle-enrollment-monitor`
3. Make it public (required for CloudFlare Pages)
4. Don't initialize with README (we'll generate our own)

### 2. Connect to CloudFlare Pages

1. Go to your [CloudFlare Dashboard](https://dash.cloudflare.com)
2. Navigate to **Pages**
3. Click **Create a project**
4. Choose **Connect to Git**
5. Select your GitHub account and repository
6. Configure build settings:
   - **Build command**: (leave empty)
   - **Build output directory**: `/` (root)
   - **Root directory**: `/` (leave empty)
7. Click **Save and Deploy**

### 3. Initial Setup

Run the setup script:

```bash
python deploy_monitor.py setup https://github.com/YOUR_USERNAME/YOUR_REPO.git
```

This will:
- Generate the initial dashboard
- Initialize git repository
- Push to GitHub
- Trigger CloudFlare Pages deployment

### 4. Automated Updates

Create a scheduled task (cron job) to update the dashboard:

**On Linux/Mac:**
```bash
# Add to crontab (crontab -e)
*/30 * * * * cd /path/to/moodle_sync && python enrollment_monitor.py && python deploy_monitor.py update
```

**On Windows (Task Scheduler):**
1. Open Task Scheduler
2. Create new task
3. Set trigger (e.g., every 30 minutes)
4. Set action: Start a program
5. Program: `python.exe`
6. Arguments: `enrollment_monitor.py && deploy_monitor.py update`
7. Start in: `C:\moodle-enrolment-monitor`

## Manual Updates

To manually update the dashboard:

```bash
python enrollment_monitor.py
python deploy_monitor.py update
```

## Configuration

The monitor uses the enrollment sync log file located at `C:\moodle_sync\enrolment_sync.log`. This file contains the latest processing data from Moodle enrollment synchronization.

## Files

- `enrollment_monitor.py` - Generates the HTML dashboard from the sync log
- `deploy_monitor.py` - Handles GitHub deployment
- `index.html` - Generated dashboard (deployed to CloudFlare Pages)

## Security Note

The dashboard displays enrollment processing information. Ensure your CloudFlare Pages site has appropriate access controls if sensitive data is shown.