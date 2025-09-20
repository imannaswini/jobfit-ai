import streamlit as st
import pandas as pd
import random
import os

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
        color: #2D3748;
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

# --- Sample Data (for demonstration) ---
job_listings = [
    {'id': 1, 'title': 'Senior Data Scientist', 'field': 'Data Science', 'company': 'TechCorp Inc', 'location': 'Hyderabad', 'job_type': 'Hybrid', 'eligibility': 'B.Tech/M.Tech in Computer Science, 3+ years experience.', 'criteria': ['Python', 'Machine Learning', 'Data Analysis', 'SQL', 'TensorFlow', 'AWS'], 'datePosted': '2024-09-15', 'applications': 245, 'shortlisted': 12, 'status': 'active'},
    {'id': 2, 'title': 'Full Stack Developer', 'field': 'Full Stack Development', 'company': 'StartupXYZ', 'location': 'Bangalore', 'job_type': 'Remote', 'eligibility': 'Any degree, 1+ years experience in a related field.', 'criteria': ['React', 'Node.js', 'MongoDB', 'JavaScript', 'CSS', 'Redis'], 'datePosted': '2024-09-18', 'applications': 189, 'shortlisted': 8, 'status': 'active'},
    {'id': 3, 'title': 'Cloud Engineer', 'field': 'Cloud Engineering', 'company': 'DataWave', 'location': 'Pune', 'job_type': 'On-site', 'eligibility': 'Any degree with a strong portfolio.', 'criteria': ['AWS', 'CI/CD', 'Python', 'Terraform', 'Kubernetes'], 'datePosted': '2024-09-20', 'applications': 152, 'shortlisted': 5, 'status': 'active'},
    {'id': 4, 'title': 'Product Manager Intern', 'field': 'Product Management', 'company': 'Innovate Solutions', 'location': 'Remote', 'job_type': 'Remote', 'eligibility': 'Currently pursuing any degree.', 'criteria': ['Product Management', 'Market Research', 'Agile Methodologies', 'Figma'], 'datePosted': '2024-09-22', 'applications': 98, 'shortlisted': 20, 'status': 'active'},
    {'id': 5, 'title': 'Digital Marketing Executive', 'field': 'Marketing', 'company': 'Growth Sparks', 'location': 'Mumbai', 'job_type': 'Hybrid', 'eligibility': 'Any degree, 2+ years of relevant experience.', 'criteria': ['SEO', 'SEM', 'Content Creation', 'Social Media Marketing'], 'datePosted': '2024-09-23', 'applications': 110, 'shortlisted': 15, 'status': 'active'}
]

