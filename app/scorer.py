import re
from statistics import mean


TECH_KEYWORDS = {
    "python", "fastapi", "api", "rest", "restful", "sql", "postgresql",
    "database", "query", "queries", "index", "indexing", "debugging",
    "performance", "scalable", "scalability", "async", "asynchronous",
    "authentication", "authorization", "logging", "monitoring", "backend",
    "endpoint", "validation", "error handling", "cache", "caching",
    "join", "joins", "execution plan", "explain", "analyze",
    "optimization", "optimize", "schema", "rate limiting", "timeout",
    "retry", "health check", "docker", "aws", "gcp", "microservice"
}

PROBLEM_SOLVING_KEYWORDS = {
    "analyze", "identified", "issue", "problem", "resolved", "fixed",
    "optimized", "improved", "steps", "root cause", "bottleneck",
    "logs", "logging", "monitoring", "execution plan", "index",
    "reduced", "compared", "measured", "before", "after", "tested",
    "solution", "approach", "debug", "investigate", "isolated"
}

COMMUNICATION_KEYWORDS = {
    "first", "then", "after", "because", "for example", "specifically",
    "clear", "explained", "approach", "structure", "step by step",
    "for instance", "i start", "i use", "i check", "i make sure"
}

RELIABILITY_KEYWORDS = {
    "error handling", "logging", "monitoring", "health check", "timeout",
    "retry", "validation", "tests", "testing", "reliable", "stability",
    "fallback", "alerting"
}

WEAK_LANGUAGE = {
    "maybe", "i think", "not sure", "kind of", "something like",
    "i guess", "probably", "a little", "some stuff"
}

STRONG_EXAMPLE_MARKERS = {
    "for example", "for instance", "in one project", "once", "i worked on",
    "in a project", "we had", "one challenge", "i fixed"
}

ROLE_KEYWORD_MAP = {
    "backend engineer": {
        "python", "fastapi", "api", "sql", "postgresql", "database",
        "performance", "debugging", "scalable", "backend", "endpoint"
    },
    "data analyst": {
        "sql", "python", "analysis", "dashboard", "statistics",
        "data cleaning", "reporting", "excel", "visualization"
    },
    "frontend engineer": {
        "javascript", "react", "frontend", "ui", "api", "css",
        "performance", "component", "state management"
    }
}


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def split_words(text: str) -> list[str]:
    return re.findall(r"[a-zA-Z_]+", text.lower())


def get_user_answers(transcript_turns: list[dict]) -> list[str]:
    answers = []
    for turn in transcript_turns:
        if turn.get("role") == "user":
            text = turn.get("text", "").strip()
            if text:
                answers.append(text)
    return answers


def count_phrase_hits(text: str, phrases: set[str]) -> int:
    normalized = normalize_text(text)
    return sum(1 for phrase in phrases if phrase in normalized)


def average_answer_length(answers: list[str]) -> float:
    if not answers:
        return 0.0
    return mean(len(split_words(a)) for a in answers)


def short_answer_ratio(answers: list[str]) -> float:
    if not answers:
        return 1.0
    lengths = [len(split_words(a)) for a in answers]
    short_count = sum(1 for n in lengths if n < 7)
    return short_count / len(lengths)


def long_answer_ratio(answers: list[str]) -> float:
    if not answers:
        return 0.0
    lengths = [len(split_words(a)) for a in answers]
    long_count = sum(1 for n in lengths if n >= 18)
    return long_count / len(lengths)


def keyword_density_score(text: str, keywords: set[str], scale: float = 1.0) -> float:
    hits = count_phrase_hits(text, keywords)
    return min(100.0, hits * 8.0 * scale)


def example_score(text: str) -> float:
    hits = count_phrase_hits(text, STRONG_EXAMPLE_MARKERS)
    return min(100.0, hits * 18.0)


def weak_language_penalty(text: str) -> float:
    hits = count_phrase_hits(text, WEAK_LANGUAGE)
    return min(25.0, hits * 6.0)


def answer_length_score(answers: list[str]) -> float:
    avg_words = average_answer_length(answers)

    if avg_words >= 28:
        return 92.0
    if avg_words >= 22:
        return 85.0
    if avg_words >= 16:
        return 75.0
    if avg_words >= 11:
        return 62.0
    if avg_words >= 7:
        return 50.0
    return 30.0


def structure_score(text: str) -> float:
    hits = count_phrase_hits(text, COMMUNICATION_KEYWORDS)
    return min(100.0, hits * 10.0)


def consistency_score(answers: list[str]) -> float:
    short_ratio = short_answer_ratio(answers)
    long_ratio = long_answer_ratio(answers)

    score = 80.0
    score -= short_ratio * 40.0
    score += long_ratio * 15.0
    return max(20.0, min(95.0, score))


def required_skills_match_score(text: str, required_skills: list[str]) -> float:
    if not required_skills:
        return 60.0

    normalized = normalize_text(text)
    hits = 0
    for skill in required_skills:
        s = skill.strip().lower()
        if s and s in normalized:
            hits += 1

    ratio = hits / len(required_skills)
    return min(100.0, 35.0 + ratio * 65.0)


def role_specific_score(text: str, role_title: str) -> float:
    role_key = role_title.strip().lower()
    role_keywords = ROLE_KEYWORD_MAP.get(role_key)

    if not role_keywords:
        return 60.0

    hits = count_phrase_hits(text, role_keywords)
    return min(100.0, 40.0 + hits * 8.0)


def clamp(score: float) -> float:
    return round(max(0.0, min(100.0, score)), 2)


