import os
import io
import pdfplumber
from docx import Document
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

# --- LLM and Embedding Model Initialization ---

# This assumes you have your Google API key set up as an environment variable.
# For local development, you can set it like this in your terminal:
# export GOOGLE_API_KEY="YOUR_API_KEY"
# Alternatively, you can uncomment the line below and paste your key directly (not recommended for public repos)
# os.environ["GOOGLE_API_KEY"] = "YOUR_API_KEY"

# Please replace "YOUR_API_KEY" with your actual key
os.environ["GOOGLE_API_KEY"] = "AIzaSyBDES5pnvYN8mtTF-baArohmjE5fW7y8YA"

# Initialize the LLM for text generation (feedback)
llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",
    temperature=0.7,
    convert_system_message_to_human=True
)

# Initialize the embedding model for semantic search
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

# --- Document Parsing Functions ---

def extract_text_from_pdf(file_bytes):
    """Extracts text from a PDF file provided as bytes using pdfplumber."""
    text = ""
    try:
        # Use an in-memory stream with pdfplumber
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for page in pdf.pages:
                text += page.extract_text()
    except Exception as e:
        print(f"Error extracting PDF text: {e}")
    return text

def extract_text_from_docx(file_bytes):
    """Extracts text from a DOCX file provided as bytes."""
    text = ""
    try:
        # Use an in-memory stream
        doc = Document(io.BytesIO(file_bytes))
        for para in doc.paragraphs:
            text += para.text + "\n"
    except Exception as e:
        print(f"Error extracting DOCX text: {e}")
    return text

# --- Core AI Analysis Logic ---

def get_relevance_score(resume_text, job_criteria):
    """
    Calculates a hybrid relevance score (0-100) and provides feedback.
    
    Args:
        resume_text (str): The full text of the resume.
        job_criteria (list): A list of required skills/keywords from the job description.
        
    Returns:
        dict: A dictionary containing the score, verdict, matched skills, missing skills, and feedback.
    """
    if not resume_text:
        return {
            "score": 0,
            "verdict": "Low",
            "matched_skills": [],
            "missing_skills": job_criteria,
            "feedback": "No text could be extracted from your resume. Please try a different file."
        }

    # 1. Hard Match (Keyword-based)
    found_skills = [skill for skill in job_criteria if skill.lower() in resume_text.lower()]
    missing_skills = [skill for skill in job_criteria if skill.lower() not in resume_text.lower()]
    hard_score = (len(found_skills) / len(job_criteria)) * 100 if len(job_criteria) > 0 else 0

    # 2. Soft Match (Semantic)
    # Generate embeddings for both the resume and the job description criteria
    jd_embedding = embedding_model.encode(" ".join(job_criteria), convert_to_tensor=True)
    resume_embedding = embedding_model.encode(resume_text, convert_to_tensor=True)
    
    # Calculate cosine similarity
    soft_score = cosine_similarity(resume_embedding.reshape(1, -1), jd_embedding.reshape(1, -1))[0][0] * 100
    
    # 3. Hybrid Scoring & Verdict
    final_score = int((0.6 * hard_score) + (0.4 * soft_score))
    
    if final_score >= 80:
        verdict = "High"
    elif final_score >= 50:
        verdict = "Medium"
    else:
        verdict = "Low"

    # 4. LLM-Powered Feedback
    prompt_template = PromptTemplate(
        input_variables=["missing_skills", "matched_skills"],
        template="""
        As a helpful career coach, provide personalized, actionable feedback for a student's resume.
        The student is applying for a job that requires the following skills:
        Matched Skills: {matched_skills}
        Missing Skills: {missing_skills}

        Based on this, offer a concise paragraph of advice. Focus on how to acquire or demonstrate the missing skills to improve their resume and job prospects.
        """
    )
    
    # Create a LangChain pipeline
    chain = prompt_template | llm | StrOutputParser()
    
    # Invoke the chain to get the feedback
    feedback = chain.invoke({
        "missing_skills": ", ".join(missing_skills) if missing_skills else "None",
        "matched_skills": ", ".join(found_skills) if found_skills else "None"
    })
    
    return {
        "score": final_score,
        "verdict": verdict,
        "matched_skills": found_skills,
        "missing_skills": missing_skills,
        "feedback": feedback
    }

# --- Main Analysis Function to be called from index.py ---

def analyze_uploaded_files(uploaded_file, job_criteria):
    """
    Main function to handle file processing and analysis.
    
    Args:
        uploaded_file (streamlit.runtime.uploaded_file_manager.UploadedFile): The file object.
        job_criteria (list): A list of required skills.
        
    Returns:
        dict: The analysis results.
    """
    # Get file bytes
    file_bytes = uploaded_file.getvalue()

    # Extract text based on file type
    if uploaded_file.type == "application/pdf":
        resume_text = extract_text_from_pdf(file_bytes)
    elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        resume_text = extract_text_from_docx(file_bytes)
    else:
        return {
            "score": 0,
            "verdict": "Low",
            "matched_skills": [],
            "missing_skills": job_criteria,
            "feedback": "Unsupported file format. Please upload a PDF or DOCX file."
        }

    # Perform the analysis
    results = get_relevance_score(resume_text, job_criteria)
    return results

if __name__ == '__main__':
    # This is a simple test case for the ai_engine.py file
    # You would not run this directly in your Streamlit app.
    
    # A dummy job description and resume
    job_desc_skills = ["Python", "Machine Learning", "Data Analysis", "SQL", "TensorFlow", "AWS", "Scikit-learn", "Git"]
    sample_resume_text = """
    John Doe
    Data Scientist with 5 years of experience in Python and SQL. 
    Skilled in data analysis and machine learning with scikit-learn.
    Worked with cloud platforms including AWS. Proficient with version control systems like Git.
    """
    
    results = get_relevance_score(sample_resume_text, job_desc_skills)
    
    print("--- AI Engine Test Results ---")
    print(f"Final Score: {results['score']}%")
    print(f"Verdict: {results['verdict']}")
    print(f"Matched Skills: {results['matched_skills']}")
    print(f"Missing Skills: {results['missing_skills']}")
    print(f"Feedback from AI:\n{results['feedback']}")
