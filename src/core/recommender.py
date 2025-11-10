# src/core/recommender.py
import chromadb
import google.generativeai as genai
import os
import json
from sentence_transformers import SentenceTransformer
from typing import List
from dotenv import load_dotenv

# Load environment variables (GEMINI_API_KEY)
load_dotenv()

# Configuration
DB_PATH = "data/processed/vector_store"
COLLECTION_NAME = "shl_assessments"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

TEST_TYPE_MAP = {
    'A': 'Ability & Aptitude',
    'B': 'Biodata & Situational Judgement',
    'C': 'Competencies',
    'D': 'Development & 360',
    'E': 'Assessment Exercises',
    'K': 'Knowledge & Skills',
    'P': 'Personality & Behavior',
    'S': 'Simulations'
}

# Configure the Gemini LLM
try:
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    # --- FIX 1 (v6): Use the full model path ---
    llm = genai.GenerativeModel('models/gemini-2.5-pro') 
    # --- END FIX 1 ---
    print("Gemini LLM configured successfully.")
except Exception as e:
    print(f"Error configuring Gemini: {e}")
    llm = None

class RAGRecommender:
    def __init__(self):
        print("Loading RAG Recommender...")
        try:
            self.client = chromadb.PersistentClient(path=DB_PATH)
            self.collection = self.client.get_collection(name=COLLECTION_NAME)
            self.embed_model = SentenceTransformer(EMBEDDING_MODEL)
            print("ChromaDB client and embedding model loaded.")
        except Exception as e:
            print(f"Error initializing RAGRecommender: {e}")
            self.client = None
            self.embed_model = None

    def _analyze_query_with_llm(self, query: str) -> List[str]:
        """Uses Gemini to analyze the query and extract relevant test types."""
        if not llm:
            print("LLM not configured. Falling back to simple search.")
            return ['K', 'P', 'A'] # Search all key types

        prompt = f"""
        You are an expert recruitment assistant. Analyze the following job query
        and identify the distinct skill domains required.
        
        The available SHL Test Type categories are:
        - A: Ability & Aptitude
        - B: Biodata & Situational Judgement
        - C: Competencies
        - D: Development & 360
        - E: Assessment Exercises
        - K: Knowledge & Skills (for specific technical skills like 'Java', 'Python', 'SQL')
        - P: Personality & Behavior (for soft skills like 'collaboration', 'leadership', 'teamwork')
        - S: Simulations

        Query: "{query}"

        Respond ONLY with a JSON list of the category letters that are
        relevant. For example, for "a Java developer who is a good team player",
        you should respond: ["K", "P"]
        """
        
        try:
            response = llm.generate_content(prompt)
            cleaned_response = response.text.strip().replace("`", "").replace("json", "")
            test_types = json.loads(cleaned_response)
            
            if isinstance(test_types, list):
                print(f"LLM identified test types: {test_types}")
                return test_types
            
            return ['K', 'P'] # Fallback
        except Exception as e:
            print(f"Error in LLM query analysis: {e}. Falling back to 'K' and 'P'.")
            return ['K', 'P']

    def _interleave_lists(self, *lists):
        """Interleaves multiple lists to create a balanced result.
           E.g., [k1, k2], [p1, p2] -> [k1, p1, k2, p2]
        """
        interleaved = []
        max_len = max(len(l) for l in lists)
        for i in range(max_len):
            for l in lists:
                if i < len(l):
                    interleaved.append(l[i])
        return interleaved

    def get_recommendations(self, query: str, max_results: int = 10) -> List[dict]:
        if not self.client or not self.embed_model:
            return [{"error": "Recommender not initialized"}]
            
        # 1. Analyze the query to get test types (e.g., ['K', 'P'])
        required_type_keys = self._analyze_query_with_llm(query)
        # Convert keys to full names (e.g., ['Knowledge & Skills', 'Personality & Behavior'])
        required_type_names = [TEST_TYPE_MAP.get(key) for key in required_type_keys if TEST_TYPE_MAP.get(key)]
        
        # 2. Embed the query
        query_embedding = self.embed_model.encode(query).tolist()
        
        # 3. --- "FETCH-THEN-RANK" ---
        print("Performing broad search (n=30)...")
        # Do a single, broad search without filtering. Get 30 results.
        try:
            broad_results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=30 
            )
        except Exception as e:
            print(f"Error querying ChromaDB: {e}")
            return []

        if not broad_results['metadatas']:
            return []

        # 4. Filter and Rank in Python to ensure balance
        ranked_lists = {name: [] for name in required_type_names}
        
        # Loop through our 30 results and sort them into buckets
        for meta in broad_results['metadatas'][0]:
            for type_name in required_type_names:
                # 'test_type' is a string like "Knowledge & Skills, Something Else"
                if type_name in meta['test_type']:
                    ranked_lists[type_name].append(meta)
                    break # Add to first matching bucket
        
        # 5. Interleave the lists to create a balanced result
        final_list = self._interleave_lists(*ranked_lists.values())
        
        # 6. De-duplicate and format the final response
        final_recommendations = []
        seen_urls = set()
        
        for meta in final_list:
            if meta['url'] not in seen_urls:
                # Convert the "test_type" string back into a list for the API response
                meta['test_type'] = [t.strip() for t in meta['test_type'].split(',')]
                
                final_recommendations.append(meta)
                seen_urls.add(meta['url'])
                
            # Stop once we have 10 balanced results
            if len(final_recommendations) >= max_results:
                break
                
        return final_recommendations