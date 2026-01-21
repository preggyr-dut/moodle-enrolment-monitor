# Moodle Enrollment Monitor

A monitoring dashboard for Moodle enrollment synchronization that displays sync status, metrics, and recent activity on a public website.

## Features

- Real-time enrollment sync metrics from log files
- **NEW:** Direct database analytics with day-by-day enrollment counts
- Success/error counts with detailed breakdowns
- Faculty and department distribution analysis
- API error tracking and batch processing details
- Recent processing activity and batch status
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

## Database Analytics Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Database Connection

Copy the example configuration file:

```bash
cp config.example.ini config.ini
```

Edit `config.ini` with your MSSQL database credentials:

```ini
[MSSQL]
server = your-server-name
database = moodle
username = your-username
password = your-password
port = 1433
```

Alternatively, set environment variables:
- `MSSQL_SERVER`
- `MSSQL_DATABASE`
- `MSSQL_USERNAME`
- `MSSQL_PASSWORD`

### 3. Test Database Connection

Run the analytics script:

```bash
python enrollment_analytics.py
```

Or use the batch file:
```bash
run_analytics.bat
```

### 4. Generate Combined Dashboard

To create a dashboard with both sync logs and database data:

```bash
python combined_dashboard.py
```

This will generate an enhanced dashboard showing:
- Sync log metrics (as before)
- Real database enrollment counts by date
- Course-specific enrollment data
- Enrollment trends and analytics

## Files

- `enrollment_monitor.py` - Generates dashboard from sync log files
- `enrollment_analytics.py` - Queries MSSQL database for enrollment analytics
- `combined_dashboard.py` - Creates enhanced dashboard with both log and database data
- `deploy_monitor.py` - Handles GitHub deployment
- `requirements.txt` - Python dependencies
- `config.example.ini` - Database configuration template
- `run_analytics.bat` - Windows batch file to run analytics
- `index.html` - Generated dashboard (deployed to CloudFlare Pages)

## Security Note

The dashboard displays enrollment processing information. Ensure your CloudFlare Pages site has appropriate access controls if sensitive data is shown.