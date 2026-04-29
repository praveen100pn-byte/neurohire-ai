import streamlit as st
import PyPDF2
import pandas as pd
import re

# ---------------- APP ---------------- #
st.set_page_config(page_title="NeuroHire AI", layout="wide")

# ---------------- CLEAN TEXT ---------------- #
def clean(text):
    return re.sub(r'[^a-zA-Z0-9 ]', ' ', text.lower())

# ---------------- PDF TEXT ---------------- #
def extract_text(file):
    reader = PyPDF2.PdfReader(file)
    return " ".join([p.extract_text() or "" for p in reader.pages]).lower()

# ---------------- EXPERIENCE ---------------- #
def extract_experience(text):
    exp = re.findall(r'(\d+)\+?\s*(years|yrs)', text)
    return max([int(x[0]) for x in exp]) if exp else 0

# ---------------- SIMILARITY SCORE ---------------- #
def similarity_score(jd, text):
    jd = clean(jd)
    text = clean(text)

    jd_words = set(jd.split())
    text_words = set(text.split())

    if not jd_words:
        return 0

    common = jd_words.intersection(text_words)
    return (len(common) / len(jd_words)) * 100

# ---------------- SKILL MATCHING ---------------- #
def skill_analysis(text, skills):
    text = clean(text)
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

# ---------------- UI ---------------- #
st.title("NeuroHire AI — ATS System (Final Version)")

col1, col2 = st.columns(2)

with col1:
    jd = st.text_area("Job Description")
    skills_input = st.text_input("Required Skills", "Python, Machine Learning, SQL, Data Structures")

with col2:
    files = st.file_uploader("Upload Resumes (PDF)", type=["pdf"], accept_multiple_files=True)

# ---------------- ANALYSIS ---------------- #
if st.button("Analyze Candidates"):

    if jd and files and skills_input:

        skills = [s.strip().lower() for s in skills_input.split(",")]
        results = []

        for f in files:
            text = extract_text(f)

            base_score = similarity_score(jd, text)

            matched, missing = skill_analysis(text, skills)
            exp = extract_experience(text)

            final_score = base_score + len(matched) * 5 + exp * 2

            tier = get_tier(final_score)

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
        st.subheader("🏆 Candidate Ranking")
        st.dataframe(df, width="stretch")

        st.subheader("📊 Score Chart")
        st.bar_chart(df.set_index("Candidate")["Score"])

        # ---------------- TOP CANDIDATE ---------------- #
        top = df.iloc[0]
        st.success(f"Top Candidate: {top['Candidate']} | {top['Tier']} | Score {top['Score']}")

        # ---------------- DOWNLOAD ---------------- #
        st.download_button(
            "Download Report",
            df.to_csv(index=False),
            "neurohire_report.csv",
            "text/csv"
        )

    else:
        st.error("Please fill all fields and upload resumes")
