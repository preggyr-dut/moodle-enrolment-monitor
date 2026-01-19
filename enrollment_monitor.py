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
    def __init__(self, log_file=r'C:\moodle_sync\enrolment_sync.log', output_dir='.'):
        self.log_file = Path(log_file)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

    def find_latest_log(self):
        """Check if the specified log file exists and return it."""
        if self.log_file.exists():
            return self.log_file
        return None

    def parse_log_file(self, log_file):
        """Parse the log file to extract key metrics."""
        metrics = {
            'last_run': None,
            'total_records': 0,
            'successful': 0,
            'errors': 0,
            'recent_entries': [],
            'course_not_found': 0,
            'user_creation_failed': 0,
            'faculty_breakdown': {},
            'department_breakdown': {},
            'api_errors': 0,
            'batch_info': []
        }

        # Faculty/Department code mappings (based on course codes observed)
        faculty_codes = {
            'FNLT': 'Faculty of Applied Sciences',
            'CAAU': 'Faculty of Accounting and Informatics', 
            'BSNC': 'Faculty of Applied Sciences',
            'BNMN': 'Faculty of Management Sciences',
            'SHPM': 'Faculty of Management Sciences',
            'IMIC': 'Faculty of Applied Sciences',
            'TRMP': 'Faculty of Engineering and the Built Environment',
            'WWRK': 'Faculty of Engineering and the Built Environment',
            'CMEP': 'Faculty of Engineering and the Built Environment',
            'REMA': 'Faculty of Management Sciences',
            'TAXB': 'Faculty of Accounting and Informatics',
            'CCHB': 'Faculty of Applied Sciences',
            'PBLF': 'Faculty of Management Sciences',
            'TIPP': 'Faculty of Management Sciences',
            'CADR': 'Faculty of Arts and Design',
            'HYSA': 'Faculty of Applied Sciences',
            'LABR': 'Faculty of Applied Sciences',
            'IMAE': 'Faculty of Applied Sciences',
            'FSTX': 'Faculty of Applied Sciences',
            'FPSO': 'Faculty of Applied Sciences',
            'FDPD': 'Faculty of Applied Sciences'
        }

        # Use file modification time as last run
        from datetime import datetime
        mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
        metrics['last_run'] = mtime.strftime('%Y-%m-%d %H:%M:%S')

        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            # Extract total records from the most recent "Processing:" line
            processing_lines = [line for line in lines if 'Processing:' in line]
            if processing_lines:
                # Get the most recent processing line
                latest_processing = processing_lines[-1]
                match = re.search(r'Processing: (\d+) enrolments', latest_processing)
                if match:
                    metrics['total_records'] = int(match.group(1))

            # Count successes, errors, and extract faculty information
            for line in lines:
                if 'Push complete:' in line:
                    # Extract final success/error counts
                    match = re.search(r'Push complete: (\d+) successful, (\d+) failed', line)
                    if match:
                        metrics['successful'] = int(match.group(1))
                        metrics['errors'] = int(match.group(2))
                elif 'Successfully removed' in line:
                    # Count unenrollments as successful operations
                    match = re.search(r'Successfully removed (\d+) enrolments', line)
                    if match:
                        metrics['successful'] += int(match.group(1))
                elif 'Moodle API Error' in line:
                    metrics['api_errors'] += 1
                    metrics['errors'] += 1
                elif 'Failed to' in line.lower() or 'error' in line.lower():
                    if 'Moodle API Error' not in line:  # Avoid double counting
                        metrics['errors'] += 1
                elif 'Course' in line and 'not found' in line:
                    metrics['course_not_found'] += 1
                elif 'Failed to create user' in line:
                    metrics['user_creation_failed'] += 1

                # Extract faculty information from course codes
                for code, faculty in faculty_codes.items():
                    if code in line and ('_SEM' in line or 'course' in line.lower()):
                        if faculty not in metrics['faculty_breakdown']:
                            metrics['faculty_breakdown'][faculty] = 0
                        metrics['faculty_breakdown'][faculty] += 1
                        
                        # Also track department (first 4 chars of course code)
                        dept_code = code
                        if dept_code not in metrics['department_breakdown']:
                            metrics['department_breakdown'][dept_code] = 0
                        metrics['department_breakdown'][dept_code] += 1

            # Get recent entries (last 10 processing lines and recent activity)
            recent_processing = processing_lines[-10:] if len(processing_lines) > 10 else processing_lines
            recent_activity = []
            
            # Get last 10 lines that show activity
            for line in reversed(lines[-50:]):  # Check last 50 lines
                if any(keyword in line.lower() for keyword in ['batch', 'success', 'error', 'complete', 'processing']):
                    recent_activity.append(line.strip())
                    if len(recent_activity) >= 10:
                        break
            
            metrics['recent_entries'] = recent_processing + recent_activity[-5:]  # Combine processing and activity

            # Extract batch information
            batch_lines = [line for line in lines if 'Batch' in line and 'Success' in line]
            for line in batch_lines[-10:]:  # Last 10 batches
                match = re.search(r'Batch (\d+) \((\d+) enrolments\) - (.+)', line)
                if match:
                    metrics['batch_info'].append({
                        'batch': int(match.group(1)),
                        'count': int(match.group(2)),
                        'status': match.group(3)
                    })

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
                <!-- Force redeploy: {datetime.now().strftime('%Y%m%d%H%M%S')} -->
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
            <div class="col-md-4">
                <div class="card metric-card">
                    <div class="card-body text-center">
                        <h5 class="card-title">API Errors</h5>
                        <p class="card-text h4 status-error">{metrics['api_errors']}</p>
                        <small class="text-muted">Moodle API issues</small>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card metric-card">
                    <div class="card-body text-center">
                        <h5 class="card-title">Courses Not Found</h5>
                        <p class="card-text h4 status-warning">{metrics['course_not_found']}</p>
                        <small class="text-muted">Missing courses</small>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card metric-card">
                    <div class="card-body text-center">
                        <h5 class="card-title">User Creation Failed</h5>
                        <p class="card-text h4 status-error">{metrics['user_creation_failed']}</p>
                        <small class="text-muted">Account issues</small>
                    </div>
                </div>
            </div>
        </div>

        <div class="row mb-4">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        <h5>Faculty Breakdown</h5>
                    </div>
                    <div class="card-body">
                        {"".join(f'''
                        <div class="d-flex justify-content-between align-items-center mb-2">
                            <span>{faculty}</span>
                            <span class="badge bg-primary">{count}</span>
                        </div>
                        ''' for faculty, count in sorted(metrics['faculty_breakdown'].items(), key=lambda x: x[1], reverse=True))}
                    </div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        <h5>Department Codes</h5>
                    </div>
                    <div class="card-body">
                        {"".join(f'''
                        <div class="d-flex justify-content-between align-items-center mb-2">
                            <span>{dept}</span>
                            <span class="badge bg-info">{count}</span>
                        </div>
                        ''' for dept, count in sorted(metrics['department_breakdown'].items(), key=lambda x: x[1], reverse=True))}
                    </div>
                </div>
            </div>
        </div>

        <div class="row mb-4">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        <h5>Recent Batch Activity</h5>
                    </div>
                    <div class="card-body">
                        <div style="max-height: 250px; overflow-y: auto;">
                            {"".join(f'''
                            <div class="d-flex justify-content-between align-items-center mb-2">
                                <span>Batch {batch['batch']} ({batch['count']} records)</span>
                                <span class="badge bg-success">{batch['status']}</span>
                            </div>
                            ''' for batch in metrics['batch_info'][-8:])}
                        </div>
                    </div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        <h5>Recent Log Activity</h5>
                    </div>
                    <div class="card-body">
                        <div style="max-height: 250px; overflow-y: auto;">
                            {"".join(f"<p class='mb-1 small text-truncate'>{entry.split(' - ', 2)[-1] if ' - ' in entry else entry}</p>" for entry in metrics['recent_entries'][-15:])}
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