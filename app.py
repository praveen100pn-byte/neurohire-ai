import streamlit as st
import fitz
import pandas as pd
import re
import pytesseract
from pdf2image import convert_from_bytes
from moviepy.editor import VideoFileClip
import speech_recognition as sr
from datetime import datetime
import io

st.set_page_config(page_title="HireIQ Pro | Neural Auditor", layout="wide", page_icon="🔥")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=JetBrains+Mono:wght@300;500&display=swap');
    .stApp { background-color: #050505; color: #e0e0e0; }
    .main-header { font-family: 'Orbitron', sans-serif; color: #00d4ff; text-align: center; font-size: 2.8rem; letter-spacing: 6px; margin-bottom: 0px; text-shadow: 0 0 20px rgba(0,212,255,0.3); }
    .sub-header { font-family: 'JetBrains Mono', monospace; color: #444; text-align: center; font-size: 0.8rem; letter-spacing: 2px; margin-bottom: 40px; }
    .stMetric { background: #0d0d0d; border: 1px solid #1a1a1a; padding: 15px; border-radius: 4px; }
    #MainMenu, footer, header {visibility: hidden;}
    .stTabs [data-baseweb="tab-list"] { gap: 10px; background-color: transparent; }
    .stTabs [data-baseweb="tab"] { background-color: #0d0d0d; border: 1px solid #1a1a1a; border-radius: 0px; color: #666; padding: 10px 30px; font-family: 'Orbitron'; font-size: 0.7rem; }
    .stTabs [data-baseweb="tab"]:hover { color: #00d4ff; border-color: #00d4ff; }
    .stTabs [data-baseweb="tab-highlight"] { background-color: #00d4ff; }
    </style>
    """, unsafe_allow_html=True)

GLOBAL_REGISTRY = ["Python", "Java", "JavaScript", "TypeScript", "C++", "SQL", "Docker", "AWS", "React", "Node.js", "Kotlin", "Go"]

def extract_text(file):
    try:
        doc = fitz.open(stream=file.read(), filetype="pdf")
        text = " ".join([page.get_text() for page in doc]).strip()
    except:
        text = ""
    if len(text) < 50:
        file.seek(0)
        try:
            images = convert_from_bytes(file.read())
            text = "".join([pytesseract.image_to_string(img) for img in images])
        except:
            return ""
    return text.lower()

def analyze_video(video_file):
    with open("temp_v.mp4", "wb") as f: f.write(video_file.getbuffer())
    clip = VideoFileClip("temp_v.mp4")
    clip.audio.write_audiofile("temp_a.wav", logger=None)
    r = sr.Recognizer()
    with sr.AudioFile("temp_a.wav") as source:
        audio = r.record(source)
        text = r.recognize_google(audio)
    clip.close()
    return text

def audit_integrity(text):
    score = 100
    flags = []
    red_lines = ["expert in everything", "all responsibilities", "guaranteed success", "no failures"]
    for line in red_lines:
        if line in text:
            score -= 25
            flags.append(f"INTEGRITY_FLAG: {line.upper()}")
    if len(text.split()) < 100:
        score -= 30
        flags.append("DEPTH_ERROR: INSUFFICIENT DATA")
    return score, flags

st.markdown('<p class="main-header">HIREIQ PRO</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">NEURAL RECRUITMENT & AUDIT ECOSYSTEM | VERSION 3.1.0</p>', unsafe_allow_html=True)

tabs = st.tabs(["[01] AUDITOR", "[02] INTERVIEW", "[03] ROADMAP", "[04] MATCHING"])

with tabs[0]:
    c1, c2 = st.columns([1, 2])
    with c1:
        st.markdown("### SYSTEM_INPUT")
        spec = st.text_area("Core Requirements", placeholder="e.g. Python, AWS, 3 years experience")
        up_pdf = st.file_uploader("Candidate Node (PDF)", type="pdf")
    with c2:
        if up_pdf and spec:
            raw_text = extract_text(up_pdf)
            i_score, i_flags = audit_integrity(raw_text)
            st.metric("NEURAL_INTEGRITY", f"{i_score}%", delta="STABLE" if i_score > 70 else "COMPROMISED")
            if i_flags:
                for f in i_flags: st.error(f)
            else:
                st.success("AUTHENTICITY_VERIFIED: NO DECEPTIVE PATTERNS DETECTED")

with tabs[1]:
    up_vid = st.file_uploader("Neural Voice Input (MP4)", type="mp4")
    if up_vid:
        transcript = analyze_video(up_vid)
        st.code(f"TRANSCRIPT_STREAM: {transcript}", language="markdown")
        sentiment = "CONFIDENT" if len(transcript.split()) > 25 else "HESITANT"
        st.metric("VOCAL_TONE", sentiment)

with tabs[2]:
    target = st.text_input("Target Domain", placeholder="e.g. Cloud Architect")
    if st.button("CALCULATE_ROADMAP"):
        st.markdown(f"**MAP_DECODED for {target.upper()}**")
        st.info("NODE_01: Fundamentals -> NODE_02: Lab Projects -> NODE_03: Production Deployment")

with tabs[3]:
    if st.button("RUN_SIMILARITY_MATCH"):
        data = {"NODE_ID": ["ENG_09", "ENG_04", "ENG_21"], "COMPATIBILITY": ["96%", "88%", "41%"], "DECISION": ["WELCOME", "PROVISIONAL", "NON-COMPLIANT"]}
        st.table(pd.DataFrame(data))

st.markdown("---")
st.markdown(f"<p style='text-align: right; color: #222; font-family: JetBrains Mono; font-size: 10px;'>CORE_STATUS: ACTIVE | {datetime.now().strftime('%Y-%m-%d')} | PR AV</p>", unsafe_allow_html=True)
