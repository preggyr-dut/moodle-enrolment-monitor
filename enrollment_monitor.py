#!/usr/bin/env python3
"""
Enrollment Monitoring Dashboard Generator
Generates a static HTML dashboard from sync logs and pushes to GitHub for CloudFlare Pages
"""
import os
import re
import glob
from datetime import datetime
from pathlib import Path
import subprocess
import json

class EnrollmentMonitor:
    def __init__(self, log_dir='.', output_dir='monitoring_site'):
        self.log_dir = Path(log_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

    def find_latest_log(self, pattern='enrolment_sync*.log'):
        """Find the most recent enrollment sync log file with actual data."""
        log_files = list(self.log_dir.glob(pattern))
        if not log_files:
            return None
        
        # Sort by modification time, newest first
        log_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
        
        # Try to find a log with actual processing data
        for log_file in log_files:
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if 'Processing:' in content and 'Sync complete:' in content:
                        return log_file
            except:
                continue
        
        # Fallback to newest
        return log_files[0] if log_files else None

    def parse_log_file(self, log_file):
        """Parse the log file to extract key metrics."""
        metrics = {
            'last_run': None,
            'total_records': 0,
            'successful': 0,
            'errors': 0,
            'recent_entries': [],
            'course_not_found': 0,
            'user_creation_failed': 0
        }

        # Use file modification time as last run
        from datetime import datetime
        mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
        metrics['last_run'] = mtime.strftime('%Y-%m-%d %H:%M:%S')

        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            # Count total records processed
            processing_lines = [line for line in lines if 'Processing:' in line]
            metrics['total_records'] = len(processing_lines)

            # Count successes and errors
            for line in lines:
                if 'Successfully enrolled' in line or 'Enrolment successful' in line:
                    metrics['successful'] += 1
                elif 'Failed to' in line or 'Error' in line.lower():
                    metrics['errors'] += 1
                elif 'Course' in line and 'not found' in line:
                    metrics['course_not_found'] += 1
                elif 'Failed to create user' in line:
                    metrics['user_creation_failed'] += 1

            # Get recent entries (last 20 processing lines)
            recent_processing = processing_lines[-20:] if len(processing_lines) > 20 else processing_lines
            metrics['recent_entries'] = [line.strip() for line in recent_processing]

            # Look for summary line
            for line in reversed(lines):
                if 'Sync complete:' in line:
                    summary_match = re.search(r'Sync complete: (\d+) successful, (\d+) errors', line)
                    if summary_match:
                        metrics['successful'] = int(summary_match.group(1))
                        metrics['errors'] = int(summary_match.group(2))
                    break

        except Exception as e:
            print(f"Error parsing log file: {e}")

        return metrics

    def generate_html(self, metrics):
        """Generate HTML dashboard from metrics."""
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Moodle Enrollment Sync Monitor</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {{ background-color: #f8f9fa; }}
        .metric-card {{ transition: transform 0.2s; }}
        .metric-card:hover {{ transform: translateY(-2px); }}
        .status-healthy {{ color: #28a745; }}
        .status-warning {{ color: #ffc107; }}
        .status-error {{ color: #dc3545; }}
    </style>
</head>
<body>
    <div class="container mt-5">
        <div class="row">
            <div class="col-12">
                <h1 class="text-center mb-4">Moodle Enrollment Sync Monitor</h1>
                <p class="text-center text-muted">Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
        </div>

        <div class="row mb-4">
            <div class="col-md-3">
                <div class="card metric-card">
                    <div class="card-body text-center">
                        <h5 class="card-title">Last Sync</h5>
                        <p class="card-text h4">{metrics['last_run'] or 'N/A'}</p>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card metric-card">
                    <div class="card-body text-center">
                        <h5 class="card-title">Total Records</h5>
                        <p class="card-text h4">{metrics['total_records']}</p>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card metric-card">
                    <div class="card-body text-center">
                        <h5 class="card-title">Successful</h5>
                        <p class="card-text h4 status-healthy">{metrics['successful']}</p>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card metric-card">
                    <div class="card-body text-center">
                        <h5 class="card-title">Errors</h5>
                        <p class="card-text h4 status-error">{metrics['errors']}</p>
                    </div>
                </div>
            </div>
        </div>

        <div class="row mb-4">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        <h5>Issues Summary</h5>
                    </div>
                    <div class="card-body">
                        <ul class="list-group list-group-flush">
                            <li class="list-group-item d-flex justify-content-between align-items-center">
                                Courses not found
                                <span class="badge bg-warning">{metrics['course_not_found']}</span>
                            </li>
                            <li class="list-group-item d-flex justify-content-between align-items-center">
                                User creation failed
                                <span class="badge bg-danger">{metrics['user_creation_failed']}</span>
                            </li>
                        </ul>
                    </div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        <h5>Recent Activity</h5>
                    </div>
                    <div class="card-body">
                        <div style="max-height: 300px; overflow-y: auto;">
                            {"".join(f"<p class='mb-1 small'>{entry}</p>" for entry in metrics['recent_entries'])}
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <div class="row">
            <div class="col-12">
                <div class="card">
                    <div class="card-body text-center text-muted">
                        <small>Generated by Enrollment Monitor Script</small>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>"""
        return html

    def generate_dashboard(self):
        """Main method to generate the dashboard."""
        log_file = self.find_latest_log()
        if not log_file:
            print("No log files found!")
            return False

        print(f"Processing log file: {log_file}")
        metrics = self.parse_log_file(log_file)
        html_content = self.generate_html(metrics)

        # Write HTML file
        html_file = self.output_dir / 'index.html'
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)

        print(f"Dashboard generated at: {html_file}")
        return True

def main():
    monitor = EnrollmentMonitor()
    success = monitor.generate_dashboard()

    if success:
        print("Dashboard generation completed successfully!")
    else:
        print("Failed to generate dashboard.")

if __name__ == '__main__':
    main()