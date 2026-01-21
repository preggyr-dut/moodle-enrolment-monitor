#!/usr/bin/env python3
"""
Quick example of using the enrollment analytics
"""
from enrollment_analytics import EnrollmentAnalytics

# Example usage
analytics = EnrollmentAnalytics(
    server='your-server',
    database='moodle',
    username='your-username',
    password='your-password'
)

if analytics.connect():
    # Get daily enrollment counts for last 30 days
    daily_counts = analytics.get_daily_enrollments(30)
    print("Daily enrollment counts:")
    for day in daily_counts:
        print(f"{day['date']}: {day['count']} enrollments")

    # Get enrollment trends for last 7 days
    trends = analytics.get_enrollment_trends(7)
    print("\nEnrollment trends:")
    for trend in trends:
        print(f"{trend['date']}: {trend['total_enrollments']} enrollments, "
              f"{trend['unique_users']} unique users")

    analytics.close()
else:
    print("Failed to connect to database")