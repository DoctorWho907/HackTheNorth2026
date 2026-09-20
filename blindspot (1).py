# BlindSpot v2 - main (Gemini + ElevenLabs + web)
# Run: python3 blindspot.py   |   Phone (same hotspot): http://<PI_IP>:5000

import io
import cv2
import requests
from flask import Flask, send_file, Response
import hardware

# ================= EDIT THESE =================
GEMINI_API_KEY  = "PASTE_YOUR_GEMINI_KEY_HERE"
ELEVEN_API_KEY  = "PASTE_YOUR_ELEVENLABS_KEY_HERE"
ELEVEN_VOICE_ID = "21m00Tcm4TlvDq8ikWAM"
GEMINI_MODEL    = "gemini-2.5-flash"
# =============================================

gemini_client = None
gemini_status = "not initialised"
try:
    from google import genai
    from google.genai import types
    gemini_client = genai.Client(api_key=GEMINI_API_KEY)
    gemini_status = "ok"
except Exception as e:
    gemini_status = f"init failed: {e}"
    print("Gemini init warning:", e)

PROMPTS = {
    "describe": (
        "You are the eyes for a blind person walking. FIRST, warn about any "
        "immediate HAZARDS (steps, stairs, curbs, traffic, obstacles, drop-offs, "
        "wet floor) with the direction. THEN briefly describe the layout ahead. "
        "Two short spoken sentences max. Calm and practical. Never say 'image'."
    ),
    "read": (
        "You are reading for a blind person. Read aloud any text, signs, or "
        "labels you can see, and say roughly where each is (left, ahead, right). "
        "If there is no text, say 'I don't see any text.' Keep it short and spoken."
    ),
    "cross": (
        "You are helping a blind person cross a street. Look for pedestrian "
        "walk/don't-walk signals, traffic, and moving vehicles. Say clearly "
        "whether it appears safe to cross right now or to wait, and why, in one "
        "or two short spoken sentences. If you cannot tell, say so plainly."
    ),
    "holding": (
        "A blind person is holding an object up to the camera. Identify what it "
        "is as specifically as you can (brand, type, any readable label). One "
        "short spoken sentence. If unclear, say what it most likely is."
    ),
    "find": (
        "A blind person is looking for something in this scene. Describe the most "
        "useful landmarks - doors, empty seats, exits, people - and give their "
        "direction (left, ahead, right) so they can move toward them. Two short "
        "spoken sentences."
    ),
    "people": (
        "You are giving social awareness to a blind person. Say how many people "
        "are visible, roughly where, and any obvious cues (someone approaching, "
        "waving, facing them). If no people, say 'No one is nearby.' Short, spoken."
    ),
    "color": (
        "A blind person wants to know a color or money. If they are holding "
        "clothing or an object, name its main color(s). If it is currency, name "
        "the bill or coin value. One short spoken sentence."
    ),
}


def gemini_describe(mode):
    if gemini_client is None:
        return f"Vision is not set up. {gemini_status}"
    frame = hardware.get_frame()
    if frame is None:
        return "I can't see anything yet."
    ok, buf = cv2.imencode(".jpg", cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
    if not ok:
        return "I couldn't capture the view."
    prompt = PROMPTS.get(mode, PROMPTS["describe"])
    try:
        resp = gemini_client.models.generate_content(
            model=GEMINI_MODEL,
            contents=[
                types.Part.from_bytes(data=buf.tobytes(), mime_type="image/jpeg"),
                prompt,
            ],
        )
        text = (resp.text or "").strip()
        return text if text else "I couldn't make anything out."
    except Exception as e:
        print("GEMINI ERROR:", repr(e))
        return "Vision error. Check the terminal."


def tts_audio(text, urgent=False):
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVEN_VOICE_ID}"
    headers = {"xi-api-key": ELEVEN_API_KEY, "Content-Type": "application/json"}
    vs = {"stability": 0.35 if urgent else 0.55, "similarity_boost": 0.75}
    data = {"text": text, "model_id": "eleven_turbo_v2", "voice_settings": vs}
    try:
        r = requests.post(url, json=data, headers=headers, timeout=20)
        if r.status_code == 200:
            return r.content
        print("ELEVENLABS ERROR:", r.status_code, r.text[:200])
    except Exception as e:
        print("ELEVENLABS EXCEPTION:", e)
    return None


app = Flask(__name__)


@app.route("/")
def index():
    return Response(PHONE_PAGE, mimetype="text/html")


@app.route("/act/<mode>")
def act(mode):
    text = gemini_describe(mode)
    print(f"[{mode}] {text}")
    urgent = mode in ("cross", "describe") and (
        "caution" in text.lower() or "stop" in text.lower() or "wait" in text.lower())
    audio = tts_audio(text, urgent=urgent)
    if audio is None:
        return Response(text, status=200, mimetype="text/plain",
                        headers={"X-Fallback": "text"})
    return send_file(io.BytesIO(audio), mimetype="audio/mpeg",
                     download_name="reply.mp3")


@app.route("/status")
def status():
    return {"gemini": gemini_status, "model": GEMINI_MODEL}


