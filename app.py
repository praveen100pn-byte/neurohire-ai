import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import streamlit as st
import PyPDF2
from sentence_transformers import SentenceTransformer, util
import pandas as pd
import re
import sqlite3
import datetime
import hashlib

# ---------------- DATABASE ---------------- #
conn = sqlite3.connect("neurohire.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY,
    password TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    candidate TEXT,
    score REAL,
    experience INTEGER,
    matched TEXT,
    missing TEXT,
    tier TEXT,
    timestamp TEXT
)
""")
conn.commit()

# ---------------- HASH ---------------- #
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# ---------------- AUTH ---------------- #
def register():
    st.sidebar.subheader("Register")
    u = st.sidebar.text_input("Username", key="reg_user")
    p = st.sidebar.text_input("Password", type="password", key="reg_pass")

    if st.sidebar.button("Create Account"):
        if u and p:
            try:
                cursor.execute("INSERT INTO users VALUES (?, ?)",
                               (u, hash_password(p)))
                conn.commit()
                st.sidebar.success("Account created")
            except:
                st.sidebar.error("User exists")

def login():
    st.sidebar.subheader("Login")
    u = st.sidebar.text_input("Username", key="log_user")
    p = st.sidebar.text_input("Password", type="password", key="log_pass")

    if st.sidebar.button("Login"):
        cursor.execute("SELECT * FROM users WHERE username=? AND password=?",
                       (u, hash_password(p)))
        if cursor.fetchone():
            st.session_state["auth"] = True
            st.session_state["user"] = u
        else:
            st.sidebar.error("Invalid login")

def logout():
    if st.sidebar.button("Logout"):
        st.session_state.clear()
        st.rerun()

# ---------------- SESSION ---------------- #
if "auth" not in st.session_state:
    st.session_state["auth"] = False

if not st.session_state["auth"]:
    login()
    register()
    st.stop()

logout()

# ---------------- MODEL ---------------- #
@st.cache_resource
def load_model():
    return SentenceTransformer('all-MiniLM-L6-v2')

model = load_model()

# ---------------- TEXT ---------------- #
def extract_text(file):
    reader = PyPDF2.PdfReader(file)
    return " ".join([p.extract_text() or "" for p in reader.pages]).lower()

def extract_experience(text):
    exp = re.findall(r'(\d+)\+?\s*(years|yrs)', text)
    return max([int(x[0]) for x in exp]) if exp else 0

# ---------------- SEMANTIC ENGINE ---------------- #
def semantic_analysis(text, jd, skills):
    chunks = [c.strip() for c in text.split("\n") if len(c.strip()) > 40]

    jd_emb = model.encode(jd, convert_to_tensor=True)
    best_sim = 0
    skill_map = {}

    for chunk in chunks:
        c_emb = model.encode(chunk, convert_to_tensor=True)
        sim = util.cos_sim(jd_emb, c_emb).item()
        best_sim = max(best_sim, sim)

        for skill in skills:
            s_emb = model.encode(skill, convert_to_tensor=True)
            s_score = util.cos_sim(c_emb, s_emb).item()

            if s_score > 0.35:
                skill_map.setdefault(skill, []).append((chunk, s_score))

    matched = list(skill_map.keys())
    missing = [s for s in skills if s not in matched]

    explanations = []
    for skill, contexts in skill_map.items():
        best = sorted(contexts, key=lambda x: x[1], reverse=True)[0]
        explanations.append(f"{skill}: {best[0][:80]}...")

    return best_sim * 100, matched, missing, explanations

# ---------------- UI ---------------- #
st.set_page_config(page_title="NeuroHire AI", layout="wide")

st.markdown("""
<style>
.title {font-size:32px;font-weight:600;}
.credit {text-align:right;font-size:12px;color:grey;}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="title">NeuroHire AI</div>', unsafe_allow_html=True)

st.markdown("""
<svg width="200" height="40">
  <path d="M10 20 Q100 50 190 20" stroke="#f39c12" stroke-width="3" fill="transparent"/>
</svg>
""", unsafe_allow_html=True)

st.markdown('<div class="credit">Made by PrAvEeN-ZorG</div>', unsafe_allow_html=True)
st.markdown("---")

# ---------------- INPUT ---------------- #
col1, col2 = st.columns(2)

with col1:
    jd = st.text_area("Job Description", height=200)
    skills_input = st.text_input("Required Skills", "Python, AI, SQL")

with col2:
    files = st.file_uploader("Upload Resumes", type=['pdf'], accept_multiple_files=True)

# ---------------- ANALYSIS ---------------- #
if st.button("Analyze Candidates"):

    if jd and files and skills_input:

        skills = [s.strip().lower() for s in skills_input.split(",")]
        results = []
        explain_all = {}

        for f in files:
            text = extract_text(f)

            sim, matched, missing, explanations = semantic_analysis(text, jd, skills)
            exp = extract_experience(text)

            score = sim + len(matched)*4 + exp*2

            tier = "🟢 Strong Fit" if score > 75 else "🟡 Moderate" if score > 50 else "🔴 Weak"

            explain_all[f.name] = explanations

            cursor.execute("""
            INSERT INTO results (username, candidate, score, experience, matched, missing, tier, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (st.session_state["user"], f.name, score, exp,
                  ",".join(matched), ",".join(missing), tier,
                  str(datetime.datetime.now())))
            conn.commit()

            results.append({
                "Candidate": f.name,
                "Score": round(score, 2),
                "Experience": exp,
                "Matched": ", ".join(matched),
                "Missing": ", ".join(missing),
                "Tier": tier
            })

        df = pd.DataFrame(results).sort_values(by="Score", ascending=False)

        st.subheader("Candidate Ranking")
        st.dataframe(df, use_container_width=True)

        top = df.iloc[0]
        st.subheader("Top Candidate")
        st.success(f"{top['Candidate']} | Score: {top['Score']} | {top['Tier']}")

        st.bar_chart(df.set_index("Candidate")["Score"])

        st.download_button("Download Report", df.to_csv(index=False), "report.csv")

        # Explainability
        st.subheader("Explainability")
        for name, exp_list in explain_all.items():
            st.write(f"Candidate: {name}")
            for e in exp_list[:3]:
                st.write("-", e)

    else:
        st.error("All fields are required")

# ---------------- HISTORY ---------------- #
st.subheader("Recent Analysis")

history = pd.read_sql(
    f"SELECT * FROM results WHERE username='{st.session_state['user']}' ORDER BY id DESC LIMIT 10",
    conn
)

st.dataframe(history, use_container_width=True)
