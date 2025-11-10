# src/api/main.py
from fastapi import FastAPI, HTTPException
from src.core.models import QueryRequest, RecommendResponse, AssessmentResponse
from src.core.recommender import RAGRecommender
import uvicorn

# Initialize the FastAPI app
app = FastAPI(
    title="SHL Assessment Recommendation System",
    description="An API to recommend SHL assessments based on job descriptions."
)

# Load the RAG "brain"
# This happens once on startup
try:
    recommender = RAGRecommender()
    print("API is ready to serve recommendations.")
except Exception as e:
    print(f"FATAL: Could not load Recommender. {e}")
    recommender = None

@app.get("/health")
def health_check():
    """Health check endpoint"""
    if not recommender:
        raise HTTPException(status_code=500, detail="Recommender model is not loaded")
    return {"status": "healthy"}

@app.post("/recommend", response_model=RecommendResponse)
def recommend_assessments(request: QueryRequest):
    """
    Takes a query and returns 5-10 relevant assessments.
    [cite: 14, 111, 113, 114]
    """
    if not recommender:
        raise HTTPException(status_code=500, detail="Recommender model is not loaded")
    
    try:
        # 1. Get recommendations from the "brain"
        results = recommender.get_recommendations(request.query)
        
        # 2. Format the results to match the required Pydantic/JSON spec [cite: 126]
        formatted_results = [AssessmentResponse(**meta) for meta in results]
        
        # 3. Return the final JSON object
        return RecommendResponse(recommended_assessments=formatted_results)
        
    except Exception as e:
        print(f"Error during recommendation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    # This allows you to run the API directly for testing
    print("Starting API server on http://127.0.0.1:8000")
    uvicorn.run(app, host="127.0.0.1", port=8000)