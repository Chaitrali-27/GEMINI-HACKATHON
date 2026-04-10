"""
chatbot.py — SentinelIQ AI Chatbot
Uses Groq API (FREE FOREVER)

Install: pip install groq
Get free API key: https://console.groq.com
"""

from groq import Groq

# ─────────────────────────────────────────
# YOUR GROQ API KEY
# Get free at: console.groq.com
# ─────────────────────────────────────────

import os
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
# ─────────────────────────────────────────
# CONFIGURE CLIENT
# ─────────────────────────────────────────
try:
    client = Groq(api_key=GROQ_API_KEY)
    GROQ_READY = True
except Exception as e:
    client = None
    GROQ_READY = False
    print(f"Groq init error: {e}")

# ─────────────────────────────────────────
# BUILD SYSTEM PROMPT
# ─────────────────────────────────────────
def build_system_prompt(machines_data):
    machines_info = ""
    for mid, info in machines_data.items():
        m    = info["machine"]
        d    = info["data"]
        p    = d["prescription"]
        rca  = d.get("root_cause_analysis", {})
        anom = d.get("anomaly_detection", {})

        top_causes = ""
        if rca.get("available") and rca.get("root_causes"):
            causes = rca["root_causes"][:3]
            top_causes = ", ".join([
                f"{c['feature']} ({c['contribution']}% - {c['direction']})"
                for c in causes
            ])

        machines_info += f"""
Machine ID     : {mid}
Factory        : {m.get('factory_name', 'N/A')}
Location       : {m.get('district', '')}, {m.get('state', '')}
Type           : {m.get('machine_type', 'N/A')}
Status         : {p['priority']}
Health Score   : {p['health_score']}/100
RUL            : {d['rul']['mean']:.1f} hours (CI: {d['rul']['lower']:.1f} - {d['rul']['upper']:.1f})
Top Failure    : {d['top_failure_mode']} ({d['top_probability']*100:.1f}%)
Recommended    : {p['recommended_action']}
Anomaly        : {"DETECTED" if anom.get('is_anomaly') else "Normal"} (score: {anom.get('anomaly_score', 0)}/100)
Root Causes    : {top_causes if top_causes else "N/A"}
Last Service   : {m.get('last_service', 'N/A')}
Next Due       : {m.get('next_service_due', 'N/A')}
---"""

    return f"""
You are SentinelIQ Assistant — an expert AI for industrial predictive maintenance.
You help factory supervisors and managers understand their machine health status.

You have access to REAL-TIME machine data:
{machines_info}

Your personality:
- Speak like an experienced maintenance engineer
- Be direct, clear and actionable
- Use simple language — avoid too much jargon
- Always prioritize safety
- If a machine is CRITICAL always mention urgency

Keep responses concise — max 4-5 sentences.
End critical alerts with a strong action recommendation.
Always base answers on the real-time data provided above.
"""

# ─────────────────────────────────────────
# ASK CHATBOT
# ─────────────────────────────────────────
def ask_chatbot(question, machines_data, chat_history):
    if not GROQ_READY or client is None:
        return "❌ Groq not initialized. Check your API key in chatbot.py"

    try:
        messages = [
            {"role": "system", "content": build_system_prompt(machines_data)}
        ]

        for msg in chat_history[-6:]:
            messages.append({
                "role":    msg["role"],
                "content": msg["content"]
            })

        messages.append({"role": "user", "content": question})

        response = client.chat.completions.create(
            model       = "llama-3.3-70b-versatile",  # updated model
            messages    = messages,
            max_tokens  = 300,
            temperature = 0.7
        )

        return response.choices[0].message.content

    except Exception as e:
        error = str(e)
        if "quota" in error.lower() or "limit" in error.lower() or "rate" in error.lower():
            return "⚠️ Groq rate limit reached. Wait 1 minute and try again. No charges applied."
        elif "api" in error.lower() or "key" in error.lower() or "auth" in error.lower():
            return "❌ Invalid API key. Please update GROQ_API_KEY in chatbot.py"
        elif "decommissioned" in error.lower() or "model" in error.lower():
            return "❌ Model error. Please check chatbot.py for latest Groq model name."
        else:
            return f"❌ Chatbot error: {error}"

# ─────────────────────────────────────────
# SUGGESTED QUESTIONS
# ─────────────────────────────────────────
SUGGESTED_QUESTIONS = [
    "Which machine needs attention first?",
    "Why is the critical machine failing?",
    "What are the root causes of failure?",
    "How much time before breakdown?",
    "Is any machine behaving abnormally?",
    "What maintenance action should I take?",
    "Compare health of all my machines",
    "When is the next service due?",
]

# ─────────────────────────────────────────
# TEST
# ─────────────────────────────────────────
if __name__ == "__main__":
    print("Testing Groq chatbot...")
    test = ask_chatbot("Hello, are you working?", {}, [])
    print("Response:", test)
