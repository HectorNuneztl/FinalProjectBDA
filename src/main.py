
from queries import (
    cosine_similarity_query,
    euclidean_distance_query,
    semantic_search
)

import subprocess
import sys
from queries import compare_documents

while True:

    print("\n===== DOCUMENT BASE SYSTEM =====")
    print("1. Generate LSI")
    print("2. Cosine similarity query")
    print("3. Euclidean distance query")
    print("4. Semantic relevance ranking")
    print("5. Compare 2 documents")
    print("6. Exit")

    option = input("\nSelect option: ")

    if option == "1":

        subprocess.run([sys.executable, "lsi.py"])

    elif option == "2":

        query = input("Enter query: ")

        cosine_similarity_query(query)

    elif option == "3":

        query = input("Enter query: ")

        euclidean_distance_query(query)

    elif option == "4":

        semantic_search()
    
    elif option == "5":
        doc1 = input("Enter first document name: ")
        doc2 = input("Enter second document name: ")
        compare_documents(doc1, doc2)

    elif option == "6":

        print("Exiting system")
        break

    else:

        print("Invalid option")