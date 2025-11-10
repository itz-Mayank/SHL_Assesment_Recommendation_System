# SHL Assessment Recommendation System

This is an intelligent recommendation system built for the SHL Generative AI Intern assignment. It takes a natural language query or job description and recommends the 5-10 most relevant SHL assessments, ensuring a balance between technical and behavioral skills.

> **Problem Statement:** Hiring managers and recruiters often struggle to find the right assessments for the roles that they are hiring for. [cite_start]The current system relies on keyword searches and filters, making the process time-consuming and inefficient. [cite: 3, 4]

This project solves this by implementing a "Balanced Retrieval-Augmented Generation (RAG)" system.

## Core Features

* [cite_start]**Balanced Recommendations:** The system intelligently analyzes a query (e.g., "Java developer who is a good team player") and returns a balanced list of both technical skill assessments (for "Java") and behavioral/personality assessments (for "team player"). [cite: 52-54]
* **End-to-End RAG Pipeline:**
    1.  **Crawl:** A Python script scrapes all 377 "Individual Test Solutions" from the SHL catalog.
    2.  **Embed:** The scraped data is vectorized using `sentence-transformers` and stored in a `ChromaDB` vector database.
    3.  **Retrieve & Rank:** A novel "Fetch-then-Rank" logic retrieves a broad set of results and then uses Python to re-rank them for balance.
* **Generative AI Query Analysis:** A Google Gemini LLM (`gemini-1.0-pro`) analyzes the user's query to identify the required *domains* (e.g., Knowledge, Personality) to search for.
* [cite_start]**FastAPI Backend:** A high-performance API backend built with FastAPI, providing `/health` and `/recommend` endpoints as specified in the assignment. [cite: 101, 111]
* **Streamlit Frontend:** A clean, user-friendly web application for easily testing and demonstrating the system.

## Project Structure

```
shl-recommender/
├── .env                  # Stores API keys (GEMINI_API_KEY)
├── README.md             # This file
├── requirements.txt      # List of Python packages
├── run_predictions.py    # Script to generate the final submission CSV
├── data/
│   ├── provided/
│   │   ├── train_set.csv   # The 10 labeled queries for evaluation
│   │   └── test_set.csv    # The 9 unlabeled queries for submission
│   ├── crawled/
│   │   └── shl_assessments.json  # The 377 scraped assessment records
│   └── processed/
│       └── vector_store/       # The ChromaDB vector database
├── src/
│   ├── api/
│   │   └── main.py         # FastAPI app (runs the API server)
│   ├── core/
│   │   ├── models.py       # Pydantic models (defines API JSON structure)
│   │   └── recommender.py  # The "brain" (RAG logic)
│   ├── data_pipeline/
│   │   ├── crawler.py      # Script to scrape the SHL website
│   │   └── embedder.py     # Script to create the vector database
│   └── frontend/
│       └── app.py          # The Streamlit web application
└── submission/
    ├── predictions.csv     # The final generated predictions
```

---

## Installation & Setup

### Prerequisites

* **Python 3.10+** (This is essential. Python 3.8/3.9 will fail).
* **Conda** (Recommended for managing complex dependencies).
* **Google Gemini API Key:** Get a free key from `https://ai.google.dev`.

### Recommended Setup (Using Conda)

We found that `pip` struggles to install the complex compiled dependencies (`torch`, `grpcio`, `pydantic-core`). **Using Conda is strongly recommended** and will save you hours of debugging.

**1. Create the Conda Environment:**
Open your Anaconda Prompt or terminal and create a new environment with Python 3.10.

```bash
conda create -n shl-project python=3.10
```

**2. Activate the Environment:**
```bash
conda activate shl-project
```
*(Your terminal should now show `(shl-project)`)*

**3. Install All Packages:**
This one command will install all complex packages correctly from the `conda-forge` channel.

```bash
conda install -c conda-forge numpy pandas pytorch sentence-transformers chromadb fastapi uvicorn beautifulsoup4 requests python-dotenv
```

**4. Install Google Gemini:**
This package is best installed with `pip`.
```bash
python -m pip install google-generativeai
```

**5. Set Your API Key:**
In the root of the project folder (`shl-recommender/`), create a new file named `.env` and add your key:

```
GEMINI_API_KEY=YOUR_API_KEY_HERE
```

---

## Running the Application

You must run these steps in order.

### Step 1: Run the Crawler (Phase 1)
This script scrapes all 377 assessments from the SHL website and creates `data/crawled/shl_assessments.json`.

```bash
# Make sure you are in the (shl-project) environment
python src/data_pipeline/crawler.py
```
[cite_start]*(**Note:** This script still has a `TODO` to find the real selectors for `description` and `duration`[cite: 16]. It currently populates them with placeholders.)*

### Step 2: Run the Embedder (Phase 2)
This script reads the JSON file and builds the vector database (the "brain") in `data/processed/vector_store/`.

```bash
python src/data_pipeline/embedder.py
```

### Step 3: Run the API Server (Phase 3)
This command starts your FastAPI backend server.

```bash
# This is the most robust way to run uvicorn in Conda
python -m uvicorn src.api.main:app --reload
```
Your API is now running at `http://127.0.0.1:8000`.

### Step 4: Run the Frontend (Phase 3.5)
Open a **new, second terminal** and activate your Conda environment.

```bash
# In your SECOND terminal
conda activate shl-project

# Run the streamlit app
streamlit run src/frontend/app.py
```
Your browser will automatically open to `http://127.0.0.1:8501`, and you can now use the application.

---

## Using the Application

### 1. Streamlit Web App
The easiest way to use the system is with the Streamlit frontend.

* **URL:** `http://127.0.0.1:8501`
* **Usage:** Type your query into the text box and press "Recommend Assessments."

**Example Query:**
```
I am hiring for a senior software engineer who is proficient in Python and SQL. They must also be a strong collaborator and have experience in leading small teams.
```

### 2. API (Directly via /docs)
You can test the API directly using the auto-generated documentation page.

* **URL:** `http://127.0.0.1:8000/docs`
* **Usage:**
    1.  Click the `POST /recommend` endpoint.
    2.  Click "Try it out."
    3.  Enter your query in the JSON body:
        ```json
        {
          "query": "I need a Java developer who is a good team player."
        }
        ```
    4.  Click "Execute" to see the raw JSON response.

### 3. API (via cURL)
You can also query the endpoint from any terminal.

```bash
curl -X 'POST' \
  '[http://127.0.0.1:8000/recommend](http://127.0.0.1:8000/recommend)' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "query": "I need a Java developer who is a good team player."
}'
```

---

## Generating Submission Files

### 1. `predictions.csv`
This script uses your recommender "brain" to generate the final `predictions.csv` file from the `test_set.csv`.

```bash
# Make sure your API is NOT running (this runs as a standalone script)
# Press Ctrl+C in your API terminal
python run_predictions.py
```
This will create your deliverable file at `submission/predictions.csv`.
