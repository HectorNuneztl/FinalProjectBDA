import os
import sqlite3
import pandas as pd
from sklearn.decomposition import TruncatedSVD

# -----------------------------
# PATHS
# -----------------------------

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DB_PATH = os.path.join(
    BASE_DIR,
    "data",
    "document_base.db"
)

# -----------------------------
# USER INPUT
# -----------------------------

k = int(input("How many components do you want for indexing? "))

# -----------------------------
# CONNECT TO DATABASE
# -----------------------------

conn = sqlite3.connect(DB_PATH)

cursor = conn.cursor()

# -----------------------------
# LOAD COMPLETE MATRIX
# -----------------------------

query = """
SELECT document_name, term, frequency
FROM COMPLETE
"""

rows = pd.read_sql_query(query, conn)

matrix = rows.pivot_table(
    index='document_name',
    columns='term',
    values='frequency'
)

# Replace possible NULL values with 0
matrix = matrix.fillna(0)

# -----------------------------
# APPLY LSI (SVD)
# -----------------------------

svd = TruncatedSVD(n_components=k)

lsi_matrix = svd.fit_transform(matrix)

# -----------------------------
# DISPLAY INFORMATION
# -----------------------------

print("\nLSI PROCESS COMPLETED\n")

print(f"Original dimensions: {matrix.shape}")

print(f"Reduced dimensions: {lsi_matrix.shape}")

documents = list(matrix.index)

print("\nSample LSI vectors:\n")

for i, vector in enumerate(lsi_matrix[:5]):

    print(f"Document {documents[i]} -> {vector}")

# -----------------------------
# SAVE LSI VECTORS
# -----------------------------

cursor.execute("DELETE FROM LSI_VECTORS")

for doc_index, document_name in enumerate(documents):

    cursor.execute(
        """
        SELECT id
        FROM DOCUMENTS
        WHERE name = ?
        """,
        (document_name,)
    )

    document_id = cursor.fetchone()[0]

    for component in range(k):

        value = float(lsi_matrix[doc_index][component])

        cursor.execute(
            """
            INSERT INTO LSI_VECTORS
            (document_id, component, value)
            VALUES (?, ?, ?)
            """,
            (document_id, component, value)
        )

conn.commit()

print("\nLSI vectors stored successfully")

# -----------------------------
# CLOSE CONNECTION
# -----------------------------

conn.close()