import os
import sqlite3
from collections import Counter
import math
import re
import unicodedata
from nltk.stem.snowball import SnowballStemmer

# -----------------------------
# DATABASE
# -----------------------------

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "document_base.db")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# -----------------------------
# PREPROCESS QUERY
# -----------------------------

stemmer = SnowballStemmer("spanish")

STOPWORDS = {
    "el", "la", "los", "las", "de", "del", "y", "en", "a",
    "un", "una", "con", "por", "para", "es", "se", "al",
    "lo", "como", "o", "u", "que", "su", "sus"
}

def preprocess_query(query):

    query = query.lower()

    query = unicodedata.normalize('NFKD', query)
    query = query.encode('ascii', 'ignore').decode('utf-8')

    query = re.sub(r'[^a-z\\s]', ' ', query)

    tokens = query.split()

    processed = []

    for token in tokens:

        if token not in STOPWORDS and len(token) > 2:

            stem = stemmer.stem(token)

            processed.append(stem)

    return Counter(processed)


# -----------------------------
# COSINE AND JACCARD SIMILARITY IN SQL
# -----------------------------

def cosine_similarity_query(query_text):

    query_freqs = preprocess_query(query_text)

    cursor.execute("DROP TABLE IF EXISTS TEMP_QUERY")

    cursor.execute(
        """
        CREATE TEMP TABLE TEMP_QUERY(
            term TEXT,
            frequency INTEGER
        )
        """
    )

    for term, freq in query_freqs.items():

        cursor.execute(
            "INSERT INTO TEMP_QUERY VALUES (?, ?)",
            (term, freq)
        )

    sql = """
    SELECT
        d.name,

        (
            SUM(f.frequency * tq.frequency) /

            (
                SQRT(SUM(f.frequency * f.frequency)) *
                SQRT(SUM(tq.frequency * tq.frequency))
            )
        ) AS cosine_similarity

    FROM FREQUENCIES f

    JOIN DOCUMENTS d
        ON f.document_id = d.id

    JOIN TERMS t
        ON f.term_id = t.id

    JOIN TEMP_QUERY tq
        ON t.term = tq.term

    GROUP BY d.name

    ORDER BY cosine_similarity DESC
    """

    cursor.execute(sql)

    results = cursor.fetchall()

    print("\nCosine Similarity Results:\n")

    for row in results:
        print(row)

def jaccard_similarity(doc1, doc2):

    sql = """

    SELECT

        CAST(COUNT(DISTINCT f1.term_id) AS FLOAT)

        /

        (

            SELECT COUNT(DISTINCT term_id)

            FROM (

                SELECT term_id
                FROM FREQUENCIES
                WHERE document_id = (
                    SELECT id FROM DOCUMENTS WHERE name = ?
                )

                UNION

                SELECT term_id
                FROM FREQUENCIES
                WHERE document_id = (
                    SELECT id FROM DOCUMENTS WHERE name = ?
                )

            )

        ) AS jaccard_similarity

    FROM FREQUENCIES f1

    JOIN FREQUENCIES f2
        ON f1.term_id = f2.term_id

    WHERE f1.document_id = (
        SELECT id FROM DOCUMENTS WHERE name = ?
    )

    AND f2.document_id = (
        SELECT id FROM DOCUMENTS WHERE name = ?
    )

    """

    cursor.execute(sql, (doc1, doc2, doc1, doc2))

    result = cursor.fetchone()[0]

    print("\nJaccard Similarity:\n")

    print(f"{doc1} vs {doc2}")

    print(f"\nJaccard Score: {result}")


# -----------------------------
# EUCLIDEAN DISTANCE IN SQL
# -----------------------------


