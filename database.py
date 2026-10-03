
import sqlite3

DATABASE = "student_relationships.db"

def get_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def create_tables():
    conn = get_connection()
    cursor = conn.cursor()

    # Students table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            roll_no TEXT UNIQUE NOT NULL,
            department TEXT NOT NULL,
            year INTEGER NOT NULL
        )
    """)

    # Relationships table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS relationships (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student1_id INTEGER NOT NULL,
            student2_id INTEGER NOT NULL,
            relation_type TEXT NOT NULL,
            FOREIGN KEY (student1_id) REFERENCES students(id),
            FOREIGN KEY (student2_id) REFERENCES students(id),
            UNIQUE (student1_id, student2_id, relation_type)
        )
    """)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    create_tables()
    print("Database and tables created successfully!")