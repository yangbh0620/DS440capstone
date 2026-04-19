# DS 440 Capstone: Restaurant Analytics Platform

**Team Members:** Bohan Yang, Luping Zhou

---

##  INSTRUCTIONS NEVER RUN THIS PROGRAM BEFORE 

This system requires running a backend server (FastAPI) and a frontend dashboard (Streamlit) simultaneously.

### Step 1: Download & Environment Setup
Open your terminal (Command Prompt/PowerShell on Windows, Terminal on Mac) and run these commands sequentially to set up a clean environment:

```bash
# 1. Clone the repository
git clone <YOUR_GITHUB_REPO_LINK>
cd <YOUR_REPO_FOLDER_NAME>

# 2. Create a clean virtual environment
python -m venv venv

# 3. Activate the virtual environment
# --> On Windows:
python -m venv .venv
.\.venv\Scripts\Activate.ps1
# --> On Mac/Linux:
# source venv/bin/activate

# 4. Install all dependencies required for the ML model and dashboards
pip install -r requirements.txt
```

### Step 2: Start the Backend System (FastAPI)
*Keep the current terminal open. Do not close it.*

```bash
# Run the FastAPI server
streamlit run main.py --server.port 8000
```
*Wait until you see `Application startup complete`. The backend is now processing the dataset and TF-IDF recommendation logic.*

### Step 3: Start the Frontend Dashboard (Streamlit)
*You MUST open a **SECOND, NEW terminal window** for this step.*

```bash
# 1. Navigate to the project folder again
cd <YOUR_REPO_FOLDER_NAME>

# 2. Activate the virtual environment again
# --> On Windows:
venv\Scripts\activate
# --> On Mac/Linux:
# source venv/bin/activate

# 3. Run the Streamlit interface
streamlit run <FRONTEND_FILE_NAME>.py
```

### Step 4: Evaluate the Results
Your default browser will automatically open the dashboard (usually at `http://localhost:8501`). Please verify the following features as detailed in our research paper:

1. **Front-of-House POS:** Contextual dish recommendations powered by our TF-IDF machine learning model.
2. **Manager Dashboard:** Real-time business analytics and visualizations generated via Plotly.
3. **Destruction Testing:** Input modules designed to test the system's security and robustness against anomalous data.


## Project Structure & File Descriptions

To help you navigate our full-stack data pipeline, here is a breakdown of the core files:

| File Name | Category | Description |
| :--- | :--- | :--- |
| **`main.py`** | Backend | FastAPI entry point. Manages API routes, computes business logic, and serves data to the frontend. |
| **`app.py`** | Frontend | Streamlit entry point. Contains the interactive Front-of-House POS UI and the Manager Dashboard. |
| **`dish_recommender.pkl`**| ML Model | Serialized **TF-IDF + Cosine Similarity** model. Pre-trained to generate contextual dish recommendations instantly. |
| **`dataclean.py`** | Data Prep | Preprocessing script used to clean, deduplicate, and standardize 140,000+ raw records. |
| **`dataset_...csv`** | Raw Data | Original scraped datasets obtained via Apify / Google Maps and Places. |
| **`stress_test.py`** | Security | Automated testing script designed to simulate high loads and inject malicious inputs to test system stability. |
| **`poisoned_...csv`** | Security | A curated dataset containing anomalous/malicious data used specifically for **Destruction Testing**. |
