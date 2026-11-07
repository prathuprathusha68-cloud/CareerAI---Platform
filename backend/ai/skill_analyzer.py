def analyze_skills(user_skills, missing_skills, target_role):
    """
    Analyze the user's current skills and missing skills
    for the selected target career.
    """

    # Clean user skills
    user_skills_clean = [
        skill.strip().lower()
        for skill in user_skills
        if skill.strip()
    ]

    # Clean missing skills
    missing_skills_clean = [
        skill.strip()
        for skill in missing_skills
        if skill.strip()
    ]

    # ---------------------------------------------------------
    # FIND STRENGTHS
    # ---------------------------------------------------------

    strengths = []

    for skill in user_skills:
        if skill.strip():
            strengths.append(skill.strip())

    # ---------------------------------------------------------
    # DETERMINE READINESS
    # ---------------------------------------------------------

    total_required = len(user_skills_clean) + len(missing_skills_clean)

    if total_required > 0:
        match_percentage = round(
            (len(user_skills_clean) / total_required) * 100
        )
    else:
        match_percentage = 0

    if match_percentage >= 80:
        readiness = "Job Ready"

    elif match_percentage >= 60:
        readiness = "Good Progress"

    elif match_percentage >= 40:
        readiness = "Needs Improvement"

    else:
        readiness = "Beginner"

    # ---------------------------------------------------------
    # GENERATE CAREER-SPECIFIC RECOMMENDATION
    # ---------------------------------------------------------

    if match_percentage >= 80:

        recommendation = (
            f"You have a strong foundation for a {target_role} career. "
            "Focus on advanced projects, interview preparation, "
            "problem-solving and real-world development experience."
        )

    elif match_percentage >= 60:

        recommendation = (
            f"You have a good foundation for a {target_role} role. "
            "Strengthen your missing technical skills and "
            "build practical projects to improve your job readiness."
        )

    elif match_percentage >= 40:

        recommendation = (
            f"You have started developing the skills required for "
            f"a {target_role} career. Focus on your missing core skills "
            "and practice them through small practical projects."
        )

    else:

        recommendation = (
            f"You are at the beginning of your journey toward becoming "
            f"a {target_role}. Start with the fundamental skills, "
            "practice regularly and gradually build real-world projects."
        )

    # ---------------------------------------------------------
    # LEARNING PRIORITIES
    # ---------------------------------------------------------

    if missing_skills_clean:

        learning_priorities = missing_skills_clean[:5]

    else:

        learning_priorities = [
            "Advanced Programming",
            "Data Structures",
            "Problem Solving",
            "Real-World Projects",
            "Interview Preparation"
        ]

    # ---------------------------------------------------------
    # RETURN AI ANALYSIS
    # ---------------------------------------------------------

    return {
        "target_role": target_role,
        "strengths": strengths,
        "missing_skills": missing_skills_clean,
        "match_percentage": match_percentage,
        "readiness": readiness,
        "learning_priorities": learning_priorities,
        "recommendation": recommendation
    }