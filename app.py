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

GLOBAL_REGISTRY = [
    "Python", "Java", "JavaScript", "TypeScript", "C++", "C#", "PHP", "Go", "Rust", 
    "Swift", "Kotlin", "Ruby", "SQL", "HTML", "CSS", "R", "MATLAB", "Scala", "Assembly"
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
            return "".join([pytesseract.image_to_string(img) for img in images]).lower()
        except:
            return ""
    return text.lower()

def clean_text(text):
    return re.sub(r'[^a-z0-9+#\s]', ' ', text.lower())

def analyze_match(jd, resume_text, manual_skills):
    detected_in_jd = [lang for lang in GLOBAL_REGISTRY if re.search(r'\b' + re.escape(lang.lower()) + r'\b', jd.lower())]
    core_requirements = list(set([s.strip().lower() for s in manual_skills if s.strip()] + [l.lower() for l in detected_in_jd]))
    
    jd_tokens = set(clean_text(jd).split())
    res_tokens = set(clean_text(resume_text).split())
    match_tokens = jd_tokens.intersection(res_tokens)
    keyword_score = (len(match_tokens) / len(jd_tokens)) * 100 if jd_tokens else 0

    verified = [s.upper() for s in core_requirements if re.search(r'\b' + re.escape(s) + r'\b', resume_text)]
    missing = [s.upper() for s in core_requirements if s.upper() not in verified]
    
    skill_match_ratio = len(verified) / max(len(core_requirements), 1)
    final_score = (keyword_score * 0.2) + (skill_match_ratio * 80)
    
    return round(final_score, 2), verified, missing

st.markdown('<div class="main-header">HIREIQ</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">AI Resume Screening System</div>', unsafe_allow_html=True)

col_l, col_r = st.columns(2)
with col_l:
    st.subheader("System Specification")
    jd_box = st.text_area("Technical Specification", height=200)
    manual_spec = st.text_input("Mandatory Constraints", "Python, SQL")
with col_r:
    st.subheader("Data Input")
    files = st.file_uploader("Source Assets (PDF)", type=["pdf"], accept_multiple_files=True)

if st.button("EXECUTE ANALYSIS"):
    if jd_box and files:
        req_list = [s.strip() for s in manual_spec.split(",") if s.strip()]
        results = []
        for f in files:
            raw = extract_text(f)
            score, verified, missing = analyze_match(jd_box, raw, req_list)
            
            if score >= 70:
                status, color = "WELCOME", "🟢"
            elif score >= 40:
                status, color = "PROVISIONAL STATUS", "🟡"
            else:
                status, color = "NON-COMPLIANT", "🔴"
                
            results.append({
                "Identity": f.name,
                "Neural Score": score,
                "Compliance": f"{color} {status}",
                "Verified Tech": ", ".join(verified),
                "Missing Nodes": ", ".join(missing)
            })
            
        df = pd.DataFrame(results).sort_values("Neural Score", ascending=False).reset_index(drop=True)
        df.insert(0, "Rank", df.apply(lambda x: df.index[df['Neural Score'] == x['Neural Score']][0] + 1 if x['Neural Score'] >= 40 else "-", axis=1))

        st.markdown("---")
        st.subheader("Intelligence Output")
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.bar_chart(df.set_index("Identity")["Neural Score"])
    else:
        st.error("Protocol Error: Requirements missing")

st.markdown("---")
st.markdown("<p style='text-align: right; font-family: Orbitron; font-size: 10px; color: #444;'>STATUS: OPERATIONAL | PR AV</p>", unsafe_allow_html=True)
