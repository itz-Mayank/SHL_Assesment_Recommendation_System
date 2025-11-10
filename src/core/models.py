# src/core/models.py
from pydantic import BaseModel
from typing import List, Optional

class QueryRequest(BaseModel):
    """Defines the structure for the /recommend request body"""
    query: str

class AssessmentResponse(BaseModel):
    """Defines the structure for a single assessment in the response"""
    url: str
    name: str
    adaptive_support: str
    description: str
    duration: int
    remote_support: str
    test_type: List[str] # This will be a list of strings

class RecommendResponse(BaseModel):
    """Defines the top-level structure for the /recommend response"""
    recommended_assessments: List[AssessmentResponse]