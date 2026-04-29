import streamlit as st
import PyPDF2
import pandas as pd
import re

# ---------------- APP ---------------- #
st.set_page_config(page_title="NeuroHire AI", layout="wide")

# ---------------- CLEAN TEXT ---------------- #
def clean(text):
    text = text.lower()
    text = re.sub(r'[^a-zA-Z0-9 ]', ' ', text)
    return text

# ---------------- PDF TEXT ---------------- #
def extract_text(file):
    reader = PyPDF2.PdfReader(file)
    text = ""

    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text

    return text.lower().strip()

# ---------------- EXPERIENCE ---------------- #
def extract_experience(text):
    exp = re.findall(r'(\d+)\+?\s*(years|yrs)', text)
    return max([int(x[0]) for x in exp]) if exp else 0

# ---------------- SIMILARITY SCORE ---------------- #
def similarity_score(jd, text):
    jd_words = set(clean(jd).split())
    text_words = set(clean(text).split())

    jd_words = {w for w in jd_words if len(w) > 2}
    text_words = {w for w in text_words if len(w) > 2}

    if not jd_words:
        return 0

    match_count = 0

    for w in jd_words:
        for t in text_words:
            if w in t or t in w:
                match_count += 1
                break

    return (match_count / len(jd_words)) * 100

# ---------------- SKILL MATCH ---------------- #
def skill_analysis(text, skills):
    text = clean(text)
    matched = []
    missing = []

    for s in skills:
        s_clean = s.lower().strip()
        if s_clean in text:
            matched.append(s_clean)
        else:
            missing.append(s_clean)

    return matched, missing

# ---------------- TIER ---------------- #
def get_tier(score):
    if score > 75:
        return "Strong (Hire)"
    elif score > 50:
        return "Medium (May be)"
    else:
        return "Weak (Reject)"

# ---------------- FINAL STATUS ---------------- #
def classify_candidate(score):
    if score >= 75:
        return "TOP CANDIDATE"
    elif score >= 50:
        return "AVERAGE CANDIDATE"
    else:
        return "POOR CANDIDATE"

# ---------------- EXPLANATION ---------------- #
def explain_candidate(matched, missing):
    reasons = []

    if matched:
        reasons.append(f"Good skill match: {', '.join(matched)}")

    if missing:
        reasons.append(f"Missing key skills: {', '.join(missing[:3])}")

    if not matched:
        reasons.append("Low alignment with job description")

    return reasons

# ---------------- UI ---------------- #
st.title("NeuroHire AI - Smart ATS System")

col1, col2 = st.columns(2)

with col1:
    jd = st.text_area("Job Description", height=200)
    skills_input = st.text_input(
        "Required Skills",
        "python, machine learning, sql, data structures, algorithms"
    )

with col2:
    files = st.file_uploader(
        "Upload Resumes (PDF)",
        type=["pdf"],
        accept_multiple_files=True
    )

# ---------------- ANALYSIS ---------------- #
if st.button("Analyze Candidates"):

    if jd and files and skills_input:

        skills = [s.strip().lower() for s in skills_input.split(",")]
        results = []

        for idx, f in enumerate(files, start=1):

            text = extract_text(f)

            base_score = similarity_score(jd, text)
            matched, missing = skill_analysis(text, skills)
            exp = extract_experience(text)

            final_score = base_score + len(matched) * 5 + exp * 2

            tier = get_tier(final_score)
            status = classify_candidate(final_score)

            reasons = explain_candidate(matched, missing)

            results.append({
                "S.No": idx,
                "Candidate": f.name,
                "Score": round(final_score, 2),
                "Experience": exp,
                "Tier": tier,
                "Status": status,
                "Matched Skills": ", ".join(matched),
                "Missing Skills": ", ".join(missing),
                "Reason": " | ".join(reasons)
            })

        df = pd.DataFrame(results).sort_values(by="Score", ascending=False).reset_index(drop=True)

        st.subheader("Candidate Ranking")
        st.dataframe(df, use_container_width=True)

        st.subheader("Score Chart")
        st.bar_chart(df.set_index("Candidate")["Score"])

        top = df.iloc[0]
        st.success(f"Top Candidate: {top['Candidate']} | {top['Status']} | {top['Score']}")

        st.subheader("AI Explanation")

        for r in results:
            st.write(r["Candidate"])
            for reason in r["Reason"].split(" | "):
                st.write("-", reason)

        st.download_button(
            "Download Report",
            df.to_csv(index=False),
            "neurohire_report.csv",
            "text/csv"
        )

    else:
        st.error("Please fill all fields and upload resumes")
