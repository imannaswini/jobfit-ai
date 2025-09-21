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

# --- Page Configuration ---
st.set_page_config(
    page_title="AI Recruitment Matcher",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom CSS for Styling ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700&family=Roboto+Mono:wght@400;700&display=swap');

    .st-emotion-cache-18ni7ap.e8zbici2 {
        background: linear-gradient(to right, #00C6FF, #0072FF);
        color: white;
    }
    .main-header {
        font-family: 'Poppins', sans-serif;
        font-weight: 700;
         
        font-size: 2.5rem;
        margin-bottom: 0.5rem;
    }
    h1, h2, h3, h4, h5, h6, .st-emotion-cache-1j02r3h.e16109c0 {
        font-family: 'Poppins', sans-serif;
        font-weight: 600;
        color: #2D3748;
    }
    .st-emotion-cache-13ln4j9.e1629p8r2 {
        font-family: 'Roboto Mono', monospace;
        font-size: 1.5rem;
        font-weight: 700;
        color: #000000;
    }
    .st-emotion-cache-1aw8v5k.e1f1d6gn4 {
        border-color: #0072FF;
    }
    .st-emotion-cache-1v04719.e1f1d6gn0 {
        border-radius: 10px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.1);
    }
    .st-emotion-cache-v0g6wz.e1f1d6gn0 {
        border-radius: 10px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.1);
    }
    .st-emotion-cache-5rimss.e1nzilvr4 {
        border-radius: 10px;
    }
    .metric-card {
        background-color: #F8F9FA;
        border: 1px solid #E2E8F0;
        border-radius: 0.75rem;
        padding: 1rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        text-align: center;
        transition: transform 0.2s;
        font-family: 'Poppins', sans-serif;
    }
    .metric-card:hover {
        transform: translateY(-5px);
    }
    .verdict-high { background-color: #D4EDDA; color: #155724; padding: 0.35rem 1rem; border-radius: 9999px; font-weight: 600; font-size: 0.95rem; display: inline-flex; align-items: center; gap: 0.5rem; }
    .verdict-medium { background-color: #FFF3CD; color: #856404; padding: 0.35rem 1rem; border-radius: 9999px; font-weight: 600; font-size: 0.95rem; display: inline-flex; align-items: center; gap: 0.5rem; }
    .verdict-low { background-color: #F8D7DA; color: #721C24; padding: 0.35rem 1rem; border-radius: 9999px; font-weight: 600; font-size: 0.95rem; display: inline-flex; align-items: center; gap: 0.5rem; }
    .ats-friendly { background-color: #D1FAE5; color: #065F46; padding: 0.25rem 0.75rem; border-radius: 9999px; font-weight: 500; font-size: 0.875rem; display: inline-flex; align-items: center; gap: 0.25rem; }
    .ats-unfriendly { background-color: #FEE2E2; color: #991B1B; padding: 0.25rem 0.75rem; border-radius: 9999px; font-weight: 500; font-size: 0.875rem; display: inline-flex; align-items: center; gap: 0.25rem; }
    .skill-matched { background-color: #E0F2FE; color: #0C4A6E; padding: 0.25rem 0.75rem; border-radius: 0.5rem; font-size: 0.8rem; font-weight: 500; }
    .skill-missing { background-color: #FFE4E6; color: #9F1239; padding: 0.25rem 0.75rem; border-radius: 0.5rem; font-size: 0.8rem; font-weight: 500; }
    .st-emotion-cache-1wv43z8.e1f1d6gn2 {
        font-family: 'Poppins', sans-serif;
    }
    .signup-form {
        background-color: #ffffff;
        padding: 30px;
        border-radius: 15px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        max-width: 600px;
        margin: auto;
    }
    .signup-header {
        text-align: center;
        margin-bottom: 20px;
        color: #0072FF;
    }
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
        str(job_data.get('criteria', [])), # Store list as a string
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
        jobs.append({
            'id': job[0],
            'title': job[1],
            'company': job[2],
            'location': job[3],
            'job_type': job[4],
            'eligibility': job[5],
            'criteria': eval(job[6]), # Convert criteria string back to list
            'datePosted': job[7],
            'applications': job[8],
            'shortlisted': random.randint(0, job[8]) # Simulated value
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
            st.success("You have successfully enrolled for this job!")
        
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
    st.title("Recruiter Dashboard 📈")
    st.markdown("### Welcome, Recruiter!")
    st.markdown("---")
    
    job_listings = get_job_listings()
    total_apps = sum(job['applications'] for job in job_listings) if job_listings else 0
    total_shortlisted = sum(job['shortlisted'] for job in job_listings) if job_listings else 0
    avg_score = round(random.randint(70,90))

    st.subheader("Key Metrics")
    st.markdown("Here's a quick overview of our current hiring pipeline and student performance.")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        with st.container(border=True):
            st.markdown("<p class='metric-card'>🏢 Active Jobs<br><h2 style='font-family: Roboto Mono;'>{}</h2></p>".format(len(job_listings)), unsafe_allow_html=True)
            st.caption("Total jobs currently posted.")
    with col2:
        with st.container(border=True):
            st.markdown("<p class='metric-card'>✉️ Total Applications<br><h2 style='font-family: Roboto Mono;'>{}</h2></p>".format(f"{total_apps:,}"), unsafe_allow_html=True)
            st.caption("Total resumes received across all jobs.")
    with col3:
        with st.container(border=True):
            st.markdown("<p class='metric-card'>🏅 Shortlisted<br><h2 style='font-family: Roboto Mono;'>{}</h2></p>".format(total_shortlisted), unsafe_allow_html=True)
            st.caption("Candidates forwarded for interviews.")
    with col4:
        with st.container(border=True):
            st.markdown("<p class='metric-card'>⭐ Avg. Score<br><h2 style='font-family: Roboto Mono;'>{}%</h2></p>".format(avg_score), unsafe_allow_html=True)
            st.caption("Average resume relevance score.")

    st.markdown("---")
    st.subheader("Manage Job Postings")
    with st.container(border=True):
        st.markdown("Upload a new Job Description to analyze student resumes and find the best fit.")
        uploaded_file = st.file_uploader("Upload JD (PDF, DOCX)", type=['pdf', 'docx'])
        
        if st.button("Post Job", type="primary", use_container_width=True):
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
                        'applications': random.randint(10, 50)
                    }
                    
                    add_job(job_data)
                    st.success(f"Job '{title}' posted successfully!")
                    st.rerun()

                except UnicodeDecodeError:
                    st.error("There was a character encoding error. Please try a different file.")
                except Exception as e:
                    st.error(f"An unexpected error occurred during file processing: {e}")
            else:
                st.warning("Please upload a job description file first.")
        
    st.markdown("---")
    st.subheader("Your Active Jobs")
    job_listings_df = pd.DataFrame(job_listings)
    if not job_listings_df.empty:
        st.dataframe(job_listings_df[['title', 'company', 'location', 'datePosted', 'applications', 'shortlisted']], use_container_width=True, hide_index=True)
    else:
        st.info("No jobs posted yet.")

def student_job_listings_page():
    st.title("Open Job Opportunities 🏢")
    st.markdown("### Find your next role, curated for you.")
    st.markdown("---")
    
    st.sidebar.markdown("### 🔎 Job Filters")
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
            with st.container(border=True):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.subheader(job['title'])
                    st.caption(f"{job['company']} | 📍 {job['location']} | **{job['job_type']}**")
                    st.markdown(f"**Eligibility:** {job['eligibility']}")
                with col2:
                    if st.button("Apply Now", key=f"apply_{job['id']}", use_container_width=True):
                        st.session_state.student_page = "job_info"
                        st.session_state.selected_job_id = job['id']
                        st.rerun()

# --- Profile Management Pages ---
def student_profile_page():
    st.title("My Profile 👤")
    st.markdown("### Edit and manage your personal details.")
    st.markdown("---")
    
    user_data = authenticate_user(st.session_state.user_data['email'], st.session_state.user_data['password'])

    with st.form("student_profile_form"):
        st.subheader("Personal Information")
        name = st.text_input("Full Name", value=user_data['name'])
        email = st.text_input("Email Address", value=user_data['email'])
        contact_number = st.text_input("Contact Number", value=user_data.get('contact_number', ''))
        linkedin = st.text_input("LinkedIn Profile URL", value=user_data.get('linkedin', ''))
        
        st.subheader("Professional Bio")
        bio = st.text_area("Write a short professional bio", value=user_data.get('bio', ''), height=150)
        
        save_button = st.form_submit_button("Save Changes", type="primary", use_container_width=True)

    if save_button:
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE users SET name=?, email=?, contact_number=?, linkedin=?, bio=? WHERE id=?
        """, (name, email, contact_number, linkedin, bio, user_data['id']))
        conn.commit()
        conn.close()
        st.success("Profile updated successfully! ✅")
    
    st.markdown("---")
    st.subheader("General Resume Checker")
    st.markdown("Upload your resume to check its overall score and ATS-friendliness.")
    uploaded_resume = st.file_uploader("Choose a PDF or DOCX file...", type=['pdf', 'docx'], key="general_resume_uploader")
    
    if uploaded_resume:
        st.success("Resume uploaded! Analyzing...")
        
        generic_skills = ["Python", "JavaScript", "SQL", "Machine Learning", "Data Analysis", "Cloud Computing", "Project Management", "Agile", "API", "Web Development", "UI/UX"]
        
        with st.spinner("Analyzing your resume with the AI engine..."):
            analysis_result = analyze_uploaded_files(uploaded_resume, generic_skills)
        
        score = analysis_result['score']
        ats_friendly = score > 60
        
        st.markdown(f"#### Your Overall Resume Score: **{score}%**")
        st.progress(score / 100)
        st.markdown(get_ats_html(ats_friendly), unsafe_allow_html=True)
        st.info("This is a general score. For a job-specific score, check the job listings.")
        
        st.subheader("AI-Powered Soft Skills Assessment")
        st.markdown("Based on your profile and resume, here is a general assessment of your soft skills:")
        
        soft_skills_scores = {
            'Communication': random.randint(60, 95),
            'Problem-Solving': random.randint(70, 99),
            'Teamwork': random.randint(65, 90),
            'Leadership': random.randint(60, 90)
        }
        
        for skill, score in soft_skills_scores.items():
            st.markdown(f"**{skill}**")
            st.progress(score / 100)
            
        st.info("These scores are a general assessment and may vary depending on the specific job role.")

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

def explore_students_page():
    st.title("Explore Students 🚀")
    st.markdown("### Discover and filter potential candidates.")
    st.markdown("---")

    simulated_students = [
        {'id': 1, 'name': 'Rahul Sharma', 'gender': 'Male', 'email': 'rahul@example.com', 'contact_number': '1234567890', 'bio': 'Aspiring Data Scientist with a strong foundation in Python and SQL.', 'job_title': 'Senior Data Scientist', 'job_id': 1, 'score': random.randint(75, 95), 'ats_friendly': True, 'matched_skills': ['Python', 'SQL', 'Machine Learning'], 'missing_skills': ['TensorFlow', 'AWS'], 'soft_skills': {'Communication': random.randint(70,95), 'Problem-Solving': random.randint(80,99), 'Teamwork': random.randint(65,90)}},
        {'id': 2, 'name': 'Priya Patel', 'gender': 'Female', 'email': 'priya@example.com', 'contact_number': '0987654321', 'bio': 'Full Stack Developer with expertise in React, Node.js, and MongoDB.', 'job_title': 'Full Stack Developer', 'job_id': 2, 'score': random.randint(70, 90), 'ats_friendly': True, 'matched_skills': ['React', 'Node.js', 'MongoDB'], 'missing_skills': ['Redis'], 'soft_skills': {'Communication': random.randint(75,99), 'Problem-Solving': random.randint(70,90), 'Teamwork': random.randint(80,95)}},
        {'id': 3, 'name': 'Amit Kumar', 'gender': 'Male', 'email': 'amit@example.com', 'contact_number': '1122334455', 'bio': 'Recent graduate passionate about cloud computing and DevOps.', 'job_title': 'Cloud Engineer', 'job_id': 3, 'score': random.randint(60, 85), 'ats_friendly': False, 'matched_skills': ['AWS', 'CI/CD'], 'missing_skills': ['Terraform', 'Kubernetes'], 'soft_skills': {'Communication': random.randint(60,85), 'Problem-Solving': random.randint(65,90), 'Teamwork': random.randint(70,95)}},
    ]

    for student in simulated_students:
        with st.container(border=True):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.subheader(f"{student['name']}")
                st.caption(f"**Bio:** {student['bio']}")
                st.markdown(get_ats_html(student['ats_friendly']), unsafe_allow_html=True)
            with col2:
                st.metric(label="Resume Score", value=f"{student['score']}%")
                st.markdown(get_verdict_html('High' if student['score'] > 80 else 'Medium'), unsafe_allow_html=True)
            
            if st.button(f"View Full Profile", key=f"view_{student['id']}", use_container_width=True):
                st.session_state.recruiter_page = "view_student_profile"
                st.session_state.selected_student_id = student['id']
                st.rerun()

def view_student_profile_page():
    job_listings = get_job_listings()
    simulated_students = [
        {'id': 1, 'name': 'Rahul Sharma', 'gender': 'Male', 'email': 'rahul@example.com', 'contact_number': '1234567890', 'bio': 'Aspiring Data Scientist with a strong foundation in Python and SQL.', 'job_title': 'Senior Data Scientist', 'job_id': 1, 'score': random.randint(75, 95), 'ats_friendly': True, 'matched_skills': ['Python', 'SQL', 'Machine Learning'], 'missing_skills': ['TensorFlow', 'AWS'], 'soft_skills': {'Communication': random.randint(70,95), 'Problem-Solving': random.randint(80,99), 'Teamwork': random.randint(65,90)}},
        {'id': 2, 'name': 'Priya Patel', 'gender': 'Female', 'email': 'priya@example.com', 'contact_number': '0987654321', 'bio': 'Full Stack Developer with expertise in React, Node.js, and MongoDB.', 'job_title': 'Full Stack Developer', 'job_id': 2, 'score': random.randint(70, 90), 'ats_friendly': True, 'matched_skills': ['React', 'Node.js', 'MongoDB'], 'missing_skills': ['Redis'], 'soft_skills': {'Communication': random.randint(75,99), 'Problem-Solving': random.randint(70,90), 'Teamwork': random.randint(80,95)}},
        {'id': 3, 'name': 'Amit Kumar', 'gender': 'Male', 'email': 'amit@example.com', 'contact_number': '1122334455', 'bio': 'Recent graduate passionate about cloud computing and DevOps.', 'job_title': 'Cloud Engineer', 'job_id': 3, 'score': random.randint(60, 85), 'ats_friendly': False, 'matched_skills': ['AWS', 'CI/CD'], 'missing_skills': ['Terraform', 'Kubernetes'], 'soft_skills': {'Communication': random.randint(60,85), 'Problem-Solving': random.randint(65,90), 'Teamwork': random.randint(70,95)}},
    ]

    student = next((s for s in simulated_students if s['id'] == st.session_state.selected_student_id), None)
    job = next((j for j in job_listings if j['id'] == student['job_id']), None)

    if not student or not job:
        st.error("Student or job data not found.")
        if st.button("⬅️ Back to Students", use_container_width=True):
            st.session_state.recruiter_page = "explore_students"
            st.rerun()
        return

    st.title(f"Profile: {student['name']}")
    st.markdown("---")
    
    col_info, col_score = st.columns([3, 1])
    with col_info:
        st.subheader("Candidate Information")
        st.markdown(f"**Bio:** {student['bio']}")
        st.markdown(f"**Email:** {student['email']}")
        st.markdown(f"**Contact:** {student['contact_number']}")
        st.markdown(f"**Applied For:** {job['title']} at {job['company']}")
        
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

    st.subheader("AI-Powered Soft Skills Assessment")
    st.markdown("A general assessment of the candidate's soft skills based on their profile and resume content.")
    for skill, score in student['soft_skills'].items():
        st.markdown(f"**{skill}**")
        st.progress(score / 100)
    
    st.markdown("---")
    
    col_accept, col_dismiss, col_back = st.columns([1, 1, 2])
    
    if col_accept.button("✅ Accept Student", type="primary", use_container_width=True):
        if 'student_notifications' not in st.session_state:
            st.session_state.student_notifications = []
        st.session_state.student_notifications.append({
            'student_id': student['id'],
            'job_title': job['title'],
            'status': 'Accepted',
            'recruiter_name': st.session_state.user_data['name'],
            'company': st.session_state.user_data.get('company', 'Recruiter')
        })
        st.success(f"Notification sent to {student['name']}! The student has been accepted for the role.")
        st.session_state.recruiter_page = "explore_students" # Navigate back to prevent multiple sends
        st.rerun()
    
    if col_dismiss.button("❌ Dismiss Student", use_container_width=True):
        st.warning(f"You have dismissed {student['name']} for this role.")
    
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


# --- Main App Logic ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'login_state' not in st.session_state:
    st.session_state.login_state = 'signup'
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
if 'live_sessions' not in st.session_state:
    st.session_state.live_sessions = [{'id': 1, 'title': 'Q&A with TechCorp Hiring Team', 'recruiter': 'John Doe', 'date': '2025-09-25', 'time': '11:00 AM', 'status': 'Upcoming', 'messages': []}]
if 'live_chat' not in st.session_state:
    st.session_state.live_chat = []
if 'interview_schedule' not in st.session_state:
    st.session_state.interview_schedule = []

init_db()

st.sidebar.title("AI Recruitment Matcher")
st.sidebar.markdown("---")

if st.session_state.logged_in:
    st.sidebar.markdown(f"**Logged in as:** {st.session_state.user_data['name']}")
    st.sidebar.markdown(f"**Role:** {st.session_state.user_data['role']}")
    if st.sidebar.button("Logout", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.login_state = 'login'
        st.rerun()
    
    if st.session_state.user_role == "Recruiter":
        st.sidebar.markdown("---")
        recruiter_nav = st.sidebar.radio("Navigation", ["Dashboard", "My Profile", "Explore Students"], key="recruiter_nav")
        
        if recruiter_nav == "Dashboard":
            recruiter_dashboard()
        elif recruiter_nav == "My Profile":
            recruiter_profile_page()
        elif recruiter_nav == "Explore Students":
            explore_students_page()
        
        if st.session_state.recruiter_page == "view_student_profile":
            view_student_profile_page()

    elif st.session_state.user_role == "Student":
        st.sidebar.markdown("---")
        student_nav = st.sidebar.radio("Navigation", ["Job Opportunities", "My Profile"], key="student_nav")
        
        if st.session_state.student_notifications:
            st.subheader("Your Notifications 🔔")
            for notification in st.session_state.student_notifications:
                if notification['status'] == 'Accepted' and notification['student_id'] == 1:
                    st.success(f"**Congratulations! 🎉** You have been selected for the **{notification['job_title']}** role by **{notification['company']}**! Please check your **My Interviews** tab to schedule your interview.")
            st.session_state.student_notifications = []
        
        if student_nav == "Job Opportunities":
            if st.session_state.student_page == "job_listings":
                student_job_listings_page()
            elif st.session_state.student_page == "job_info":
                get_job_info_page(st.session_state.selected_job_id)
        elif student_nav == "My Profile":
            student_profile_page()
            
else:
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
