import time

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from livekit import api

from app.config import (
    LIVEKIT_API_KEY,
    LIVEKIT_API_SECRET,
    LIVEKIT_URL,
    DEFAULT_LANGUAGE,
)
from app.schemas import StartInterviewRequest, TokenRequestModel
from app.storage import (
    new_id,
    save_json,
    load_json,
    config_path,
    session_path,
    report_path,
)
from app.scorer import analyze_interview

app = FastAPI(title="AI Interview Agent")

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def home():
    return FileResponse("static/index.html")


@app.post("/api/interview/start")
async def start_interview(payload: StartInterviewRequest):
    session_id = new_id("session")
    room_name = f"room_{int(time.time())}"
    candidate_identity = f"user_{int(time.time())}"

    skills = [s.strip() for s in payload.required_skills.split(",") if s.strip()]

    config_data = {
        "session_id": session_id,
        "room_name": room_name,
        "candidate_name": payload.candidate_name.strip() or "Candidate",
        "role_title": payload.role_title.strip(),
        "seniority": payload.seniority.strip(),
        "question_count": int(payload.question_count),
        "language": payload.language or DEFAULT_LANGUAGE,
        "required_skills": skills,
        "job_description": payload.job_description.strip(),
    }

    save_json(config_path(room_name), config_data)

    return {
        "session_id": session_id,
        "room_name": room_name,
        "candidate_identity": candidate_identity,
        "participant_name": config_data["candidate_name"],
        "livekit_url": LIVEKIT_URL,
    }


@app.post("/api/token", status_code=201)
async def get_token(request: TokenRequestModel):
    if not all([LIVEKIT_API_KEY, LIVEKIT_API_SECRET, LIVEKIT_URL]):
        raise HTTPException(status_code=500, detail="Missing LiveKit env vars")

    room_name = request.room_name or f"room-{int(time.time())}"
    participant_identity = request.participant_identity or f"user-{int(time.time())}"
    participant_name = request.participant_name or "User"

    token = (
    api.AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
    .with_identity(participant_identity)
    .with_name(participant_name)
    .with_grants(
        api.VideoGrants(
            room_join=True,
            room=room_name,
            can_publish=True,
            can_subscribe=True,
        )
    )
    .with_room_config(
        api.RoomConfiguration(
            agents=[
                api.RoomAgentDispatch(
                    agent_name="interview-agent"
                )
            ]
        )
    )
)

    if request.participant_metadata:
        token = token.with_metadata(request.participant_metadata)

    if request.participant_attributes:
        token = token.with_attributes(request.participant_attributes)

    if request.room_config:
        token = token.with_room_config(request.room_config)

    participant_token = token.to_jwt()

    return {
        "server_url": LIVEKIT_URL,
        "participant_token": participant_token,
    }


@app.get("/api/session/{session_id}")
async def get_session(session_id: str):
    path = session_path(session_id)
    if not path.exists():
        return JSONResponse(
            status_code=404,
            content={"error": "Session not found yet"},
        )
    return load_json(path)


@app.post("/api/report/{session_id}")
async def generate_report(session_id: str):
    spath = session_path(session_id)

    if not spath.exists():
        raise HTTPException(status_code=404, detail="Session transcript not found")

    session_data = load_json(spath)

    report = analyze_interview(
        role_title=session_data["role_title"],
        job_description=session_data["job_description"],
        required_skills=session_data["required_skills"],
        transcript_turns=session_data["transcript_turns"],
    )

    save_json(report_path(session_id), report)
    return report


@app.get("/api/report/{session_id}")
async def get_report(session_id: str):
    rpath = report_path(session_id)
    if not rpath.exists():
        raise HTTPException(status_code=404, detail="Report not found")
    return load_json(rpath)