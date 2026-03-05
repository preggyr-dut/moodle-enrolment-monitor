# registrar_report_actual.py
import pandas as pd
from datetime import datetime
from pathlib import Path

print("=" * 80)
print("🎓 REGISTRAR'S OFFICE - ACTUAL ENROLLMENT REPORT")
print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 80)

# File paths
PEOPLESOFT_FILE = "C:\\integrator\\enrollment-system\\pipeline_data\\03_output\\simple_ready_20260303_083234.csv"
MOODLE_FILE = "C:\\Users\\preggyr\\Documents\\moodle_user_enrolments_04032026.txt"
OUTPUT_DIR = Path("registrar_reports_final")
OUTPUT_DIR.mkdir(exist_ok=True)

# Step 1: Load PeopleSoft data
print(f"\n📥 Loading PeopleSoft enrollment data...")
ps_df = pd.read_csv(PEOPLESOFT_FILE)
print(f"✅ Loaded {len(ps_df):,} enrollment records")
print(f"   Columns: {list(ps_df.columns)}")

# Rename PeopleSoft columns to standard names (if needed)
# Assuming your file has 'username' and 'course1' columns
ps_df.rename(columns={'username': 'student_id', 'course1': 'course'}, inplace=True)

# PeopleSoft statistics
ps_total_students = ps_df['student_id'].nunique()
ps_total_enrollments = len(ps_df)
ps_unique_courses = ps_df['course'].nunique()

print(f"\n📊 PEOPLESOFT STATISTICS:")
print(f"   • Total Students: {ps_total_students:,}")
print(f"   • Total Enrollments: {ps_total_enrollments:,}")
print(f"   • Unique Courses: {ps_unique_courses:,}")

# Step 2: Load Moodle data
print(f"\n📥 Loading Moodle enrollment data...")

# Read the text file (assuming it's comma-separated with headers)
moodle_df = pd.read_csv(MOODLE_FILE)
print(f"✅ Loaded {len(moodle_df):,} enrollment records")
print(f"   Columns: {list(moodle_df.columns)}")

# Rename Moodle columns to standard names
# Your file has 'course1', 'username' - adjust if column names are different
moodle_df.rename(columns={'username': 'student_id', 'course1': 'course'}, inplace=True)

# Clean student IDs (remove any @dut4life.ac.za if present)
moodle_df['student_id'] = moodle_df['student_id'].astype(str).str.replace('@dut4life.ac.za', '', regex=False)

# Moodle statistics
moodle_total_students = moodle_df['student_id'].nunique()
moodle_total_enrollments = len(moodle_df)
moodle_unique_courses = moodle_df['course'].nunique()

print(f"\n📊 MOODLE STATISTICS:")
print(f"   • Total Students: {moodle_total_students:,}")
print(f"   • Total Enrollments: {moodle_total_enrollments:,}")
print(f"   • Unique Courses: {moodle_unique_courses:,}")

# Step 3: Compare students
print("\n🔍 COMPARING STUDENTS BETWEEN SYSTEMS")

ps_students = set(ps_df['student_id'].astype(str))
moodle_students = set(moodle_df['student_id'].astype(str))

students_in_both = ps_students.intersection(moodle_students)
students_only_in_ps = ps_students - moodle_students
students_only_in_moodle = moodle_students - ps_students

print(f"\n📊 STUDENT COMPARISON:")
print(f"   • Students in both systems: {len(students_in_both):,}")
print(f"   • Students only in PeopleSoft: {len(students_only_in_ps):,}")
print(f"   • Students only in Moodle: {len(students_only_in_moodle):,}")

# Step 4: Compare enrollments
print("\n🔍 COMPARING ENROLLMENTS")

# Create enrollment keys (student + course combination)
ps_df['enrollment_key'] = ps_df['student_id'].astype(str) + '|' + ps_df['course'].astype(str)
moodle_df['enrollment_key'] = moodle_df['student_id'].astype(str) + '|' + moodle_df['course'].astype(str)

ps_enrollments = set(ps_df['enrollment_key'].unique())
moodle_enrollments = set(moodle_df['enrollment_key'].unique())

enrollments_in_both = ps_enrollments.intersection(moodle_enrollments)
enrollments_only_in_ps = ps_enrollments - moodle_enrollments
enrollments_only_in_moodle = moodle_enrollments - ps_enrollments

print(f"\n📊 ENROLLMENT COMPARISON:")
print(f"   • Enrollments in both systems: {len(enrollments_in_both):,}")
print(f"   • Enrollments only in PeopleSoft: {len(enrollments_only_in_ps):,}")
print(f"   • Enrollments only in Moodle: {len(enrollments_only_in_moodle):,}")

# Step 5: Compare courses
ps_courses = set(ps_df['course'].unique())
moodle_courses = set(moodle_df['course'].unique())

courses_in_both = ps_courses.intersection(moodle_courses)
courses_only_in_ps = ps_courses - moodle_courses
courses_only_in_moodle = moodle_courses - ps_courses

print(f"\n📚 COURSE COMPARISON:")
print(f"   • Courses in both systems: {len(courses_in_both):,}")
print(f"   • Courses only in PeopleSoft: {len(courses_only_in_ps):,}")
print(f"   • Courses only in Moodle: {len(courses_only_in_moodle):,}")

