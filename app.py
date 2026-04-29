import os
os.environ["TRANSFORMERS_NO_TORCHVISION"] = "1"
os.environ["STREAMLIT_WATCHER_TYPE"] = "none"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import streamlit as st
import PyPDF2
from sentence_transformers import SentenceTransformer, util
import pandas as pd
import re
import sqlite3
import datetime
from io import BytesIO
from reportlab.pdfgen import canvas

# ---------------- APP ---------------- #
st.set_page_config(page_title="NeuroHire AI", layout="wide")

# ---------------- DATABASE ---------------- #
db_path = os.path.join(os.getcwd(), "neurohire.db")
conn = sqlite3.connect(db_path, check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user TEXT,
    candidate TEXT,
    score REAL,
    tier TEXT,
    decision TEXT,
    timestamp TEXT
)
""")
conn.commit()

# ---------------- MODEL ---------------- #
@st.cache_resource
def load_model():
    return SentenceTransformer("all-MiniLM-L6-v2")

model = load_model()

# ---------------- TEXT ---------------- #
def extract_text(file):
    reader = PyPDF2.PdfReader(file)
    return " ".join([p.extract_text() or "" for p in reader.pages]).lower()

def extract_experience(text):
    exp = re.findall(r'(\d+)\+?\s*(years|yrs)', text)
    return max([int(x[0]) for x in exp]) if exp else 0

# ---------------- AI CORE ---------------- #
def analyze(text, jd, skills):
    jd_emb = model.encode(jd, convert_to_tensor=True)
    text_emb = model.encode(text, convert_to_tensor=True)

    score = util.cos_sim(jd_emb, text_emb).item() * 100

    matched = []
    missing = []

    for s in skills:
        s_emb = model.encode(s, convert_to_tensor=True)
        sim = util.cos_sim(text_emb, s_emb).item()

        if sim > 0.35:
            matched.append(s)
        else:
            missing.append(s)

    return score, matched, missing

# ---------------- LOGIC ---------------- #
def tier(score):
    return "🟢 Strong Fit" if score > 75 else "🟡 Moderate" if score > 50 else "🔴 Weak"

def decision(score, exp):
    if score > 80 and exp >= 3:
        return "🟢 HIRE"
    elif score > 60:
        return "🟡 MAYBE"
    return "🔴 REJECT"

def improve(missing, exp):
    tips = []

    if missing:
        tips.append("Add skills: " + ", ".join(missing))
    if exp < 2:
        tips.append("Gain real project experience")
    tips.append("Add measurable achievements")
    tips.append("Include GitHub / portfolio")

    return tips

# ---------------- CHATBOT ---------------- #
def chatbot(query, df):
    top = df.iloc[0]

    if "best" in query.lower():
        return f"Best Candidate: {top['Candidate']} ({top['Score']})"

    if "compare" in query.lower():
        return df[['Candidate', 'Score', 'Decision']].to_string()

    if "why" in query.lower():
        return f"{top['Candidate']} selected due to highest semantic match + experience weight."

    return "Ask: best / compare / why"

# ---------------- UI ---------------- #
st.title("NeuroHire AI — Final Stable System")

col1, col2 = st.columns(2)

with col1:
    jd = st.text_area("Job Description")
    skills_input = st.text_input("Skills", "Python, AI, SQL")

with col2:
    files = st.file_uploader("Upload Resumes", type=["pdf"], accept_multiple_files=True)

chat = st.text_input("AI Assistant")

# ---------------- RUN ---------------- #
if st.button("Analyze"):

    skills = [s.strip().lower() for s in skills_input.split(",")]
    results = []

    for f in files:
        text = extract_text(f)

        score, matched, missing = analyze(text, jd, skills)
        exp = extract_experience(text)

        final_score = score + len(matched)*3 + exp*2

        t = tier(final_score)
        d = decision(final_score, exp)

        results.append({
            "Candidate": f.name,
            "Score": round(final_score, 2),
            "Tier": t,
            "Decision": d
        })

        cursor.execute("""
        INSERT INTO results (user, candidate, score, tier, decision, timestamp)
        VALUES (?, ?, ?, ?, ?, ?)
        """, ("user", f.name, final_score, t, d,
              str(datetime.datetime.now())))
        conn.commit()

    df = pd.DataFrame(results).sort_values(by="Score", ascending=False)

    st.subheader("Ranking")
    st.dataframe(df)

    st.bar_chart(df.set_index("Candidate")["Score"])

    if chat:
        st.info(chatbot(chat, df))

    st.subheader("Improvement Suggestions")
    for r in results:
        st.write(f"### {r['Candidate']}")
        for tip in improve([], 2):
            st.write("•", tip)

# ---------------- HISTORY ---------------- #
st.subheader("History")
st.write("Stored results saved in database")
