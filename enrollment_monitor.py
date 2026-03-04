#!/usr/bin/env python3
"""
Enhanced Enrollment Monitoring Dashboard Generator
Handles logs from:
- simple_enroll.py (moodle_enroll_*.log)
- flexible_pipeline.py (pipeline_*.log)  
- seis_wrapper.py (seis_wrapper_*.log)
- Original sync logs (enrolment_sync.log)
"""

import os
import re
import glob
from datetime import datetime, timedelta
from pathlib import Path
import json

class EnrollmentMonitor:
    def __init__(self, log_dirs=None, output_dir='.'):
        """
        Initialize monitor with multiple log directories
        
        Args:
            log_dirs: List of directories to scan for logs
            output_dir: Output directory for dashboard
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Default log directories to scan
        if log_dirs is None:
            self.log_dirs = [
                r'C:\integrator\enrollment-system\logs',  # Pipeline logs
                r'C:\integrator\enrollment-system',       # Root directory
                r'C:\moodle_sync',                         # Original sync
                r'C:\moodle_sync\src\main_scripts',       # Scripts directory
                '.',                                        # Current directory
            ]
        else:
            self.log_dirs = log_dirs
            
        # Log patterns to look for
        self.log_patterns = {
            'pipeline': 'pipeline_*.log',
            'wrapper': 'seis_wrapper_*.log',
            'enroll': 'moodle_enroll_*.log',
            'sync': 'enrolment_sync.log',
            'simple': 'simple_enroll.log',
            'results': 'enrollment_results_*.json'
        }
        
        # Find all logs
        self.logs = self.find_all_logs()
        
    def find_all_logs(self):
        """Find all log files in configured directories"""
        all_logs = {}
        
        print("\n🔍 Scanning for log files...")
        
        for log_dir in self.log_dirs:
            dir_path = Path(log_dir)
            if not dir_path.exists():
                continue
                
            for log_type, pattern in self.log_patterns.items():
                for log_file in dir_path.glob(pattern):
                    mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
                    all_logs[str(log_file)] = {
                        'path': log_file,
                        'type': log_type,
                        'mtime': mtime,
                        'size': log_file.stat().st_size / 1024  # KB
                    }
                    print(f"  📄 {log_type}: {log_file.name} ({mtime.strftime('%Y-%m-%d %H:%M:%S')})")
        
        # Sort by modification time (newest first)
        sorted_logs = dict(sorted(all_logs.items(), 
                                 key=lambda x: x[1]['mtime'], 
                                 reverse=True))
        
        print(f"\n✅ Found {len(sorted_logs)} log files")
        return sorted_logs
    
    def get_latest_by_type(self, log_type):
        """Get the latest log of a specific type"""
        type_logs = {k: v for k, v in self.logs.items() if v['type'] == log_type}
        if type_logs:
            return list(type_logs.values())[0]['path']
        return None
    
    def parse_pipeline_log(self, log_file):
        """Parse flexible_pipeline.py log format"""
        metrics = {
            'source_type': 'unknown',
            'steps_completed': [],
            'total_records': 0,
            'successful': 0,
            'errors': 0,
            'extraction_file': None,
            'enrollment_file': None,
            'processing_time': None
        }
        
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            for line in lines:
                # Extract source type
                if 'Source type:' in line:
                    metrics['source_type'] = line.split('Source type:')[-1].strip()
                
                # Extract step completion
                if 'STEP 1:' in line and 'complete' in line.lower():
                    metrics['steps_completed'].append('extraction')
                elif 'STEP 2:' in line and 'complete' in line.lower():
                    metrics['steps_completed'].append('processing')
                elif 'STEP 3:' in line and 'complete' in line.lower():
                    metrics['steps_completed'].append('enrollment')
                
                # Extract enrollment stats
                if 'Enrollments:' in line:
                    match = re.search(r'Enrollments: (\d+) successful, (\d+) failed', line)
                    if match:
                        metrics['successful'] = int(match.group(1))
                        metrics['errors'] = int(match.group(2))
                        metrics['total_records'] = metrics['successful'] + metrics['errors']
                
                # Extract file paths
                if 'Extraction complete:' in line:
                    match = re.search(r'Extraction complete: (.+\.csv)', line)
                    if match:
                        metrics['extraction_file'] = Path(match.group(1)).name
                
                if 'enrollment_ready' in line:
                    match = re.search(r'Output file: (.+\.csv)', line)
                    if match:
                        metrics['enrollment_file'] = Path(match.group(1)).name
                
                # Extract processing time
                if 'Time:' in line and 'seconds' in line:
                    match = re.search(r'Time: ([\d.]+) seconds', line)
                    if match:
                        metrics['processing_time'] = float(match.group(1))
                        
        except Exception as e:
            print(f"Error parsing pipeline log: {e}")
        
        return metrics
    
    def parse_enrollment_results(self, json_file):
        """Parse enrollment_results_*.json files"""
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return {
                'total_records': data.get('total_records_processed', 0),
                'successful': data.get('successful_operations', 0),
                'errors': data.get('failed_operations', 0),
                'users_found': data.get('users_found', 0),
                'users_missing': data.get('unique_users', 0) - data.get('users_found', 0),
                'courses_found': data.get('courses_found', 0),
                'courses_missing': data.get('unique_courses', 0) - data.get('courses_found', 0),
                'users_created': data.get('users_created', 0),
                'dry_run': data.get('dry_run', True),
                'batch_size': data.get('batch_size', 500),
                'workers': data.get('workers', 4),
                'parallel': data.get('parallel', False)
            }
        except Exception as e:
            print(f"Error parsing results JSON: {e}")
            return None
    
    def generate_combined_metrics(self):
        """Generate combined metrics from all log types"""
        combined = {
            'last_run': None,
            'total_records_24h': 0,
            'successful_24h': 0,
            'errors_24h': 0,
            'pipelines': [],
            'recent_enrollments': [],
            'system_status': 'healthy',
            'log_summary': {}
        }
        
        cutoff_24h = datetime.now() - timedelta(hours=24)
        
        for log_path_str, log_info in self.logs.items():
            log_path = log_info['path']
            log_type = log_info['type']
            log_time = log_info['mtime']
            
            # Track latest run overall
            if combined['last_run'] is None or log_time > combined['last_run']:
                combined['last_run'] = log_time
            
            # Summarize by type
            if log_type not in combined['log_summary']:
                combined['log_summary'][log_type] = {
                    'count': 0,
                    'latest': None,
                    'size_kb': 0
                }
            
            combined['log_summary'][log_type]['count'] += 1
            combined['log_summary'][log_type]['size_kb'] += log_info['size']
            
            if combined['log_summary'][log_type]['latest'] is None or log_time > combined['log_summary'][log_type]['latest']:
                combined['log_summary'][log_type]['latest'] = log_time
            
            # Parse based on type
            metrics = None
            if log_type == 'results' and log_time > cutoff_24h:
                metrics = self.parse_enrollment_results(log_path)
                if metrics:
                    combined['recent_enrollments'].append({
                        'time': log_time,
                        'file': log_path.name,
                        'metrics': metrics
                    })
                    combined['total_records_24h'] += metrics['total_records']
                    combined['successful_24h'] += metrics['successful']
                    combined['errors_24h'] += metrics['errors']
            
            elif log_type == 'pipeline' and log_time > cutoff_24h:
                metrics = self.parse_pipeline_log(log_path)
                if metrics:
                    combined['pipelines'].append({
                        'time': log_time,
                        'file': log_path.name,
                        'metrics': metrics
                    })
        
        # Determine system status
        if combined['errors_24h'] > 100:
            combined['system_status'] = 'critical'
        elif combined['errors_24h'] > 10:
            combined['system_status'] = 'warning'
        elif combined['total_records_24h'] == 0:
            combined['system_status'] = 'inactive'
        
        return combined
    
    def generate_html(self, combined_metrics):
        """Generate enhanced HTML dashboard"""
        
        status_colors = {
            'healthy': 'success',
            'warning': 'warning',
            'critical': 'danger',
            'inactive': 'secondary'
        }
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Moodle Enrollment System Monitor</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {{ background-color: #f8f9fa; }}
        .metric-card {{ transition: transform 0.2s; }}
        .metric-card:hover {{ transform: translateY(-2px); box-shadow: 0 4px 8px rgba(0,0,0,0.15); }}
        .log-entry {{ 
            font-family: 'Courier New', monospace; 
            font-size: 0.85rem;
            border-left: 3px solid transparent;
            padding: 2px 8px;
            margin: 2px 0;
        }}
        .log-pipeline {{ border-left-color: #007bff; background-color: #f0f7ff; }}
        .log-enroll {{ border-left-color: #28a745; background-color: #f0fff0; }}
        .log-wrapper {{ border-left-color: #ffc107; background-color: #fff8e0; }}
    </style>
</head>
<body>
    <div class="container mt-4">
        <!-- Header -->
        <div class="row mb-4">
            <div class="col-12">
                <div class="card">
                    <div class="card-body">
                        <h1 class="text-center">
                            🎓 Moodle Enrollment System Monitor
                            <span class="badge bg-{status_colors.get(combined_metrics['system_status'], 'secondary')} ms-2">
                                {combined_metrics['system_status'].upper()}
                            </span>
                        </h1>
                        <p class="text-center text-muted">
                            Last activity: {combined_metrics['last_run'].strftime('%Y-%m-%d %H:%M:%S') if combined_metrics['last_run'] else 'Never'} |
                            Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                        </p>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- 24h Summary -->
        <div class="row mb-4">
            <div class="col-md-4">
                <div class="card metric-card">
                    <div class="card-body text-center">
                        <h5 class="text-muted">Last 24h Enrollments</h5>
                        <h2 class="text-primary">{combined_metrics['total_records_24h']:,}</h2>
                        <small>Total records processed</small>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card metric-card">
                    <div class="card-body text-center">
                        <h5 class="text-muted">Successful</h5>
                        <h2 class="text-success">{combined_metrics['successful_24h']:,}</h2>
                        <small>{combined_metrics['successful_24h']/max(combined_metrics['total_records_24h'],1)*100:.1f}% success rate</small>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card metric-card">
                    <div class="card-body text-center">
                        <h5 class="text-muted">Errors</h5>
                        <h2 class="text-danger">{combined_metrics['errors_24h']:,}</h2>
                        <small>{combined_metrics['errors_24h']/max(combined_metrics['total_records_24h'],1)*100:.1f}% error rate</small>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Log Files Summary -->
        <div class="row mb-4">
            <div class="col-12">
                <div class="card">
                    <div class="card-header bg-info text-white">
                        <h5 class="mb-0">📋 Log Files Overview</h5>
                    </div>
                    <div class="card-body">
                        <div class="row">
                            {self.generate_log_summary_html(combined_metrics['log_summary'])}
                        </div>
                    </div>
                </div>
            </div>
        </div>"""
        
        # Recent Enrollments from JSON Results
        if combined_metrics['recent_enrollments']:
            html += f"""
        <div class="row mb-4">
            <div class="col-12">
                <div class="card">
                    <div class="card-header bg-success text-white">
                        <h5 class="mb-0">✅ Recent Enrollment Operations (Last 24h)</h5>
                    </div>
                    <div class="card-body">
                        <div class="table-responsive">
                            <table class="table table-sm table-hover">
                                <thead>
                                    <tr>
                                        <th>Time</th>
                                        <th>File</th>
                                        <th>Records</th>
                                        <th>Success</th>
                                        <th>Errors</th>
                                        <th>Users Found</th>
                                        <th>Users Missing</th>
                                        <th>Courses Found</th>
                                        <th>Users Created</th>
                                        <th>Mode</th>
                                    </tr>
                                </thead>
                                <tbody>"""
            
            for enroll in combined_metrics['recent_enrollments'][:10]:
                m = enroll['metrics']
                html += f"""
                                    <tr>
                                        <td>{enroll['time'].strftime('%H:%M:%S')}</td>
                                        <td><small>{enroll['file'][:30]}</small></td>
                                        <td class="text-center">{m['total_records']:,}</td>
                                        <td class="text-success text-center">{m['successful']:,}</td>
                                        <td class="text-danger text-center">{m['errors']:,}</td>
                                        <td class="text-center">{m['users_found']:,}</td>
                                        <td class="text-center text-warning">{m['users_missing']:,}</td>
                                        <td class="text-center">{m['courses_found']:,}</td>
                                        <td class="text-center">{m['users_created']:,}</td>
                                        <td><span class="badge bg-{'warning' if m['dry_run'] else 'success'}">{'DRY RUN' if m['dry_run'] else 'LIVE'}</span></td>
                                    </tr>"""
            
            html += """
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        </div>"""
        
        # Recent Pipeline Runs
        if combined_metrics['pipelines']:
            html += f"""
        <div class="row mb-4">
            <div class="col-12">
                <div class="card">
                    <div class="card-header bg-primary text-white">
                        <h5 class="mb-0">🔄 Recent Pipeline Runs</h5>
                    </div>
                    <div class="card-body">
                        <div class="table-responsive">
                            <table class="table table-sm">
                                <thead>
                                    <tr>
                                        <th>Time</th>
                                        <th>Source Type</th>
                                        <th>Steps</th>
                                        <th>Records</th>
                                        <th>Success</th>
                                        <th>Errors</th>
                                        <th>Extraction File</th>
                                        <th>Processing Time</th>
                                    </tr>
                                </thead>
                                <tbody>"""
            
            for pipeline in combined_metrics['pipelines']:
                m = pipeline['metrics']
                steps_badge = ''.join([f'<span class="badge bg-success me-1">✓{s[:3]}</span>' for s in m['steps_completed']])
                html += f"""
                                    <tr>
                                        <td>{pipeline['time'].strftime('%H:%M:%S')}</td>
                                        <td>{m['source_type']}</td>
                                        <td>{steps_badge}</td>
                                        <td>{m['total_records']:,}</td>
                                        <td class="text-success">{m['successful']:,}</td>
                                        <td class="text-danger">{m['errors']:,}</td>
                                        <td><small>{m['extraction_file'] or 'N/A'}</small></td>
                                        <td>{m['processing_time']:.1f}s</td>
                                    </tr>"""
            
            html += """
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        </div>"""
        
        # Recent Log Entries from All Logs
        html += f"""
        <div class="row mb-4">
            <div class="col-12">
                <div class="card">
                    <div class="card-header bg-secondary text-white">
                        <h5 class="mb-0">📝 Recent Activity (All Logs)</h5>
                    </div>
                    <div class="card-body" style="max-height: 400px; overflow-y: auto;">
                        {self.get_recent_log_entries()}
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Footer -->
        <div class="row">
            <div class="col-12">
                <div class="card">
                    <div class="card-body text-center text-muted small">
                        Generated by Enhanced Enrollment Monitor | 
                        Scanning {len(self.logs)} log files in {len(self.log_dirs)} directories |
                        {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>"""
        
        return html
    
    def generate_log_summary_html(self, log_summary):
        """Generate HTML for log summary"""
        html = ''
        for log_type, info in log_summary.items():
            latest = info['latest'].strftime('%H:%M:%S') if info['latest'] else 'Never'
            html += f"""
                <div class="col-md-3 mb-3">
                    <div class="card">
                        <div class="card-body text-center">
                            <h6 class="text-muted">{log_type.upper()}</h6>
                            <h3>{info['count']}</h3>
                            <small>Files</small>
                            <p class="mt-2 mb-0"><small class="text-muted">Latest: {latest}</small></p>
                            <p><small class="text-muted">Total: {info['size_kb']:.0f} KB</small></p>
                        </div>
                    </div>
                </div>"""
        return html
    
    def get_recent_log_entries(self, max_entries=50):
        """Get recent entries from all log files"""
        all_entries = []
        
        for log_path_str, log_info in list(self.logs.items())[:10]:  # Check latest 10 logs
            log_path = log_info['path']
            log_type = log_info['type']
            
            try:
                with open(log_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    # Get last 10 lines from each log
                    for line in lines[-10:]:
                        if line.strip():
                            all_entries.append({
                                'time': log_info['mtime'],
                                'type': log_type,
                                'line': line.strip(),
                                'file': log_path.name
                            })
            except Exception:
                continue
        
        # Sort by time (newest first) and limit
        all_entries.sort(key=lambda x: x['time'], reverse=True)
        
        html = '<div class="list-group list-group-flush">'
        for entry in all_entries[:max_entries]:
            # Truncate long lines
            line = entry['line']
            if len(line) > 150:
                line = line[:147] + '...'
            
            # Color code by type
            type_class = {
                'pipeline': 'log-pipeline',
                'enroll': 'log-enroll',
                'wrapper': 'log-wrapper',
                'results': 'log-results',
                'sync': 'log-sync'
            }.get(entry['type'], '')
            
            html += f'<div class="log-entry {type_class} small" title="{entry["file"]}"><span class="text-muted">[{entry["time"].strftime("%H:%M:%S")}]</span> {line}</div>'
        
        html += '</div>'
        return html
    
    def generate_dashboard(self):
        """Generate the complete dashboard"""
        print("\n" + "="*60)
        print("📊 Generating Enhanced Enrollment Dashboard")
        print("="*60)
        
        # Find all logs
        self.find_all_logs()
        
        # Generate combined metrics
        combined_metrics = self.generate_combined_metrics()
        
        # Print summary
        print(f"\n📋 System Status: {combined_metrics['system_status'].upper()}")
        print(f"  • Last activity: {combined_metrics['last_run'].strftime('%Y-%m-%d %H:%M:%S') if combined_metrics['last_run'] else 'Never'}")
        print(f"  • Last 24h: {combined_metrics['total_records_24h']:,} records")
        print(f"  • Success rate: {combined_metrics['successful_24h']/max(combined_metrics['total_records_24h'],1)*100:.1f}%")
        
        print(f"\n📋 Log Summary:")
        for log_type, info in combined_metrics['log_summary'].items():
            print(f"  • {log_type}: {info['count']} files ({info['size_kb']:.0f} KB)")
        
        # Generate HTML
        html_content = self.generate_html(combined_metrics)
        
        # Write to file
        html_file = self.output_dir / 'index.html'
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"\n✅ Dashboard generated: {html_file}")
        print("="*60)
        
        return True


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate Enhanced Enrollment Monitor Dashboard')
    parser.add_argument('--log-dirs', nargs='+', help='Directories to scan for logs')
    parser.add_argument('--output-dir', default='.', help='Output directory for dashboard')
    
    args = parser.parse_args()
    
    monitor = EnrollmentMonitor(
        log_dirs=args.log_dirs,
        output_dir=args.output_dir
    )
    
    success = monitor.generate_dashboard()
    
    if success:
        print("\n✅ Dashboard generation completed successfully!")
    else:
        print("\n❌ Failed to generate dashboard.")
        exit(1)


if __name__ == '__main__':
    main()