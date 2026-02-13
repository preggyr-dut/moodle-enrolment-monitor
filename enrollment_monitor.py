#!/usr/bin/env python3
"""
Enhanced Enrollment Monitoring Dashboard Generator
Handles both original sync logs and simple_enroll.py logs
Generates static HTML dashboard and pushes to GitHub for CloudFlare Pages
"""
import os
import re
import glob
from datetime import datetime
from pathlib import Path
import subprocess
import json

class EnrollmentMonitor:
    def __init__(self, log_file=None, output_dir='.'):
        """Initialize with auto-detection of latest log file"""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Auto-detect the most recent log file if not specified
        if log_file is None:
            self.log_file = self.find_latest_log()
        else:
            self.log_file = Path(log_file)
            
        # Track which log format we're processing
        self.log_format = 'unknown'

    def find_latest_log(self):
        """Find the most recent log file from possible locations"""
        possible_patterns = [
            r'C:\moodle_sync\enrolment_sync.log',
            r'C:\moodle_sync\simple_enroll.log',
            r'C:\moodle_sync\moodle_enroll_*.log',
            r'C:\moodle_sync\src\main_scripts\moodle_sync_*.log',
            r'*.log'  # Current directory logs
        ]
        
        latest_log = None
        latest_time = 0
        
        print("🔍 Scanning for log files...")
        for pattern in possible_patterns:
            for log_path in glob.glob(pattern):
                if Path(log_path).exists():
                    mtime = Path(log_path).stat().st_mtime
                    if mtime > latest_time:
                        latest_time = mtime
                        latest_log = Path(log_path)
                        print(f"  Found: {log_path} ({datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')})")
        
        if latest_log:
            print(f"✅ Selected: {latest_log}")
            return latest_log
        else:
            print("⚠️  No log files found, using default")
            return Path(r'C:\moodle_sync\enrolment_sync.log')

    def detect_log_format(self, lines):
        """Detect whether this is simple_enroll.py format or original format"""
        sample = ' '.join(lines[:50]).lower()
        
        if 'resolved' in sample and 'users' in sample:
            return 'simple_enroll'
        elif 'push complete:' in sample:
            return 'original_push'
        elif 'batch' in sample and 'enrolments' in sample:
            return 'original_batch'
        elif 'prepared' in sample and 'enrollments' in sample:
            return 'simple_enroll'
        else:
            return 'unknown'

    def parse_log_file(self, log_file):
        """Parse the log file to extract key metrics - supports multiple formats"""
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
            'batch_info': [],
            'users_found': 0,
            'users_missing': 0,
            'courses_found': 0,
            'courses_missing': 0,
            'skipped_records': 0,
            'log_format': 'unknown',
            'processing_time': None,
            'total_batches': 0,
            'successful_batches': 0,
            'failed_batches': 0
        }

        # Faculty/Department code mappings (based on course codes observed)
        faculty_codes = {
            'ANLA': 'Faculty of Arts and Design',
            'RSMH': 'Faculty of Applied Sciences',
            'AOMT': 'Faculty of Management Sciences',
            'CSTN': 'Faculty of Accounting and Informatics',
            'RERE': 'Faculty of Applied Sciences',
            'RSPM': 'Faculty of Management Sciences',
            'APEM': 'Faculty of Management Sciences',
            'ARMP': 'Faculty of Management Sciences',
            'PMIR': 'Faculty of Management Sciences',
            'ADFM': 'Faculty of Accounting and Informatics',
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

        try:
            # Get file modification time
            mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
            metrics['last_run'] = mtime.strftime('%Y-%m-%d %H:%M:%S')
            
            # Read log file
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Detect log format
            metrics['log_format'] = self.detect_log_format(lines)
            print(f"📋 Detected log format: {metrics['log_format']}")
            
            # Track batch processing
            current_batch = None
            batch_success = True
            
            for i, line in enumerate(lines):
                line_lower = line.lower()
                
                # Extract course codes for faculty breakdown
                for code, faculty in faculty_codes.items():
                    if code in line and ('_SEM' in line or 'course' in line_lower):
                        # Faculty breakdown
                        if faculty not in metrics['faculty_breakdown']:
                            metrics['faculty_breakdown'][faculty] = 0
                        metrics['faculty_breakdown'][faculty] += 1
                        
                        # Department breakdown (first 4 chars of course code)
                        dept_code = code
                        if dept_code not in metrics['department_breakdown']:
                            metrics['department_breakdown'][dept_code] = 0
                        metrics['department_breakdown'][dept_code] += 1
                
                # PARSE SIMPLE_ENROLL FORMAT
                if metrics['log_format'] == 'simple_enroll':
                    # User resolution
                    if 'resolved' in line_lower and 'users' in line_lower:
                        match = re.search(r'Resolved (\d+)/(\d+) users', line)
                        if match:
                            metrics['users_found'] = int(match.group(1))
                            total_users = int(match.group(2))
                            metrics['users_missing'] = total_users - metrics['users_found']
                    
                    # Course resolution
                    elif 'resolved' in line_lower and 'courses' in line_lower:
                        match = re.search(r'Resolved (\d+)/(\d+) courses', line)
                        if match:
                            metrics['courses_found'] = int(match.group(1))
                            total_courses = int(match.group(2))
                            metrics['courses_missing'] = total_courses - metrics['courses_found']
                    
                    # Prepared enrollments
                    elif 'prepared' in line_lower and 'enrollments' in line_lower:
                        match = re.search(r'Prepared (\d+)[,]*(\d*).*\((\d+)[,]*(\d*) skipped\)', line)
                        if match:
                            metrics['total_records'] = int(match.group(1).replace(',', ''))
                            metrics['skipped_records'] = int(match.group(3).replace(',', ''))
                    
                    # Success/Error summary
                    elif 'enrollment complete' in line_lower:
                        # Look ahead for success/failed line
                        for j in range(i, min(i+5, len(lines))):
                            if 'successful:' in lines[j].lower() and 'failed:' in lines[j].lower():
                                match = re.search(r'successful: (\d+).*failed: (\d+)', lines[j])
                                if match:
                                    metrics['successful'] = int(match.group(1))
                                    metrics['errors'] = int(match.group(2))
                                break
                
                # PARSE ORIGINAL BATCH FORMAT (YOUR CURRENT LOG)
                else:
                    # Total records from summary
                    if 'total enrollments:' in line_lower:
                        match = re.search(r'Total enrollments: (\d+)', line)
                        if match:
                            metrics['total_records'] = int(match.group(1))
                    
                    # User resolution stats
                    if 'unique users:' in line_lower:
                        match = re.search(r'Unique users: (\d+)', line)
                        if match:
                            metrics['users_found'] = int(match.group(1))
                    
                    # Course resolution stats
                    if 'unique courses:' in line_lower:
                        match = re.search(r'Unique courses: (\d+)', line)
                        if match:
                            metrics['courses_found'] = int(match.group(1))
                    
                    # Batch processing lines
                    if 'batch' in line_lower and 'enrollments' in line_lower:
                        # Start of a batch
                        match = re.search(r'Batch (\d+): (\d+) enrollments', line)
                        if match:
                            current_batch = {
                                'batch': int(match.group(1)),
                                'count': int(match.group(2)),
                                'status': 'Processing'
                            }
                            metrics['total_batches'] += 1
                    
                    # Batch success/failure
                    elif 'success' in line_lower and ('batch' in line_lower or '✓' in line):
                        if current_batch:
                            current_batch['status'] = 'Success'
                            metrics['batch_info'].append(current_batch)
                            metrics['successful_batches'] += 1
                            metrics['successful'] += current_batch['count']
                            current_batch = None
                    
                    elif 'fail' in line_lower and ('batch' in line_lower or '✗' in line):
                        if current_batch:
                            current_batch['status'] = 'Failed'
                            metrics['batch_info'].append(current_batch)
                            metrics['failed_batches'] += 1
                            metrics['errors'] += current_batch['count']
                            current_batch = None
                    
                    # API Errors
                    elif 'api call' in line_lower and 'failed' in line_lower:
                        metrics['api_errors'] += 1
                    
                    # Final summary line
                    elif 'enrollment complete:' in line_lower:
                        match = re.search(r'(\d+) success, (\d+) failed', line)
                        if match:
                            metrics['successful'] = int(match.group(1))
                            metrics['errors'] = int(match.group(2))
                    
                    # Prepared enrollments (with skipped)
                    elif 'prepared' in line_lower and 'enrollments' in line_lower:
                        match = re.search(r'Prepared (\d+) enrollments \((\d+) skipped\)', line)
                        if match:
                            metrics['total_records'] = int(match.group(1))
                            metrics['skipped_records'] = int(match.group(2))
            
            # Get recent entries (last 30 lines)
            metrics['recent_entries'] = [line.strip() for line in lines[-30:] if line.strip()]
            
            # Calculate derived metrics
            if metrics['successful'] == 0 and metrics['errors'] == 0:
                # Try to calculate from batches
                metrics['successful'] = sum(b['count'] for b in metrics['batch_info'] if b['status'] == 'Success')
                metrics['errors'] = sum(b['count'] for b in metrics['batch_info'] if b['status'] == 'Failed')
            
            # Ensure total_records is at least successful+errors
            if metrics['total_records'] == 0:
                metrics['total_records'] = metrics['successful'] + metrics['errors'] + metrics['skipped_records']
            
        except Exception as e:
            print(f"❌ Error parsing log file: {e}")
            import traceback
            traceback.print_exc()

        return metrics

    def generate_html(self, metrics):
        """Generate enhanced HTML dashboard from metrics."""
        
        # Determine badge color based on log format
        format_badge = {
            'simple_enroll': '<span class="badge bg-success">simple_enroll.py</span>',
            'original_push': '<span class="badge bg-primary">original push</span>',
            'original_batch': '<span class="badge bg-info">batch sync</span>',
            'unknown': '<span class="badge bg-secondary">unknown format</span>'
        }.get(metrics['log_format'], '<span class="badge bg-secondary">unknown</span>')
        
        # Calculate success rate
        success_rate = (metrics['successful'] / max(metrics['total_records'], 1)) * 100
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Moodle Enrollment Sync Monitor</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {{ background-color: #f8f9fa; }}
        .metric-card {{ transition: transform 0.2s; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .metric-card:hover {{ transform: translateY(-2px); box-shadow: 0 4px 8px rgba(0,0,0,0.15); }}
        .status-healthy {{ color: #28a745; font-weight: bold; }}
        .status-warning {{ color: #ffc107; font-weight: bold; }}
        .status-error {{ color: #dc3545; font-weight: bold; }}
        .section-header {{ border-left: 4px solid #007bff; padding-left: 10px; margin: 20px 0 15px 0; }}
        .progress {{ height: 8px; margin-bottom: 10px; }}
        .log-line {{ 
            font-family: 'Courier New', monospace; 
            font-size: 0.8rem;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}
        .log-line:hover {{
            white-space: normal;
            background-color: #f8f9fa;
        }}
    </style>
</head>
<body>
    <div class="container mt-5">
        <div class="row">
            <div class="col-12">
                <h1 class="text-center mb-4">
                    Moodle Enrollment Sync Monitor
                    {format_badge}
                </h1>
                <p class="text-center text-muted">
                    Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | 
                    Log file: {self.log_file.name} | 
                    Format: {metrics['log_format']}
                </p>
                <!-- Force redeploy: {datetime.now().strftime('%Y%m%d%H%M%S')} -->
            </div>
        </div>

        <!-- Main Metrics Row -->
        <div class="row mb-4">
            <div class="col-md-3">
                <div class="card metric-card">
                    <div class="card-body text-center">
                        <h5 class="card-title text-muted">Last Sync</h5>
                        <p class="card-text h4">{metrics['last_run'] or 'N/A'}</p>
                        <small class="text-muted">Log timestamp</small>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card metric-card">
                    <div class="card-body text-center">
                        <h5 class="card-title text-muted">Total Enrollments</h5>
                        <p class="card-text h4">{metrics['total_records']:,}</p>
                        <small class="text-muted">Records processed</small>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card metric-card">
                    <div class="card-body text-center">
                        <h5 class="card-title text-muted">Successful</h5>
                        <p class="card-text h4 status-healthy">{metrics['successful']:,}</p>
                        <small class="text-muted">{success_rate:.1f}% success rate</small>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card metric-card">
                    <div class="card-body text-center">
                        <h5 class="card-title text-muted">Errors</h5>
                        <p class="card-text h4 status-error">{metrics['errors']:,}</p>
                        <small class="text-muted">{100-success_rate:.1f}% error rate</small>
                    </div>
                </div>
            </div>
        </div>"""

        # Add Resolution Metrics
        if metrics.get('users_found', 0) > 0 or metrics.get('courses_found', 0) > 0:
            html += f"""
        <!-- Resolution Metrics Row -->
        <div class="row mb-4">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header bg-info text-white">
                        <h5 class="mb-0">👥 User Resolution</h5>
                    </div>
                    <div class="card-body">
                        <div class="row text-center">
                            <div class="col-6">
                                <h3 class="status-healthy">{metrics.get('users_found', 0):,}</h3>
                                <small>Found in Moodle</small>
                                <div class="progress">
                                    <div class="progress-bar bg-success" style="width: {((metrics.get('users_found',0)/max(metrics.get('users_found',0)+metrics.get('users_missing',0),1))*100):.1f}%"></div>
                                </div>
                            </div>
                            <div class="col-6">
                                <h3 class="status-error">{metrics.get('users_missing', 0):,}</h3>
                                <small>Missing from Moodle</small>
                                <div class="progress">
                                    <div class="progress-bar bg-danger" style="width: {((metrics.get('users_missing',0)/max(metrics.get('users_found',0)+metrics.get('users_missing',0),1))*100):.1f}%"></div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header bg-info text-white">
                        <h5 class="mb-0">📚 Course Resolution</h5>
                    </div>
                    <div class="card-body">
                        <div class="row text-center">
                            <div class="col-6">
                                <h3 class="status-healthy">{metrics.get('courses_found', 0):,}</h3>
                                <small>Found in Moodle</small>
                                <div class="progress">
                                    <div class="progress-bar bg-success" style="width: {((metrics.get('courses_found',0)/max(metrics.get('courses_found',0)+metrics.get('courses_missing',0),1))*100):.1f}%"></div>
                                </div>
                            </div>
                            <div class="col-6">
                                <h3 class="status-error">{metrics.get('courses_missing', 0):,}</h3>
                                <small>Missing from Moodle</small>
                                <div class="progress">
                                    <div class="progress-bar bg-danger" style="width: {((metrics.get('courses_missing',0)/max(metrics.get('courses_found',0)+metrics.get('courses_missing',0),1))*100):.1f}%"></div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>"""

        # Skipped Records
        if metrics.get('skipped_records', 0) > 0:
            html += f"""
        <div class="row mb-4">
            <div class="col-md-12">
                <div class="card">
                    <div class="card-body">
                        <div class="row">
                            <div class="col-md-4 text-center">
                                <h5>Skipped Records</h5>
                                <h3 class="status-warning">{metrics.get('skipped_records', 0):,}</h3>
                                <small>Enrollments skipped due to missing users/courses</small>
                            </div>
                            <div class="col-md-4 text-center">
                                <h5>API Errors</h5>
                                <h3 class="status-error">{metrics.get('api_errors', 0)}</h3>
                                <small>Moodle API communication issues</small>
                            </div>
                            <div class="col-md-4 text-center">
                                <h5>Success Rate</h5>
                                <h3 class="status-healthy">{success_rate:.1f}%</h3>
                                <small>Of total records</small>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>"""

        # Faculty and Department Breakdown
        if metrics['faculty_breakdown'] or metrics['department_breakdown']:
            html += f"""
        <div class="section-header">
            <h4>📊 Enrollment Distribution</h4>
        </div>
        <div class="row mb-4">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header bg-primary text-white">
                        <h5 class="mb-0">🏫 Faculty Breakdown</h5>
                    </div>
                    <div class="card-body" style="max-height: 400px; overflow-y: auto;">
                        {self.generate_distribution_html(metrics['faculty_breakdown'], 'primary')}
                    </div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header bg-info text-white">
                        <h5 class="mb-0">📋 Department Codes</h5>
                    </div>
                    <div class="card-body" style="max-height: 400px; overflow-y: auto;">
                        {self.generate_distribution_html(metrics['department_breakdown'], 'info')}
                    </div>
                </div>
            </div>
        </div>"""

        # Recent Activity
        html += f"""
        <div class="section-header">
            <h4>⚡ Recent Activity</h4>
        </div>
        <div class="row mb-4">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header bg-success text-white">
                        <h5 class="mb-0">📦 Recent Batch Activity</h5>
                    </div>
                    <div class="card-body" style="max-height: 300px; overflow-y: auto;">
                        {self.generate_batch_html(metrics['batch_info'])}
                    </div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header bg-secondary text-white">
                        <h5 class="mb-0">📝 Recent Log Entries</h5>
                    </div>
                    <div class="card-body" style="max-height: 300px; overflow-y: auto;">
                        {self.generate_log_entries_html(metrics['recent_entries'])}
                    </div>
                </div>
            </div>
        </div>

        <!-- Footer -->
        <div class="row mt-4">
            <div class="col-12">
                <div class="card">
                    <div class="card-body text-center text-muted">
                        <small>
                            Generated by Enhanced Enrollment Monitor Script | 
                            Log: {self.log_file} | 
                            Format: {metrics['log_format']} |
                            {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                        </small>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>"""
        return html

    def generate_distribution_html(self, data, badge_color='primary'):
        """Generate HTML for distribution lists"""
        if not data:
            return '<p class="text-muted text-center">No data available</p>'
        
        sorted_items = sorted(data.items(), key=lambda x: x[1], reverse=True)
        total = sum(data.values())
        
        html = ''
        for item, count in sorted_items[:20]:  # Show top 20
            percentage = (count / total * 100) if total > 0 else 0
            html += f'''
            <div class="d-flex justify-content-between align-items-center mb-2">
                <span>{item}</span>
                <div>
                    <span class="badge bg-{badge_color} me-2">{count}</span>
                    <small class="text-muted">({percentage:.1f}%)</small>
                </div>
            </div>
            <div class="progress mb-3">
                <div class="progress-bar bg-{badge_color}" style="width: {percentage}%"></div>
            </div>'''
        
        if len(sorted_items) > 20:
            html += f'<p class="text-muted text-center mt-2">... and {len(sorted_items) - 20} more</p>'
        
        return html

    def generate_batch_html(self, batch_info):
        """Generate HTML for batch information"""
        if not batch_info:
            return '<p class="text-muted text-center">No batch data available</p>'
        
        html = ''
        for batch in batch_info[-15:]:  # Show last 15 batches
            status_class = 'success' if 'Success' in batch['status'] else 'warning'
            html += f'''
            <div class="d-flex justify-content-between align-items-center mb-2 border-bottom pb-1">
                <span>Batch {batch['batch']}</span>
                <span>
                    <span class="badge bg-secondary me-2">{batch['count']} records</span>
                    <span class="badge bg-{status_class}">{batch['status']}</span>
                </span>
            </div>'''
        
        return html

    def generate_log_entries_html(self, entries):
        """Generate HTML for log entries"""
        if not entries:
            return '<p class="text-muted text-center">No recent entries</p>'
        
        html = '<div class="list-group list-group-flush">'
        for entry in entries[-20:]:  # Show last 20 entries
            # Color code based on content
            entry_lower = entry.lower()
            if 'error' in entry_lower or 'fail' in entry_lower or '✗' in entry:
                color_class = 'text-danger'
                icon = '❌'
            elif 'success' in entry_lower or '✓' in entry or '✅' in entry:
                color_class = 'text-success'
                icon = '✅'
            elif 'warning' in entry_lower or '⚠️' in entry:
                color_class = 'text-warning'
                icon = '⚠️'
            else:
                color_class = 'text-muted'
                icon = '📝'
            
            # Truncate long entries
            if len(entry) > 100:
                display_entry = entry[:97] + '...'
            else:
                display_entry = entry
            
            html += f'<div class="list-group-item {color_class} small py-1 log-line" title="{entry}">{icon} {display_entry}</div>'
        
        html += '</div>'
        return html

    def generate_dashboard(self):
        """Main method to generate the dashboard."""
        if not self.log_file.exists():
            print(f"❌ Log file not found: {self.log_file}")
            return False

        print(f"\n{'='*60}")
        print(f"📊 Generating Enrollment Dashboard")
        print(f"{'='*60}")
        print(f"📁 Log file: {self.log_file}")
        print(f"📁 Output directory: {self.output_dir}")
        
        metrics = self.parse_log_file(self.log_file)
        
        # Print summary to console
        print(f"\n📋 Summary:")
        print(f"  • Format: {metrics['log_format']}")
        print(f"  • Last run: {metrics['last_run']}")
        print(f"  • Total records: {metrics['total_records']:,}")
        print(f"  • Successful: {metrics['successful']:,}")
        print(f"  • Errors: {metrics['errors']:,}")
        
        if metrics.get('users_found', 0) > 0:
            print(f"  • Users found: {metrics['users_found']:,}")
            print(f"  • Users missing: {metrics['users_missing']:,}")
        if metrics.get('courses_found', 0) > 0:
            print(f"  • Courses found: {metrics['courses_found']:,}")
            print(f"  • Courses missing: {metrics['courses_missing']:,}")
        if metrics.get('skipped_records', 0) > 0:
            print(f"  • Skipped: {metrics['skipped_records']:,}")
        if metrics.get('api_errors', 0) > 0:
            print(f"  • API Errors: {metrics['api_errors']}")
        
        html_content = self.generate_html(metrics)

        # Write HTML file
        html_file = self.output_dir / 'index.html'
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)

        print(f"\n✅ Dashboard generated: {html_file}")
        print(f"{'='*60}\n")
        return True

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate Enrollment Monitor Dashboard')
    parser.add_argument('--log-file', help='Specific log file to process')
    parser.add_argument('--output-dir', default='.', help='Output directory for dashboard')
    
    args = parser.parse_args()
    
    monitor = EnrollmentMonitor(
        log_file=args.log_file,
        output_dir=args.output_dir
    )
    
    success = monitor.generate_dashboard()

    if success:
        print("✅ Dashboard generation completed successfully!")
    else:
        print("❌ Failed to generate dashboard.")
        exit(1)

if __name__ == '__main__':
    main()