# Simulated student profiles for recruiter view
simulated_students = [
    {'id': 1, 'name': 'Rahul Sharma', 'gender': 'Male', 'email': 'rahul@example.com', 'contact_number': '1234567890', 'bio': 'Aspiring Data Scientist with a strong foundation in Python and SQL.', 'job_title': 'Senior Data Scientist', 'job_id': 1, 'score': random.randint(75, 95), 'ats_friendly': True, 'matched_skills': ['Python', 'SQL', 'Machine Learning'], 'missing_skills': ['TensorFlow', 'AWS'], 'soft_skills': {'Communication': random.randint(70,95), 'Problem-Solving': random.randint(80,99), 'Teamwork': random.randint(65,90)}},
    {'id': 2, 'name': 'Priya Patel', 'gender': 'Female', 'email': 'priya@example.com', 'contact_number': '0987654321', 'bio': 'Full Stack Developer with expertise in React, Node.js, and MongoDB.', 'job_title': 'Full Stack Developer', 'job_id': 2, 'score': random.randint(70, 90), 'ats_friendly': True, 'matched_skills': ['React', 'Node.js', 'MongoDB'], 'missing_skills': ['Redis'], 'soft_skills': {'Communication': random.randint(75,99), 'Problem-Solving': random.randint(70,90), 'Teamwork': random.randint(80,95)}},
    {'id': 3, 'name': 'Amit Kumar', 'gender': 'Male', 'email': 'amit@example.com', 'contact_number': '1122334455', 'bio': 'Recent graduate passionate about cloud computing and DevOps.', 'job_title': 'Cloud Engineer', 'job_id': 3, 'score': random.randint(60, 85), 'ats_friendly': False, 'matched_skills': ['AWS', 'CI/CD'], 'missing_skills': ['Terraform', 'Kubernetes'], 'soft_skills': {'Communication': random.randint(60,85), 'Problem-Solving': random.randint(65,90), 'Teamwork': random.randint(70,95)}},
]

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
    job = next((item for item in job_listings if item['id'] == job_id), None)
    if not job:
        st.error("Job not found.")
        return
        
    st.title(job['title'])
    st.markdown(f"**Company:** {job['company']} | **Location:** {job['location']} | **Job Type:** {job['job_type']}")
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
        score = random.randint(50, 95)
        matched_skills = random.sample(job['criteria'], k=min(len(job['criteria']) - 2, 4))
        missing_skills = [skill for skill in job['criteria'] if skill not in matched_skills]
        
        st.markdown(f"#### Your Resume Match Score: **{score}%**")
        st.progress(score / 100)
        
        st.markdown("---")
        st.subheader("Personalized Feedback for this Role")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### ✅ Matched Skills")
            skills_html = "".join([f'<span class="skill-matched">{skill}</span>' for skill in matched_skills])
            st.markdown(f'<div style="display: flex; flex-wrap: wrap; gap: 0.5rem;">{skills_html}</div>', unsafe_allow_html=True)
            
        with col2:
            st.markdown("#### ❌ Missing Skills")
            skills_html = "".join([f'<span class="skill-missing">{skill}</span>' for skill in missing_skills])
            st.markdown(f'<div style="display: flex; flex-wrap: wrap; gap: 0.5rem;">{skills_html}</div>', unsafe_allow_html=True)
        
        st.subheader("Your Action Plan")
        st.info("Here are some steps to bridge your skill gaps and boost your score:")
        for skill in missing_skills:
            st.markdown(f"- **{skill}:** Consider completing an online certification or a personal project focused on this technology.")

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
    
    st.subheader("Key Metrics")
    st.markdown("Here's a quick overview of our current hiring pipeline and student performance.")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        with st.container(border=True):
            st.markdown("<p class='metric-card'>🏢 Active Jobs<br><h2 style='font-family: Roboto Mono;'>{}</h2></p>".format(len(job_listings)), unsafe_allow_html=True)
            st.caption("Total jobs currently posted.")
    with col2:
        total_apps = sum(job['applications'] for job in job_listings)
        with st.container(border=True):
            st.markdown("<p class='metric-card'>✉️ Total Applications<br><h2 style='font-family: Roboto Mono;'>{}</h2></p>".format(f"{total_apps:,}"), unsafe_allow_html=True)
            st.caption("Total resumes received across all jobs.")
    with col3:
        total_shortlisted = sum(job['shortlisted'] for job in job_listings)
        with st.container(border=True):
            st.markdown("<p class='metric-card'>🏅 Shortlisted<br><h2 style='font-family: Roboto Mono;'>{}</h2></p>".format(total_shortlisted), unsafe_allow_html=True)
            st.caption("Candidates forwarded for interviews.")
    with col4:
        avg_score = round(random.randint(70,90))
        with st.container(border=True):
            st.markdown("<p class='metric-card'>⭐ Avg. Score<br><h2 style='font-family: Roboto Mono;'>{}%</h2></p>".format(avg_score), unsafe_allow_html=True)
            st.caption("Average resume relevance score.")

    st.markdown("---")
    st.subheader("Manage Job Postings")
    with st.container(border=True):
        st.markdown("Upload a new Job Description to analyze student resumes and find the best fit.")
        uploaded_file = st.file_uploader("Upload JD (PDF, DOCX)", type=['pdf', 'docx'])
        st.button("Post Job", type="primary", use_container_width=True)
        
    st.markdown("---")
    st.subheader("Your Active Jobs")
    st.dataframe(pd.DataFrame(job_listings), use_container_width=True, hide_index=True)

