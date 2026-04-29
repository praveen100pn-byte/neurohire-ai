import streamlit as st
import PyPDF2
import pandas as pd
import re
import requests

# ---------------- APP ---------------- #
st.set_page_config(page_title="NeuroHire AI", layout="wide")

# ---------------- PDF ---------------- #
def extract_text(file):
    reader = PyPDF2.PdfReader(file)
    return " ".join([p.extract_text() or "" for p in reader.pages]).lower()

# ---------------- EXPERIENCE ---------------- #
def extract_experience(text):
    exp = re.findall(r'(\d+)\+?\s*(years|yrs)', text)
    return max([int(x[0]) for x in exp]) if exp else 0

# ---------------- SMART SEMANTIC SCORE (NO ML DEPENDENCY) ---------------- #
def semantic_score(jd, text):
    jd_words = set(jd.lower().split())
    text_words = set(text.lower().split())

    if not jd_words or not text_words:
        return 0

    overlap = jd_words.intersection(text_words)
    return len(overlap) / len(jd_words.union(text_words))

# ---------------- SKILL ANALYSIS ---------------- #
def skill_analysis(text, skills):
    matched = []
    missing = []

    for s in skills:
        if s in text:
            matched.append(s)
        else:
            missing.append(s)

    return matched, missing

# ---------------- TIER SYSTEM ---------------- #
def get_tier(score):
    if score > 75:
        return "🟢 Strong (Hire)"
    elif score > 50:
        return "🟡 Medium (May be)"
    else:
        return "🔴 Weak (Reject)"

# ---------------- AI EXPLANATION ---------------- #
def explain(matched, missing, exp):
    reasons = []

    if matched:
        reasons.append("Strong skill match: " + ", ".join(matched[:3]))

    if missing:
        reasons.append("Missing skills: " + ", ".join(missing[:3]))

    if exp >= 3:
        reasons.append("Good experience level")
    elif exp == 0:
        reasons.append("No clear experience found")

    return reasons

# ---------------- UI ---------------- #
st.title("NeuroHire AI — Advanced Recruitment System")

col1, col2 = st.columns(2)

with col1:
    jd = st.text_area("Job Description")
    skills_input = st.text_input("Required Skills", "Python, AI, SQL, ML")

with col2:
    files = st.file_uploader("Upload Resumes (PDF)", type=["pdf"], accept_multiple_files=True)

# ---------------- RUN ---------------- #
if st.button("Analyze Candidates"):

    if jd and files and skills_input:

        skills = [s.strip().lower() for s in skills_input.split(",")]
        results = []
        explanations = {}

        for f in files:
            text = extract_text(f)

            base_score = semantic_score(jd, text) * 100

            matched, missing = skill_analysis(text, skills)
            exp = extract_experience(text)

            final_score = base_score + len(matched)*6 + exp*2

            tier = get_tier(final_score)

            explanations[f.name] = explain(matched, missing, exp)

            results.append({
                "Candidate": f.name,
                "Score": round(final_score, 2),
                "Experience": exp,
                "Tier": tier,
                "Matched Skills": ", ".join(matched),
                "Missing Skills": ", ".join(missing)
            })

        df = pd.DataFrame(results).sort_values(by="Score", ascending=False)

        # ---------------- OUTPUT ---------------- #
        st.subheader("🫡 Candidate Ranking")
        st.dataframe(df, use_container_width=True)

        st.subheader("📊 Score Distribution")
        st.bar_chart(df.set_index("Candidate")["Score"])

        # ---------------- TOP CANDIDATE ---------------- #
        top = df.iloc[0]
        st.success(f"Top Candidate: {top['Candidate']} | {top['Tier']} | Score {top['Score']}")

        # ---------------- AI EXPLANATION ---------------- #
        st.subheader("🧠 AI Explanation")
        for name, reasons in explanations.items():
            st.write(f"### {name}")
            for r in reasons:
                st.write("•", r)

        # ---------------- DOWNLOAD ---------------- #
        st.download_button(
            "Download Report",
            df.to_csv(index=False),
            "neurohire_report.csv",
            "text/csv"
        )

    else:
        st.error("Please fill all fields and upload resumes")
