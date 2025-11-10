import pandas as pd
from src.core.recommender import RAGRecommender # Import your "brain"
import os

print("Starting prediction script...")

# --- Configuration ---
TEST_SET_PATH = "data/provided/test_set.csv"
OUTPUT_DIR = "submission"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "predictions.csv")

# --- Main Script ---
def main():
    # 1. Create submission directory if it doesn't exist
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # 2. Load the unlabeled test queries
    try:
        test_df = pd.read_csv(TEST_SET_PATH)
        queries = test_df['Query'].tolist()
        print(f"Loaded {len(queries)} queries from {TEST_SET_PATH}")
    except Exception as e:
        print(f"Error loading {TEST_SET_PATH}: {e}")
        return

    # 3. Load your recommender "brain"
    try:
        recommender = RAGRecommender()
    except Exception as e:
        print(f"Error loading RAGRecommender: {e}")
        return
        
    print("Recommender loaded. Generating predictions...")
    
    # 4. Loop, predict, and format
    
    # This list will hold all our final rows
    submission_rows = [] 
    
    for query in queries:
        # Get the list of recommendation dicts
        recommendations = recommender.get_recommendations(query)
        
        if not recommendations:
            print(f"Warning: No recommendations found for query: '{query[:50]}...'")
            continue
            
        # Format for the CSV as per the PDF spec [cite: 153-164]
        for rec in recommendations:
            submission_rows.append({
                "Query": query,
                "Assessment_url": rec['url']
            })

    # 5. Create DataFrame and save to CSV
    if not submission_rows:
        print("No predictions were generated. Exiting.")
        return
        
    submission_df = pd.DataFrame(submission_rows)
    
    try:
        submission_df.to_csv(OUTPUT_FILE, index=False)
        print(f"\n--- Success! ---")
        print(f"Predictions file saved to {OUTPUT_FILE}")
    except Exception as e:
        print(f"Error saving CSV to {OUTPUT_FILE}: {e}")

if __name__ == "__main__":
    main()