"""
voice_engine.py — SentinelIQ Voice System
Speaks alerts and chatbot responses out loud.
Uses pyttsx3 — 100% free, offline, no API key needed.

Install: pip install pyttsx3
"""

import pyttsx3
import threading

# ─────────────────────────────────────────
# INIT ENGINE
# ─────────────────────────────────────────
def get_engine():
    engine = pyttsx3.init()
    engine.setProperty("rate", 165)      # speaking speed
    engine.setProperty("volume", 1.0)    # full volume
    # try to set a clear voice
    voices = engine.getProperty("voices")
    for v in voices:
        if "english" in v.name.lower() or "zira" in v.name.lower() or "david" in v.name.lower():
            engine.setProperty("voice", v.id)
            break
    return engine

# ─────────────────────────────────────────
# SPEAK IN BACKGROUND THREAD
# (so dashboard doesn't freeze)
# ─────────────────────────────────────────
def speak(text):
    """Speak text in background thread so UI doesn't freeze."""
    def _speak():
        try:
            engine = get_engine()
            engine.say(text)
            engine.runAndWait()
            engine.stop()
        except Exception as e:
            print(f"Voice error: {e}")
    t = threading.Thread(target=_speak, daemon=True)
    t.start()

# ─────────────────────────────────────────
# CRITICAL ALERT VOICE
# ─────────────────────────────────────────
def speak_critical_alert(machine_id, failure_mode, rul, action):
    text = (
        f"Warning! Warning! Machine {machine_id} is in critical condition. "
        f"{failure_mode} failure predicted. "
        f"Only {rul:.0f} hours remaining before breakdown. "
        f"Immediate action required. "
        f"{action}. "
        f"Please attend to this machine immediately."
    )
    speak(text)

# ─────────────────────────────────────────
# WARNING ALERT VOICE
# ─────────────────────────────────────────
def speak_warning_alert(machine_id, failure_mode, rul):
    text = (
        f"Attention! Machine {machine_id} requires maintenance soon. "
        f"{failure_mode} detected. "
        f"Remaining useful life is {rul:.0f} hours. "
        f"Please schedule maintenance this week."
    )
    speak(text)

# ─────────────────────────────────────────
# CHATBOT RESPONSE VOICE
# ─────────────────────────────────────────
def speak_chatbot_response(text):
    """Speak chatbot answer out loud."""
    # Clean text for speaking (remove markdown symbols)
    clean = text.replace("**","").replace("*","").replace("#","").replace("`","").replace("→","").replace("✅","").replace("⚠️","warning").replace("🔴","critical").replace("🟡","warning").replace("🟢","healthy")
    # limit to first 300 chars for speech
    if len(clean) > 300:
        clean = clean[:300] + "... Please read the full response on screen."
    speak(clean)

# ─────────────────────────────────────────
# TEST
# ─────────────────────────────────────────
if __name__ == "__main__":
    print("Testing voice engine...")
    speak("Hello! SentinelIQ voice system is working correctly. Predict. Prevent. Protect.")
    import time; time.sleep(5)
    print("Voice test complete!")
