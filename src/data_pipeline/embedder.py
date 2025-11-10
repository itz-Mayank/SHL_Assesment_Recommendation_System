import json
import pandas as pd
import chromadb
import os

# 1. Import the embedding model
from sentence_transformers import SentenceTransformer

# --- Configuration ---
JSON_FILE_PATH = "data/crawled/shl_assessments.json"
DB_PATH = "data/processed/vector_store"
COLLECTION_NAME = "shl_assessments"
EMBEDDING_MODEL = "all-MiniLM-L6-v2" 

def load_data(file_path):
    """Loads the crawled JSON data."""
    try:
        df = pd.read_json(file_path)
        print(f"Successfully loaded {len(df)} assessments from {file_path}")
        df['description'] = df['description'].fillna('')
        return df
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return None

def create_document_chunks(df):
    """
    Creates the text 'document' to be embedded for each assessment.
    """
    documents = []
    metadatas = []
    ids = []

    for i, row in df.iterrows():
        
        test_type_list = row['test_type'] 
        # --- THIS IS THE FIX (v4) ---
        # Convert the list back to a comma-separated string
        test_type_str = ", ".join(test_type_list) 
        
        doc_text = f"Name: {row['name']}\nType: {test_type_str}\nDescription: {row['description']}"
        
        documents.append(doc_text)
        
        metadatas.append({
            "name": row['name'],
            "url": row['url'],
            "description": row['description'],
            "test_type": test_type_str, # <-- Store the string, this fixes the error
            "duration": int(row['duration']) if pd.notna(row['duration']) else -1,
            "adaptive_support": row['adaptive_support'],
            "remote_support": row['remote_support']
        })
        # --- END FIX ---
        
        ids.append(f"assessment_{i}")
        
    print(f"Created {len(documents)} documents for embedding.")
    return documents, metadatas, ids

def main():
    print("Starting Phase 2: Processing and Embedding (v4)...")
    
    # 1. Load the data
    df = load_data(JSON_FILE_PATH)
    if df is None:
        return

    # 2. Initialize the embedding model
    print(f"Loading embedding model: {EMBEDDING_MODEL}")
    model = SentenceTransformer(EMBEDDING_MODEL)
    print("Model loaded.")

    # 3. Initialize the Vector Database (ChromaDB)
    client = chromadb.PersistentClient(path=DB_PATH)
    
    # Delete old collection if it exists
    try:
        client.delete_collection(name=COLLECTION_NAME)
        print(f"Deleted old collection '{COLLECTION_NAME}'.")
    except Exception:
        pass 
    
    # Create the collection
    collection = client.create_collection(name=COLLECTION_NAME)
    print(f"Vector collection '{COLLECTION_NAME}' created.")

    # 4. Create the documents and metadata
    documents, metadatas, ids = create_document_chunks(df)

    # 5. Embed and store the documents in ChromaDB
    print("Embedding documents... (This may take a moment)")
    
    batch_size = 100
    for i in range(0, len(documents), batch_size):
        print(f"  Embedding batch {i//batch_size + 1}/{ (len(documents)//batch_size) + 1}...")
        
        batch_docs = documents[i:i+batch_size]
        batch_metadatas = metadatas[i:i+batch_size]
        batch_ids = ids[i:i+batch_size]
        
        batch_embeddings = model.encode(batch_docs).tolist()
        
        collection.add(
            embeddings=batch_embeddings,
            documents=batch_docs,
            metadatas=batch_metadatas,
            ids=batch_ids
        )

    print("\n--- Embedding Complete ---")
    print(f"Successfully added {len(ids)} assessments to the vector database.")
    print(f"Your 'brain' is now ready in: {DB_PATH}")


if __name__ == "__main__":
    main()