# Step 6: Calculate completion percentages
student_completion = (moodle_total_students / ps_total_students) * 100 if ps_total_students > 0 else 0
enrollment_completion = (moodle_total_enrollments / ps_total_enrollments) * 100 if ps_total_enrollments > 0 else 0
course_completion = (moodle_unique_courses / ps_unique_courses) * 100 if ps_unique_courses > 0 else 0

print(f"\n📊 COMPLETION PERCENTAGES:")
print(f"   • Student Sync: {student_completion:.1f}%")
print(f"   • Enrollment Sync: {enrollment_completion:.1f}%")
print(f"   • Course Creation: {course_completion:.1f}%")

# Step 7: Create summary table
print("\n📋 SUMMARY TABLE")
print("=" * 90)
print(f"{'Metric':<30} {'PeopleSoft':>15} {'Moodle':>15} {'Difference':>15} {'% Complete':>12}")
print("-" * 90)
print(f"{'Total Students':<30} {ps_total_students:>15,} {moodle_total_students:>15,} {ps_total_students - moodle_total_students:>15,} {student_completion:>11.1f}%")
print(f"{'Total Enrollments':<30} {ps_total_enrollments:>15,} {moodle_total_enrollments:>15,} {ps_total_enrollments - moodle_total_enrollments:>15,} {enrollment_completion:>11.1f}%")
print(f"{'Unique Courses':<30} {ps_unique_courses:>15,} {moodle_unique_courses:>15,} {ps_unique_courses - moodle_unique_courses:>15,} {course_completion:>11.1f}%")
print("-" * 90)

# Step 8: Generate final report
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
report_file = OUTPUT_DIR / f"enrollment_comparison_report_{timestamp}.txt"

with open(report_file, 'w', encoding='utf-8') as f:
    f.write("=" * 100 + "\n")
    f.write("ENROLLMENT COMPARISON REPORT\n")
    f.write(f"Durban University of Technology\n")
    f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    f.write("=" * 100 + "\n\n")
    
    f.write("EXECUTIVE SUMMARY\n")
    f.write("-" * 50 + "\n")
    f.write(f"PeopleSoft contains {ps_total_students:,} unique students with {ps_total_enrollments:,} enrollments\n")
    f.write(f"Moodle contains {moodle_total_students:,} unique students with {moodle_total_enrollments:,} enrollments\n")
    f.write(f"Student sync completion: {student_completion:.1f}%\n")
    f.write(f"Enrollment sync completion: {enrollment_completion:.1f}%\n\n")
    
    f.write("KEY FINDINGS\n")
    f.write("-" * 50 + "\n")
    f.write(f"• Students in both systems: {len(students_in_both):,}\n")
    f.write(f"• Students only in PeopleSoft: {len(students_only_in_ps):,}\n")
    f.write(f"• Students only in Moodle: {len(students_only_in_moodle):,}\n")
    f.write(f"• Enrollments in both systems: {len(enrollments_in_both):,}\n")
    f.write(f"• Enrollments only in PeopleSoft: {len(enrollments_only_in_ps):,}\n")
    f.write(f"• Enrollments only in Moodle: {len(enrollments_only_in_moodle):,}\n\n")
    
    f.write("RECOMMENDATIONS\n")
    f.write("-" * 50 + "\n")
    if len(students_only_in_ps) > 0:
        f.write(f"• Add {len(students_only_in_ps):,} PeopleSoft students to Moodle\n")
    if len(students_only_in_moodle) > 0:
        f.write(f"• Review {len(students_only_in_moodle):,} Moodle students not in PeopleSoft (possibly from previous years)\n")
    if len(enrollments_only_in_ps) > 0:
        f.write(f"• Complete {len(enrollments_only_in_ps):,} missing enrollments in Moodle\n")
    if len(courses_only_in_ps) > 0:
        f.write(f"• Create {len(courses_only_in_ps):,} missing courses in Moodle\n")
    
    f.write("\n" + "=" * 100 + "\n")
    f.write("END OF REPORT\n")
    f.write("=" * 100 + "\n")

print(f"\n✅ Final report saved to: {report_file}")

print("\n📋 QUICK SUMMARY:")
print(f"   • Moodle Students: {moodle_total_students:,} / {ps_total_students:,} ({student_completion:.1f}%)")
print(f"   • Moodle Enrollments: {moodle_total_enrollments:,} / {ps_total_enrollments:,} ({enrollment_completion:.1f}%)")
print(f"   • Moodle Courses: {moodle_unique_courses:,} / {ps_unique_courses:,} ({course_completion:.1f}%)")
print("=" * 80)

# Optional: Save detailed discrepancies to CSV files
if len(enrollments_only_in_ps) > 0:
    missing_df = ps_df[ps_df['enrollment_key'].isin(enrollments_only_in_ps)][['student_id', 'course']]
    missing_df.to_csv(OUTPUT_DIR / f"missing_in_moodle_{timestamp}.csv", index=False)
    print(f"   • Saved {len(missing_df)} missing enrollments to CSV")

if len(enrollments_only_in_moodle) > 0:
    extra_df = moodle_df[moodle_df['enrollment_key'].isin(enrollments_only_in_moodle)][['student_id', 'course']]
    extra_df.to_csv(OUTPUT_DIR / f"extra_in_moodle_{timestamp}.csv", index=False)
    print(f"   • Saved {len(extra_df)} extra enrollments to CSV")