PHONE_PAGE = """<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>BlindSpot</title>
<style>
  :root { color-scheme: dark; }
  * { box-sizing:border-box; -webkit-tap-highlight-color:transparent; }
  html,body { height:100%; margin:0; }
  body { background:#0b0f14; color:#eaf0f7;
    font-family:-apple-system,system-ui,sans-serif;
    display:flex; flex-direction:column; align-items:center;
    padding:24px 18px calc(24px + env(safe-area-inset-bottom));
    padding-top:calc(20px + env(safe-area-inset-top)); }
  h1 { font-size:24px; font-weight:680; letter-spacing:-.02em; margin:0 0 2px; }
  .sub { color:#7d8ba0; font-size:14px; margin:0 0 18px; }
  #status { min-height:20px; color:#8aa0bd; font-size:14px; text-align:center; margin:4px 0 16px; }
  .big { width:100%; max-width:420px; height:120px; border:none; border-radius:20px;
    background:#2f6df6; color:#fff; font-size:22px; font-weight:650; margin-bottom:12px;
    box-shadow:0 8px 30px rgba(47,109,246,.35); transition:transform .08s, background .2s; }
  .big:active { transform:scale(.97); background:#245ad0; }
  .grid { width:100%; max-width:420px; display:grid; grid-template-columns:1fr 1fr; gap:10px; }
  .grid button { height:74px; border:none; border-radius:16px; background:#18202c;
    color:#eaf0f7; font-size:16px; font-weight:560; transition:transform .08s, background .2s; }
  .grid button:active { transform:scale(.96); background:#232f3f; }
  .busy { opacity:.55; }
  .wake { margin-top:18px; display:flex; align-items:center; gap:9px; color:#7d8ba0; font-size:14px; }
  .wake input { width:19px; height:19px; accent-color:#2f6df6; }
  audio { display:none; }
</style></head>
<body>
  <h1>BlindSpot</h1>
  <p class="sub">Your AI eyes</p>
  <button class="big" id="describe">Describe &amp; warn me</button>
  <div class="grid">
    <button data-mode="read">Read text</button>
    <button data-mode="cross">Safe to cross?</button>
    <button data-mode="holding">What am I holding?</button>
    <button data-mode="find">Find something</button>
    <button data-mode="people">Who's around?</button>
    <button data-mode="color">Color / money</button>
  </div>
  <p id="status">Tap a button to hear what's around you</p>
  <label class="wake"><input type="checkbox" id="wake"> Listen for &ldquo;hey spot&rdquo;</label>
  <audio id="player"></audio>
<script>
const status=document.getElementById('status');
const player=document.getElementById('player');
let busy=false;

async function run(mode){
  if(busy) return; busy=true;
  document.body.classList.add('busy');
  status.textContent='Looking...';
  try{
    const res=await fetch('/act/'+mode);
    if(res.headers.get('X-Fallback')==='text'){
      const t=await res.text(); status.textContent=t;
      speak(t);
    } else {
      const blob=await res.blob();
      player.src=URL.createObjectURL(blob); await player.play();
      status.textContent='Tap a button to hear what\\'s around you';
    }
  }catch(e){ status.textContent='Something went wrong. Tap to try again.'; }
  busy=false; document.body.classList.remove('busy');
}
function speak(t){ try{ const u=new SpeechSynthesisUtterance(t); speechSynthesis.speak(u);}catch(e){} }

document.getElementById('describe').addEventListener('click',()=>run('describe'));
document.querySelectorAll('.grid button').forEach(b=>
  b.addEventListener('click',()=>run(b.dataset.mode)));

let recog=null;
const wake=document.getElementById('wake');
function startRecog(){
  const SR=window.SpeechRecognition||window.webkitSpeechRecognition;
  if(!SR){ status.textContent='Voice input not supported in this browser'; wake.checked=false; return; }
  recog=new SR(); recog.continuous=true; recog.interimResults=true; recog.lang='en-US';
  recog.onresult=(e)=>{ for(let i=e.resultIndex;i<e.results.length;i++){
    const t=e.results[i][0].transcript.toLowerCase();
    if(t.includes('hey spot')||t.includes('a spot')||t.includes('spot')){
      if(t.includes('read')) run('read');
      else if(t.includes('cross')) run('cross');
      else if(t.includes('holding')||t.includes('hold')) run('holding');
      else if(t.includes('find')) run('find');
      else if(t.includes('who')||t.includes('people')) run('people');
      else if(t.includes('color')||t.includes('money')) run('color');
      else run('describe');
    }
  }};
  recog.onerror=(e)=>{ status.textContent='Voice error: '+e.error+' (tap buttons instead)'; };
  recog.onend=()=>{ if(wake.checked){ try{recog.start();}catch(e){} } };
  try{ recog.start(); status.textContent='Listening for "hey spot"'; }
  catch(e){ status.textContent='Could not start listening'; }
}
wake.addEventListener('change',()=>{
  if(wake.checked) startRecog();
  else if(recog){ recog.stop(); status.textContent='Tap a button to hear what\\'s around you'; }
});
</script></body></html>"""


def main():
    hardware.start_camera()
    print("Gemini status:", gemini_status)
    print("BlindSpot v2 running. Phone (same hotspot): http://<PI_IP>:5000")
    try:
        app.run(host="0.0.0.0", port=5000, threaded=True)
    finally:
        hardware.stop_camera()


if __name__ == "__main__":
    main()
