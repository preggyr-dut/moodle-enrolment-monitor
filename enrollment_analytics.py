#!/usr/bin/env python3
"""
Daily Enrollment Count Query
Queries MSSQL database for day-by-day enrollment counts
"""
import pyodbc
import pandas as pd
from datetime import datetime, timedelta
import os
from pathlib import Path

class EnrollmentAnalytics:
    def __init__(self, server=None, database=None, username=None, password=None):
        self.server = server or os.getenv('MSSQL_SERVER', 'localhost')
        self.database = database or os.getenv('MSSQL_DATABASE', 'moodle')
        self.username = username or os.getenv('MSSQL_USERNAME', 'sa')
        self.password = password or os.getenv('MSSQL_PASSWORD', '')

        # Connection string for MSSQL
        self.conn_str = (
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={self.server};"
            f"DATABASE={self.database};"
            f"UID={self.username};"
            f"PWD={self.password};"
            "TrustServerCertificate=yes;"
        )

    def connect(self):
        """Establish database connection"""
        try:
            self.conn = pyodbc.connect(self.conn_str)
            self.cursor = self.conn.cursor()
            print(f"✅ Connected to MSSQL database: {self.database}")
            return True
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            return False

    def get_daily_enrollments(self, days_back=30):
        """Get daily enrollment counts for the specified number of days"""
        try:
            query = """
            SELECT
                CAST(timecreated AS DATE) as enrollment_date,
                COUNT(*) as enrollment_count
            FROM mdl_user_enrolments
            WHERE timecreated >= DATEADD(DAY, -?, GETDATE())
            GROUP BY CAST(timecreated AS DATE)
            ORDER BY enrollment_date DESC
            """

            self.cursor.execute(query, days_back)
            results = self.cursor.fetchall()

            # Convert to list of dictionaries
            daily_counts = []
            for row in results:
                daily_counts.append({
                    'date': row.enrollment_date,
                    'count': row.enrollment_count
                })

            return daily_counts

        except Exception as e:
            print(f"❌ Query failed: {e}")
            return []

    def get_enrollment_trends(self, days_back=30):
        """Get enrollment trends with additional metrics"""
        try:
            query = """
            SELECT
                CAST(ue.timecreated AS DATE) as enrollment_date,
                COUNT(*) as total_enrollments,
                COUNT(DISTINCT ue.userid) as unique_users,
                COUNT(DISTINCT e.courseid) as unique_courses,
                AVG(DATEDIFF(DAY,
                    (SELECT MIN(timecreated) FROM mdl_user_enrolments WHERE userid = ue.userid),
                    ue.timecreated
                )) as avg_days_since_first_enrollment
            FROM mdl_user_enrolments ue
            JOIN mdl_enrol e ON ue.enrolid = e.id
            WHERE ue.timecreated >= DATEADD(DAY, -?, GETDATE())
            GROUP BY CAST(ue.timecreated AS DATE)
            ORDER BY enrollment_date DESC
            """

            self.cursor.execute(query, days_back)
            results = self.cursor.fetchall()

            trends = []
            for row in results:
                trends.append({
                    'date': row.enrollment_date,
                    'total_enrollments': row.total_enrollments,
                    'unique_users': row.unique_users,
                    'unique_courses': row.unique_courses,
                    'avg_days_since_first': float(row.avg_days_since_first_enrollment) if row.avg_days_since_first_enrollment else 0
                })

            return trends

        except Exception as e:
            print(f"❌ Trends query failed: {e}")
            return []

    def get_course_enrollments_by_date(self, target_date=None):
        """Get course-specific enrollment counts for a specific date"""
        if target_date is None:
            target_date = datetime.now().date()

        try:
            query = """
            SELECT
                c.fullname as course_name,
                c.shortname as course_code,
                cat.name as category_name,
                COUNT(ue.id) as enrollment_count
            FROM mdl_user_enrolments ue
            JOIN mdl_enrol e ON ue.enrolid = e.id
            JOIN mdl_course c ON e.courseid = c.id
            LEFT JOIN mdl_course_categories cat ON c.category = cat.id
            WHERE CAST(ue.timecreated AS DATE) = ?
            GROUP BY c.fullname, c.shortname, cat.name
            ORDER BY enrollment_count DESC, c.fullname
            """

            self.cursor.execute(query, target_date)
            results = self.cursor.fetchall()

            course_enrollments = []
            for row in results:
                course_enrollments.append({
                    'course_name': row.course_name,
                    'course_code': row.course_code,
                    'category': row.category_name or 'Uncategorized',
                    'enrollments': row.enrollment_count
                })

            return course_enrollments

        except Exception as e:
            print(f"❌ Course enrollments query failed: {e}")
            return []

    def close(self):
        """Close database connection"""
        if hasattr(self, 'cursor') and self.cursor:
            self.cursor.close()
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()

def main():
    # Initialize analytics
    analytics = EnrollmentAnalytics()

    if not analytics.connect():
        return

    try:
        print("\n" + "="*60)
        print("📊 MOODLE DAILY ENROLLMENT ANALYTICS")
        print("="*60)

        # Get daily enrollment counts
        print(f"\n📅 Daily Enrollment Counts (Last 30 Days):")
        print("-" * 40)
        daily_counts = analytics.get_daily_enrollments(30)

        if daily_counts:
            for day in daily_counts:
                print(f"{day['date']}: {day['count']} enrollments")
        else:
            print("No enrollment data found")

        # Get enrollment trends
        print(f"\n📈 Enrollment Trends (Last 7 Days):")
        print("-" * 40)
        trends = analytics.get_enrollment_trends(7)

        if trends:
            for trend in trends:
                print(f"{trend['date']}: {trend['total_enrollments']} enrollments, "
                      f"{trend['unique_users']} users, {trend['unique_courses']} courses")
        else:
            print("No trend data found")

        # Get today's course enrollments
        today = datetime.now().date()
        print(f"\n📚 Course Enrollments for {today}:")
        print("-" * 40)
        course_enrollments = analytics.get_course_enrollments_by_date(today)

        if course_enrollments:
            for course in course_enrollments[:10]:  # Show top 10
                print(f"{course['course_code']}: {course['enrollments']} enrollments")
            if len(course_enrollments) > 10:
                print(f"... and {len(course_enrollments) - 10} more courses")
        else:
            print("No course enrollment data found for today")

        print(f"\n✅ Analytics completed successfully!")

    except Exception as e:
        print(f"❌ Error during analysis: {e}")

    finally:
        analytics.close()

if __name__ == '__main__':
    main()