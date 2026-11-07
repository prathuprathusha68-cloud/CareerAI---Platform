import os

from PyPDF2 import PdfReader
from docx import Document


# ---------------------------------------------------------
# EXTRACT TEXT FROM PDF
# ---------------------------------------------------------

def extract_text_from_pdf(file_path):

    text = ""

    try:

        reader = PdfReader(file_path)

        for page in reader.pages:

            page_text = page.extract_text()

            if page_text:
                text += page_text + "\n"

    except Exception as e:

        print("PDF extraction error:", e)

    return text


# ---------------------------------------------------------
# EXTRACT TEXT FROM DOCX
# ---------------------------------------------------------

def extract_text_from_docx(file_path):

    text = ""

    try:

        document = Document(file_path)

        for paragraph in document.paragraphs:

            if paragraph.text.strip():
                text += paragraph.text + "\n"

    except Exception as e:

        print("DOCX extraction error:", e)

    return text


# ---------------------------------------------------------
# EXTRACT RESUME TEXT
# ---------------------------------------------------------

def extract_resume_text(file_path):

    if not file_path:
        return ""

    extension = os.path.splitext(file_path)[1].lower()

    if extension == ".pdf":

        return extract_text_from_pdf(file_path)

    elif extension == ".docx":

        return extract_text_from_docx(file_path)

    else:

        return ""


# ---------------------------------------------------------
# FIND SKILLS IN RESUME
# ---------------------------------------------------------

def detect_skills_from_resume(resume_text):

    # Skills that CareerAI can currently recognize
    known_skills = [

        "Python",
        "Java",
        "C",
        "C++",
        "C#",

        "SQL",
        "MySQL",
        "MongoDB",

        "HTML",
        "CSS",
        "JavaScript",

        "React",
        "Angular",
        "Node.js",

        "Django",
        "Flask",

        "Git",
        "GitHub",

        "REST API",
        "REST APIs",

        "OOP",
        "Object Oriented Programming",

        "Data Structures",
        "Algorithms",

        "Machine Learning",
        "Deep Learning",
        "Artificial Intelligence",

        "AWS",
        "Azure",
        "Google Cloud",

        "Docker",
        "Kubernetes",

        "Power BI",
        "Tableau",

        "Excel"
    ]

    resume_text_lower = resume_text.lower()

    detected_skills = []

    for skill in known_skills:

        if skill.lower() in resume_text_lower:

            detected_skills.append(skill)

    # Remove duplicate skills
    detected_skills = list(dict.fromkeys(detected_skills))

    return detected_skills


# ---------------------------------------------------------
# COMPLETE RESUME ANALYSIS
# ---------------------------------------------------------

def analyze_resume(file_path):

    resume_text = extract_resume_text(file_path)

    detected_skills = detect_skills_from_resume(
        resume_text
    )

    return {
        "resume_text": resume_text,
        "detected_skills": detected_skills,
        "skill_count": len(detected_skills)
    }