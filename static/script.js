import { Room, RoomEvent, createLocalAudioTrack } from "https://cdn.jsdelivr.net/npm/livekit-client/dist/livekit-client.esm.mjs";

const startBtn = document.getElementById("startBtn");
const endBtn = document.getElementById("endBtn");
const reportBtn = document.getElementById("reportBtn");

const transcriptBox = document.getElementById("transcriptBox");
const sessionStatus = document.getElementById("sessionStatus");
const candidateNamePreview = document.getElementById("candidateNamePreview");
const rolePreview = document.getElementById("rolePreview");
const connectionBadge = document.getElementById("connectionBadge");

const candidateNameInput = document.getElementById("candidateName");
const roleTitleInput = document.getElementById("roleTitle");

const finalScore = document.getElementById("finalScore");
const recommendation = document.getElementById("recommendation");
const summaryText = document.getElementById("summaryText");
const technicalScore = document.getElementById("technicalScore");
const problemSolvingScore = document.getElementById("problemSolvingScore");
const communicationScore = document.getElementById("communicationScore");
const roleFitScore = document.getElementById("roleFitScore");
const strengthsList = document.getElementById("strengthsList");
const concernsList = document.getElementById("concernsList");

let room = null;
let currentSessionId = null;
let currentRoomName = null;

candidateNameInput.addEventListener("input", () => {
  candidateNamePreview.textContent = candidateNameInput.value.trim() || "Not set";
});

roleTitleInput.addEventListener("input", () => {
  rolePreview.textContent = roleTitleInput.value.trim() || "Not set";
});

function addMessage(role, text) {
  const wrapper = document.createElement("div");
  wrapper.className = `message ${role === "system" ? "assistant" : role}`;

  const roleLabel = document.createElement("span");
  roleLabel.className = "message-role";

  if (role === "assistant") {
    roleLabel.textContent = "AI Interviewer";
  } else if (role === "user") {
    roleLabel.textContent = "Candidate";
  } else {
    roleLabel.textContent = "System";
  }

  const messageText = document.createElement("p");
  messageText.textContent = text;

  wrapper.appendChild(roleLabel);
  wrapper.appendChild(messageText);
  transcriptBox.appendChild(wrapper);
  transcriptBox.scrollTop = transcriptBox.scrollHeight;
}

async function postJSON(url, payload) {
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `HTTP ${res.status}`);
  }

  return res.json();
}

async function getJSON(url) {
  const res = await fetch(url);

  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `HTTP ${res.status}`);
  }

  return res.json();
}

async function startInterview() {
  sessionStatus.textContent = "Preparing";
  connectionBadge.textContent = "Preparing";
  transcriptBox.innerHTML = "";

  const payload = {
    candidate_name: document.getElementById("candidateName").value || "Candidate",
    role_title: document.getElementById("roleTitle").value || "Backend Engineer",
    seniority: document.getElementById("seniority").value || "Mid-Level",
    question_count: Number(document.getElementById("questionCount").value || 6),
    language: "Arabic",
    required_skills: document.getElementById("skills").value || "",
    job_description: document.getElementById("jobDescription").value || "General interview.",
  };

  const startData = await postJSON("/api/interview/start", payload);
  currentSessionId = startData.session_id;
  currentRoomName = startData.room_name;

  const tokenData = await postJSON("/api/token", {
    room_name: startData.room_name,
    participant_identity: startData.candidate_identity,
    participant_name: startData.participant_name,
  });

  room = new Room();

  room.on(RoomEvent.Connected, async () => {
    sessionStatus.textContent = "Connected";
    connectionBadge.textContent = "Connected";
    addMessage("system", "Connected to the interview room. Please allow microphone access and start speaking.");
  });

  room.on(RoomEvent.Disconnected, () => {
    sessionStatus.textContent = "Disconnected";
    connectionBadge.textContent = "Disconnected";
    addMessage("system", "Interview room disconnected.");
  });

  room.on(RoomEvent.TrackSubscribed, (track, publication, participant) => {
  console.log("TRACK RECEIVED:", track.kind, participant?.identity);

  if (track.kind === "audio") {
    const audioElement = track.attach();
    audioElement.autoplay = true;
    audioElement.controls = true;
    document.body.appendChild(audioElement);
  }
});

room.on(RoomEvent.ParticipantConnected, (participant) => {
  console.log("PARTICIPANT CONNECTED:", participant.identity);
});

  await room.connect(tokenData.server_url, tokenData.participant_token);

  const micTrack = await createLocalAudioTrack();
  await room.localParticipant.publishTrack(micTrack);

  sessionStatus.textContent = "Interview Running";
  connectionBadge.textContent = "Live";
}

