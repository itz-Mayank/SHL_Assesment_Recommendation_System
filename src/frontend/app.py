# src/frontend/app.py
import streamlit as st
import requests
import json
import pandas as pd

# --- Configuration ---
API_URL = "http://127.0.0.1:8000/recommend"  # This is your locally running FastAPI
st.set_page_config(page_title="SHL Recommender", layout="wide")

# --- Header ---
st.title("SHL Assessment Recommendation System")
st.write("Enter a job description or query to find the 5-10 most relevant SHL assessments.")

# --- Input Form ---
# We use a form so the page doesn't re-run on every keypress
with st.form(key="query_form"):
    query_text = st.text_area(
        "Enter your query or job description:",
        height=150,
        placeholder="e.g., I am hiring for a Java developer who can collaborate with my business teams."
    )
    
    submit_button = st.form_submit_button(label="Recommend Assessments")

# --- Logic to run on submit ---
if submit_button and query_text:
    with st.spinner("Analyzing query and searching 377 assessments..."):
        try:
            # 1. Define the data to send to the API
            api_payload = {"query": query_text}
            
            # 2. Call your FastAPI
            response = requests.post(API_URL, json=api_payload)
            
            if response.status_code == 200:
                # 3. Get the JSON response
                data = response.json()
                assessments = data.get("recommended_assessments", [])
                
                if assessments:
                    st.success(f"Found {len(assessments)} recommendations!")
                    
                    # 4. Display the results in a clean table
                    # We'll create a list of dictionaries for the DataFrame
                    display_data = []
                    for item in assessments:
                        display_data.append({
                            "Assessment Name": item['name'],
                            "Test Type(s)": ", ".join(item['test_type']),
                            "Description": item['description'],
                            "URL": item['url']
                        })
                    
                    # Create DataFrame and display
                    df = pd.DataFrame(display_data)
                    st.dataframe(
                        df,
                        # Make the URL column clickable
                        column_config={"URL": st.column_config.LinkColumn("View Assessment")},
                        use_container_width=True
                    )
                else:
                    st.warning("Your query was successful, but no matching assessments were found. Please try a different query.")
            
            else:
                # Show the error from the API
                st.error(f"Error from API: {response.text}")

        except requests.exceptions.ConnectionError:
            st.error("Error: Could not connect to the API. Is your API server running?")
            st.code("python -m uvicorn src.api.main:app")
        except Exception as e:
            st.error(f"An unknown error occurred: {e}")