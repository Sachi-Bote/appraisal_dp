# scoring/pbas_raw.py

# ============================================================
# CONSTANTS
# ============================================================

MAX_LIMITS = {
    "teaching_process": 25,
    "feedback": 25,
    "department": 20,
    "institute": 10,
    "acr": 10,
    "society": 10,
}

ACR_GRADE_POINTS = {
    "A+": 10,
    "A": 8,
    "B": 6,
    "C": 4,
}

# ============================================================
# SECTION A — TEACHING PROCESS
# ============================================================

def calculate_teaching_process(courses: list) -> float:
    total_scheduled = sum(c["scheduled"] for c in courses)
    total_held = sum(c["held"] for c in courses)

    if total_scheduled == 0:
        return 0.0

    score = (total_held / total_scheduled) * MAX_LIMITS["teaching_process"]
    return round(min(score, MAX_LIMITS["teaching_process"]), 2)

# ============================================================
# SECTION B — STUDENT FEEDBACK
# ============================================================

def calculate_feedback(feedback_scores: list) -> float:
    if not feedback_scores:
        return 0.0

    avg = sum(feedback_scores) / len(feedback_scores)
    return round(min(avg, MAX_LIMITS["feedback"]), 2)

# ============================================================
# SECTION C — DEPARTMENTAL ACTIVITIES
# ============================================================

def calculate_department(activities: list) -> int:
    total = sum(a["credits"] for a in activities)
    return min(total, MAX_LIMITS["department"])

# ============================================================
# SECTION D — INSTITUTE ACTIVITIES
# ============================================================

def calculate_institute(activities: list) -> int:
    total = sum(a["credits"] for a in activities)
    return min(total, MAX_LIMITS["institute"])

# ============================================================
# SECTION E — ACR
# ============================================================

def calculate_acr(grade: str) -> int:
    return ACR_GRADE_POINTS.get(grade.upper(), 0)

# ============================================================
# SECTION F — CONTRIBUTION TO SOCIETY
# ============================================================

def calculate_society(activities: list) -> int:
    total = sum(a["credits"] for a in activities)
    return min(total, MAX_LIMITS["society"])