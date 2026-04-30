import streamlit as st
import PyPDF2
import pandas as pd
import re
import pytesseract
from pdf2image import convert_from_bytes
import io

st.set_page_config(page_title="HireIQ", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Inter:wght@300;500;700&display=swap');
    .stApp { background-color: #0e1117; }
    .main-header { font-family: 'Orbitron', sans-serif; color: #00d4ff; text-align: center; font-size: 2.5rem; letter-spacing: 4px; }
    .sub-header { font-family: 'Inter', sans-serif; color: #8b949e; text-align: center; font-size: 0.9rem; text-transform: uppercase; margin-bottom: 40px; }
    .stButton>button { width: 100%; background-color: #00d4ff; color: #0e1117; font-weight: 700; border: none; border-radius: 4px; }
    </style>
    """, unsafe_allow_html=True)

ELIGIBILITY_REGISTRY = [
    "Python", "Java", "JavaScript", "TypeScript", "C++", "C#", "PHP", "Go", "Golang",
    "Rust", "Swift", "Kotlin", "Ruby", "Dart", "R", "SQL", "HTML", "CSS", "MATLAB",
    "Scala", "Perl", "Haskell", "Lua", "Julia", "Cobol", "Fortran", "Pascal", 
    "Objective-C", "Shell", "Bash", "PowerShell", "Solidity", "VHDL", "Verilog",
    "C", "Assembly", "Groovy", "Elixir", "Erlang", "Clojure", "F#", "Visual Basic",
    "VB.NET", "SAS", "Apex", "Delphi", "Lisp", "Ada", "Tcl", "Scheme"
]

def extract_text(file):
    try:
        reader = PyPDF2.PdfReader(file)
        text = " ".join([p.extract_text() or "" for p in reader.pages]).strip()
    except:
        text = ""
    if len(text) < 50:
        file.seek(0)
        try:
            images = convert_from_bytes(file.read())
            ocr_text = ""
            for img in images:
                ocr_text += pytesseract.image_to_string(img)
            return ocr_text.lower()
        except:
            return ""
    return text.lower()

def clean_text(text):
    return re.sub(r'[^a-z0-9+#\s]', ' ', text.lower())

def analyze_match(jd, resume_text, user_skills):
    detected_in_jd = [lang for lang in ELIGIBILITY_REGISTRY if re.search(r'\b' + re.escape(lang.lower()) + r'\b', jd.lower())]
    full_requirements = list(set([s.strip().lower() for s in user_skills] + [l.lower() for l in detected_in_jd]))
    
    jd_words = set(clean_text(jd).split())
    res_words = set(clean_text(resume_text).split())
    jd_words = {w for w in jd_words if len(w) > 2}
    keyword_score = (len(jd_words.intersection(res_words)) / len(jd_words)) * 100 if jd_words else 0

    matched = []
    for s in full_requirements:
        if re.search(r'\b' + re.escape(s) + r'\b', resume_text):
            matched.append(s.upper())
            
    missing = [s.upper() for s in full_requirements if s.upper() not in matched]
    exp_find = re.findall(r'(\d+)\+?\s*(years|yrs|experience)', resume_text)
    exp_val = max([int(x[0]) for x in exp_find]) if exp_find else 0
    final_score = (keyword_score * 0.3) + (len(matched)/max(len(full_requirements), 1) * 60) + (min(exp_val, 10) * 1)
    return round(final_score, 2), matched, missing, exp_val

st.markdown('<div class="main-header">HIREIQ</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">AI Resume Screening System</div>', unsafe_allow_html=True)

col_l, col_r = st.columns(2)
with col_l:
    st.subheader("System Specification")
    jd_box = st.text_area("Technical Specification", height=200)
    manual_skills = st.text_input("Mandatory Constraints", "Docker, AWS, Kubernetes")
with col_r:
    st.subheader("Data Input")
    files = st.file_uploader("Source Assets (PDF)", type=["pdf"], accept_multiple_files=True)

if st.button("EXECUTE ANALYSIS"):
    if jd_box and files:
        skill_list = [s.strip() for s in manual_skills.split(",") if s.strip()]
        final_data = []
        for f in files:
            raw = extract_text(f)
            score, matched, missing, exp = analyze_match(jd_box, raw, skill_list)
            if score >= 80:
                status, color = "OPTIMAL COMPATIBILITY", "🟢"
            elif score >= 50:
                status, color = "PROVISIONAL STATUS", "🟡"
            else:
                status, color = "NON-COMPLIANT", "🔴"
            final_data.append({
                "Candidate": f.name,
                "Neural Score": score,
                "Tenure": f"{exp} YRS",
                "Compliance": f"{color} {status}",
                "Verified Tech": ", ".join(matched),
                "Missing Nodes": ", ".join(missing)
            })
        df = pd.DataFrame(final_data).sort_values("Neural Score", ascending=False).reset_index(drop=True)
        df.insert(0, "Rank", range(1, len(df) + 1))
        st.markdown("---")
        st.subheader("Intelligence Output")
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.subheader("Performance Metrics Visualization")
        st.bar_chart(df.set_index("Candidate")["Neural Score"])
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("EXPORT SYSTEM REPORT", data=csv, file_name="HireIQ_Report.csv", mime="text/csv")
    else:
        st.error("System Error: Required data missing")

st.markdown("---")
st.markdown("<p style='text-align: right; font-family: Orbitron; font-size: 10px; color: #444;'>STATUS: OPERATIONAL | PR AV</p>", unsafe_allow_html=True)
