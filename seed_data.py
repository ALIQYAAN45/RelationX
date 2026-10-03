
import sqlite3

from database import get_connection, create_tables

create_tables()
conn = get_connection()
cursor = conn.cursor()

# Sample students
students = [
    ("Ali", "101", "CSE", 2),
    ("Rahul", "102", "CSE", 2),
    ("Priya", "103", "AIML", 2),
    ("Sneha", "104", "AIML", 2),
    ("Aman", "105", "CSE", 2)
]

# Add students without duplicating existing roll numbers
for student in students:
    cursor.execute("""
        INSERT OR IGNORE INTO students
        (name, roll_no, department, year)
        VALUES (?, ?, ?, ?)
    """, student)

# Find student IDs using their roll numbers
cursor.execute("SELECT id, roll_no FROM students")
student_ids = {
    row["roll_no"]: row["id"]
    for row in cursor.fetchall()
}

# Sample relationships
relationships = [
    ("101", "102", "Friendship"),
    ("102", "101", "Friendship"),
    ("101", "103", "Study Partner"),
    ("103", "104", "Study Partner"),
    ("102", "105", "Classmate"),
    ("105", "104", "Mentor"),
    ("104", "101", "Friendship")
]

# Add relationships without duplicating existing pairs
for roll1, roll2, relation_type in relationships:
    cursor.execute("""
        INSERT OR IGNORE INTO relationships
        (student1_id, student2_id, relation_type)
        VALUES (?, ?, ?)
    """, (
        student_ids[roll1],
        student_ids[roll2],
        relation_type
    ))

conn.commit()

cursor.execute("SELECT COUNT(*) FROM students")
student_count = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM relationships")
relationship_count = cursor.fetchone()[0]

conn.close()

print("Sample data added successfully!")
print("Total students:", student_count)
print("Total relationships:", relationship_count)