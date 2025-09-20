```markdown
# 🚀 Resume Screening & Job Match System

## 📌 Overview
The Resume Screening & Job Match System is an AI-powered web application designed to streamline campus recruitment and placement readiness.  
It helps recruiters and placement teams automatically **match resumes against job descriptions (JDs)** and generate structured evaluations with **scores, missing skills, and improvement tips**.  

This reduces manual screening time, increases accuracy, and provides students with actionable feedback.

---

## ✨ Features
- 📄 Resume & JD Upload – Upload resumes (PDF/DOCX) and job descriptions.  
- 🧠 AI-Powered Screening – Combines **keyword matching + semantic similarity** for better accuracy.  
- 📊 Scoring & Verdicts – Provides:
  - Match Score (0–100)  
  - Verdict: High / Medium / Low Fit  
  - Missing & Extra Skills  
  - Suggestions for improvement  
- 📈 Evaluator Dashboard(Streamlit)  
  - Searchable table of evaluated resumes  
  - Filters by role, score range, and verdict  
  - Detailed view for feedback & recommendations

- 🗄️ Database Storage (SQLite) – Stores JDs, resumes, and evaluations for audit & retrieval.  
- ⚡ Fast Processing – Supports multiple resumes in bulk.  

---

## 🏗️ Tech Stack
### 🔹 Frontend
- [Streamlit](https://streamlit.io/) – Interactive evaluator dashboard  

### 🔹 Backend
- [Flask](https://flask.palletsprojects.com/) – API service for resume evaluation  
- [spaCy / NLTK] – NLP-based text extraction & preprocessing  
- [Sentence Transformers / Hugging Face] – Semantic similarity with embeddings  

### 🔹 Database
- **SQLite** (MVP)

---

## 📂 Project Structure
```

resume-screening-system/
│── backend/
│   ├── app.py              # Flask API entry point
│   ├── models/             # ML/NLP models
│   ├── utils/              # Parsing & scoring helpers
│   ├── requirements.txt    # Backend dependencies
│
│── frontend/
│   ├── streamlit\_app.py    # Streamlit dashboard
│   ├── pages/              # Extra pages (Upload, Dashboard, Details)
│
│── database/
│   ├── schema.sql          # DB schema for resumes, JDs, evaluations
│
│── README.md

````

---

## ⚙️ Installation & Setup
### 1️⃣ Clone the Repository
```bash
git clone https://github.com/<your-team>/resume-screening-system.git
cd resume-screening-system
````

### 2️⃣ Setup Backend (Flask)

```bash
cd backend
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Flask server will start at `http://127.0.0.1:5000/`

### 3️⃣ Setup Frontend (Streamlit)

```bash
cd frontend
pip install -r requirements.txt
streamlit run streamlit_app.py
```

### 4️⃣ Database Setup

* For **SQLite**: Schema auto-creates on first run.
* For **MySQL**: Run `database/schema.sql` and update DB credentials in `backend/config.py`.

---

## 🚀 Usage

1. Run **Flask Backend** (`app.py`).
2. Run **Streamlit Frontend** (`streamlit_app.py`).
3. Upload a **Job Description (JD)**.
4. Upload **Resumes** for evaluation.
5. View scores, verdicts, and improvement tips on the **Dashboard**.

---

## 👥 Team Roles

* **Member 1 (Backend + AI)**: Resume parsing, scoring, Flask APIs.
* **Member 2 (Frontend)**: Streamlit UI, dashboard, integration with backend.
* **Member 3 (Database + Integration)**: DB schema, API-DB integration, deployment setup.

---

## 📊 Future Enhancements

* ✅ Bulk resume upload (ZIP/PDFs)
* ✅ Student self-check portal
* ✅ Advanced analytics dashboard (per JD, skill gap trends)
* ✅ Integration with ATS (Applicant Tracking Systems)

---

## 📜 License

This project is licensed under the MIT License.

