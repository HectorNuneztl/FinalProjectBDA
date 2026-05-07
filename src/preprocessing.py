
import os
import re
import unicodedata
from nltk.stem.snowball import SnowballStemmer

# -----------------------------
# STOPWORDS
# -----------------------------

STOPWORDS = {
    "el", "la", "los", "las", "de", "del", "y", "en", "a",
    "un", "una", "con", "por", "para", "es", "se", "al",
    "lo", "como", "o", "u", "que", "su", "sus"
}

# -----------------------------
# STEMMER
# -----------------------------

stemmer = SnowballStemmer("spanish")

# -----------------------------
# NORMALIZAR TEXTO
# -----------------------------


def normalize_text(text):

    text = text.lower()

    text = unicodedata.normalize('NFKD', text)
    text = text.encode('ascii', 'ignore').decode('utf-8')

    text = re.sub(r'[^a-z\s]', ' ', text)

    return text


# -----------------------------
# TOKENIZAR + STEMMING
# -----------------------------


def preprocess_text(text):

    text = normalize_text(text)

    tokens = text.split()

    processed = []

    for token in tokens:

        if token not in STOPWORDS and len(token) > 2:

            stem = stemmer.stem(token)

            processed.append(stem)

    return processed


# -----------------------------
# PROCESAR DOCUMENTOS
# -----------------------------


def process_documents(input_folder, output_folder):

    os.makedirs(output_folder, exist_ok=True)

    for filename in os.listdir(input_folder):

        if filename.endswith('.txt'):

            filepath = os.path.join(input_folder, filename)

            with open(filepath, 'r', encoding='utf-8') as f:
                text = f.read()

            processed_tokens = preprocess_text(text)

            output_path = os.path.join(output_folder, filename)

            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(' '.join(processed_tokens))

    print("Semantic preprocessing completed")


if __name__ == "__main__":

    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    docs_path = os.path.join(BASE_DIR, "docs")
    processed_path = os.path.join(BASE_DIR, "processed")

    process_documents(docs_path, processed_path)
