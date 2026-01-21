#!/usr/bin/env python3
"""
Daily Enrollment Dashboard Updater
Combines sync log monitoring with database analytics
"""
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
import configparser
import json

# Import our modules
from enrollment_monitor import EnrollmentMonitor
from enrollment_analytics import EnrollmentAnalytics

class CombinedDashboard:
    def __init__(self, config_file='config.ini'):
        self.config_file = Path(config_file)
        self.db_config = self.load_db_config()

        # Initialize components
        self.monitor = EnrollmentMonitor()
        self.analytics = EnrollmentAnalytics(
            server=self.db_config.get('server'),
            database=self.db_config.get('database'),
            username=self.db_config.get('username'),
            password=self.db_config.get('password')
        )

    def load_db_config(self):
        """Load database configuration"""
        config = {
            'server': os.getenv('MSSQL_SERVER', 'localhost'),
            'database': os.getenv('MSSQL_DATABASE', 'moodle'),
            'username': os.getenv('MSSQL_USERNAME', 'sa'),
            'password': os.getenv('MSSQL_PASSWORD', '')
        }

        if self.config_file.exists():
            try:
                parser = configparser.ConfigParser()
                parser.read(self.config_file)

                if 'MSSQL' in parser:
                    config.update({
                        'server': parser['MSSQL'].get('server', config['server']),
                        'database': parser['MSSQL'].get('database', config['database']),
                        'username': parser['MSSQL'].get('username', config['username']),
                        'password': parser['MSSQL'].get('password', config['password'])
                    })
            except Exception as e:
                print(f"Warning: Could not load config file: {e}")

        return config

    def generate_combined_dashboard(self):
        """Generate dashboard with both sync log and database data"""
        print("🔄 Generating combined enrollment dashboard...")

        # Get sync log metrics
        log_metrics = self.monitor.parse_log_file(self.monitor.log_file)

        # Get database analytics
        db_connected = self.analytics.connect()
        db_metrics = {}

        if db_connected:
            try:
                # Get daily enrollment counts
                daily_counts = self.analytics.get_daily_enrollments(30)
                db_metrics['daily_enrollments'] = daily_counts

                # Get enrollment trends
                trends = self.analytics.get_enrollment_trends(7)
                db_metrics['trends'] = trends

                # Get today's course enrollments
                today_courses = self.analytics.get_course_enrollments_by_date()
                db_metrics['today_courses'] = today_courses

                # Calculate summary stats
                if daily_counts:
                    total_30_days = sum(day['count'] for day in daily_counts)
                    db_metrics['total_30_days'] = total_30_days
                    db_metrics['avg_daily'] = round(total_30_days / len(daily_counts), 1)

                print("✅ Database analytics retrieved successfully")
            except Exception as e:
                print(f"❌ Database analytics failed: {e}")
                db_metrics = {'error': str(e)}
            finally:
                self.analytics.close()
        else:
            print("⚠️  Database connection failed - dashboard will show sync log data only")
            db_metrics = {'error': 'Database connection failed'}

        # Generate enhanced HTML
        html_content = self.generate_enhanced_html(log_metrics, db_metrics)

        # Save dashboard
        dashboard_file = Path('index.html')
        with open(dashboard_file, 'w', encoding='utf-8') as f:
            f.write(html_content)

        print(f"✅ Combined dashboard generated: {dashboard_file}")
        return True

    def generate_enhanced_html(self, log_metrics, db_metrics):
        """Generate HTML with both sync log and database data"""
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
        .db-section {{ background-color: #e3f2fd; border-left: 4px solid #2196f3; }}
        .sync-section {{ background-color: #f3e5f5; border-left: 4px solid #9c27b0; }}
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

        <!-- Database Status -->
        <div class="row mb-4">
            <div class="col-12">
                <div class="card {'bg-success text-white' if 'error' not in db_metrics else 'bg-warning text-dark'}">
                    <div class="card-body text-center">
                        <h5>Database Connection Status</h5>
                        <p class="mb-0">
                            {'✅ Connected - Real-time enrollment data available' if 'error' not in db_metrics else f'⚠️  Disconnected - {db_metrics.get("error", "Unknown error")}'}
                        </p>
                    </div>
                </div>
            </div>
        </div>

        <!-- Main Metrics -->
        <div class="row mb-4">
            <div class="col-md-3">
                <div class="card metric-card sync-section">
                    <div class="card-body text-center">
                        <h5 class="card-title">Last Sync</h5>
                        <p class="card-text h4">{log_metrics['last_run'] or 'N/A'}</p>
                        <small class="text-muted">From sync logs</small>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card metric-card sync-section">
                    <div class="card-body text-center">
                        <h5 class="card-title">Sync Records</h5>
                        <p class="card-text h4">{log_metrics['total_records']}</p>
                        <small class="text-muted">Processed in sync</small>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card metric-card db-section">
                    <div class="card-body text-center">
                        <h5 class="card-title">30-Day Total</h5>
                        <p class="card-text h4 status-healthy">{db_metrics.get('total_30_days', 'N/A')}</p>
                        <small class="text-muted">From database</small>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card metric-card db-section">
                    <div class="card-body text-center">
                        <h5 class="card-title">Daily Average</h5>
                        <p class="card-text h4 status-healthy">{db_metrics.get('avg_daily', 'N/A')}</p>
                        <small class="text-muted">Last 30 days</small>
                    </div>
                </div>
            </div>
        </div>

        <!-- Success/Error Metrics -->
        <div class="row mb-4">
            <div class="col-md-3">
                <div class="card metric-card sync-section">
                    <div class="card-body text-center">
                        <h5 class="card-title">Sync Success</h5>
                        <p class="card-text h4 status-healthy">{log_metrics['successful']}</p>
                        <small class="text-muted">From sync logs</small>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card metric-card sync-section">
                    <div class="card-body text-center">
                        <h5 class="card-title">Sync Errors</h5>
                        <p class="card-text h4 status-error">{log_metrics['errors']}</p>
                        <small class="text-muted">From sync logs</small>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card metric-card sync-section">
                    <div class="card-body text-center">
                        <h5 class="card-title">API Errors</h5>
                        <p class="card-text h4 status-error">{log_metrics['api_errors']}</p>
                        <small class="text-muted">Moodle API issues</small>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card metric-card sync-section">
                    <div class="card-body text-center">
                        <h5 class="card-title">User Creation Failed</h5>
                        <p class="card-text h4 status-error">{log_metrics['user_creation_failed']}</p>
                        <small class="text-muted">Account issues</small>
                    </div>
                </div>
            </div>
        </div>"""

        # Add database analytics sections if available
        if 'error' not in db_metrics:
            html += self.generate_database_sections(db_metrics)

        # Add sync log sections
        html += self.generate_sync_sections(log_metrics)

        # Close HTML
        html += """
        <div class="row">
            <div class="col-12">
                <div class="card">
                    <div class="card-body text-center text-muted">
                        <small>Generated by Combined Enrollment Monitor Script</small>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>"""

        return html

    def generate_database_sections(self, db_metrics):
        """Generate HTML sections for database analytics"""
        html = ""

        # Daily Enrollment Chart
        if 'daily_enrollments' in db_metrics and db_metrics['daily_enrollments']:
            html += """
        <div class="row mb-4">
            <div class="col-md-6">
                <div class="card db-section">
                    <div class="card-header">
                        <h5>📊 Daily Enrollment Counts (Database)</h5>
                    </div>
                    <div class="card-body">
                        <div style="max-height: 300px; overflow-y: auto;">
            """

            for day in db_metrics['daily_enrollments'][:14]:  # Show last 14 days
                html += f'''
                        <div class="d-flex justify-content-between align-items-center mb-2">
                            <span>{day['date']}</span>
                            <span class="badge bg-primary">{day['count']}</span>
                        </div>'''

            html += """
                        </div>
                    </div>
                </div>
            </div>
            """

        # Today's Course Enrollments
        if 'today_courses' in db_metrics and db_metrics['today_courses']:
            html += """
            <div class="col-md-6">
                <div class="card db-section">
                    <div class="card-header">
                        <h5>📚 Today's Course Enrollments</h5>
                    </div>
                    <div class="card-body">
                        <div style="max-height: 300px; overflow-y: auto;">
            """

            for course in db_metrics['today_courses'][:10]:  # Show top 10
                html += f'''
                        <div class="d-flex justify-content-between align-items-center mb-2">
                            <span class="text-truncate" style="max-width: 70%;">{course['course_code']}</span>
                            <span class="badge bg-success">{course['enrollments']}</span>
                        </div>'''

            html += """
                        </div>
                    </div>
                </div>
            </div>
        </div>
            """

        return html

    def generate_sync_sections(self, log_metrics):
        """Generate HTML sections for sync log data"""
        html = f"""
        <!-- Faculty and Department Breakdowns -->
        <div class="row mb-4">
            <div class="col-md-6">
                <div class="card sync-section">
                    <div class="card-header">
                        <h5>🏫 Faculty Breakdown</h5>
                    </div>
                    <div class="card-body">
                        {"".join(f'''
                        <div class="d-flex justify-content-between align-items-center mb-2">
                            <span>{faculty}</span>
                            <span class="badge bg-primary">{count}</span>
                        </div>
                        ''' for faculty, count in sorted(log_metrics['faculty_breakdown'].items(), key=lambda x: x[1], reverse=True))}
                    </div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="card sync-section">
                    <div class="card-header">
                        <h5>📋 Department Codes</h5>
                    </div>
                    <div class="card-body">
                        {"".join(f'''
                        <div class="d-flex justify-content-between align-items-center mb-2">
                            <span>{dept}</span>
                            <span class="badge bg-info">{count}</span>
                        </div>
                        ''' for dept, count in sorted(log_metrics['department_breakdown'].items(), key=lambda x: x[1], reverse=True)[:20])}
                    </div>
                </div>
            </div>
        </div>

        <!-- Batch Activity and Recent Logs -->
        <div class="row mb-4">
            <div class="col-md-6">
                <div class="card sync-section">
                    <div class="card-header">
                        <h5>⚡ Recent Batch Activity</h5>
                    </div>
                    <div class="card-body">
                        <div style="max-height: 250px; overflow-y: auto;">
                            {"".join(f'''
                            <div class="d-flex justify-content-between align-items-center mb-2">
                                <span>Batch {batch['batch']} ({batch['count']} records)</span>
                                <span class="badge bg-success">{batch['status']}</span>
                            </div>
                            ''' for batch in log_metrics['batch_info'][-8:])}
                        </div>
                    </div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="card sync-section">
                    <div class="card-header">
                        <h5>📝 Recent Log Activity</h5>
                    </div>
                    <div class="card-body">
                        <div style="max-height: 250px; overflow-y: auto;">
                            {"".join(f"<p class='mb-1 small text-truncate'>{entry.split(' - ', 2)[-1] if ' - ' in entry else entry}</p>" for entry in log_metrics['recent_entries'][-15:])}
                        </div>
                    </div>
                </div>
            </div>
        </div>"""

        return html

def main():
    dashboard = CombinedDashboard()

    if dashboard.generate_combined_dashboard():
        print("✅ Combined dashboard generated successfully!")
    else:
        print("❌ Failed to generate dashboard")

if __name__ == '__main__':
    main()