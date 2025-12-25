import sqlite3

conn = sqlite3.connect("survey.db")
c = conn.cursor()

c.execute("SELECT * FROM survey_responses;")
rows = c.fetchall()
c.execute("SELECT * FROM survey_questions;")
rows = c.fetchall()

for row in rows:
    print(row)

c.execute("SELECT COUNT(*) FROM survey_responses;")
print("Total rows responses:", c.fetchone()[0])

c.execute("SELECT COUNT(*) FROM survey_questions;")
print("Total rows questions : ", c.fetchone()[0])

conn.close()

print("Done")