def student_job_listings_page():
    st.title("Open Job Opportunities 🏢")
    st.markdown("### Find your next role, curated for you.")
    st.markdown("---")
    
    st.sidebar.markdown("### 🔎 Job Filters")
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

    with st.form("student_profile_form"):
        st.subheader("Personal Information")
        name = st.text_input("Full Name", value=st.session_state.user_data['name'])
        email = st.text_input("Email Address", value=st.session_state.user_data['email'])
        contact_number = st.text_input("Contact Number", value=st.session_state.user_data.get('contact_number', ''))
        linkedin = st.text_input("LinkedIn Profile URL", value=st.session_state.user_data.get('linkedin', ''))
        
        st.subheader("Professional Bio")
        bio = st.text_area("Write a short professional bio", value=st.session_state.user_data.get('bio', ''), height=150)
        
        save_button = st.form_submit_button("Save Changes", type="primary", use_container_width=True)

    if save_button:
        st.session_state.user_data.update({
            'name': name,
            'email': email,
            'contact_number': contact_number,
            'linkedin': linkedin,
            'bio': bio
        })
        st.success("Profile updated successfully! ✅")
    
    st.markdown("---")
    st.subheader("General Resume Checker")
    st.markdown("Upload your resume to check its overall score and ATS-friendliness.")
    uploaded_resume = st.file_uploader("Choose a PDF or DOCX file...", type=['pdf', 'docx'], key="general_resume_uploader")
    
    if uploaded_resume:
        st.success("Resume uploaded! Analyzing...")
        score = random.randint(70, 99)
        ats_friendly = random.choice([True, False, True])
        
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
    
    with st.form("recruiter_profile_form"):
        st.subheader("Personal & Company Information")
        name = st.text_input("Full Name", value=st.session_state.user_data['name'])
        email = st.text_input("Email Address", value=st.session_state.user_data['email'])
        company = st.text_input("Company Name", value=st.session_state.user_data.get('company', ''))
        designation = st.text_input("Designation", value=st.session_state.user_data.get('designation', ''))
        linkedin = st.text_input("LinkedIn Profile URL", value=st.session_state.user_data.get('linkedin', ''))
        
        save_button = st.form_submit_button("Save Changes", type="primary", use_container_width=True)

    if save_button:
        st.session_state.user_data.update({
            'name': name,
            'email': email,
            'company': company,
            'designation': designation,
            'linkedin': linkedin
        })
        st.success("Profile updated successfully! ✅")

# --- Recruiter "Explore" Page ---
def explore_students_page():
    st.title("Explore Students 🚀")
    st.markdown("### Discover and filter potential candidates.")
    st.markdown("---")

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

# --- Recruiter "View Student Profile" Page ---
def view_student_profile_page():
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

def show_login_page():
    st.title("Login to AI Recruitment Matcher 🤖")
    st.markdown("---")
    st.subheader("Welcome back!")

    with st.form("login_form"):
        email = st.text_input("Email ID", placeholder="Enter your email")
        password = st.text_input("Password", type="password", placeholder="Enter your password")
        login_button = st.form_submit_button("Log In", type="primary", use_container_width=True)
    
    if login_button:
        if email == st.session_state.user_data['email'] and password == st.session_state.user_data['password']:
            st.session_state.logged_in = True
            st.session_state.user_role = st.session_state.user_data['role']
            st.success("Login successful! Redirecting to your dashboard...")
            st.rerun()
        else:
            st.error("Invalid email or password.")
    
    st.markdown("---")
    st.markdown("Don't have an account? [Sign Up](#sign-up-page)")

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
            st.session_state.user_data = {
                'name': name,
                'email': email,
                'password': password,
                'role': role,
                'gender': gender
            }
            if role == "Recruiter":
                st.session_state.user_data.update({'company': company, 'designation': designation, 'linkedin': linkedin})
            else:
                st.session_state.user_data.update({'bio': bio, 'linkedin': linkedin, 'contact_number': contact_number})
            
            st.success(f"Account for {role} created successfully! Redirecting to your dashboard...")
            st.session_state.logged_in = True
            st.session_state.user_role = role
            st.rerun()
        else:
            st.error("Please fill in all required fields.")
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("Already have an account? [Log In](#log-in-page)")

# --- Main App Logic ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'show_login' not in st.session_state:
    st.session_state.show_login = False
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
    st.session_state.live_sessions = [{'id': 1, 'title': 'Q&A with TechCorp Hiring Team', 'date': 'Sep 25', 'time': '11:00 AM', 'status': 'Upcoming', 'messages': []}]
if 'live_chat' not in st.session_state:
    st.session_state.live_chat = []
if 'interview_schedule' not in st.session_state:
    st.session_state.interview_schedule = []

