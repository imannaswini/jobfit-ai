import streamlit as st
import pandas as pd
import random
import os
import smtplib # This library is for sending emails. Actual implementation would require configuration.
from email.message import EmailMessage
from ai_engine import analyze_uploaded_files # Updated import
import sqlite3
from passlib.hash import pbkdf2_sha256
import io
from docx import Document
import pdfplumber
import re
import json
import ast

# --- Page Configuration ---
st.set_page_config(
    page_title="AI Recruitment Matcher",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Professional Custom CSS for Styling ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    /* Global Styles */
    .stApp {
        background: #f8fafc;
    }
    
    .main .block-container {
        padding: 2rem;
        max-width: 1200px;
        margin: 0 auto;
    }

    /* Typography */
    * {
        font-family: 'Inter', sans-serif;
    }
    
    h1, h2, h3 {
        color: #1a202c;
        font-weight: 600;
    }

    /* Home Page Styles */
    .hero-section {
        text-align: center;
        padding: 4rem 2rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 16px;
        margin-bottom: 3rem;
    }
    
    .hero-title {
        font-size: 3.5rem;
        font-weight: 700;
        margin-bottom: 1rem;
        line-height: 1.2;
    }
    
    .hero-subtitle {
        font-size: 1.3rem;
        opacity: 0.9;
        margin-bottom: 2rem;
    }
    
    .role-card {
        background: white;
        border-radius: 16px;
        padding: 2rem;
        text-align: center;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
        cursor: pointer;
        border: 2px solid transparent;
    }
    
    .role-card:hover {
        transform: translateY(-8px);
        box-shadow: 0 16px 48px rgba(0,0,0,0.15);
        border-color: #667eea;
    }
    
    .role-icon {
        font-size: 4rem;
        margin-bottom: 1rem;
    }
    
    .role-title {
        font-size: 1.5rem;
        font-weight: 600;
        color: #2d3748;
        margin-bottom: 0.5rem;
    }
    
    .role-description {
        color: #4a5568;
        font-size: 1rem;
    }

    /* Clean Card Styles */
    .card {
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 4px 16px rgba(0,0,0,0.08);
        border: 1px solid #e2e8f0;
        margin-bottom: 1rem;
    }
    
    .card:hover {
        box-shadow: 0 8px 24px rgba(0,0,0,0.12);
    }

    /* Button Styles */
    .stButton > button {
        border-radius: 8px;
        font-weight: 500;
        transition: all 0.2s ease;
    }
    
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border: none;
    }

    /* Form Styles */
    .auth-container {
        max-width: 400px;
        margin: 2rem auto;
        padding: 2rem;
        background: white;
        border-radius: 16px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
    }
    
    .auth-header {
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .auth-title {
        font-size: 2rem;
        font-weight: 600;
        color: #2d3748;
        margin-bottom: 0.5rem;
    }
    
    .auth-subtitle {
        color: #4a5568;
        font-size: 1rem;
    }

    /* Hide Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- SQLite Database Functions ---
def init_db():
    """Initializes the SQLite databases and creates the tables if they don't exist."""
    # Users database
    conn_users = sqlite3.connect('users.db')
    cursor_users = conn_users.cursor()
    cursor_users.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            gender TEXT,
            company TEXT,
            designation TEXT,
            bio TEXT,
            contact_number TEXT,
            linkedin TEXT
        );
    """)
    conn_users.commit()
    conn_users.close()

    # Jobs database
    conn_jobs = sqlite3.connect('jobs.db')
    cursor_jobs = conn_jobs.cursor()
    cursor_jobs.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            company TEXT NOT NULL,
            location TEXT,
            job_type TEXT,
            eligibility TEXT,
            criteria TEXT NOT NULL,
            date_posted TEXT,
            applications INTEGER
        );
    """)
    conn_jobs.commit()
    conn_jobs.close()

def add_user(user_data):
    """Adds a new user to the database."""
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    hashed_password = pbkdf2_sha256.hash(user_data['password'])
    
    try:
        cursor.execute(f"""
            INSERT INTO users (name, email, password, role, gender, company, designation, bio, contact_number, linkedin)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_data['name'], 
            user_data['email'], 
            hashed_password, 
            user_data['role'], 
            user_data['gender'], 
            user_data.get('company'), 
            user_data.get('designation'), 
            user_data.get('bio'), 
            user_data.get('contact_number'), 
            user_data.get('linkedin')
        ))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        st.error("Error: An account with this email already exists.")
        return False
    finally:
        conn.close()

def authenticate_user(email, password):
    """Authenticates a user from the database and returns their data if successful."""
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email=?", (email,))
    user_record = cursor.fetchone()
    conn.close()
    
    if user_record and pbkdf2_sha256.verify(password, user_record[3]):
        user_data = {
            'id': user_record[0],
            'name': user_record[1],
            'email': user_record[2],
            'password': user_record[3],
            'role': user_record[4],
            'gender': user_record[5],
            'company': user_record[6],
            'designation': user_record[7],
            'bio': user_record[8],
            'contact_number': user_record[9],
            'linkedin': user_record[10]
        }
        return user_data
    return None

def add_job(job_data):
    """Adds a new job to the database."""
    conn = sqlite3.connect('jobs.db')
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO jobs (title, company, location, job_type, eligibility, criteria, date_posted, applications)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        job_data['title'],
        job_data['company'],
        job_data.get('location', ''),
        job_data.get('job_type', ''),
        job_data.get('eligibility', ''),
        json.dumps(job_data.get('criteria', [])), # Store list as JSON string
        job_data.get('date_posted', ''),
        job_data.get('applications', 0)
    ))
    conn.commit()
    conn.close()

def get_job_listings():
    """Fetches all jobs from the database."""
    conn = sqlite3.connect('jobs.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM jobs")
    job_records = cursor.fetchall()
    conn.close()
    
    # Convert records to a list of dictionaries
    jobs = []
    for job in job_records:
        # Safely parse criteria field
        criteria = []
        if job[6]:  # Check if criteria field is not None or empty
            try:
                # Try to parse as JSON first
                criteria = json.loads(job[6])
            except (json.JSONDecodeError, TypeError):
                try:
                    # Fallback to ast.literal_eval for Python literals
                    criteria = ast.literal_eval(job[6])
                except (ValueError, SyntaxError, TypeError):
                    # If all else fails, treat as comma-separated string
                    criteria = [item.strip() for item in str(job[6]).split(',') if item.strip()]
        
        jobs.append({
            'id': job[0],
            'title': job[1],
            'company': job[2],
            'location': job[3],
            'job_type': job[4],
            'eligibility': job[5],
            'criteria': criteria,
            'datePosted': job[7],
            'applications': job[8],
            'shortlisted': random.randint(0, job[8]) if job[8] > 0 else 0 # Simulated value
        })
    return jobs

# --- Helper Functions ---
def get_verdict_html(verdict):
    if verdict == 'High':
        return f'<span class="verdict-high">✅ High</span>'
    elif verdict == 'Medium':
        return f'<span class="verdict-medium">⚠️ Medium</span>'
    else:
        return f'<span class="verdict-low">❌ Low</span>'

def get_ats_html(is_friendly):
    if is_friendly:
        return f'<span class="ats-friendly">✅ ATS Friendly</span>'
    else:
        return f'<span class="ats-unfriendly">⚠️ Not ATS Friendly</span>'

# --- Main Page Functions ---
def get_job_info_page(job_id):
    job_listings = get_job_listings()
    job = next((item for item in job_listings if item['id'] == job_id), None)
    if not job:
        st.error("Job not found.")
        return
        
    st.title(job['title'])
    st.markdown(f"Company: {job['company']} | Location: {job['location']} | Job Type: {job['job_type']}")
    st.markdown("---")
    
    st.subheader("Role & Information")
    st.info(f"The company is hiring for the role of a **{job['title']}**. This is a **{job['job_type']}** position based in **{job['location']}**.")
    
    st.subheader("Eligibility Criteria")
    st.warning(job['eligibility'])
    
    st.subheader("Key Skills & Criteria")
    criteria_html = "".join([f'<span class="skill-missing">{skill}</span>' for skill in job['criteria']])
    st.markdown(f'<div style="display: flex; flex-wrap: wrap; gap: 0.5rem;">{criteria_html}</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    st.subheader("Resume Score Checker")
    st.markdown("Upload your resume below to check how well it matches this job's criteria.")
    
    uploaded_file = st.file_uploader("Upload your resume (PDF, DOCX)", type=['pdf', 'docx'], key=f"job_resume_uploader_{job_id}")
    
    if uploaded_file:
        st.success("Resume uploaded successfully! Analyzing...")
        
        with st.spinner("Analyzing your resume with the AI engine..."):
            analysis_result = analyze_uploaded_files(uploaded_file, job['criteria'])
        
        score = analysis_result['score']
        matched_skills = analysis_result['matched_skills']
        missing_skills = analysis_result['missing_skills']
        feedback = analysis_result['feedback']
        
        st.markdown(f"#### Your Resume Match Score: **{score}%**")
        st.progress(score / 100)
        
        st.markdown("---")
        st.subheader("Personalized Feedback for this Role")
        st.info(feedback)
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### ✅ Matched Skills")
            skills_html = "".join([f'<span class="skill-matched">{skill}</span>' for skill in matched_skills])
            st.markdown(f'<div style="display: flex; flex-wrap: wrap; gap: 0.5rem;">{skills_html}</div>', unsafe_allow_html=True)
            
        with col2:
            st.markdown("#### ❌ Missing Skills")
            skills_html = "".join([f'<span class="skill-missing">{skill}</span>' for skill in missing_skills])
            st.markdown(f'<div style="display: flex; flex-wrap: wrap; gap: 0.5rem;">{skills_html}</div>', unsafe_allow_html=True)
        
        st.markdown("---")
        col_enroll, col_back = st.columns(2)
        if col_enroll.button("Enroll for this Job", use_container_width=True, type="primary"):
            # Initialize enrolled students list if it doesn't exist
            if 'enrolled_students' not in st.session_state:
                st.session_state.enrolled_students = []
            
            # Create enrollment record
            enrollment = {
                'student_id': st.session_state.user_data['id'],
                'student_name': st.session_state.user_data['name'],
                'student_email': st.session_state.user_data['email'],
                'student_bio': st.session_state.user_data.get('bio', ''),
                'student_contact': st.session_state.user_data.get('contact_number', ''),
                'job_id': job['id'],
                'job_title': job['title'],
                'company': job['company'],
                'score': score,
                'matched_skills': matched_skills,
                'missing_skills': missing_skills,
                'ats_friendly': score > 60,
                'enrollment_date': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S'),
                'status': 'Applied'
            }
            
            # Check if already enrolled
            already_enrolled = any(
                e['student_id'] == st.session_state.user_data['id'] and e['job_id'] == job['id']
                for e in st.session_state.enrolled_students
            )
            
            if not already_enrolled:
                st.session_state.enrolled_students.append(enrollment)
                st.success("You have successfully enrolled for this job!")
                # Navigate back to job opportunities
                st.session_state.student_page = "job_listings"
                st.rerun()
            else:
                st.warning("You have already enrolled for this job!")
        
        if col_back.button("⬅️ Back to Job Listings", use_container_width=True):
            st.session_state.student_page = "job_listings"
            st.rerun()
    else:
        if st.button("⬅️ Back to Job Listings", use_container_width=True):
            st.session_state.student_page = "job_listings"
            st.rerun()
    
    st.markdown("---")
    st.subheader("Anonymous Q&A")
    st.markdown("Ask a question about this job or company anonymously. The recruiter might answer it here!")
    
    if 'job_questions' not in st.session_state:
        st.session_state.job_questions = {}
    if job_id not in st.session_state.job_questions:
        st.session_state.job_questions[job_id] = [{'question': 'What is the work culture like?', 'answer': 'We have a very collaborative and innovative environment.'}] # Dummy Q&A
    
    with st.form(f"question_form_{job_id}"):
        new_question = st.text_area("Your question:", key=f"question_box_{job_id}")
        submit_question = st.form_submit_button("Post Anonymously")
        if submit_question and new_question:
            st.session_state.job_questions[job_id].append({'question': new_question, 'answer': None})
            st.success("Your question has been posted!")
    
    for qa in st.session_state.job_questions[job_id]:
        st.markdown(f"**Q:** {qa['question']}")
        if qa['answer']:
            st.info(f"**A:** {qa['answer']}")
        else:
            st.warning("Awaiting answer from recruiter.")

def recruiter_dashboard():
    # Enhanced header with welcome message
    st.markdown(f"""
    <div style="text-align: center; margin-bottom: 3rem;">
        <h1 style="font-size: 3.5rem; margin-bottom: 0.5rem;">📈 Recruiter Dashboard</h1>
        <p style="font-size: 1.3rem; color: #4a5568; margin: 0;">Welcome back, {st.session_state.user_data.get('name', 'Recruiter')}! 👋</p>
        <p style="font-size: 1rem; color: #718096; margin-top: 0.5rem;">Here's your recruitment overview and analytics</p>
    </div>
    """, unsafe_allow_html=True)
    
    job_listings = get_job_listings()
    enrolled_students = st.session_state.get('enrolled_students', [])
    total_apps = len(enrolled_students)
    total_shortlisted = len([s for s in enrolled_students if s.get('status') == 'Accepted'])
    avg_score = sum(s.get('score', 0) for s in enrolled_students) // len(enrolled_students) if enrolled_students else 0

    # Enhanced metrics section
    st.markdown("""
    <div style="margin-bottom: 2rem;">
        <h2 style="color: #2d3748; margin-bottom: 1rem; display: flex; align-items: center; gap: 0.5rem;">
            📊 Key Performance Metrics
        </h2>
        <p style="color: #4a5568; margin-bottom: 2rem;">Real-time insights into your recruitment pipeline and candidate performance</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">🏢</div>
            <h2 style="font-family: 'Inter', sans-serif; font-size: 2.5rem; margin: 0.5rem 0; color: #2d3748;">{len(job_listings)}</h2>
            <p style="color: #4a5568; margin: 0; font-weight: 500;">Active Jobs</p>
            <p style="color: #718096; font-size: 0.9rem; margin-top: 0.5rem;">Currently posted positions</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">📝</div>
            <h2 style="font-family: 'Inter', sans-serif; font-size: 2.5rem; margin: 0.5rem 0; color: #2d3748;">{total_apps}</h2>
            <p style="color: #4a5568; margin: 0; font-weight: 500;">Applications</p>
            <p style="color: #718096; font-size: 0.9rem; margin-top: 0.5rem;">Total resumes received</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">✅</div>
            <h2 style="font-family: 'Inter', sans-serif; font-size: 2.5rem; margin: 0.5rem 0; color: #2d3748;">{total_shortlisted}</h2>
            <p style="color: #4a5568; margin: 0; font-weight: 500;">Accepted</p>
            <p style="color: #718096; font-size: 0.9rem; margin-top: 0.5rem;">Candidates selected</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">⭐</div>
            <h2 style="font-family: 'Inter', sans-serif; font-size: 2.5rem; margin: 0.5rem 0; color: #2d3748;">{avg_score}%</h2>
            <p style="color: #4a5568; margin: 0; font-weight: 500;">Avg. Score</p>
            <p style="color: #718096; font-size: 0.9rem; margin-top: 0.5rem;">Resume relevance score</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # Enhanced job posting section
    st.markdown("""
    <div style="margin-bottom: 2rem;">
        <h2 style="color: #2d3748; margin-bottom: 1rem; display: flex; align-items: center; gap: 0.5rem;">
            📋 Job Management Center
        </h2>
        <p style="color: #4a5568; margin-bottom: 2rem;">Post new positions and manage your active job listings</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Enhanced job posting card
    st.markdown("""
    <div style="background: linear-gradient(135deg, #ffffff 0%, #f7fafc 100%); border-radius: 20px; padding: 2rem; margin: 1rem 0; box-shadow: 0 8px 32px rgba(0,0,0,0.08); border: 1px solid rgba(255,255,255,0.5);">
        <h3 style="color: #2d3748; margin-bottom: 1rem; display: flex; align-items: center; gap: 0.5rem;">
            🚀 Post New Job
        </h3>
        <p style="color: #4a5568; margin-bottom: 1.5rem;">
            Upload a job description and let our AI analyze candidate resumes to find the perfect match for your role.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Enhanced file uploader
    st.markdown("""
    <div style="background: linear-gradient(135deg, #edf2f7 0%, #e2e8f0 100%); padding: 2rem; border-radius: 16px; margin: 1rem 0; text-align: center; border: 2px dashed #cbd5e0;">
        <h4 style="color: #2d3748; margin-bottom: 1rem;">📎 Upload Job Description</h4>
        <p style="color: #4a5568; margin-bottom: 1rem;">Supported formats: PDF, DOCX (Max 10MB)</p>
    </div>
    """, unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader("Choose job description file", type=['pdf', 'docx'], label_visibility="collapsed")
    
    if st.button("🚀 Post Job", type="primary", use_container_width=True):
        if uploaded_file:
            # Extract text from the uploaded file
            text = ""
            try:
                if uploaded_file.name.endswith('.docx'):
                    doc = Document(io.BytesIO(uploaded_file.getvalue()))
                    text = "\n".join([para.text for para in doc.paragraphs])
                elif uploaded_file.name.endswith('.pdf'):
                    with pdfplumber.open(io.BytesIO(uploaded_file.getvalue())) as pdf:
                        text = "\n".join([page.extract_text() for page in pdf.pages])
                else:
                    st.error("Unsupported file type for JD parsing. Please use DOCX or PDF.")
                    return

                # Simple JD parsing logic to extract key details
                title_match = re.search(r"Job Title:\s*(.*)", text, re.IGNORECASE)
                title = title_match.group(1).strip() if title_match else uploaded_file.name.replace('.docx', '').replace('.pdf', '').strip()
                
                company_match = re.search(r"Company:\s*(.*)", text, re.IGNORECASE)
                company = company_match.group(1).strip() if company_match else st.session_state.user_data.get('company', 'Unknown Company')

                # Simple skills extraction
                skills_match = re.search(r"(skills|requirements|criteria|qualifications):(.*)", text, re.IGNORECASE | re.DOTALL)
                if skills_match:
                    skills_text = skills_match.group(2)
                    criteria = [s.strip() for s in skills_text.split(',')]
                else:
                    criteria = ["No specific skills found"]
                
                job_data = {
                    'title': title,
                    'company': company,
                    'location': 'N/A', # Placeholder for demo
                    'job_type': 'N/A', # Placeholder for demo
                    'eligibility': 'N/A', # Placeholder for demo
                    'criteria': criteria,
                    'date_posted': pd.Timestamp.now().strftime('%Y-%m-%d'),
                    'applications': 25  # Fixed number instead of random
                }
                
                add_job(job_data)
                st.success(f"✅ Job '{title}' posted successfully!")
                st.rerun()

            except UnicodeDecodeError:
                st.error("There was a character encoding error. Please try a different file.")
            except Exception as e:
                st.error(f"An unexpected error occurred during file processing: {e}")
        else:
            st.warning("Please upload a job description file first.")
        
    # Enhanced active jobs section
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("""
    <div style="margin-bottom: 2rem;">
        <h2 style="color: #2d3748; margin-bottom: 1rem; display: flex; align-items: center; gap: 0.5rem;">
            📊 Your Active Job Listings
        </h2>
        <p style="color: #4a5568; margin-bottom: 2rem;">Monitor and manage your posted positions</p>
    </div>
    """, unsafe_allow_html=True)
    
    if job_listings:
        for job in job_listings:
            enrolled_for_job = [s for s in enrolled_students if s.get('job_id') == job['id']]
            applications_count = len(enrolled_for_job)
            accepted_count = len([s for s in enrolled_for_job if s.get('status') == 'Accepted'])
            
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #ffffff 0%, #f7fafc 100%); border-radius: 16px; padding: 2rem; margin: 1rem 0; box-shadow: 0 8px 24px rgba(0,0,0,0.06); border: 1px solid rgba(255,255,255,0.8);">
                <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 1rem;">
                    <div>
                        <h3 style="color: #2d3748; margin: 0 0 0.5rem 0;">{job['title']}</h3>
                        <p style="color: #4a5568; margin: 0; display: flex; align-items: center; gap: 1rem;">
                            <span>🏢 {job['company']}</span>
                            <span>📅 Posted: {job['datePosted']}</span>
                        </p>
                    </div>
                    <div style="text-align: right;">
                        <div style="background: linear-gradient(135deg, #4299e1, #3182ce); color: white; padding: 0.5rem 1rem; border-radius: 12px; font-weight: 600; margin-bottom: 0.5rem;">
                            {applications_count} Applications
                        </div>
                        <div style="background: linear-gradient(135deg, #48bb78, #38a169); color: white; padding: 0.5rem 1rem; border-radius: 12px; font-weight: 600;">
                            {accepted_count} Accepted
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="text-align: center; padding: 3rem; background: linear-gradient(135deg, #edf2f7 0%, #e2e8f0 100%); border-radius: 16px; margin: 1rem 0;">
            <div style="font-size: 4rem; margin-bottom: 1rem;">📋</div>
            <h3 style="color: #2d3748; margin-bottom: 1rem;">No Jobs Posted Yet</h3>
            <p style="color: #4a5568;">Upload your first job description to start finding the perfect candidates!</p>
        </div>
        """, unsafe_allow_html=True)

def student_job_listings_page():
    # Enhanced header
    st.markdown("""
    <div style="text-align: center; margin-bottom: 3rem;">
        <h1 style="font-size: 3.5rem; margin-bottom: 0.5rem;">🏢 Job Opportunities</h1>
        <p style="font-size: 1.3rem; color: #4a5568; margin: 0;">Discover your next career opportunity</p>
        <p style="font-size: 1rem; color: #718096; margin-top: 0.5rem;">AI-powered job matching tailored for you</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Enhanced sidebar filters
    st.sidebar.markdown("""
    <div style="background: linear-gradient(135deg, #ffffff 0%, #f7fafc 100%); padding: 1.5rem; border-radius: 16px; margin-bottom: 1rem;">
        <h3 style="color: #2d3748; margin-bottom: 1rem; display: flex; align-items: center; gap: 0.5rem;">
            🔎 Smart Filters
        </h3>
    </div>
    """, unsafe_allow_html=True)
    job_listings = get_job_listings()
    job_types = st.sidebar.multiselect("Job Type", ["Remote", "Hybrid", "On-site"])
    job_fields = st.sidebar.multiselect("Desired Field", ["Data Science", "Full Stack Development", "Cloud Engineering", "Product Management", "Marketing"])
    search_query = st.sidebar.text_input("Search by Title or Company")

    filtered_jobs = job_listings
    if job_types:
        filtered_jobs = [job for job in filtered_jobs if job['job_type'] in job_types]
    if job_fields:
        filtered_jobs = [job for job in filtered_jobs if job['field'] in job_fields]
    if search_query:
        filtered_jobs = [job for job in filtered_jobs if search_query.lower() in job['title'].lower() or search_query.lower() in job['company'].lower()]

    if not filtered_jobs:
        st.warning("No opportunities found matching your filters. Try a different search!")
    else:
        for job in filtered_jobs:
            # Enhanced job card with custom HTML
            st.markdown(f"""
            <div class="job-card">
                <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                    <div style="flex: 1;">
                        <h3 style="margin: 0 0 0.5rem 0; color: #1a202c; font-size: 1.5rem;">{job['title']}</h3>
                        <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 1rem; color: #4a5568;">
                            <span style="display: flex; align-items: center; gap: 0.3rem;">
                                🏢 <strong>{job['company']}</strong>
                            </span>
                            <span style="display: flex; align-items: center; gap: 0.3rem;">
                                📍 {job['location']}
                            </span>
                            <span style="display: flex; align-items: center; gap: 0.3rem;">
                                💼 {job['job_type']}
                            </span>
                        </div>
                        <div style="background: linear-gradient(135deg, #edf2f7 0%, #e2e8f0 100%); padding: 1rem; border-radius: 12px; margin-bottom: 1rem;">
                            <strong style="color: #2d3748;">Eligibility:</strong> 
                            <span style="color: #4a5568;">{job['eligibility']}</span>
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Button section
            col1, col2, col3 = st.columns([2, 1, 1])
            with col3:
                # Check if student has already applied to this job
                has_applied = False
                if 'enrolled_students' in st.session_state and 'user_data' in st.session_state:
                    has_applied = any(
                        enrollment['student_id'] == st.session_state.user_data.get('id') and 
                        enrollment['job_id'] == job['id']
                        for enrollment in st.session_state.enrolled_students
                    )
                
                if has_applied:
                    st.button("✅ Applied", key=f"applied_{job['id']}", use_container_width=True, disabled=True, type="secondary")
                else:
                    if st.button("🚀 Apply Now", key=f"apply_{job['id']}", use_container_width=True, type="primary"):
                        st.session_state.student_page = "job_info"
                        st.session_state.selected_job_id = job['id']
                        st.rerun()
            
            st.markdown("<br>", unsafe_allow_html=True)

# --- Profile Management Pages ---
def student_profile_page():
    st.markdown("""
    <div style="text-align: center; margin-bottom: 2rem;">
        <h1 style="font-size: 3rem; margin-bottom: 0.5rem;">👤 My Profile</h1>
        <p style="font-size: 1.2rem; color: #4a5568; margin: 0;">Edit and manage your personal details</p>
    </div>
    """, unsafe_allow_html=True)
    
    user_data = st.session_state.user_data

    # --- Enhanced Profile Information Form ---
    st.markdown("""
    <div class="profile-section">
        <h2 style="color: #2d3748; margin-bottom: 1.5rem; display: flex; align-items: center; gap: 0.5rem;">
            📝 Personal Information
        </h2>
    </div>
    """, unsafe_allow_html=True)
    
    with st.form("student_profile_form"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("👤 Full Name", value=user_data.get('name', ''), placeholder="Enter your full name")
            contact_number = st.text_input("📱 Contact Number", value=user_data.get('contact_number', ''), placeholder="+1 (555) 123-4567")
        with col2:
            email = st.text_input("📧 Email Address", value=user_data.get('email', ''), placeholder="your.email@example.com")
            linkedin = st.text_input("🔗 LinkedIn Profile URL", value=user_data.get('linkedin', ''), placeholder="https://linkedin.com/in/yourprofile")
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("### 💼 Professional Bio")
        bio = st.text_area("Tell us about your professional background, skills, and career goals", 
                          value=user_data.get('bio', ''), 
                          height=150,
                          placeholder="e.g., Aspiring Data Scientist with strong foundation in Python, SQL, and Machine Learning. Passionate about solving complex problems with data-driven insights...")
        
        st.markdown("<br>", unsafe_allow_html=True)
        save_button = st.form_submit_button("💾 Save Changes", type="primary", use_container_width=True)

    if save_button:
        # Database update logic
        with sqlite3.connect('users.db') as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET name=?, email=?, contact_number=?, linkedin=?, bio=? WHERE id=?",
                           (name, email, contact_number, linkedin, bio, user_data['id']))
        st.success("Profile updated successfully! ✅")
        
        # Refresh session state with the new data
        st.session_state.user_data.update({
            'name': name, 'email': email, 'contact_number': contact_number, 
            'linkedin': linkedin, 'bio': bio
        })
        st.rerun()

    # --- Enhanced Resume Checker Section ---
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("""
    <div class="profile-section">
        <h2 style="color: #2d3748; margin-bottom: 1.5rem; display: flex; align-items: center; gap: 0.5rem;">
            📄 AI Resume Analyzer
        </h2>
        <p style="color: #4a5568; margin-bottom: 1.5rem;">
            Upload your resume to get an instant AI-powered analysis with personalized feedback and ATS compatibility check.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Enhanced file uploader section
    st.markdown("""
    <div style="background: linear-gradient(135deg, #edf2f7 0%, #e2e8f0 100%); padding: 2rem; border-radius: 16px; margin: 1rem 0; text-align: center; border: 2px dashed #cbd5e0;">
        <h4 style="color: #2d3748; margin-bottom: 1rem;">📎 Upload Your Resume</h4>
        <p style="color: #4a5568; margin-bottom: 1rem;">Supported formats: PDF, DOCX (Max 10MB)</p>
    </div>
    """, unsafe_allow_html=True)
    
    uploaded_resume = st.file_uploader("Choose your resume file", type=['pdf', 'docx'], key="general_resume_uploader", label_visibility="collapsed")
    
    if uploaded_resume:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%); padding: 1.5rem; border-radius: 12px; margin: 1rem 0;">
            <h4 style="color: #155724; margin: 0; display: flex; align-items: center; gap: 0.5rem;">
                ✅ Resume uploaded successfully! Analyzing with AI...
            </h4>
        </div>
        """, unsafe_allow_html=True)
        
        generic_skills = ["Python", "JavaScript", "SQL", "Machine Learning", "Data Analysis", "Cloud Computing", "Project Management", "Communication", "Leadership", "Problem Solving"]
        
        with st.spinner("🤖 AI is analyzing your resume..."):
            analysis_result = analyze_uploaded_files(uploaded_resume, generic_skills)
        
        score = analysis_result['score']
        ats_friendly = score > 60
        
        # Enhanced results display
        st.markdown("<br>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown(f"""
            <div style="text-align: center; background: linear-gradient(135deg, #ffffff 0%, #f7fafc 100%); padding: 2rem; border-radius: 20px; box-shadow: 0 8px 32px rgba(0,0,0,0.1);">
                <h2 style="color: #2d3748; margin-bottom: 1rem;">📊 Your Resume Score</h2>
                <div style="font-size: 4rem; font-weight: bold; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin: 1rem 0;">
                    {score}%
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.progress(score / 100)
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(get_ats_html(ats_friendly), unsafe_allow_html=True)
        with col2:
            st.markdown(get_verdict_html('High' if score > 80 else 'Medium' if score > 60 else 'Low'), unsafe_allow_html=True)
        
        st.markdown("""
        <div style="background: linear-gradient(135deg, #bee3f8 0%, #90cdf4 100%); padding: 1.5rem; border-radius: 12px; margin: 1rem 0;">
            <p style="color: #1a365d; margin: 0; display: flex; align-items: center; gap: 0.5rem;">
                💡 <strong>Pro Tip:</strong> This is a general analysis. For job-specific scores and detailed feedback, apply to specific positions in the Job Opportunities section!
            </p>
        </div>
        """, unsafe_allow_html=True)

def recruiter_profile_page():
    st.title("My Profile 👤")
    st.markdown("### Edit and manage your personal and company details.")
    st.markdown("---")
    
    user_data = authenticate_user(st.session_state.user_data['email'], st.session_state.user_data['password'])

    with st.form("recruiter_profile_form"):
        st.subheader("Personal & Company Information")
        name = st.text_input("Full Name", value=user_data['name'])
        email = st.text_input("Email Address", value=user_data['email'])
        company = st.text_input("Company Name", value=user_data.get('company', ''))
        designation = st.text_input("Designation", value=user_data.get('designation', ''))
        linkedin = st.text_input("LinkedIn Profile URL", value=user_data.get('linkedin', ''))
        
        save_button = st.form_submit_button("Save Changes", type="primary", use_container_width=True)

    if save_button:
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE users SET name=?, email=?, company=?, designation=?, linkedin=? WHERE id=?
        """, (name, email, company, designation, linkedin, user_data['id']))
        conn.commit()
        conn.close()
        st.success("Profile updated successfully! ✅")

def get_simulated_students():
    """Get simulated students with consistent scores stored in session state"""
    if 'simulated_students' not in st.session_state:
        # Initialize with fixed scores that won't change
        st.session_state.simulated_students = [
            {'id': 1, 'name': 'Rahul Sharma', 'gender': 'Male', 'email': 'rahul@example.com', 'contact_number': '1234567890', 'bio': 'Aspiring Data Scientist with a strong foundation in Python and SQL.', 'job_title': 'Senior Data Scientist', 'job_id': 1, 'score': 87, 'ats_friendly': True, 'matched_skills': ['Python', 'SQL', 'Machine Learning'], 'missing_skills': ['TensorFlow', 'AWS'], 'soft_skills': {'Communication': 85, 'Problem-Solving': 92, 'Teamwork': 78}},
            {'id': 2, 'name': 'Priya Patel', 'gender': 'Female', 'email': 'priya@example.com', 'contact_number': '0987654321', 'bio': 'Full Stack Developer with expertise in React, Node.js, and MongoDB.', 'job_title': 'Full Stack Developer', 'job_id': 2, 'score': 82, 'ats_friendly': True, 'matched_skills': ['React', 'Node.js', 'MongoDB'], 'missing_skills': ['Redis'], 'soft_skills': {'Communication': 89, 'Problem-Solving': 85, 'Teamwork': 91}},
            {'id': 3, 'name': 'Amit Kumar', 'gender': 'Male', 'email': 'amit@example.com', 'contact_number': '1122334455', 'bio': 'Recent graduate passionate about cloud computing and DevOps.', 'job_title': 'Cloud Engineer', 'job_id': 3, 'score': 74, 'ats_friendly': False, 'matched_skills': ['AWS', 'CI/CD'], 'missing_skills': ['Terraform', 'Kubernetes'], 'soft_skills': {'Communication': 72, 'Problem-Solving': 88, 'Teamwork': 85}},
        ]
    return st.session_state.simulated_students

def explore_students_page():
    st.title("Explore Students 🚀")
    st.markdown("### Discover and filter potential candidates.")
    st.markdown("---")

    # Get enrolled students instead of simulated ones
    enrolled_students = st.session_state.get('enrolled_students', [])
    
    if not enrolled_students:
        st.info("No students have enrolled for jobs yet. Students will appear here once they apply for positions.")
        return

    for student in enrolled_students:
        with st.container(border=True):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.subheader(f"{student['student_name']}")
                st.caption(f"**Bio:** {student['student_bio']}")
                st.caption(f"**Applied for:** {student['job_title']} at {student['company']}")
                st.caption(f"**Applied on:** {student['enrollment_date']}")
                st.markdown(get_ats_html(student['ats_friendly']), unsafe_allow_html=True)
            with col2:
                st.metric(label="Resume Score", value=f"{student['score']}%")
                st.markdown(get_verdict_html('High' if student['score'] > 80 else 'Medium'), unsafe_allow_html=True)
            
            if st.button(f"View Full Profile", key=f"view_{student['student_id']}_{student['job_id']}", use_container_width=True):
                st.session_state.recruiter_page = "view_student_profile"
                st.session_state.selected_enrolled_student = student
                st.rerun()

def view_student_profile_page():
    # Add JavaScript to scroll to top
    st.markdown("""
    <script>
    window.parent.document.querySelector('.main').scrollTop = 0;
    </script>
    """, unsafe_allow_html=True)
    
    # Get the selected enrolled student
    if 'selected_enrolled_student' not in st.session_state:
        st.error("No student selected.")
        if st.button("⬅️ Back to Students", use_container_width=True):
            st.session_state.recruiter_page = "explore_students"
            st.rerun()
        return
    
    student = st.session_state.selected_enrolled_student
    job_listings = get_job_listings()
    
    # Find the job the student applied for
    job = None
    if job_listings:
        job = next((j for j in job_listings if j['id'] == student['job_id']), None)
    
    # Create job info from enrollment data if job not found in listings
    if not job:
        job = {
            'id': student['job_id'],
            'title': student['job_title'],
            'company': student['company'],
            'location': 'N/A',
            'job_type': 'N/A'
        }

    st.title(f"Profile: {student['student_name']}")
    st.markdown("---")
    
    col_info, col_score = st.columns([3, 1])
    with col_info:
        st.subheader("Candidate Information")
        st.markdown(f"**Bio:** {student['student_bio']}")
        st.markdown(f"**Email:** {student['student_email']}")
        st.markdown(f"**Contact:** {student['student_contact']}")
        st.markdown(f"**Applied For:** {job['title']} at {job['company']}")
        st.markdown(f"**Application Date:** {student['enrollment_date']}")
        st.markdown(f"**Status:** {student['status']}")
        
    with col_score:
        st.metric(label="Resume Score", value=f"{student['score']}%")
        st.markdown(get_verdict_html('High' if student['score'] > 80 else 'Medium'), unsafe_allow_html=True)
        st.markdown(get_ats_html(student['ats_friendly']), unsafe_allow_html=True)
        
    st.markdown("---")
    
    st.subheader("Job Match Analysis")
    st.info(f"This profile was evaluated against the criteria for the **{job['title']}** role.")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### ✅ Matched Skills")
        matched_html = "".join([f'<span class="skill-matched">{skill}</span>' for skill in student['matched_skills']])
        st.markdown(f'<div style="display: flex; flex-wrap: wrap; gap: 0.5rem;">{matched_html}</div>', unsafe_allow_html=True)
    with col2:
        st.markdown("#### ❌ Missing Skills")
        missing_html = "".join([f'<span class="skill-missing">{skill}</span>' for skill in student['missing_skills']])
        st.markdown(f'<div style="display: flex; flex-wrap: wrap; gap: 0.5rem;">{missing_html}</div>', unsafe_allow_html=True)
        
    st.markdown("---")
    
    col_accept, col_dismiss, col_back = st.columns([1, 1, 2])
    
    if col_accept.button("✅ Accept Student", type="primary", use_container_width=True):
        if 'student_notifications' not in st.session_state:
            st.session_state.student_notifications = []
        
        # Add notification for the student
        notification = {
            'student_id': student['student_id'],
            'student_name': student['student_name'],
            'student_email': student['student_email'],
            'job_title': job['title'],
            'job_id': job['id'],
            'status': 'Accepted',
            'recruiter_name': st.session_state.user_data['name'],
            'company': st.session_state.user_data.get('company', 'Unknown Company'),
            'message': f"Congratulations! You have been selected for the {job['title']} role.",
            'timestamp': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        st.session_state.student_notifications.append(notification)
        
        # Update the student's status in enrolled_students
        for i, enrolled_student in enumerate(st.session_state.enrolled_students):
            if (enrolled_student['student_id'] == student['student_id'] and 
                enrolled_student['job_id'] == student['job_id']):
                st.session_state.enrolled_students[i]['status'] = 'Accepted'
                break
        
        # Show success message without balloons
        st.success(f"✅ **{student['student_name']}** has been accepted for the **{job['title']}** position!")
        st.info(f"📧 Notification sent to: **{student['student_email']}**")
        st.info(f"🏢 Company: **{st.session_state.user_data.get('company', 'Your Company')}**")
    
    if col_dismiss.button("❌ Dismiss Student", use_container_width=True):
        # Remove the student from the enrolled students database
        if 'enrolled_students' in st.session_state:
            st.session_state.enrolled_students = [
                s for s in st.session_state.enrolled_students 
                if not (s['student_id'] == student['student_id'] and s['job_id'] == student['job_id'])
            ]
        st.success(f"Student {student['student_name']} has been dismissed and removed from the database.")
        st.session_state.recruiter_page = "explore_students"  # Navigate back to student list
        st.rerun()
    
    if col_back.button("⬅️ Back to Students", use_container_width=True):
        st.session_state.recruiter_page = "explore_students"
        st.rerun()

# --- Authentication Logic (Simulated) ---
def redirect_to_login():
    st.session_state.login_state = 'login'
    st.rerun()

def redirect_to_signup():
    st.session_state.login_state = 'signup'
    st.rerun()

def show_login_page():
    st.title("Login to AI Recruitment Matcher 🤖")
    st.markdown("---")
    st.subheader("Welcome back!")

    with st.form("login_form"):
        email = st.text_input("Email ID", placeholder="Enter your email")
        password = st.text_input("Password", type="password", placeholder="Enter your password")
        login_button = st.form_submit_button("Log In", type="primary", use_container_width=True)
    
    if login_button:
        user_data = authenticate_user(email, password)
        if user_data:
            st.session_state.logged_in = True
            st.session_state.user_role = user_data['role']
            st.session_state.user_data = user_data
            st.session_state.page = 'dashboard'
            st.success("Login successful! Redirecting to your dashboard...")
            st.rerun()
        else:
            st.error("Invalid email or password.")
    
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("Don't have an account?")
        if st.button("Sign Up", key="login_signup_button", use_container_width=True):
            redirect_to_signup()
    with col2:
        st.markdown("Forgot your password?")
        if st.button("Forgot Password?", key="forgot_password_button", use_container_width=True):
            st.session_state.login_state = 'forgot_password'
            st.rerun()
            
def show_forgot_password_page():
    st.title("Forgot Password? 🤔")
    st.markdown("---")
    st.info("Enter your registered email or contact number to receive a one-time password (OTP).")
    
    with st.form("forgot_password_form"):
        contact_info = st.text_input("Registered Email or Contact Number")
        send_otp_button = st.form_submit_button("Send OTP", type="primary")
        
    if send_otp_button:
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email=?", (contact_info,))
        user_record = cursor.fetchone()
        conn.close()

        if user_record:
            otp = random.randint(100000, 999999)
            st.session_state.otp = otp
            st.session_state.forgot_password_email = contact_info
            st.success(f"OTP sent to {contact_info}! Your OTP is: **{otp}** (Simulated)")
            st.session_state.login_state = 'verify_otp'
            st.rerun()
        else:
            st.error("Could not find an account with that information.")

def show_verify_otp_page():
    st.title("Verify OTP 🔐")
    st.markdown("---")
    st.info(f"An OTP has been sent to {st.session_state.get('forgot_password_email', 'your email')}. Please enter it below.")
    
    with st.form("verify_otp_form"):
        otp_input = st.text_input("Enter OTP", type="password")
        verify_button = st.form_submit_button("Verify", type="primary")
        
    if verify_button:
        if otp_input == str(st.session_state.get('otp')):
            st.success("OTP verified successfully!")
            st.session_state.login_state = 'reset_password'
            st.rerun()
        else:
            st.error("Invalid OTP. Please try again.")

def show_reset_password_page():
    st.title("Reset Password 🔑")
    st.markdown("---")
    st.info("Please enter your new password.")
    
    with st.form("reset_password_form"):
        new_password = st.text_input("New Password", type="password")
        confirm_password = st.text_input("Confirm New Password", type="password")
        reset_button = st.form_submit_button("Reset Password", type="primary")
        
    if reset_button:
        if new_password == confirm_password and new_password:
            conn = sqlite3.connect('users.db')
            cursor = conn.cursor()
            hashed_password = pbkdf2_sha256.hash(new_password)
            cursor.execute("UPDATE users SET password=? WHERE email=?", (hashed_password, st.session_state.forgot_password_email))
            conn.commit()
            conn.close()
            st.success("Password reset successfully! You can now log in with your new password.")
            st.session_state.login_state = 'login'
            st.rerun()
        else:
            st.error("Passwords do not match or are empty. Please try again.")

def show_signup_page():
    st.markdown('<div class="signup-form">', unsafe_allow_html=True)
    st.markdown('<h2 class="signup-header">Create Your Account 🎉</h2>', unsafe_allow_html=True)
    st.markdown("---")
    
    st.subheader("1. Select Your Role")
    role = st.radio("I am a:", ("Recruiter", "Student"), key="signup_role")
    
    st.subheader(f"2. Enter Your Details")
    with st.form("signup_form"):
        name = st.text_input("Full Name")
        email = st.text_input("Email ID")
        password = st.text_input("Create Password", type="password")
        gender = st.selectbox("Gender", ["Prefer not to say", "Male", "Female", "Other"])

        if role == "Recruiter":
            st.info("Please provide your company details.")
            company = st.text_input("Company Name")
            designation = st.text_input("Designation")
            linkedin = st.text_input("LinkedIn Profile URL (Optional)")
            
        else: # Student
            st.info("Tell us a bit about your professional and academic background.")
            contact_number = st.text_input("Contact Number")
            bio = st.text_area("Write a short professional bio (e.g., Aspiring Data Scientist with...)", height=150)
            linkedin = st.text_input("LinkedIn Profile URL (Optional)")
            
        signup_button = st.form_submit_button("Sign Up", type="primary", use_container_width=True)

    if signup_button:
        if name and email and password:
            user_data = {
                'name': name,
                'email': email,
                'password': password,
                'role': role,
                'gender': gender
            }
            if role == "Recruiter":
                user_data.update({'company': company, 'designation': designation, 'linkedin': linkedin})
            else:
                user_data.update({'bio': bio, 'linkedin': linkedin, 'contact_number': contact_number})
            
            if add_user(user_data):
                st.success(f"Account for {role} created successfully! Please log in.")
                st.session_state.login_state = 'login'
                st.rerun()
        else:
            st.error("Please fill in all required fields.")
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("Already have an account?")
    if st.button("Log In", key="signup_login_button"):
        redirect_to_login()


# --- Home Page ---
def home_page():
    st.markdown("""\
    <div class="hero-section">
        <h1 class="hero-title">AI-Powered Resume Evaluator</h1>
        <p class="hero-subtitle">Revolutionizing recruitment with intelligent matching technology</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### Choose Your Role")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        col_recruiter, col_student = st.columns(2)
        
        with col_recruiter:
            if st.button("", key="recruiter_card", help="Click to access recruiter portal"):
                st.session_state.selected_role = "Recruiter"
                st.session_state.page = "auth"
                st.rerun()
            
            st.markdown("""\
            <div class="role-card" onclick="document.querySelector('[data-testid=\'recruiter_card\']').click()">
                <div class="role-icon">👔</div>
                <h3 class="role-title">Recruiter</h3>
                <p class="role-description">Post jobs, review candidates, and find the perfect match for your team</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col_student:
            if st.button("", key="student_card", help="Click to access student portal"):
                st.session_state.selected_role = "Student"
                st.session_state.page = "auth"
                st.rerun()
            
            st.markdown("""\
            <div class="role-card" onclick="document.querySelector('[data-testid=\'student_card\']').click()">
                <div class="role-icon">🎓</div>
                <h3 class="role-title">Student</h3>
                <p class="role-description">Discover opportunities, get resume feedback, and land your dream job</p>
            </div>
            """, unsafe_allow_html=True)

# --- Session State Initialization ---
if 'page' not in st.session_state:
    st.session_state.page = 'home'
if 'selected_role' not in st.session_state:
    st.session_state.selected_role = None
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'login_state' not in st.session_state:
    st.session_state.login_state = 'login'
if 'user_role' not in st.session_state:
    st.session_state.user_role = None
if 'user_data' not in st.session_state:
    st.session_state.user_data = {}
if 'student_page' not in st.session_state:
    st.session_state.student_page = "job_listings"
if 'recruiter_page' not in st.session_state:
    st.session_state.recruiter_page = "explore_students"
if 'student_notifications' not in st.session_state:
    st.session_state.student_notifications = []
if 'enrolled_students' not in st.session_state:
    st.session_state.enrolled_students = []
if 'live_sessions' not in st.session_state:
    st.session_state.live_sessions = [{'id': 1, 'title': 'Q&A with TechCorp Hiring Team', 'recruiter': 'John Doe', 'date': '2025-09-25', 'time': '11:00 AM', 'status': 'Upcoming', 'messages': []}]
if 'live_chat' not in st.session_state:
    st.session_state.live_chat = []
if 'interview_schedule' not in st.session_state:
    st.session_state.interview_schedule = []

init_db()

# --- Main Navigation Logic ---
if st.session_state.page == 'home':
    home_page()
elif st.session_state.page == 'auth':
    # Show authentication pages based on selected role
    if not st.session_state.logged_in:
        st.markdown(f"""
        <div class="auth-container">
            <div class="auth-header">
                <h1 class="auth-title">{st.session_state.selected_role} Portal</h1>
                <p class="auth-subtitle">Welcome to the AI-Powered Resume Evaluator</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.session_state.login_state == 'login':
            show_login_page()
        elif st.session_state.login_state == 'forgot_password':
            show_forgot_password_page()
        elif st.session_state.login_state == 'verify_otp':
            show_verify_otp_page()
        elif st.session_state.login_state == 'reset_password':
            show_reset_password_page()
        else:
            show_signup_page()
    else:
        # Redirect to dashboard after login
        st.session_state.page = 'dashboard'
        st.rerun()

elif st.session_state.page == 'dashboard' and st.session_state.logged_in:
    # Sidebar for logged-in users
    st.sidebar.title("🤖 AI Recruitment Matcher")
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"**Welcome, {st.session_state.user_data['name']}**")
    st.sidebar.markdown(f"**Role:** {st.session_state.user_data['role']}")
    
    if st.sidebar.button("🏠 Home", use_container_width=True):
        st.session_state.page = 'home'
        st.session_state.logged_in = False
        st.rerun()
    
    if st.sidebar.button("🚪 Logout", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.login_state = 'login'
        st.session_state.page = 'home'
        st.rerun()
    
    st.sidebar.markdown("---")
    
    if st.session_state.user_role == "Recruiter":
        recruiter_nav = st.sidebar.radio("Navigation", ["Dashboard", "My Profile", "Explore Students"], key="recruiter_nav")
        
        # Check if we're viewing a student profile first
        if st.session_state.recruiter_page == "view_student_profile":
            view_student_profile_page()
        elif recruiter_nav == "Dashboard":
            recruiter_dashboard()
        elif recruiter_nav == "My Profile":
            recruiter_profile_page()
        elif recruiter_nav == "Explore Students":
            # Reset the recruiter_page when going back to explore students
            if st.session_state.recruiter_page != "explore_students":
                st.session_state.recruiter_page = "explore_students"
            explore_students_page()

    elif st.session_state.user_role == "Student":
        # Check if there are notifications for this student
        student_notification_count = 0
        if st.session_state.student_notifications:
            for notification in st.session_state.student_notifications:
                if (notification['status'] == 'Accepted' and 
                    notification.get('student_email') == st.session_state.user_data.get('email')):
                    student_notification_count += 1
        
        # Show notification badge in sidebar
        if student_notification_count > 0:
            st.sidebar.markdown(f"""
            <div style="background-color: #ff4444; color: white; padding: 10px; border-radius: 10px; text-align: center; margin-bottom: 10px;">
                🔔 <strong>{student_notification_count} New Notification{'s' if student_notification_count > 1 else ''}!</strong>
            </div>
            """, unsafe_allow_html=True)
        
        student_nav = st.sidebar.radio("Navigation", ["Job Opportunities", "My Profile"], key="student_nav")
        
        if st.session_state.student_notifications:
            st.subheader("Your Notifications 🔔")
            notifications_to_show = []
            remaining_notifications = []
            
            for notification in st.session_state.student_notifications:
                # Show notifications for the current logged-in student
                if (notification['status'] == 'Accepted' and 
                    notification.get('student_email') == st.session_state.user_data.get('email')):
                    notifications_to_show.append(notification)
                else:
                    remaining_notifications.append(notification)
            
            # Display notifications
            for notification in notifications_to_show:
                st.success(f"""
                **🎉 CONGRATULATIONS! 🎉**
                
                You have been **SELECTED** for the **{notification['job_title']}** role!
                
                **Company:** {notification['company']}  
                **Recruiter:** {notification['recruiter_name']}  
                **Time:** {notification.get('timestamp', 'Just now')}
                
                📧 Check your email for further instructions!
                """)
                
            # Keep other notifications that aren't for this student
            st.session_state.student_notifications = remaining_notifications
        
        if student_nav == "Job Opportunities":
            if st.session_state.student_page == "job_listings":
                student_job_listings_page()
            elif st.session_state.student_page == "job_info":
                get_job_info_page(st.session_state.selected_job_id)
        elif student_nav == "My Profile":
            student_profile_page()

else:
    # Redirect to home if not logged in and not on auth page
    if st.session_state.page != 'auth':
        st.session_state.page = 'home'
        st.rerun()