async function disconnectInterview() {
  if (room) {
    await room.disconnect();
    room = null;
  }

  sessionStatus.textContent = "Ended";
  connectionBadge.textContent = "Disconnected";
}

async function generateReport() {
  if (!currentSessionId) {
    alert("ابدئي المقابلة أولاً");
    return;
  }

  await disconnectInterview();

  let sessionData;
  try {
    sessionData = await getJSON(`/api/session/${currentSessionId}`);
  } catch (e) {
    alert("الـ transcript لم يُحفظ بعد. انتظري شوي ثم حاولي مرة ثانية.");
    return;
  }

  transcriptBox.innerHTML = "";
  for (const turn of sessionData.transcript_turns || []) {
    addMessage(turn.role, turn.text);
  }

  const report = await postJSON(`/api/report/${currentSessionId}`, {});

  finalScore.textContent = Math.round(report.final_score);
  recommendation.textContent = report.recommendation;
  summaryText.textContent = report.summary;

  const map = {};
  for (const item of report.section_scores || []) {
    map[item.name] = item.score;
  }

  technicalScore.textContent = map.technical_knowledge ?? "--";
  problemSolvingScore.textContent = map.problem_solving ?? "--";
  communicationScore.textContent = map.communication ?? "--";
  roleFitScore.textContent = map.role_fit ?? "--";

  strengthsList.innerHTML = "";
  for (const s of report.strengths || []) {
    const li = document.createElement("li");
    li.textContent = s;
    strengthsList.appendChild(li);
  }

  concernsList.innerHTML = "";
  for (const c of report.concerns || []) {
    const li = document.createElement("li");
    li.textContent = c;
    concernsList.appendChild(li);
  }

  addMessage("system", "Final evaluation report generated successfully.");
}

startBtn.addEventListener("click", async () => {
  try {
    await startInterview();
  } catch (err) {
    console.error(err);
    alert("فشل بدء المقابلة. تأكدي من تشغيل الـ backend والـ agent وصحة مفاتيح LiveKit.");
  }
});

endBtn.addEventListener("click", async () => {
  try {
    await disconnectInterview();
  } catch (err) {
    console.error(err);
  }
});

reportBtn.addEventListener("click", async () => {
  try {
    await generateReport();
  } catch (err) {
    console.error(err);
    alert("فشل إنشاء التقرير النهائي.");
  }
});

/* canvas background */
const canvas = document.getElementById("bg-canvas");
const ctx = canvas.getContext("2d");
let particles = [];
const particleCount = 70;

function resizeCanvas() {
  canvas.width = window.innerWidth;
  canvas.height = window.innerHeight;
}

function createParticles() {
  particles = [];
  for (let i = 0; i < particleCount; i++) {
    particles.push({
      x: Math.random() * canvas.width,
      y: Math.random() * canvas.height,
      vx: (Math.random() - 0.5) * 0.22,
      vy: (Math.random() - 0.5) * 0.22,
      r: Math.random() * 1.5 + 0.5
    });
  }
}

function drawParticles() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  for (let i = 0; i < particles.length; i++) {
    const p = particles[i];
    p.x += p.vx;
    p.y += p.vy;

    if (p.x < 0 || p.x > canvas.width) p.vx *= -1;
    if (p.y < 0 || p.y > canvas.height) p.vy *= -1;

    ctx.beginPath();
    ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
    ctx.fillStyle = "rgba(255,255,255,0.18)";
    ctx.fill();

    for (let j = i + 1; j < particles.length; j++) {
      const q = particles[j];
      const dx = p.x - q.x;
      const dy = p.y - q.y;
      const dist = Math.sqrt(dx * dx + dy * dy);

      if (dist < 120) {
        ctx.beginPath();
        ctx.moveTo(p.x, p.y);
        ctx.lineTo(q.x, q.y);
        ctx.strokeStyle = `rgba(255,255,255,${0.05 * (1 - dist / 120)})`;
        ctx.lineWidth = 1;
        ctx.stroke();
      }
    }
  }

  requestAnimationFrame(drawParticles);
}

resizeCanvas();
createParticles();
drawParticles();

window.addEventListener("resize", () => {
  resizeCanvas();
  createParticles();
});