def recommendation_from_score(score: float) -> str:
    if score >= 88:
        return "Strong Hire"
    if score >= 75:
        return "Hire"
    if score >= 60:
        return "Borderline"
    return "No Hire"


def build_strengths(scores: dict, text: str, answers: list[str]) -> list[str]:
    strengths = []

    if scores["technical_knowledge"] >= 78:
        strengths.append("Good technical understanding of backend concepts")
    if scores["problem_solving"] >= 75:
        strengths.append("Shows a practical and structured problem-solving approach")
    if scores["communication"] >= 78:
        strengths.append("Communicates clearly and explains ideas in a simple way")
    if scores["role_fit"] >= 75:
        strengths.append("Demonstrates good alignment with the role requirements")
    if example_score(text) >= 18:
        strengths.append("Used practical examples to support answers")

    if not strengths:
        strengths.append("Showed basic understanding of the interview topics")

    return strengths[:4]


def build_concerns(scores: dict, text: str, answers: list[str]) -> list[str]:
    concerns = []

    if scores["technical_knowledge"] < 70:
        concerns.append("Technical answers need more depth and specific details")
    if scores["problem_solving"] < 70:
        concerns.append("Problem-solving examples could be stronger")
    if scores["communication"] < 70:
        concerns.append("Some answers were too short or not fully developed")
    if scores["role_fit"] < 70:
        concerns.append("More role-specific examples would improve the evaluation")
    if weak_language_penalty(text) >= 10:
        concerns.append("Some answers sounded uncertain and could be more confident")
    if len(answers) < 5:
        concerns.append("The interview did not include enough detailed responses")

    if not concerns:
        concerns.append("A little more depth in some answers would make the profile stronger")

    return concerns[:4]


def build_summary(final_score: float, recommendation: str, scores: dict) -> str:
    strongest_area = max(scores, key=scores.get).replace("_", " ")
    weakest_area = min(scores, key=scores.get).replace("_", " ")

    return (
        f"The candidate showed a solid overall performance with a final score of {round(final_score)}. "
        f"The strongest area was {strongest_area}, while {weakest_area} could be improved further. "
        f"Overall, the evaluation supports a {recommendation.lower()} decision."
    )


def analyze_interview(
    role_title: str,
    job_description: str,
    required_skills: list[str],
    transcript_turns: list[dict],
) -> dict:
    answers = get_user_answers(transcript_turns)
    all_user_text = " ".join(answers)
    normalized_text = normalize_text(all_user_text)

    base_length = answer_length_score(answers)
    base_consistency = consistency_score(answers)
    technical_density = keyword_density_score(normalized_text, TECH_KEYWORDS, scale=1.0)
    problem_density = keyword_density_score(normalized_text, PROBLEM_SOLVING_KEYWORDS, scale=1.0)
    communication_density = structure_score(normalized_text)
    reliability_density = keyword_density_score(normalized_text, RELIABILITY_KEYWORDS, scale=0.8)
    examples = example_score(normalized_text)
    penalty = weak_language_penalty(normalized_text)
    skill_match = required_skills_match_score(normalized_text, required_skills)
    role_match = role_specific_score(normalized_text, role_title)

    technical_knowledge = (
        technical_density * 0.45
        + base_length * 0.18
        + base_consistency * 0.12
        + skill_match * 0.15
        + role_match * 0.10
        - penalty * 0.15
    )

    problem_solving = (
        problem_density * 0.40
        + examples * 0.20
        + base_length * 0.15
        + base_consistency * 0.15
        + communication_density * 0.10
        - penalty * 0.10
    )

    communication = (
        communication_density * 0.35
        + base_length * 0.30
        + base_consistency * 0.20
        + examples * 0.10
        - penalty * 0.10
    )

    role_fit = (
        skill_match * 0.40
        + role_match * 0.25
        + technical_density * 0.15
        + reliability_density * 0.10
        + base_consistency * 0.10
        - penalty * 0.08
    )

    scores = {
        "technical_knowledge": clamp(technical_knowledge),
        "problem_solving": clamp(problem_solving),
        "communication": clamp(communication),
        "role_fit": clamp(role_fit),
    }

    section_scores = [
        {
            "name": "technical_knowledge",
            "score": scores["technical_knowledge"],
            "weight": 0.35,
            "justification": "Scored based on technical terminology, role-relevant skills, and answer depth."
        },
        {
            "name": "problem_solving",
            "score": scores["problem_solving"],
            "weight": 0.25,
            "justification": "Scored based on examples, troubleshooting language, and structured reasoning."
        },
        {
            "name": "communication",
            "score": scores["communication"],
            "weight": 0.20,
            "justification": "Scored based on clarity, answer structure, and consistency."
        },
        {
            "name": "role_fit",
            "score": scores["role_fit"],
            "weight": 0.20,
            "justification": "Scored based on alignment with required skills and the target role."
        },
    ]

    final_score = clamp(
        scores["technical_knowledge"] * 0.35
        + scores["problem_solving"] * 0.25
        + scores["communication"] * 0.20
        + scores["role_fit"] * 0.20
    )

    recommendation = recommendation_from_score(final_score)
    strengths = build_strengths(scores, normalized_text, answers)
    concerns = build_concerns(scores, normalized_text, answers)
    summary = build_summary(final_score, recommendation, scores)

    suggested_next_step = (
        "Proceed to the next interview stage"
        if final_score >= 75
        else "Conduct a deeper technical follow-up interview"
    )

    return {
        "role_title": role_title,
        "final_score": final_score,
        "recommendation": recommendation,
        "strengths": strengths,
        "concerns": concerns,
        "section_scores": section_scores,
        "summary": summary,
        "suggested_next_step": suggested_next_step,
    }