import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from dotenv import load_dotenv

from livekit import agents
from livekit.agents import Agent, AgentSession, AgentServer, TurnHandlingOptions, inference
from livekit.plugins import silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel

from app.prompts import INTERVIEWER_PROMPT_TEMPLATE
from app.storage import config_path, session_path, save_json, load_json

load_dotenv()

server = AgentServer()


class InterviewAgent(Agent):
    def __init__(self, instructions: str):
        super().__init__(instructions=instructions)


@server.rtc_session(agent_name="interview-agent")
async def entrypoint(ctx: agents.JobContext):
    print("ENTRYPOINT CALLED FOR ROOM:", ctx.room.name)

    room_name = ctx.room.name
    cfg_path = config_path(room_name)

    if not cfg_path.exists():
        config = {
            "session_id": "unknown",
            "room_name": room_name,
            "candidate_name": "Candidate",
            "role_title": "General Role",
            "seniority": "Mid-Level",
            "question_count": 6,
            "language": "Arabic and English",
            "required_skills": ["Communication", "Problem Solving"],
            "job_description": "Interview the candidate professionally.",
        }
    else:
        config = load_json(cfg_path)

    transcript_turns = []

    instructions = INTERVIEWER_PROMPT_TEMPLATE.format(
        role_title=config["role_title"],
        seniority=config["seniority"],
        language="Arabic and English",
        question_count=config["question_count"],
        required_skills=", ".join(config["required_skills"]),
        job_description=config["job_description"],
    )

    instructions += """

Additional bilingual behavior rules:
- You are fully bilingual in Arabic and English.
- If the candidate starts in Arabic, respond in Arabic.
- If the candidate starts in English, respond in English.
- If the candidate mixes Arabic and English, respond naturally in the same mixed style.
- Keep pronunciation and wording clear and professional.
- Do not switch language unnecessarily.
- Keep questions concise and interview-focused.
"""

    vad = silero.VAD.load()

    session = AgentSession(
        vad=vad,
        stt=inference.STT(
            model="deepgram/nova-3",
            language="multi",
        ),
        llm="openai/gpt-4.1-mini",
        tts=inference.TTS(
            model="cartesia/sonic-3",
            language="en",
        ),
        turn_handling=TurnHandlingOptions(
            turn_detection=MultilingualModel(),
        ),
    )

    @session.on("user_input_transcribed")
    def on_user_input_transcribed(event):
        if getattr(event, "is_final", False) and getattr(event, "transcript", "").strip():
            user_text = event.transcript.strip()
            print("USER:", user_text)

            transcript_turns.append({
                "role": "user",
                "text": user_text,
            })

    @session.on("conversation_item_added")
    def on_conversation_item_added(event):
        item = getattr(event, "item", None)
        if item is None:
            return

        role = getattr(item, "role", None)
        text_content = getattr(item, "text_content", None)

        if role == "assistant" and text_content:
            assistant_text = text_content.strip()
            print("ASSISTANT:", assistant_text)

            transcript_turns.append({
                "role": "assistant",
                "text": assistant_text,
            })

    @session.on("close")
    def on_close(_event):
        print("SESSION CLOSED FOR ROOM:", room_name)

        payload = {
            "session_id": config["session_id"],
            "room_name": config["room_name"],
            "candidate_name": config["candidate_name"],
            "role_title": config["role_title"],
            "seniority": config["seniority"],
            "job_description": config["job_description"],
            "required_skills": config["required_skills"],
            "transcript_turns": transcript_turns,
        }
        save_json(session_path(config["session_id"]), payload)

    await session.start(
        room=ctx.room,
        agent=InterviewAgent(instructions=instructions),
    )

    await session.generate_reply(
        instructions=(
            f"Start the interview now. "
            f"Greet the candidate {config['candidate_name']} briefly in a bilingual style. "
            f"Example style: 'مرحبًا، Hello, welcome to the interview.' "
            f"Then continue in the candidate's main language. "
            f"If the candidate speaks Arabic, continue in Arabic. "
            f"If the candidate speaks English, continue in English. "
            f"If the candidate mixes both, respond naturally in both. "
            f"Then ask the first interview question for the role {config['role_title']}."
        )
    )


if __name__ == "__main__":
    agents.cli.run_app(server)