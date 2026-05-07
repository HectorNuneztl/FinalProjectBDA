import os
import sqlite3
from collections import Counter

# -----------------------------
# DATABASE CONNECTION
# -----------------------------

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DB_PATH = os.path.join(BASE_DIR, "data", "document_base.db")
PROCESSED_PATH = os.path.join(BASE_DIR, "processed")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# -----------------------------
# DROP TABLES (OPTIONAL)
# -----------------------------

cursor.executescript("""
DROP TABLE IF EXISTS FREQUENCIES;
DROP TABLE IF EXISTS LSI_VECTORS;
DROP TABLE IF EXISTS QUERIES;
DROP TABLE IF EXISTS TERMS;
DROP TABLE IF EXISTS DOCUMENTS;
""")

conn.commit()

# -----------------------------
# CREATE TABLES
# -----------------------------

cursor.executescript("""
CREATE TABLE DOCUMENTS(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL
);

CREATE TABLE TERMS(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    term TEXT UNIQUE NOT NULL
);

CREATE TABLE FREQUENCIES(
    document_id INTEGER,
    term_id INTEGER,
    frequency INTEGER,

    PRIMARY KEY(document_id, term_id),

    FOREIGN KEY(document_id) REFERENCES DOCUMENTS(id),
    FOREIGN KEY(term_id) REFERENCES TERMS(id)
);

CREATE TABLE QUERIES(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    query_text TEXT
);

CREATE TABLE LSI_VECTORS(
    document_id INTEGER,
    component INTEGER,
    value REAL,

    PRIMARY KEY(document_id, component),

    FOREIGN KEY(document_id) REFERENCES DOCUMENTS(id)
);
""")

conn.commit()

# -----------------------------
# LOAD DOCUMENTS
# -----------------------------

for filename in os.listdir(PROCESSED_PATH):

    if filename.endswith('.txt'):

        cursor.execute(
            "INSERT INTO DOCUMENTS(name) VALUES(?)",
            (filename,)
        )

        conn.commit()

        cursor.execute(
            "SELECT id FROM DOCUMENTS WHERE name=?",
            (filename,)
        )

        document_id = cursor.fetchone()[0]

        filepath = os.path.join(PROCESSED_PATH, filename)

        with open(filepath, 'r', encoding='utf-8') as f:
            tokens = f.read().split()

        frequencies = Counter(tokens)

        for term, freq in frequencies.items():

            cursor.execute(
                "INSERT OR IGNORE INTO TERMS(term) VALUES(?)",
                (term,)
            )

            cursor.execute(
                "SELECT id FROM TERMS WHERE term=?",
                (term,)
            )

            term_id = cursor.fetchone()[0]

            cursor.execute(
                """
                INSERT INTO FREQUENCIES(document_id, term_id, frequency)
                VALUES (?, ?, ?)
                """,
                (document_id, term_id, freq)
            )

conn.commit()

# -----------------------------
# COMPLETE VIEW
# -----------------------------

cursor.executescript("""
DROP VIEW IF EXISTS COMPLETE;

CREATE VIEW COMPLETE AS

SELECT
    d.id AS document_id,
    d.name AS document_name,
    t.id AS term_id,
    t.term AS term,
    COALESCE(f.frequency, 0) AS frequency

FROM DOCUMENTS d
CROSS JOIN TERMS t

LEFT JOIN FREQUENCIES f
ON d.id = f.document_id
AND t.id = f.term_id;
""")

conn.commit()

print("Database schema created successfully")

cursor.execute("""
SELECT name
FROM sqlite_master
WHERE type='view'
""")

print(cursor.fetchall())

conn.close()
