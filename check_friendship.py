
from database import get_connection

conn = get_connection()
cursor = conn.cursor()

cursor.execute("""
    SELECT s1.name AS student1,
           s2.name AS student2,
           r.relation_type
    FROM relationships r
    JOIN students s1 ON r.student1_id = s1.id
    JOIN students s2 ON r.student2_id = s2.id
    WHERE r.relation_type = ?
""", ("Friendship",))

rows = cursor.fetchall()

print("\nFriendship Relationships:")
print("-------------------------")

for row in rows:
    print(row["student1"], "->", row["student2"])

conn.close()