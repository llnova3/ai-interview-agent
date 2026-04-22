FROM python:3.11

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir fastapi uvicorn python-dotenv pydantic openai livekit-api livekit-agents livekit-plugins-openai livekit-plugins-silero livekit-plugins-turn-detector livekit-plugins-noise-cancellation

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]