# --- Live Chat Functions ---
def live_chat_page(session_id):
    session = next((s for s in st.session_state.live_sessions if s['id'] == session_id), None)
    if not session:
        st.error("Live session not found.")
        return
        
    st.title(f"Live Session: {session['title']}")
    st.markdown("---")

    # Chat display area
    chat_container = st.container(height=300, border=True)
    for message in st.session_state.live_chat:
        if message['role'] == 'recruiter':
            chat_container.info(f"**{session['recruiter']}:** {message['text']}")
        else:
            chat_container.markdown(f"**You:** {message['text']}")
    
    st.markdown("---")
    
    # Message input area
    with st.form("chat_form", clear_on_submit=True):
        new_message = st.text_input("Type your message...", key="message_input")
        send_button = st.form_submit_button("Send")
        if send_button and new_message:
            st.session_state.live_chat.append({'role': 'student', 'text': new_message})
            st.rerun()

# --- Recruiter Communication Pages ---
def manage_qa_page():
    st.title("Manage Q&A Sessions 💬")
    st.markdown("### Answer student questions about your job postings.")
    st.markdown("---")
    
    for job in job_listings:
        if st.session_state.get('job_questions') and job['id'] in st.session_state.job_questions:
            questions = st.session_state.job_questions[job['id']]
            unanswered_count = sum(1 for q in questions if not q['answer'])
            
            if unanswered_count > 0:
                with st.expander(f"**{job['title']}** ({unanswered_count} new questions)", expanded=True):
                    for qa in questions:
                        st.markdown(f"**Q:** {qa['question']}")
                        if qa['answer']:
                            st.info(f"**A:** {qa['answer']}")
                        else:
                            with st.form(f"answer_form_{qa['question']}"):
                                answer = st.text_area("Your answer:", key=f"answer_box_{qa['question']}")
                                submit_answer = st.form_submit_button("Post Answer")
                                if submit_answer and answer:
                                    qa['answer'] = answer
                                    st.success("Answer posted!")
                                    st.rerun()
                                st.warning("Awaiting your answer...")

def recruiter_live_sessions():
    st.title("Manage Live Sessions 🗣️")
    st.markdown("### Schedule and host live Q&A sessions for students.")
    st.markdown("---")
    
    st.subheader("Schedule a New Session")
    with st.form("new_session_form"):
        title = st.text_input("Session Title")
        date = st.date_input("Date")
        time = st.time_input("Time")
        schedule_button = st.form_submit_button("Schedule Session", type="primary")
        if schedule_button:
            new_id = len(st.session_state.live_sessions) + 1
            st.session_state.live_sessions.append({'id': new_id, 'title': title, 'date': date, 'time': time, 'status': 'Upcoming', 'recruiter': st.session_state.user_data['name'], 'messages': []})
            st.success("Session scheduled!")
    
    st.subheader("Your Upcoming Sessions")
    for session in st.session_state.live_sessions:
        with st.container(border=True):
            st.markdown(f"**{session['title']}**")
            st.caption(f"🗓️ {session['date']} at {session['time']}")
            st.button(f"Start Session", key=f"start_{session['id']}")

def student_live_sessions():
    st.title("Upcoming Live Sessions 🗣️")
    st.markdown("### Join live Q&A sessions with recruiters.")
    st.markdown("---")
    
    for session in st.session_state.live_sessions:
        with st.container(border=True):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.subheader(session['title'])
                st.caption(f"Host: {session.get('recruiter', 'Recruiter')} | 🗓️ {session['date']} at {session['time']}")
            with col2:
                if st.button("Join Now", key=f"join_{session['id']}", use_container_width=True):
                    st.session_state.student_page = "live_chat"
                    st.session_state.current_session_id = session['id']
                    st.rerun()

# --- Student Interview Scheduling ---
def student_interviews_page():
    st.title("My Interviews 🗓️")
    st.markdown("### Congratulations! Here are your scheduled and pending interviews.")
    st.markdown("---")

    if not st.session_state.interview_schedule:
        st.info("You don't have any pending interviews at the moment.")
    else:
        for interview in st.session_state.interview_schedule:
            with st.container(border=True):
                st.success(f"**{interview['job_title']}** at **{interview['company']}**")
                st.markdown(f"**Status:** Accepted 🎉")
                st.markdown("Please choose an interview slot below.")
                
                selected_slot = st.selectbox("Select a slot:", ["Select...", "Oct 1, 10:00 AM", "Oct 2, 02:00 PM", "Oct 3, 09:30 AM"])
                if st.button("Confirm Slot", key=f"confirm_{interview['job_title']}", type="primary"):
                    if selected_slot != "Select...":
                        st.success(f"You have confirmed your interview for **{selected_slot}** with **{interview['company']}**.")
                        st.session_state.interview_schedule.remove(interview) # Remove from pending list
                        st.balloons()
                    else:
                        st.error("Please select a valid slot.")