def euclidean_distance_query(query_text):

    query_freqs = preprocess_query(query_text)

    cursor.execute("DROP TABLE IF EXISTS TEMP_QUERY")

    cursor.execute(
        """
        CREATE TEMP TABLE TEMP_QUERY(
            term TEXT,
            frequency INTEGER
        )
        """
    )

    for term, freq in query_freqs.items():

        cursor.execute(
            "INSERT INTO TEMP_QUERY VALUES (?, ?)",
            (term, freq)
        )

    sql = """
    SELECT
        d.name,

        SQRT(
            SUM(
                (COALESCE(f.frequency, 0) - COALESCE(tq.frequency, 0)) *
                (COALESCE(f.frequency, 0) - COALESCE(tq.frequency, 0))
            )
        ) AS euclidean_distance

    FROM COMPLETE c

    JOIN DOCUMENTS d
        ON c.document_id = d.id

    LEFT JOIN FREQUENCIES f
        ON c.document_id = f.document_id
        AND c.term_id = f.term_id

    LEFT JOIN TERMS t
        ON c.term_id = t.id

    LEFT JOIN TEMP_QUERY tq
        ON t.term = tq.term

    GROUP BY d.name

    ORDER BY euclidean_distance ASC
    """

    cursor.execute(sql)

    results = cursor.fetchall()

    print("\nEuclidean Distance Results:\n")

    for row in results:
        print(row)


# -----------------------------
# SEMANTIC SEARCH USING LSI
# -----------------------------


def semantic_search():

    sql = """
    SELECT
        d.name,

        SQRT(SUM(l.value * l.value)) AS semantic_score

    FROM LSI_VECTORS l

    JOIN DOCUMENTS d
        ON l.document_id = d.id

    GROUP BY d.name

    ORDER BY semantic_score DESC
    """

    cursor.execute(sql)

    results = cursor.fetchall()

    print("\\nSemantic Ranking:\\n")

    for row in results:
        print(row)

def compare_documents(doc1, doc2):

    # -----------------------------
    # COSINE SIMILARITY
    # -----------------------------

    sql_cosine = """

    SELECT

        SUM(f1.frequency * f2.frequency) * 1.0

        /

        (

            SQRT(SUM(f1.frequency * f1.frequency))

            *

            SQRT(SUM(f2.frequency * f2.frequency))

        )

        AS cosine_similarity

    FROM FREQUENCIES f1

    JOIN FREQUENCIES f2
        ON f1.term_id = f2.term_id

    JOIN DOCUMENTS d1
        ON f1.document_id = d1.id

    JOIN DOCUMENTS d2
        ON f2.document_id = d2.id

    WHERE d1.name = ?
    AND d2.name = ?

    """

    cursor.execute(sql_cosine, (doc1, doc2))

    cosine_result = cursor.fetchone()[0]

    # -----------------------------
    # EUCLIDEAN DISTANCE
    # -----------------------------

    sql_euclidean = """

    SELECT

        SQRT(

            SUM(

                (COALESCE(f1.frequency,0) - COALESCE(f2.frequency,0))

                *

                (COALESCE(f1.frequency,0) - COALESCE(f2.frequency,0))

            )

        )

        AS euclidean_distance

    FROM TERMS t

    LEFT JOIN FREQUENCIES f1
        ON t.id = f1.term_id
        AND f1.document_id = (
            SELECT id
            FROM DOCUMENTS
            WHERE name = ?
        )

    LEFT JOIN FREQUENCIES f2
        ON t.id = f2.term_id
        AND f2.document_id = (
            SELECT id
            FROM DOCUMENTS
            WHERE name = ?
        )

    """

    cursor.execute(sql_euclidean, (doc1, doc2))

    euclidean_result = cursor.fetchone()[0]

    # -----------------------------
    # JACCARD SIMILARITY
    # -----------------------------

    jaccard_result = jaccard_similarity(doc1, doc2)

    # -----------------------------
    # DISPLAY RESULTS
    # -----------------------------

    print("\nDOCUMENT COMPARISON\n")

    print(f"{doc1} vs {doc2}")

    print("\nSimilarity Techniques:")

    print(f"\nCosine Similarity: {cosine_result}")

    print(f"Jaccard Similarity: {jaccard_result}")

    print("\nDissimilarity Technique:")

    print(f"\nEuclidean Distance: {euclidean_result}")


if __name__ == "__main__":

    query = input("Enter query: ")

    cosine_similarity_query(query)

    euclidean_distance_query(query)

    semantic_search()

    conn.close()
