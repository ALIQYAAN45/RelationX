
from flask import Flask, render_template, request, redirect, url_for, flash
from database import create_tables, get_connection

app = Flask(__name__)
app.secret_key = "student_analyzer_secret"

create_tables()


# ==============================
# DASHBOARD
# ==============================

@app.route("/")
def home():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM students")
    total_students = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM relationships")
    total_relationships = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(DISTINCT relation_type)
        FROM relationships
    """)
    relation_types = cursor.fetchone()[0]

    # Count relationships by type
    cursor.execute("""
        SELECT relation_type, COUNT(*) AS total
        FROM relationships
        GROUP BY relation_type
        ORDER BY relation_type
    """)
    relationship_distribution = cursor.fetchall()

    # Count unique student pairs
    cursor.execute("""
        SELECT COUNT(*)
        FROM (
            SELECT
                MIN(student1_id) AS student_a,
                MAX(student2_id) AS student_b
            FROM relationships
            GROUP BY
                MIN(student1_id, student2_id),
                MAX(student1_id, student2_id)
        )
    """)
    unique_connections = cursor.fetchone()[0]

    # Calculate network density
    if total_students > 1:
        max_connections = total_students * (total_students - 1) / 2
        density = (unique_connections / max_connections) * 100
    else:
        density = 0

    conn.close()

    return render_template(
        "index.html",
        total_students=total_students,
        total_relationships=total_relationships,
        relation_types=relation_types,
        relationship_distribution=relationship_distribution,
        density=round(density, 2)
    )


# ==============================
# STUDENT MANAGEMENT
# ==============================
@app.route("/students", methods=["GET", "POST"])
def students():
    conn = get_connection()
    cursor = conn.cursor()

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        roll_no = request.form.get("roll_no", "").strip()
        department = request.form.get("department", "").strip()
        year = request.form.get("year", "").strip()

        if not all([name, roll_no, department, year]):
            flash("Please fill in all fields.", "error")

        elif not year.isdigit() or int(year) < 1 or int(year) > 6:
            flash("Enter a valid year between 1 and 6.", "error")

        else:
            try:
                cursor.execute("""
                    INSERT INTO students (name, roll_no, department, year)
                    VALUES (?, ?, ?, ?)
                """, (name, roll_no, department, int(year)))

                conn.commit()
                flash("Student added successfully!", "success")

            except Exception as e:
                if "UNIQUE constraint failed" in str(e):
                    flash("This roll number already exists.", "error")
                else:
                    flash("Unable to add student.", "error")

        conn.close()
        return redirect(url_for("students"))

    cursor.execute("SELECT * FROM students ORDER BY id DESC")
    all_students = cursor.fetchall()

    conn.close()

    return render_template("students.html", students=all_students)


# ==============================
# EDIT STUDENT
# ==============================
@app.route("/edit-student/<int:student_id>", methods=["GET", "POST"])
def edit_student(student_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM students WHERE id = ?",
        (student_id,)
    )
    student = cursor.fetchone()

    if student is None:
        conn.close()
        flash("Student not found.", "error")
        return redirect(url_for("students"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        roll_no = request.form.get("roll_no", "").strip()
        department = request.form.get("department", "").strip()
        year = request.form.get("year", "").strip()

        if not all([name, roll_no, department, year]):
            flash("Please fill in all fields.", "error")

        elif not year.isdigit() or int(year) < 1 or int(year) > 6:
            flash("Enter a valid year between 1 and 6.", "error")

        else:
            try:
                cursor.execute("""
                    UPDATE students
                    SET name = ?, roll_no = ?, department = ?, year = ?
                    WHERE id = ?
                """, (name, roll_no, department, int(year), student_id))

                conn.commit()
                conn.close()

                flash("Student updated successfully!", "success")
                return redirect(url_for("students"))

            except Exception as e:
                if "UNIQUE constraint failed" in str(e):
                    flash("This roll number already exists.", "error")
                else:
                    flash("Unable to update student.", "error")

    conn.close()
    return render_template("edit_student.html", student=student)


# ==============================
# DELETE STUDENT
# ==============================
@app.route("/delete-student/<int:student_id>", methods=["POST"])
def delete_student(student_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM relationships
        WHERE student1_id = ? OR student2_id = ?
    """, (student_id, student_id))

    cursor.execute(
        "DELETE FROM students WHERE id = ?",
        (student_id,)
    )

    conn.commit()
    conn.close()

    flash("Student deleted successfully!", "success")
    return redirect(url_for("students"))


# ==============================
# RELATIONSHIP MANAGEMENT
# ==============================
@app.route("/relationships", methods=["GET", "POST"])
def relationships():
    conn = get_connection()
    cursor = conn.cursor()

    if request.method == "POST":
        student1_id = request.form.get("student1_id", "").strip()
        student2_id = request.form.get("student2_id", "").strip()
        relation_type = request.form.get("relation_type", "").strip()

        allowed_types = [
            "Friendship",
            "Study Partner",
            "Classmate",
            "Mentor"
        ]

        if not student1_id or not student2_id or not relation_type:
            flash("Please fill in all fields.", "error")

        elif relation_type not in allowed_types:
            flash("Select a valid relationship type.", "error")

        elif student1_id == student2_id:
            flash("Select two different students.", "error")

        else:
            try:
                cursor.execute("""
                    INSERT INTO relationships
                    (student1_id, student2_id, relation_type)
                    VALUES (?, ?, ?)
                """, (student1_id, student2_id, relation_type))

                conn.commit()
                flash("Relationship added successfully!", "success")

            except Exception as e:
                if "UNIQUE constraint failed" in str(e):
                    flash("This relationship already exists.", "error")
                else:
                    flash("Unable to add relationship.", "error")

        conn.close()
        return redirect(url_for("relationships"))

    cursor.execute("SELECT * FROM students ORDER BY name")
    all_students = cursor.fetchall()

    cursor.execute("""
        SELECT
            r.id,
            r.relation_type,
            s1.name AS student1_name,
            s1.roll_no AS student1_roll,
            s2.name AS student2_name,
            s2.roll_no AS student2_roll
        FROM relationships r
        JOIN students s1 ON r.student1_id = s1.id
        JOIN students s2 ON r.student2_id = s2.id
        ORDER BY r.id DESC
    """)

    all_relationships = cursor.fetchall()

    conn.close()

    return render_template(
        "relationships.html",
        students=all_students,
        relationships=all_relationships
    )


