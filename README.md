# CareerAI – AI-Powered Graduate Employment Readiness and Career Bridge Platform

CareerAI is a web-based career readiness platform designed to help graduates understand how well their current skills match a selected job role. It brings resume skill extraction, skill-gap analysis, career guidance, assessments, learning resources, course progress tracking, and certificates together in one platform.

## Project Overview

Many graduates are unsure which skills are required for a particular job and what they should learn next. CareerAI addresses this problem by allowing users to provide their profile details, select a target career, and review their current skills against the skills required for that role.

The platform presents the user's strengths, missing skills, readiness level, learning priorities, and recommendations to support focused career preparation.

## Key Features

- **User profile and career selection** – Enter profile, education, experience, skills, and target job role.
- **Resume analysis** – Upload a PDF or DOCX resume and extract recognised technical skills.
- **Skill-gap analysis** – Compare existing skills with the requirements of the selected career.
- **Career readiness indication** – Display a skill-match percentage and a readiness category.
- **Personalised learning priorities** – Highlight skills that should be developed next.
- **Assessment module** – Attempt a timed assessment containing aptitude, reasoning, programming, OOP, data structures, SQL/DBMS, and web/API/Git topics. The configured assessment contains 64 questions and a 125-minute duration.
- **Reassessment** – Revisit readiness after improving skills.
- **Learning roadmap** – View learning guidance for the selected career.
- **Courses and lessons** – Browse courses, view course details, enrol, and access lessons.
- **Progress tracking** – Record completed lessons for enrolled courses.
- **Certificates** – View course certificates after completing the relevant learning requirements.

## Technology Stack

| Area | Technologies |
|---|---|
| Backend | Python, Flask |
| Frontend | HTML, CSS, JavaScript, Jinja2 templates |
| Database | SQLite |
| Resume processing | PyPDF2, python-docx |
| Development tools | Visual Studio Code, Git, GitHub |

## How the Platform Works

1. The user opens CareerAI and signs in.
2. The user enters profile information and selects a target career.
3. The resume analyzer extracts recognised skills from an uploaded PDF or DOCX file.
4. CareerAI compares the user's skills with the selected role's skill requirements.
5. The platform displays strengths, missing skills, a match percentage, readiness category, and recommendations.
6. The user follows the learning roadmap and studies relevant courses.
7. The user completes assessments to evaluate knowledge and can use reassessment to review progress.
8. Course enrolment and lesson completion are recorded, and certificates can be viewed through the platform.

## Project Structure

```text
CareerAI---Platform/
└── backend/
    ├── ai/
    │   ├── resume_analyzer.py
    │   └── skill_analyzer.py
    ├── database/
    │   ├── assessment_questions.py
    │   ├── course_lessons.py
    │   ├── courses.py
    │   └── skill_requirements.py
    ├── static/
    │   └── Images/
    ├── templates/
    │   ├── home.html
    │   ├── login.html
    │   ├── career_setup.html
    │   ├── analyze_profile.html
    │   ├── skill_gap.html
    │   ├── assessment.html
    │   ├── assessment_result.html
    │   ├── roadmap.html
    │   ├── dashboard.html
    │   ├── courses.html
    │   ├── course_detail.html
    │   ├── course_learning.html
    │   ├── my_courses.html
    │   └── certificate-related pages
    ├── app.py
    └── careerai_courses.db
```

## Getting Started

### Prerequisites

- Python 3.10 or later
- Git
- Visual Studio Code (recommended)

### 1. Clone the repository

```bash
git clone https://github.com/prathupprathusha68-cloud/CareerAI---Platform.git
cd CareerAI---Platform
```

### 2. Open the backend folder

```bash
cd backend
```

### 3. Create and activate a virtual environment

**Windows PowerShell:**

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, use Command Prompt:

```bat
venv\Scripts\activate
```

### 4. Install the required packages

```bash
pip install Flask PyPDF2 python-docx
```

### 5. Run the application

```bash
python app.py
```

Open the local address shown in the terminal, usually:

```text
http://127.0.0.1:5000/
```

## Database

CareerAI uses SQLite for course-related data. The backend creates and uses the `careerai_courses.db` database for course enrolments and lesson-completion progress. Other career skill requirements, course information, lesson content, and assessment questions are maintained in Python modules under `backend/database/`.

## How the Skill Analysis Works

The current implementation uses programmed skill lists and rule-based matching:

- The resume analyzer extracts text from PDF and DOCX files.
- It searches the extracted text for recognised skill keywords.
- The skill analyzer compares the user's listed skills with the missing skills for the selected role.
- It calculates a match percentage and assigns a readiness category:
  - **80% and above:** Job Ready
  - **60%–79%:** Good Progress
  - **40%–59%:** Needs Improvement
  - **Below 40%:** Beginner

The platform provides rule-based analysis and recommendations; it does not claim to train a custom machine-learning model.

## Future Enhancements

- Improve resume parsing and support additional resume formats.
- Add more job roles and regularly updated skill requirements.
- Introduce more role-specific assessments and coding challenges.
- Enhance learning recommendations using learner performance and progress.
- Add secure authentication, deployment configuration, and production-level testing.
- Integrate verified external learning resources and job opportunities.

## Project Purpose

This project was developed as an academic major project to demonstrate how a web-based platform can help graduates assess their employment readiness, identify skill gaps, and plan their learning journey.

---

**Project:** CareerAI – AI-Powered Graduate Employment Readiness and Career Bridge Platform
