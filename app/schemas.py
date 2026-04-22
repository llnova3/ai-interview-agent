from typing import List, Optional, Literal
from pydantic import BaseModel, Field


class InterviewConfig(BaseModel):
    session_id: str
    room_name: str
    candidate_name: str = "Candidate"
    role_title: str
    seniority: str = "Mid-Level"
    question_count: int = 6
    language: str = "Arabic"
    required_skills: List[str] = Field(default_factory=list)
    job_description: str


class TranscriptTurn(BaseModel):
    role: Literal["assistant", "user"]
    text: str


class StartInterviewRequest(BaseModel):
    candidate_name: str
    role_title: str
    seniority: str
    question_count: int
    language: str = "Arabic"
    required_skills: str
    job_description: str


class StartInterviewResponse(BaseModel):
    session_id: str
    room_name: str
    candidate_identity: str
    participant_name: str
    livekit_url: str


class TokenRequestModel(BaseModel):
    room_name: Optional[str] = None
    participant_identity: Optional[str] = None
    participant_name: Optional[str] = None
    participant_metadata: Optional[str] = None
    participant_attributes: Optional[dict] = None
    room_config: Optional[dict] = None


class SectionScore(BaseModel):
    name: str
    score: float
    weight: float
    justification: str


class InterviewReport(BaseModel):
    role_title: str
    final_score: float
    recommendation: Literal["Strong Hire", "Hire", "Borderline", "No Hire"]
    strengths: List[str]
    concerns: List[str]
    section_scores: List[SectionScore]
    summary: str
    suggested_next_step: str