# ==============================
# DELETE RELATIONSHIP
# ==============================
@app.route("/delete-relationship/<int:relationship_id>", methods=["POST"])
def delete_relationship(relationship_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM relationships WHERE id = ?",
        (relationship_id,)
    )

    conn.commit()
    conn.close()

    flash("Relationship deleted successfully!", "success")
    return redirect(url_for("relationships"))


# ==============================
# RELATION ANALYZER
# ==============================
@app.route("/analyzer", methods=["GET", "POST"])
def analyzer():
    conn = get_connection()
    cursor = conn.cursor()

    # Get all students
    cursor.execute("""
        SELECT id, name, roll_no
        FROM students
        ORDER BY name
    """)
    all_students = cursor.fetchall()

    # Get available relationship types
    cursor.execute("""
        SELECT DISTINCT relation_type
        FROM relationships
        ORDER BY relation_type
    """)
    relation_types = [
        row["relation_type"] for row in cursor.fetchall()
    ]

    results = None
    selected_type = ""

    if request.method == "POST":
        selected_type = request.form.get(
            "relation_type", ""
        ).strip()

        if selected_type not in relation_types:
            flash("Please select a valid relationship type.", "error")

        else:
            # Fetch ordered pairs for the selected relation
            cursor.execute("""
                SELECT student1_id, student2_id
                FROM relationships
                WHERE relation_type = ?
            """, (selected_type,))

            pairs = {
                (row["student1_id"], row["student2_id"])
                for row in cursor.fetchall()
            }

            # Set of all students
            student_ids = {
                student["id"] for student in all_students
            }

            # 1. Reflexive
            reflexive = all(
                (student_id, student_id) in pairs
                for student_id in student_ids
            )

            # 2. Symmetric
            symmetric = all(
                (b, a) in pairs
                for a, b in pairs
            )

            # 3. Antisymmetric
            antisymmetric = all(
                a == b or (b, a) not in pairs
                for a, b in pairs
            )

            # 4. Transitive
            transitive = True

            for a, b in pairs:
                for x, c in pairs:
                    if b == x and (a, c) not in pairs:
                        transitive = False
                        break
                if not transitive:
                    break

            results = {
                "reflexive": reflexive,
                "symmetric": symmetric,
                "antisymmetric": antisymmetric,
                "transitive": transitive,
                "pair_count": len(pairs)
            }

    conn.close()

    return render_template(
        "analyzer.html",
        students=all_students,
        relation_types=relation_types,
        selected_type=selected_type,
        results=results
    )


# ==============================
# RUN APPLICATION
# ==============================


# ==============================
# RELATION MATRIX
# ==============================
@app.route("/matrix", methods=["GET", "POST"])
def matrix():
    conn = get_connection()
    cursor = conn.cursor()

    # Get all students
    cursor.execute("""
        SELECT id, name, roll_no
        FROM students
        ORDER BY name
    """)
    students = cursor.fetchall()

    # Get available relationship types
    cursor.execute("""
        SELECT DISTINCT relation_type
        FROM relationships
        ORDER BY relation_type
    """)
    relation_types = [
        row["relation_type"] for row in cursor.fetchall()
    ]

    selected_type = ""
    matrix_data = None

    if request.method == "POST":
        selected_type = request.form.get(
            "relation_type", ""
        ).strip()

        if selected_type not in relation_types:
            flash("Please select a valid relationship type.", "error")
        else:
            # Fetch the selected relationship pairs
            cursor.execute("""
                SELECT student1_id, student2_id
                FROM relationships
                WHERE relation_type = ?
            """, (selected_type,))

            pairs = {
                (row["student1_id"], row["student2_id"])
                for row in cursor.fetchall()
            }

            # Build the matrix
            matrix_data = []

            for student1 in students:
                row = []

                for student2 in students:
                    if (student1["id"], student2["id"]) in pairs:
                        row.append(1)
                    else:
                        row.append(0)

                matrix_data.append(row)

    conn.close()

    return render_template(
        "matrix.html",
        students=students,
        relation_types=relation_types,
        selected_type=selected_type,
        matrix_data=matrix_data
    )


# ==============================
# NETWORK GRAPH
# ==============================
@app.route("/network")
def network():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, name, roll_no, department
        FROM students
        ORDER BY name
    """)
    students = cursor.fetchall()

    cursor.execute("""
        SELECT
            r.id,
            r.relation_type,
            s1.id AS student1_id,
            s1.name AS student1_name,
            s2.id AS student2_id,
            s2.name AS student2_name
        FROM relationships r
        JOIN students s1 ON r.student1_id = s1.id
        JOIN students s2 ON r.student2_id = s2.id
        ORDER BY r.id
    """)
    relationships = cursor.fetchall()

    conn.close()

    return render_template(
        "network.html",
        students=students,
        relationships=relationships
    )

if __name__ == "__main__":
    app.run(debug=True)