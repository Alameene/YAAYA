// Frontend logic: fetch /chat, voice input (Web Speech API), and TTS
const chatEl = document.getElementById("chat");
const messageInput = document.getElementById("message");
const sendBtn = document.getElementById("sendBtn");
const micBtn = document.getElementById("micBtn");
let recognizing = false;
let recognition = null;

// Utility to append messages
function appendBubble(text, who="bot"){
  const wrap = document.createElement("div");
  wrap.className = "bubble " + (who==="user"? "user":"bot");
  wrap.textContent = text;
  chatEl.appendChild(wrap);
  chatEl.scrollTop = chatEl.scrollHeight;
}

// Send message to backend
async function sendMessage(text){
  appendBubble(text, "user");
  messageInput.value = "";
  try{
    const res = await fetch("/chat", {
      method: "POST",
      headers: {"Content-Type":"application/json"},
      body: JSON.stringify({message: text})
    });
    const data = await res.json();
    const reply = data.reply || "No reply.";
    appendBubble(reply, "bot");
    speakText(reply);
  }catch(err){
    appendBubble("Network error. Please try again.", "bot");
  }
}

// TTS
function speakText(txt){
  try{
    const ut = new SpeechSynthesisUtterance(txt);
    // pick a voice that matches the device
    const voices = speechSynthesis.getVoices();
    if(voices && voices.length>0){
      ut.voice = voices.find(v=>v.lang.startsWith("en")) || voices[0];
    }
    speechSynthesis.cancel();
    speechSynthesis.speak(ut);
  }catch(e){
    console.warn("TTS failed", e);
  }
}

// Basic UI events
sendBtn.addEventListener("click", ()=>{
  const t = messageInput.value.trim();
  if(t) sendMessage(t);
});
messageInput.addEventListener("keydown", (e)=>{
  if(e.key==="Enter" && !e.shiftKey){
    e.preventDefault();
    const t = messageInput.value.trim();
    if(t) sendMessage(t);
  }
});

// Voice recognition (works in Chrome/Edge)
if("webkitSpeechRecognition" in window || "SpeechRecognition" in window){
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  recognition = new SpeechRecognition();
  recognition.lang = "en-US";
  recognition.interimResults = false;
  recognition.maxAlternatives = 1;

  recognition.onresult = (e)=>{
    const txt = e.results[0][0].transcript;
    sendMessage(txt);
  };
  recognition.onend = ()=>{ recognizing = false; micBtn.textContent = "🎤"; }
  recognition.onerror = (e)=>{ recognizing = false; micBtn.textContent = "🎤"; console.warn("Speech error", e); }

  micBtn.addEventListener("click", ()=>{
    if(recognizing){
      recognition.stop();
    } else {
      try{
        recognition.start();
        recognizing = true;
        micBtn.textContent = "● Listening...";
      }catch(e){ console.warn(e); }
    }
  });
} else {
  // disable mic if not supported
  micBtn.style.opacity = 0.45;
  micBtn.title = "Voice input not supported on this browser";
}

// Welcome message
appendBubble("Hello! I'm YAAYA — ask me anything. (Try \"Who created you?\")", "bot");