# --- Authentication Logic (Simulated) ---

def show_login_page():
    st.title("Login to AI Recruitment Matcher 🤖")
    st.markdown("---")
    st.subheader("Welcome back!")

    with st.form("login_form"):
        email = st.text_input("Email ID", placeholder="Enter your email")
        password = st.text_input("Password", type="password", placeholder="Enter your password")
        login_button = st.form_submit_button("Log In", type="primary", use_container_width=True)
    
    if login_button:
        if email == st.session_state.user_data['email'] and password == st.session_state.user_data['password']:
            st.session_state.logged_in = True
            st.session_state.user_role = st.session_state.user_data['role']
            st.success("Login successful! Redirecting to your dashboard...")
            st.rerun()
        else:
            st.error("Invalid email or password.")
    
    st.markdown("---")
    st.markdown("Don't have an account? [Sign Up](#sign-up-page)")

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
            st.session_state.user_data = {
                'name': name,
                'email': email,
                'password': password,
                'role': role,
                'gender': gender
            }
            if role == "Recruiter":
                st.session_state.user_data.update({'company': company, 'designation': designation, 'linkedin': linkedin})
            else:
                st.session_state.user_data.update({'bio': bio, 'linkedin': linkedin, 'contact_number': contact_number})
            
            st.success(f"Account for {role} created successfully! Redirecting to your dashboard...")
            st.session_state.logged_in = True
            st.session_state.user_role = role
            st.rerun()
        else:
            st.error("Please fill in all required fields.")
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("Already have an account? [Log In](#log-in-page)")

# --- Main App Logic ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'show_login' not in st.session_state:
    st.session_state.show_login = False
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

# Sidebar for navigation
st.sidebar.title("AI Recruitment Matcher")
st.sidebar.markdown("---")

if st.session_state.logged_in:
    st.sidebar.markdown(f"**Logged in as:** {st.session_state.user_data['name']}")
    st.sidebar.markdown(f"**Role:** {st.session_state.user_data['role']}")
    if st.sidebar.button("Logout", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.show_login = False
        st.rerun()
    
    if st.session_state.user_role == "Recruiter":
        st.sidebar.markdown("---")
        recruiter_nav = st.sidebar.radio("Navigation", ["Dashboard", "My Profile", "Explore Students", "Live Sessions", "Manage Q&A"], key="recruiter_nav")
        
        if recruiter_nav == "Dashboard":
            recruiter_dashboard()
        elif recruiter_nav == "My Profile":
            recruiter_profile_page()
        elif recruiter_nav == "Explore Students":
            explore_students_page()
        elif recruiter_nav == "Live Sessions":
            recruiter_live_sessions()
        elif recruiter_nav == "Manage Q&A":
            manage_qa_page()
        
        if st.session_state.recruiter_page == "view_student_profile":
            view_student_profile_page()

    elif st.session_state.user_role == "Student":
        st.sidebar.markdown("---")
        student_nav = st.sidebar.radio("Navigation", ["Job Opportunities", "My Profile", "Live Sessions", "My Interviews"], key="student_nav")
        
        # Display notifications to the student
        if st.session_state.student_notifications:
            st.subheader("Your Notifications 🔔")
            for notification in st.session_state.student_notifications:
                # Assuming 'Rahul Sharma' (id 1) is the logged-in student for this example
                if notification['status'] == 'Accepted' and notification['student_id'] == 1:
                    st.success(f"**Congratulations! 🎉** You have been selected for the **{notification['job_title']}** role by **{notification['company']}**! Please check your **My Interviews** tab to schedule your interview.")
            st.session_state.student_notifications = [] # Clear after showing
        
        if student_nav == "Job Opportunities":
            if st.session_state.student_page == "job_listings":
                student_job_listings_page()
            elif st.session_state.student_page == "job_info":
                get_job_info_page(st.session_state.selected_job_id)
        elif student_nav == "My Profile":
            student_profile_page()
        elif student_nav == "Live Sessions":
            if st.session_state.student_page == "live_sessions":
                student_live_sessions()
            elif st.session_state.student_page == "live_chat":
                live_chat_page(st.session_state.current_session_id)
        elif student_nav == "My Interviews":
            student_interviews_page()
            
else:
    if st.session_state.show_login:
        show_login_page()
    else:
        show_signup_page()