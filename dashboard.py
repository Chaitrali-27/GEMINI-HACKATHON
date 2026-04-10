"""
dashboard.py — SentinelIQ Complete Dashboard
Predict. Prevent. Protect.
"""

import streamlit as st
import requests, random, time, smtplib
import plotly.graph_objects as go
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from database import (
    verify_login, get_machines_for_user, create_user,
    get_users_by_role, get_machine_by_id, get_alerts_for_machine,
    log_alert, get_all_states, get_districts, get_machine_types,
    get_sensor_ranges, save_otp, verify_otp, generate_otp,
    get_manager_email_for_machine, get_higher_authority_email
)
from chatbot import ask_chatbot, SUGGESTED_QUESTIONS
from voice_engine import speak_critical_alert, speak_warning_alert, speak_chatbot_response
from federated_learning import load_federated_results

st.set_page_config(page_title="SentinelIQ", page_icon="🛡️", layout="wide", initial_sidebar_state="collapsed")

GMAIL_ADDRESS  = "your_gmail@gmail.com"
GMAIL_PASSWORD = "xxxx xxxx xxxx xxxx"

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@400;600;700&family=Share+Tech+Mono&display=swap');
html,body,[class*="css"]{background-color:#050d1a;color:#c8d8e8;font-family:'Rajdhani',sans-serif;}
.stApp{background:linear-gradient(135deg,#050d1a 0%,#0a1628 60%,#050d1a 100%);}
.login-wrap{max-width:500px;margin:40px auto;background:linear-gradient(145deg,#0d1f38,#0a1628);border:1px solid #1e3a5f;border-radius:16px;padding:40px;box-shadow:0 0 50px rgba(0,120,255,.12);}
.brand-big{font-size:2.8rem;font-weight:700;color:#4da6ff;text-align:center;letter-spacing:4px;}
.brand-tag{font-size:.78rem;color:#2a5a8a;text-align:center;letter-spacing:3px;margin-bottom:24px;}
.mcard{background:linear-gradient(145deg,#0d1f38,#0a1628);border:1px solid #1e3a5f;border-radius:14px;padding:18px 22px;margin-bottom:12px;}
.mcard-critical{border-left:4px solid #ff4444;box-shadow:0 0 18px rgba(255,68,68,.12);}
.mcard-warning{border-left:4px solid #ffaa00;box-shadow:0 0 18px rgba(255,170,0,.12);}
.mcard-healthy{border-left:4px solid #00cc66;box-shadow:0 0 12px rgba(0,204,102,.07);}
.mlabel{font-size:.7rem;color:#5a7a9a;letter-spacing:1px;text-transform:uppercase;}
.mval{font-size:1.4rem;font-weight:700;color:#c8d8e8;font-family:'Share Tech Mono',monospace;}
.mid-tag{font-size:.82rem;background:#0d2040;color:#4da6ff;border:1px solid #1e3a5f;border-radius:4px;padding:3px 10px;font-family:'Share Tech Mono',monospace;display:inline-block;margin-bottom:6px;}
.action-box{background:#0d1f38;border:1px solid #1e3a5f;border-radius:8px;padding:10px 14px;font-size:.82rem;color:#4da6ff;margin-top:8px;}
.algo-box{background:#0a1628;border:1px solid #1e3a5f;border-radius:10px;padding:14px 18px;margin-bottom:10px;}
.algo-title{font-size:.72rem;color:#5a7a9a;letter-spacing:2px;text-transform:uppercase;margin-bottom:8px;}
.rca-item{background:#0d1f38;border:1px solid #1e3a5f;border-radius:8px;padding:10px 14px;margin-bottom:6px;}
.chat-user{background:#0d2040;border:1px solid #1e3a5f;border-radius:12px 12px 0 12px;padding:10px 14px;margin:6px 0;font-size:.85rem;color:#c8d8e8;max-width:80%;margin-left:auto;}
.chat-ai{background:#0a1628;border:1px solid #1e3a5f;border-radius:12px 12px 12px 0;padding:10px 14px;margin:6px 0;font-size:.85rem;color:#4da6ff;max-width:90%;}
.chat-label-user{font-size:.65rem;color:#5a7a9a;text-align:right;margin-bottom:2px;}
.chat-label-ai{font-size:.65rem;color:#2a5a8a;margin-bottom:2px;}
.section-hdr{color:#5a7a9a;font-size:.7rem;letter-spacing:2px;text-transform:uppercase;margin-bottom:10px;}
.divider{border-color:#1e3a5f;margin:8px 0 18px 0;}
.user-row{background:#0d1f38;border:1px solid #1e3a5f;border-radius:8px;padding:12px 16px;margin-bottom:8px;font-size:.85rem;}
.fed-box{background:#0a1628;border:1px solid #1e5a3f;border-radius:10px;padding:16px 20px;margin-bottom:12px;}
.otp-box{background:#0a1628;border:2px solid #4da6ff;border-radius:10px;padding:16px 20px;margin:10px 0;}
.info-tag{background:#0d1f38;border:1px solid #4da6ff;border-radius:8px;padding:8px 12px;color:#4da6ff;font-size:.85rem;margin-top:6px;margin-bottom:6px;}
div[data-testid="stButton"] button{background:linear-gradient(135deg,#1a4a8a,#0d2d5e);color:#4da6ff;border:1px solid #2a5a9a;border-radius:8px;font-family:'Rajdhani',sans-serif;font-weight:600;letter-spacing:1px;}
div[data-testid="stSelectbox"]>div,div[data-testid="stTextInput"] input{background:#0d1f38 !important;border:1px solid #1e3a5f !important;color:#c8d8e8 !important;border-radius:8px !important;}
#MainMenu{visibility:hidden;}footer{visibility:hidden;}header{visibility:hidden;}
</style>
""", unsafe_allow_html=True)

for k,v in {
    "logged_in":False,"user":None,"history":{},"alerted":set(),
    "chat_history":[],"machines_data":{},"notifications":[],
    "reg_step":1,"reg_email":"","reg_form_data":{}
}.items():
    if k not in st.session_state: st.session_state[k] = v

# ════════════════════════════════════
# EMAIL FUNCTIONS
# ════════════════════════════════════
def send_otp_email(to_email, otp):
    try:
        msg = MIMEMultipart()
        msg["From"]    = GMAIL_ADDRESS
        msg["To"]      = to_email
        msg["Subject"] = "SentinelIQ — Email Verification OTP"
        body = f"""
SentinelIQ | Predict. Prevent. Protect.
─────────────────────────────────────────
Your Email Verification OTP:

        {otp}

Valid for 10 minutes. Do not share.
─────────────────────────────────────────
SentinelIQ v1.0 — MIT Academy of Engineering, Pune
"""
        msg.attach(MIMEText(body,"plain"))
        with smtplib.SMTP_SSL("smtp.gmail.com",465) as s:
            s.login(GMAIL_ADDRESS, GMAIL_PASSWORD)
            s.sendmail(GMAIL_ADDRESS, to_email, msg.as_string())
        return True
    except Exception as e:
        print(f"Email error: {e}")
        return False

def send_machine_alert(machine, data, to_email, to_name="Manager"):
    """Send alert to manager's registered email automatically."""
    p = data["prescription"]
    body = f"""
SentinelIQ | Predict. Prevent. Protect.
{'='*50}
MACHINE ALERT — Immediate Action Required
{'='*50}

Dear {to_name},

Your machine requires immediate attention:

Machine ID   : {machine['machine_id']}
Type         : {machine['machine_type']}
Factory      : {machine['factory_name']}
Location     : {machine['district']}, {machine['state']}
Status       : {p['priority']}
Health Score : {p['health_score']}/100
RUL          : {data['rul']['mean']:.1f} hours remaining
Top Failure  : {data['top_failure_mode']} ({data['top_probability']*100:.1f}%)
Action       : {p['recommended_action']}
Time         : {datetime.now().strftime('%d %b %Y %H:%M:%S')}

Please take immediate action to prevent breakdown.
─────────────────────────────────────────
SentinelIQ v1.0 — MIT Academy of Engineering, Pune
"""
    try:
        msg = MIMEMultipart()
        msg["From"]    = GMAIL_ADDRESS
        msg["To"]      = to_email
        msg["Subject"] = f"⚠️ ALERT — {machine['machine_id']} is {p['priority']}"
        msg.attach(MIMEText(body,"plain"))
        with smtplib.SMTP_SSL("smtp.gmail.com",465) as s:
            s.login(GMAIL_ADDRESS, GMAIL_PASSWORD)
            s.sendmail(GMAIL_ADDRESS, to_email, msg.as_string())
        log_alert(machine["machine_id"],p["priority"],data["rul"]["mean"],
                  data["top_failure_mode"],p["recommended_action"])
        return True
    except Exception as e:
        print(f"Alert email error: {e}")
        return False

# ════════════════════════════════════
# PREDICTION
# ════════════════════════════════════
def get_prediction(machine):
    ranges = get_sensor_ranges(machine.get("machine_type","Other"))
    sensor = {f:round(random.uniform(lo,hi),3) for f,(lo,hi) in ranges.items()}
    try:
        r = requests.post("http://127.0.0.1:5000/predict",
                          json={"machine_id":machine["machine_id"],"sensor_data":sensor},timeout=5)
        if r.status_code == 200: return r.json()
    except: pass
    return None

# ════════════════════════════════════
# CHARTS
# ════════════════════════════════════
BG = "rgba(0,0,0,0)"

def gauge(score):
    color = "#00cc66" if score>60 else "#ffaa00" if score>30 else "#ff4444"
    fig = go.Figure(go.Indicator(
        mode="gauge+number",value=score,
        number={"font":{"size":28,"color":color,"family":"Share Tech Mono"},"suffix":"%"},
        gauge={"axis":{"range":[0,100],"tickcolor":"#1e3a5f","tickfont":{"color":"#5a7a9a","size":9}},
               "bar":{"color":color},"bgcolor":"#0a1628","bordercolor":"#1e3a5f",
               "steps":[{"range":[0,30],"color":"#1a0a0a"},{"range":[30,60],"color":"#1a1200"},{"range":[60,100],"color":"#001a0d"}],
               "threshold":{"line":{"color":color,"width":3},"thickness":0.75,"value":score}}))
    fig.update_layout(height=175,margin=dict(l=10,r=10,t=25,b=5),paper_bgcolor=BG,plot_bgcolor=BG,font={"color":"#c8d8e8"})
    return fig

def rul_chart(history):
    fig = go.Figure()
    fig.add_trace(go.Scatter(y=history,mode="lines+markers",
        line=dict(color="#4da6ff",width=2),marker=dict(size=4,color="#4da6ff"),
        fill="tozeroy",fillcolor="rgba(77,166,255,0.07)"))
    fig.update_layout(height=140,margin=dict(l=5,r=5,t=5,b=5),paper_bgcolor=BG,plot_bgcolor=BG,
        xaxis=dict(showgrid=False,showticklabels=False),
        yaxis=dict(showgrid=True,gridcolor="#0d1f38",color="#5a7a9a",title="RUL"),showlegend=False)
    return fig

def prob_chart(breakdown):
    labels=[b["failure_mode"] for b in breakdown]
    values=[b["probability"]*100 for b in breakdown]
    colors=["#ff4444" if v==max(values) else "#1e3a5f" for v in values]
    fig=go.Figure(go.Bar(x=values,y=labels,orientation="h",marker_color=colors,
        text=[f"{v:.1f}%" for v in values],textposition="outside",textfont=dict(color="#c8d8e8",size=11)))
    fig.update_layout(height=160,margin=dict(l=5,r=55,t=5,b=5),paper_bgcolor=BG,plot_bgcolor=BG,
        xaxis=dict(showgrid=False,showticklabels=False,range=[0,130]),
        yaxis=dict(showgrid=False,color="#5a7a9a"),showlegend=False)
    return fig

# ════════════════════════════════════
# HEADER
# ════════════════════════════════════
def show_header(user):
    role_labels = {"superadmin":"SUPER ADMIN","state_admin":"STATE ADMIN","district_admin":"DISTRICT ADMIN","manager":"MANAGER"}
    loc=""
    if user.get("state"):    loc+=f" • {user['state']}"
    if user.get("district"): loc+=f" • {user['district']}"
    h1,h2,h3 = st.columns([2.5,4,1.5])
    with h1:
        st.markdown("<div style='padding-top:6px;'><span style='font-size:1.7rem;font-weight:700;color:#4da6ff;letter-spacing:3px;'>🛡️ SentinelIQ</span><br><span style='font-size:.65rem;color:#2a4a6a;letter-spacing:2px;'>PREDICT. PREVENT. PROTECT.</span></div>", unsafe_allow_html=True)
    with h2:
        st.markdown(f"<div style='text-align:center;padding-top:14px;'><span style='color:#5a7a9a;font-size:.76rem;'>🟢 LIVE &nbsp;•&nbsp; {datetime.now().strftime('%d %b %Y &nbsp; %H:%M:%S')} &nbsp;•&nbsp; <span style='color:#4da6ff;'>{user['name'].upper()}</span> [{role_labels.get(user['role'],'USER')}{loc}]</span></div>", unsafe_allow_html=True)
    with h3:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🚪 Logout",use_container_width=True):
            for k in list(st.session_state.keys()): del st.session_state[k]
            st.rerun()
    st.markdown("<hr style='border-color:#1e3a5f;margin:8px 0 18px 0;'>", unsafe_allow_html=True)

# ════════════════════════════════════
# NOTIFICATIONS
# ════════════════════════════════════
def show_notifications():
    if st.session_state.notifications:
        for notif in st.session_state.notifications[-3:]:
            color = "#ff4444" if notif["type"]=="CRITICAL" else "#ffaa00"
            st.markdown(f"""
            <div style='background:#1a0505;border:2px solid {color};border-radius:10px;padding:12px 18px;margin-bottom:8px;'>
                <span style='color:{color};font-weight:700;'>🔔 {notif["type"]}: {notif["machine_id"]}</span>
                <span style='color:#c8d8e8;font-size:.82rem;'> — {notif["message"]}</span>
                <span style='color:#5a7a9a;font-size:.72rem;float:right;'>{notif["time"]}</span>
            </div>""", unsafe_allow_html=True)

# ════════════════════════════════════
# GLOBAL SEARCH
# ════════════════════════════════════
def show_global_search():
    sc1,sc2 = st.columns([4,1])
    with sc1:
        search_id = st.text_input("Search",placeholder="🔍 Search any Machine ID — e.g. MH-PUN-FAC001-MCH001",
                                   key="global_search",label_visibility="collapsed")
    with sc2:
        search_btn = st.button("Search",use_container_width=True,key="global_search_btn")
    if search_btn and search_id:
        machine = get_machine_by_id(search_id.strip().upper())
        if machine:
            d = get_prediction(machine)
            if d:
                st.success(f"✅ Found: {search_id.upper()}")
                show_machine_card(machine,d,expanded=True)
            else:
                st.error("❌ Machine found but Flask API unreachable.")
        else:
            st.error(f"❌ Machine ID **{search_id.upper()}** not found in system.")
        return True
    return False

# ════════════════════════════════════
# MACHINE CARD
# ════════════════════════════════════
def show_machine_card(machine, data, expanded=True):
    p=data["prescription"]; priority=p["priority"]; health=p["health_score"]; rul=data["rul"]["mean"]
    symbol={"CRITICAL":"🔴","WARNING":"🟡","HEALTHY":"🟢"}[priority]; cls=priority.lower()
    mid=machine["machine_id"]
    top_mode=data.get("top_failure_mode","Unknown"); top_prob=data.get("top_probability",0)
    breakdown=data.get("failure_breakdown",[]); anom=data.get("anomaly_detection",{}); rca=data.get("root_cause_analysis",{})
    due_str=machine.get("next_service_due","N/A")
    try: overdue=datetime.strptime(due_str,"%Y-%m-%d")<datetime.now()
    except: overdue=False

    with st.expander(f"{symbol}  {mid}  —  {machine.get('machine_type','')}  |  {priority}  |  Health {health}/100  |  RUL {rul:.1f} hrs", expanded=expanded):
        c1,c2,c3,c4 = st.columns([1.1,1.5,1.6,1.8])
        with c1:
            st.plotly_chart(gauge(health),use_container_width=True,config={"displayModeBar":False},key=f"gauge_{mid}")
            badge_color={"CRITICAL":"#ff4444","WARNING":"#ffaa00","HEALTHY":"#00cc66"}[priority]
            badge_text={"CRITICAL":"#fff","WARNING":"#000","HEALTHY":"#000"}[priority]
            st.markdown(f"<div style='text-align:center;background:{badge_color};color:{badge_text};padding:4px 12px;border-radius:20px;font-size:.75rem;font-weight:700;'>{priority}</div>", unsafe_allow_html=True)
        with c2:
            st.markdown(f"""
            <div class='mlabel'>Machine ID</div><div class='mid-tag'>{mid}</div>
            <div class='mlabel' style='margin-top:12px;'>Supervised Learning — Gradient Boosting RUL</div>
            <div class='mval'>{rul:.1f} hrs</div>
            <div style='color:#5a7a9a;font-size:.72rem;margin-bottom:8px;'>95% CI: {data['rul']['lower']:.1f} – {data['rul']['upper']:.1f} hrs</div>
            <div class='mlabel'>Health Score</div>
            <div style='font-size:1.2rem;font-weight:700;color:#4da6ff;font-family:Share Tech Mono,monospace;'>{health}/100</div>
            <div class='action-box'>⚙️ {p['recommended_action']}</div>
            """, unsafe_allow_html=True)
        with c3:
            st.markdown("<div class='mlabel'>RUL Trend Over Time</div>", unsafe_allow_html=True)
            st.plotly_chart(rul_chart(st.session_state.history.get(mid,[rul])),use_container_width=True,config={"displayModeBar":False},key=f"rul_{mid}")
        with c4:
            st.markdown("<div class='mlabel'>Supervised Learning — Random Forest Failure Prediction</div>", unsafe_allow_html=True)
            st.plotly_chart(prob_chart(breakdown),use_container_width=True,config={"displayModeBar":False},key=f"prob_{mid}")

        st.markdown("<hr class='divider'>", unsafe_allow_html=True)

        a1,a2,a3 = st.columns(3)
        with a1:
            st.markdown(f"""
            <div class='algo-box'>
                <div class='algo-title'>🌲 Supervised Learning — Random Forest<br>Failure Classification</div>
                <div style='color:#ff8844;font-size:1.1rem;font-weight:700;'>{top_mode}</div>
                <div style='color:#5a7a9a;font-size:.78rem;margin-bottom:10px;'>Probability: {top_prob*100:.1f}%</div>
            """, unsafe_allow_html=True)
            for b in breakdown[:4]:
                bar_w=int(b["probability"]*100)
                color="#ff4444" if b["failure_mode"]==top_mode else "#1e3a5f"
                st.markdown(f"""
                <div style='margin-bottom:6px;'>
                    <div style='display:flex;justify-content:space-between;font-size:.75rem;'>
                        <span style='color:#c8d8e8;'>{b['failure_mode']}</span>
                        <span style='color:#5a7a9a;'>{b['probability']*100:.1f}%</span>
                    </div>
                    <div style='background:#0a1628;border-radius:4px;height:6px;margin-top:3px;'>
                        <div style='background:{color};width:{bar_w}%;height:6px;border-radius:4px;'></div>
                    </div>
                </div>""", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with a2:
            st.markdown('<div class="algo-box"><div class="algo-title">🤖 Unsupervised Learning — Autoencoder<br>Anomaly Detection</div>', unsafe_allow_html=True)
            if anom.get("available"):
                is_anom=anom.get("is_anomaly",False); score=anom.get("anomaly_score",0)
                anom_color="#ff4444" if is_anom else "#00cc66"
                st.markdown(f"""
                <div style='font-size:1.1rem;font-weight:700;color:{anom_color};'>{"⚠️ ANOMALY DETECTED" if is_anom else "✅ NORMAL BEHAVIOR"}</div>
                <div style='color:#5a7a9a;font-size:.78rem;margin-top:6px;'>Anomaly Score: <span style='color:#c8d8e8;'>{score}/100</span></div>
                <div style='color:#5a7a9a;font-size:.78rem;'>Recon Error: <span style='color:#c8d8e8;'>{anom.get('reconstruction_error',0):.6f}</span></div>
                <div style='background:#0a1628;border-radius:4px;height:8px;margin-top:10px;'>
                    <div style='background:{anom_color};width:{min(score,100)}%;height:8px;border-radius:4px;'></div>
                </div>
                <div style='color:#5a7a9a;font-size:.72rem;margin-top:4px;'>{anom.get("message","")}</div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("<div style='color:#5a7a9a;font-size:.82rem;margin-top:8px;'>Run: pip install tensorflow then retrain model.</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with a3:
            st.markdown('<div class="algo-box"><div class="algo-title">🔍 Explainable AI (XAI) — SHAP<br>Root Cause Analysis</div>', unsafe_allow_html=True)
            if rca.get("available"):
                st.markdown(f"<div style='color:#4da6ff;font-size:.8rem;margin-bottom:10px;font-weight:600;'>{rca.get('summary','')}</div>", unsafe_allow_html=True)
                rank_colors=["#ff4444","#ff8844","#ffaa00","#88aa44","#4da6ff"]
                for i,cause in enumerate(rca.get("root_causes",[])[:5]):
                    c=rank_colors[i] if i<len(rank_colors) else "#5a7a9a"
                    st.markdown(f"""
                    <div class='rca-item'>
                        <div style='display:flex;justify-content:space-between;'>
                            <span style='color:#c8d8e8;font-size:.8rem;font-weight:600;'>{cause['feature']}</span>
                            <span style='color:{c};font-size:.9rem;font-weight:700;'>{cause['contribution']}%</span>
                        </div>
                        <div style='color:#5a7a9a;font-size:.72rem;'>{cause['direction']}</div>
                        <div style='background:#0a1628;border-radius:3px;height:4px;margin-top:4px;'>
                            <div style='background:{c};width:{min(int(cause["contribution"]),100)}%;height:4px;border-radius:3px;'></div>
                        </div>
                    </div>""", unsafe_allow_html=True)
            else:
                st.markdown("<div style='color:#5a7a9a;font-size:.82rem;margin-top:8px;'>Run: pip install shap then retrain model.</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<hr class='divider'>", unsafe_allow_html=True)
        i1,i2,i3 = st.columns([1.5,1.5,1.2])
        with i1:
            st.markdown(f"""
            <div class='mcard mcard-{cls}'>
                <div class='mlabel' style='margin-bottom:8px;'>Machine Information</div>
                <div style='font-size:.83rem;line-height:1.9;'>
                    <span style='color:#5a7a9a;'>Factory  :</span> {machine.get('factory_name','')}<br>
                    <span style='color:#5a7a9a;'>Location :</span> {machine.get('district','')}, {machine.get('state','')}<br>
                    <span style='color:#5a7a9a;'>Type     :</span> {machine.get('machine_type','')}<br>
                    <span style='color:#5a7a9a;'>Installed:</span> {machine.get('installation_date','N/A')}<br>
                    <span style='color:#5a7a9a;'>Read at  :</span> {datetime.now().strftime('%d %b %Y %H:%M')}
                </div>
            </div>""", unsafe_allow_html=True)
        with i2:
            st.markdown(f"""
            <div class='mcard'>
                <div class='mlabel' style='margin-bottom:8px;'>Maintenance History</div>
                <div style='font-size:.83rem;line-height:1.9;'>
                    <span style='color:#5a7a9a;'>Last Service :</span> {machine.get('last_service','N/A')}<br>
                    <span style='color:#5a7a9a;'>Next Due     :</span>
                    <span style='color:{"#ff4444" if overdue else "#00cc66"};'>{"⚠️ OVERDUE " if overdue else ""}{due_str}</span><br>
                    <span style='color:#5a7a9a;'>RUL          :</span> {rul:.1f} hours<br>
                    <span style='color:#5a7a9a;'>Health Score :</span> {health}/100
                </div>
            </div>""", unsafe_allow_html=True)
        with i3:
            st.markdown("<div class='mlabel' style='margin-bottom:8px;'>Send Manual Alert</div>", unsafe_allow_html=True)
            # show manager email info
            mgr = get_manager_email_for_machine(mid)
            if mgr:
                st.markdown(f"<div style='color:#5a7a9a;font-size:.72rem;margin-bottom:6px;'>Auto alert → {mgr['email']}</div>", unsafe_allow_html=True)
            alert_email = st.text_input("Send to",key=f"email_{mid}",placeholder="other@email.com",label_visibility="collapsed")
            if st.button(f"📧 Send Alert",key=f"btn_{mid}",use_container_width=True):
                target = alert_email if alert_email else (mgr["email"] if mgr else None)
                if not target: st.warning("Enter recipient email.")
                else:
                    ok = send_machine_alert(machine,data,target, mgr["name"] if mgr else "Manager")
                    st.success(f"✅ Alert sent to {target}!") if ok else st.error("❌ Failed. Check Gmail credentials in dashboard.py")

# ════════════════════════════════════
# LOGIN PAGE
# ════════════════════════════════════
def show_login():
    st.markdown("<div class='login-wrap'><div class='brand-big'>🛡️ SentinelIQ</div><div class='brand-tag'>PREDICT. PREVENT. PROTECT.</div></div>", unsafe_allow_html=True)
    c1,c2,c3 = st.columns([1,2,1])
    with c2:
        tab1,tab2 = st.tabs(["🔐 Login","📝 Register as Manager"])

        # ── LOGIN ──
        with tab1:
            st.markdown("<br>", unsafe_allow_html=True)
            role = st.selectbox("Select Your Role",
                ["-- Select Role --","Super Admin","State Admin","District Admin","Manager"],
                key="login_role")

            sel_state = sel_district = username = password = None

            if role == "Super Admin":
                st.markdown("<div class='info-tag'>🔑 Super Admin — Full India access</div>", unsafe_allow_html=True)
                username = st.text_input("Username", placeholder="Enter username", key="l_user")
                password = st.text_input("Password", type="password", placeholder="Enter password", key="l_pass")

            elif role == "State Admin":
                sel_state = st.selectbox("Select Your State", ["-- Select State --"]+get_all_states(), key="l_state")
                if sel_state != "-- Select State --":
                    st.markdown(f"<div class='info-tag'>📍 Managing all districts in {sel_state}</div>", unsafe_allow_html=True)
                username = st.text_input("Username", placeholder="Enter username", key="l_user")
                password = st.text_input("Password", type="password", placeholder="Enter password", key="l_pass")

            elif role == "District Admin":
                sel_state = st.selectbox("Select Your State", ["-- Select State --"]+get_all_states(), key="l_state")
                if sel_state and sel_state != "-- Select State --":
                    sel_district = st.selectbox("Select Your District", ["-- Select District --"]+get_districts(sel_state), key="l_dist")
                    if sel_district and sel_district != "-- Select District --":
                        st.markdown(f"<div class='info-tag'>🏙️ Managing {sel_district}, {sel_state}</div>", unsafe_allow_html=True)
                username = st.text_input("Username", placeholder="Enter username", key="l_user")
                password = st.text_input("Password", type="password", placeholder="Enter password", key="l_pass")

            elif role == "Manager":
                sel_state = st.selectbox("Select Your State", ["-- Select State --"]+get_all_states(), key="l_state")
                if sel_state and sel_state != "-- Select State --":
                    sel_district = st.selectbox("Select Your District", ["-- Select District --"]+get_districts(sel_state), key="l_dist")
                username = st.text_input("Username", placeholder="Enter username", key="l_user")
                password = st.text_input("Password", type="password", placeholder="Enter password", key="l_pass")

            st.markdown("<br>", unsafe_allow_html=True)

            if st.button("🔐  LOGIN →", use_container_width=True, key="login_btn"):
                if role == "-- Select Role --":
                    st.error("❌ Please select your role first.")
                elif not username or not password:
                    st.error("❌ Please enter username and password.")
                else:
                    user = verify_login(username, password)
                    if user:
                        role_map = {"Super Admin":"superadmin","State Admin":"state_admin","District Admin":"district_admin","Manager":"manager"}
                        if user["role"] != role_map[role]:
                            st.error(f"❌ Role mismatch. Your account role is not {role}.")
                        else:
                            st.session_state.logged_in = True
                            st.session_state.user = user
                            st.rerun()
                    else:
                        st.error("❌ Incorrect username or password. Please try again.")

            st.markdown("<div style='text-align:center;color:#1e3a5f;font-size:.7rem;margin-top:14px;'>SentinelIQ v1.0 • MIT Academy of Engineering, Pune</div>", unsafe_allow_html=True)

        # ── REGISTER WITH OTP ──
        with tab2:
            st.markdown("<div style='color:#5a7a9a;font-size:.75rem;margin-bottom:10px;'>Register your factory. Email OTP verification required.</div>", unsafe_allow_html=True)

            if st.session_state.reg_step == 1:
                r_name    = st.text_input("Full Name",       placeholder="e.g. Rajesh Kumar",          key="r_name")
                r_user    = st.text_input("Choose Username", placeholder="e.g. rajesh_pune",            key="r_user")
                r_pass    = st.text_input("Password",        type="password", placeholder="Min 6 chars", key="r_pass")
                r_email   = st.text_input("Email Address",   placeholder="your@email.com",              key="r_email")
                r_state   = st.selectbox("Select State",     ["-- Select --"]+get_all_states(),          key="r_state")
                r_dist    = None
                if r_state != "-- Select --":
                    r_dist = st.selectbox("Select District", ["-- Select --"]+get_districts(r_state),   key="r_dist")
                r_factory = st.text_input("Factory Name",    placeholder="e.g. Pune Precision Parts",   key="r_factory")
                r_mtype   = st.selectbox("Machine Type",     ["-- Select --"]+get_machine_types(),       key="r_mtype")

                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("📧 Send OTP to Email", use_container_width=True, key="send_otp_btn"):
                    errors = []
                    if not all([r_name,r_user,r_pass,r_email,r_factory]): errors.append("Please fill all fields.")
                    if r_state=="-- Select --" or not r_dist or r_dist=="-- Select --": errors.append("Select State and District.")
                    if r_mtype=="-- Select --": errors.append("Select Machine Type.")
                    if len(r_pass or "")<6: errors.append("Password min 6 characters.")
                    if errors:
                        for e in errors: st.error(e)
                    else:
                        st.session_state.reg_form_data = {
                            "name":r_name,"username":r_user,"password":r_pass,
                            "email":r_email,"state":r_state,"district":r_dist,
                            "factory":r_factory,"mtype":r_mtype
                        }
                        otp = generate_otp()
                        save_otp(r_email, otp)
                        ok  = send_otp_email(r_email, otp)
                        st.session_state.reg_email = r_email
                        st.session_state.reg_step  = 2
                        if ok:
                            st.success(f"✅ OTP sent to {r_email}! Check your inbox.")
                        else:
                            print(f"\n>>> OTP for {r_email}: {otp} <<<\n")
                            st.warning("⚠️ Gmail not configured. OTP printed in terminal for testing.")
                        st.rerun()

            elif st.session_state.reg_step == 2:
                st.markdown(f"<div class='otp-box'><div style='color:#4da6ff;'>📧 OTP sent to <b>{st.session_state.reg_email}</b><br><span style='color:#5a7a9a;font-size:.75rem;'>Check inbox. Valid 10 minutes.</span></div></div>", unsafe_allow_html=True)
                entered_otp = st.text_input("Enter 6-digit OTP", placeholder="e.g. 492817", key="otp_input", max_chars=6)
                c1,c2 = st.columns(2)
                with c1:
                    if st.button("✅ Verify & Create Account", use_container_width=True, key="verify_btn"):
                        if not entered_otp: st.error("Enter OTP.")
                        else:
                            ok, msg = verify_otp(st.session_state.reg_email, entered_otp)
                            if ok:
                                fd = st.session_state.reg_form_data
                                mid, result = create_user(fd["name"],fd["username"],fd["password"],
                                    "manager",fd["state"],fd["district"],fd["factory"],fd["mtype"],
                                    fd["email"],email_verified=1)
                                if result == "Success":
                                    st.success("✅ Account created!")
                                    st.markdown(f"""
                                    <div style='background:#0d2040;border:1px solid #4da6ff;border-radius:8px;padding:16px;text-align:center;margin-top:10px;'>
                                        <div style='color:#5a7a9a;font-size:.75rem;margin-bottom:6px;'>YOUR MACHINE ID</div>
                                        <div style='color:#4da6ff;font-family:Share Tech Mono,monospace;font-size:1.2rem;font-weight:700;'>{mid}</div>
                                        <div style='color:#5a7a9a;font-size:.72rem;margin-top:6px;'>Save this! Go to Login tab.</div>
                                    </div>""", unsafe_allow_html=True)
                                    st.session_state.reg_step = 1
                                    st.session_state.reg_form_data = {}
                                else:
                                    st.error(f"❌ {result}")
                            else:
                                st.error(f"❌ {msg}")
                with c2:
                    if st.button("🔄 Resend OTP", use_container_width=True, key="resend_btn"):
                        otp = generate_otp()
                        save_otp(st.session_state.reg_email, otp)
                        ok  = send_otp_email(st.session_state.reg_email, otp)
                        print(f"\n>>> New OTP for {st.session_state.reg_email}: {otp} <<<\n")
                        st.success("New OTP sent!" if ok else "OTP printed in terminal.")
                if st.button("← Back to Form", key="back_btn"):
                    st.session_state.reg_step = 1
                    st.rerun()

# ════════════════════════════════════
# ADMIN MANAGE TAB
# ════════════════════════════════════
def show_manage_tab(user):
    role = user["role"]
    if role == "superadmin":
        create_role  = "state_admin"
        create_label = "State Admin"
        existing     = get_users_by_role("state_admin")
    elif role == "state_admin":
        create_role  = "district_admin"
        create_label = "District Admin"
        existing     = get_users_by_role("district_admin", state=user["state"])
    else:
        create_role  = "manager"
        create_label = "Factory Manager"
        existing     = get_users_by_role("manager", state=user["state"], district=user["district"])

    st.markdown(f"<div style='color:#4da6ff;font-size:.95rem;font-weight:700;margin-bottom:14px;'>➕ Add New {create_label}</div>", unsafe_allow_html=True)

    f1,f2 = st.columns(2)
    new_state = new_dist = new_factory = new_mtype = None

    with f1:
        new_name  = st.text_input("Full Name",    key="new_name",  placeholder="Full name")
        new_user  = st.text_input("Username",     key="new_user",  placeholder="e.g. amit_mh")
        new_email = st.text_input("Email",        key="new_email", placeholder="Email address")

    with f2:
        new_pass = st.text_input("Password", type="password", key="new_pass", placeholder="Min 6 chars")

        # Super Admin → must select State for State Admin
        if create_role == "state_admin":
            new_state = st.selectbox("Select State for this Admin",
                ["-- Select State --"] + get_all_states(), key="new_state")
            if new_state and new_state != "-- Select State --":
                # check if already exists
                exists_users = get_users_by_role("state_admin", state=new_state)
                if exists_users:
                    st.error(f"❌ State Admin for {new_state} already exists: {exists_users[0]['name']}. Only one State Admin per state allowed.")

        # State Admin → State fixed, must select District for District Admin
        elif create_role == "district_admin":
            new_state = user["state"]
            st.markdown(f"<div class='info-tag'>📍 State: {new_state}</div>", unsafe_allow_html=True)
            new_dist = st.selectbox("Select District for this Admin",
                ["-- Select District --"] + get_districts(new_state), key="new_dist")
            if new_dist and new_dist != "-- Select District --":
                # check if already exists
                exists_users = get_users_by_role("district_admin", state=new_state, district=new_dist)
                if exists_users:
                    st.error(f"❌ District Admin for {new_dist} already exists: {exists_users[0]['name']}. Only one District Admin per district allowed.")

        # District Admin → State+District fixed, enter factory details
        elif create_role == "manager":
            new_state = user["state"]
            new_dist  = user["district"]
            st.markdown(f"<div class='info-tag'>📍 {new_state} &nbsp;|&nbsp; 🏙️ {new_dist}</div>", unsafe_allow_html=True)
            new_factory = st.text_input("Factory Name", key="new_factory", placeholder="e.g. Pune Precision Parts")
            new_mtype   = st.selectbox("Machine Type",  ["-- Select --"]+get_machine_types(), key="new_mtype")

    st.markdown("<br>", unsafe_allow_html=True)

    if st.button(f"➕ Create {create_label}", use_container_width=True, key="create_btn"):
        errors = []
        if not all([new_name,new_user,new_pass]): errors.append("Fill all required fields.")
        if len(new_pass or "") < 6: errors.append("Password must be at least 6 characters.")
        if create_role == "state_admin" and (not new_state or new_state=="-- Select State --"):
            errors.append("Please select a State.")
        if create_role == "district_admin" and (not new_dist or new_dist=="-- Select District --"):
            errors.append("Please select a District.")
        if create_role == "manager" and not new_factory:
            errors.append("Please enter Factory Name.")
        if create_role == "manager" and (not new_mtype or new_mtype=="-- Select --"):
            errors.append("Please select Machine Type.")

        if errors:
            for e in errors: st.error(e)
        else:
            result, msg = create_user(
                new_name, new_user, new_pass, create_role,
                new_state, new_dist, new_factory,
                new_mtype if new_mtype and new_mtype!="-- Select --" else None,
                new_email, email_verified=1
            )
            if msg == "Success":
                st.success(f"✅ {create_label} '{new_name}' created successfully!")
                if create_role == "manager":
                    st.markdown(f"""
                    <div style='background:#0d2040;border:1px solid #4da6ff;border-radius:8px;padding:12px;text-align:center;margin-top:8px;'>
                        <div style='color:#5a7a9a;font-size:.75rem;'>Machine ID Assigned</div>
                        <div style='color:#4da6ff;font-family:Share Tech Mono,monospace;font-size:1.1rem;font-weight:700;'>{result}</div>
                    </div>""", unsafe_allow_html=True)
            else:
                st.error(msg)

    # Existing users list
    st.markdown("<hr class='divider'>", unsafe_allow_html=True)
    st.markdown(f"<div style='color:#4da6ff;font-size:.9rem;font-weight:700;margin-bottom:12px;'>📋 Existing {create_label}s ({len(existing)})</div>", unsafe_allow_html=True)
    if not existing:
        st.markdown("<div style='color:#5a7a9a;font-size:.85rem;padding:20px;text-align:center;'>No users created yet.</div>", unsafe_allow_html=True)
    else:
        for u in existing:
            loc=""
            if u.get("state"):        loc+=f" • {u['state']}"
            if u.get("district"):     loc+=f" • {u['district']}"
            if u.get("factory_name"): loc+=f" • {u['factory_name']}"
            verified = "✅ Verified" if u.get("email_verified") else "⚠️ Unverified"
            st.markdown(f"""
            <div class='user-row'>
                <span style='color:#4da6ff;font-weight:700;'>{u['name']}</span>
                <span style='color:#5a7a9a;'> @{u['username']}</span>
                <span style='color:#3a6a9a;font-size:.75rem;'>{loc}</span><br>
                <span style='color:#5a7a9a;font-size:.72rem;'>{u.get('email','')} &nbsp;|&nbsp; {verified} &nbsp;|&nbsp; Joined {u.get('created_at','')[:10]}</span>
            </div>""", unsafe_allow_html=True)

# ════════════════════════════════════
# MACHINES STATUS TAB
# ════════════════════════════════════
def show_machines_tab(user, results):
    if results:
        total=len(results)
        critical=sum(1 for _,d in results.values() if d["prescription"]["priority"]=="CRITICAL")
        warning=sum(1 for _,d in results.values() if d["prescription"]["priority"]=="WARNING")
        healthy=total-critical-warning
        sc1,sc2,sc3,sc4=st.columns(4)
        for col,label,val,color in [(sc1,"Total Machines",total,"#4da6ff"),(sc2,"🔴 Critical",critical,"#ff4444"),(sc3,"🟡 Warning",warning,"#ffaa00"),(sc4,"🟢 Healthy",healthy,"#00cc66")]:
            with col:
                st.markdown(f"<div class='mcard' style='text-align:center;'><div class='mlabel'>{label}</div><div style='font-size:2rem;font-weight:700;color:{color};font-family:Share Tech Mono,monospace;'>{val}</div></div>", unsafe_allow_html=True)
        st.markdown("<hr class='divider'>", unsafe_allow_html=True)
        grouped={}
        for mid,(m,d) in results.items():
            grouped.setdefault(m["state"],{}).setdefault(m["district"],{}).setdefault(m["factory_name"],[]).append((m,d))
        for state in sorted(grouped.keys()):
            st.markdown(f"<div style='font-size:1rem;font-weight:700;color:#4da6ff;margin:16px 0 8px;letter-spacing:2px;'>📍 {state.upper()}</div>", unsafe_allow_html=True)
            for district in sorted(grouped[state].keys()):
                st.markdown(f"<div style='font-size:.85rem;color:#5a7a9a;margin:8px 0 6px 16px;'>🏙️ {district}</div>", unsafe_allow_html=True)
                for factory in sorted(grouped[state][district].keys()):
                    st.markdown(f"<div style='font-size:.8rem;color:#3a6a9a;margin:4px 0 8px 32px;'>🏭 {factory}</div>", unsafe_allow_html=True)
                    for m,d in grouped[state][district][factory]:
                        show_machine_card(m,d,expanded=False)
    else:
        st.markdown("<div style='text-align:center;padding:40px;color:#5a7a9a;'>No machines registered yet.</div>", unsafe_allow_html=True)

# ════════════════════════════════════
# CHATBOT TAB
# ════════════════════════════════════
def show_chatbot_tab():
    st.markdown("<div class='section-hdr'>🤖 SentinelIQ AI Assistant</div>", unsafe_allow_html=True)
    st.markdown("<div style='color:#5a7a9a;font-size:.82rem;margin-bottom:16px;'>Ask anything about your machines or industrial maintenance.</div>", unsafe_allow_html=True)
    cols = st.columns(4)
    for i,q in enumerate(SUGGESTED_QUESTIONS[:8]):
        with cols[i%4]:
            if st.button(q,key=f"sq_{i}",use_container_width=True):
                st.session_state.chat_history.append({"role":"user","content":q})
                with st.spinner("Thinking..."):
                    answer = ask_chatbot(q,st.session_state.machines_data,st.session_state.chat_history)
                st.session_state.chat_history.append({"role":"assistant","content":answer})
                speak_chatbot_response(answer)
                st.rerun()
    st.markdown("<hr class='divider'>", unsafe_allow_html=True)
    for msg in st.session_state.chat_history:
        if msg["role"]=="user":
            st.markdown(f"<div class='chat-label-user'>You</div><div style='display:flex;justify-content:flex-end;'><div class='chat-user'>{msg['content']}</div></div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='chat-label-ai'>🛡️ SentinelIQ AI</div><div class='chat-ai'>{msg['content']}</div>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    q1,q2 = st.columns([5,1])
    with q1:
        user_q = st.text_input("Ask...",key="chat_input",placeholder="e.g. Why is MCH-003 critical? What causes bearing failure?",label_visibility="collapsed")
    with q2:
        send = st.button("Ask 🎤",use_container_width=True,key="chat_send")
    if send and user_q:
        st.session_state.chat_history.append({"role":"user","content":user_q})
        with st.spinner("SentinelIQ AI is thinking..."):
            answer = ask_chatbot(user_q,st.session_state.machines_data,st.session_state.chat_history)
        st.session_state.chat_history.append({"role":"assistant","content":answer})
        speak_chatbot_response(answer)
        st.rerun()
    if st.button("🗑️ Clear Chat",key="clear_chat"):
        st.session_state.chat_history = []
        st.rerun()

# ════════════════════════════════════
# FEDERATED LEARNING TAB
# ════════════════════════════════════
def show_federated_tab():
    st.markdown("<div class='section-hdr'>🌐 Federated Learning — Privacy Preserving AI</div>", unsafe_allow_html=True)
    results = load_federated_results()
    if not results:
        st.markdown("<div class='fed-box'><div style='color:#4da6ff;font-size:.9rem;font-weight:700;margin-bottom:10px;'>Run Federated Learning First</div><div style='color:#5a7a9a;font-size:.82rem;'>Open terminal and run:</div><div style='color:#4da6ff;font-family:Share Tech Mono,monospace;font-size:.9rem;margin-top:8px;'>python federated_learning.py</div></div>", unsafe_allow_html=True)
        return
    st.markdown(f"""<div class='fed-box'><div style='display:flex;gap:40px;flex-wrap:wrap;'>
        <div><div class='mlabel'>Factories</div><div class='mval'>{results['n_factories']}</div></div>
        <div><div class='mlabel'>Total Samples</div><div class='mval'>{results['total_samples']}</div></div>
        <div><div class='mlabel'>Classifier Accuracy</div><div class='mval' style='color:#00cc66;'>{results['agg_clf_score']:.1%}</div></div>
        <div><div class='mlabel'>Regressor R²</div><div class='mval' style='color:#00cc66;'>{results['agg_reg_score']:.1%}</div></div>
        <div><div class='mlabel'>Privacy</div><div style='color:#00cc66;font-size:1rem;font-weight:700;'>✅ Preserved</div></div>
    </div></div>""", unsafe_allow_html=True)
    for fs in results.get("factory_scores",[]):
        st.markdown(f"""<div class='mcard' style='padding:12px 18px;'>
            <div style='display:flex;justify-content:space-between;align-items:center;'>
                <span style='color:#4da6ff;font-weight:700;'>Factory {fs['factory_id']}</span>
                <span style='color:#5a7a9a;font-size:.78rem;'>Classifier: <span style='color:#c8d8e8;'>{fs['clf_score']:.1%}</span> &nbsp;|&nbsp; Regressor R²: <span style='color:#c8d8e8;'>{fs['reg_score']:.1%}</span></span>
            </div>
            <div style='background:#0a1628;border-radius:4px;height:6px;margin-top:8px;'><div style='background:#4da6ff;width:{fs['clf_score']*100:.0f}%;height:6px;border-radius:4px;'></div></div>
        </div>""", unsafe_allow_html=True)

# ════════════════════════════════════
# HISTORY TAB
# ════════════════════════════════════
def show_history_tab():
    st.markdown("<div class='section-hdr'>Machine Alert History</div>", unsafe_allow_html=True)
    search = st.text_input("Enter Machine ID", placeholder="e.g. MH-PUN-FAC001-MCH001", key="hist_search")
    if st.button("🔍 Search History", key="hist_btn"):
        if not search: st.warning("Enter a Machine ID.")
        else:
            machine = get_machine_by_id(search.strip().upper())
            if not machine: st.error("❌ Machine ID not found.")
            else:
                alerts = get_alerts_for_machine(search.strip().upper())
                st.markdown(f"<div style='color:#4da6ff;font-size:.9rem;font-weight:700;margin:12px 0;'>Machine: {search.upper()} — {machine.get('machine_type','')} — {machine.get('factory_name','')}</div>", unsafe_allow_html=True)
                if not alerts: st.info("No alert history found.")
                else:
                    for a in alerts:
                        color={"CRITICAL":"#ff4444","WARNING":"#ffaa00","HEALTHY":"#00cc66"}.get(a["priority"],"#4da6ff")
                        st.markdown(f"""<div class='mcard'>
                            <div style='display:flex;justify-content:space-between;'>
                                <span style='color:{color};font-weight:700;'>{a['priority']}</span>
                                <span style='color:#5a7a9a;font-size:.75rem;'>{a['sent_at']}</span>
                            </div>
                            <div style='font-size:.83rem;margin-top:6px;'>
                                <span style='color:#5a7a9a;'>RUL:</span> {a['rul']:.1f} hrs &nbsp;
                                <span style='color:#5a7a9a;'>Failure:</span> {a['failure_mode']} &nbsp;
                                <span style='color:#5a7a9a;'>Action:</span> {a['action']}
                            </div></div>""", unsafe_allow_html=True)

# ════════════════════════════════════
# MAIN DASHBOARD
# ════════════════════════════════════
def show_dashboard():
    user = st.session_state.user
    role = user["role"]
    show_header(user)
    searched = show_global_search()
    if searched: return

    machines = get_machines_for_user(user)
    results  = {}
    for m in machines:
        mid = m["machine_id"]
        d   = get_prediction(m)
        if d:
            results[mid] = (m,d)
            st.session_state.machines_data[mid] = {"machine":m,"data":d}
            if mid not in st.session_state.history: st.session_state.history[mid] = []
            st.session_state.history[mid].append(d["rul"]["mean"])
            if len(st.session_state.history[mid])>30: st.session_state.history[mid].pop(0)

            priority = d["prescription"]["priority"]
            if priority == "CRITICAL" and mid not in st.session_state.alerted:
                # add notification
                st.session_state.notifications.append({
                    "type":"CRITICAL","machine_id":mid,
                    "message":f"RUL {d['rul']['mean']:.0f} hrs — {d['top_failure_mode']}",
                    "time":datetime.now().strftime("%H:%M:%S")
                })
                # voice alert
                speak_critical_alert(mid,d["top_failure_mode"],d["rul"]["mean"],d["prescription"]["recommended_action"])
                # auto email to manager
                mgr = get_manager_email_for_machine(mid)
                if mgr and mgr.get("email"):
                    ok = send_machine_alert(m,d,mgr["email"],mgr["name"])
                    print(f"Auto alert {'sent' if ok else 'failed'} to manager {mgr['name']} ({mgr['email']})")
                st.session_state.alerted.add(mid)

            elif priority == "WARNING" and mid+"_w" not in st.session_state.alerted:
                st.session_state.notifications.append({
                    "type":"WARNING","machine_id":mid,
                    "message":f"RUL {d['rul']['mean']:.0f} hrs — schedule maintenance",
                    "time":datetime.now().strftime("%H:%M:%S")
                })
                speak_warning_alert(mid,d["top_failure_mode"],d["rul"]["mean"])
                # auto email to manager
                mgr = get_manager_email_for_machine(mid)
                if mgr and mgr.get("email"):
                    send_machine_alert(m,d,mgr["email"],mgr["name"])
                st.session_state.alerted.add(mid+"_w")

    show_notifications()

    if role in ("superadmin","state_admin","district_admin"):
        tab1,tab2,tab3,tab4 = st.tabs(["👥 Manage Users","🖥️ Machine Status","🤖 AI Chatbot","🌐 Federated Learning"])
        with tab1: show_manage_tab(user)
        with tab2: show_machines_tab(user,results)
        with tab3: show_chatbot_tab()
        with tab4: show_federated_tab()
    else:
        tab1,tab2,tab3,tab4 = st.tabs(["📊 Live Status","🤖 AI Chatbot","🕐 History","🌐 Federated Learning"])
        with tab1:
            if not results: st.error("❌ Cannot reach Flask API. Make sure app.py is running.")
            else:
                st.markdown("<div class='section-hdr'>Your Machines — Sorted by RUL (Most Critical First)</div>", unsafe_allow_html=True)
                for m,d in sorted(results.values(),key=lambda x:x[1]["rul"]["mean"]):
                    show_machine_card(m,d,expanded=True)
                crits=[m["machine_id"] for m,d in results.values() if d["prescription"]["priority"]=="CRITICAL"]
                if crits: st.error(f"🚨 CRITICAL: {', '.join(crits)} needs immediate attention!")
        with tab2: show_chatbot_tab()
        with tab3: show_history_tab()
        with tab4: show_federated_tab()

    st.markdown("<div style='color:#1e3a5f;font-size:.66rem;text-align:right;'>⟳ Auto-refreshes every 5 seconds</div>", unsafe_allow_html=True)
    time.sleep(5)
    st.rerun()

# ════════════════════════════════════
# ENTRY POINT
# ════════════════════════════════════
if not st.session_state.logged_in:
    show_login()
else:
    show_dashboard()
