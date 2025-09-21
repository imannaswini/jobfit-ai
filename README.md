

```markdown
JobFit-AI

An AI-powered job–candidate matching engine.  
This project uses a Python backend with SQLite databases to store job postings and user profiles,
and integrates with modern AI tools to recommend the best matches.

---

## 📂 Project Structure  ```

hack.jobfit-ai/
├── ai_engine.py        # Core AI logic for job-fit matching
├── jobs.db             # (Optional) SQLite database of job postings
├── users.db            # (Optional) SQLite database of user profiles
├── requirements.txt    # Python dependencies
├── .gitignore          # Git ignore rules (excludes venv & temp files)
└── .gitattributes      # Git LFS / repo attributes  ````


> **Note:** Local virtual environments (`venv/`, `venv_fresh/`) are intentionally excluded.

---

## 🚀 Getting Started

### 1️⃣ Clone the Repository
```bash
git clone https://github.com/imannaswini/jobfit-ai.git
cd jobfit-ai
````

### 2️⃣ Create & Activate a Virtual Environment

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate
```

### 3️⃣ Install Dependencies

Install all required third-party libraries with:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

If you prefer to install specific key libraries manually:

```bash
pip install pandas
pip install langchain
pip install langchain-google-genai==1.0.1   # 1.0.0 does not exist
```

*(Standard-library modules like `sqlite3` need no installation.)*

### 4️⃣ Database Setup

* If you have starter `jobs.db` and `users.db` files, place them in the project root.
* Otherwise, create new SQLite databases or modify `ai_engine.py` to generate them.

### 5️⃣ Run the AI Engine

```bash
python ai_engine.py
```

---

## 🛠 Development Notes

* Python Version: 3.9+ recommended
* Environment: Do **not** commit your virtual environment or large binaries.
* Large Files: Git LFS is configured in `.gitattributes` if you ever need to track large model files.

---

## 📝 Roadmap

* [ ] REST API endpoints for job matching
* [ ] Web frontend integration
* [ ] Advanced candidate ranking using LLMs
* [ ] Deployment on cloud (Docker / CI/CD)

---

## 🤝 Contributing

1. Fork the repo and create a feature branch.
2. Commit your changes and push to your branch.
3. Open a Pull Request.

---

## 📜 License

MIT License – feel free to use and modify.

````

---

Save this as **`README.md`** in the root of your repo:

```bash
echo "<paste content above>" > README.md
git add README.md
git commit -m "Update README with library installation details"
git push origin main
````

This version now clearly documents **how to install required libraries** and the exact version of `langchain-google-genai` to avoid installation errors.
