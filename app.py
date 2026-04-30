import streamlit as st
import PyPDF2
import pandas as pd
import re
import pytesseract
from pdf2image import convert_from_bytes
import io

st.set_page_config(page_title="ResumeParser Pro", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Inter:wght@300;500;700&display=swap');
    .stApp { background-color: #0e1117; }
    .main-header { font-family: 'Orbitron', sans-serif; color: #00d4ff; text-align: center; font-size: 2.5rem; letter-spacing: 4px; }
    .sub-header { font-family: 'Inter', sans-serif; color: #8b949e; text-align: center; font-size: 0.9rem; text-transform: uppercase; margin-bottom: 40px; }
    .stButton>button { width: 100%; background-color: #00d4ff; color: #0e1117; font-weight: 700; border: none; border-radius: 4px; }
    </style>
    """, unsafe_allow_html=True)

CORE_LANGUAGE_REGISTRY = [
    "Python", "Java", "JavaScript", "TypeScript", "C++", "C#", "PHP", "Go", "Rust", 
    "Swift", "Kotlin", "Ruby", "SQL", "Scala", "Lua", "Julia", "Solidity", "VHDL", 
    "Verilog", "Assembly", "Groovy", "Elixir", "Erlang", "Clojure", "F#", "Fortran"
]

def extract_document_text(file):
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

def clean_buffer(text):
    return re.sub(r'[^a-z0-9+#\s]', ' ', text.lower())

def execute_neural_match(jd, resume_raw, manual_criteria):
    auto_detected = [l for l in CORE_LANGUAGE_REGISTRY if re.search(r'\b' + re.escape(l.lower()) + r'\b', jd.lower())]
    integrated_criteria = list(set([s.strip().lower() for s in manual_criteria] + [l.lower() for l in auto_detected]))
    jd_tokens = set(clean_buffer(jd).split())
    res_tokens = set(clean_buffer(resume_raw).split())
    jd_tokens = {t for t in jd_tokens if len(t) > 2}
    semantic_score = (len(jd_tokens.intersection(res_tokens)) / len(jd_tokens)) * 100 if jd_tokens else 0
    verified = []
    for criterion in integrated_criteria:
        if re.search(r'\b' + re.escape(criterion) + r'\b', resume_raw):
            verified.append(criterion.upper())
    unverified = [c.upper() for c in integrated_criteria if c.upper() not in verified]
    exp_vectors = re.findall(r'(\d+)\+?\s*(years|yrs|experience)', resume_raw)
    exp_magnitude = max([int(v[0]) for v in exp_vectors]) if exp_vectors else 0
    aggregate_index = (semantic_score * 0.3) + (len(verified)/max(len(integrated_criteria), 1) * 60) + (min(exp_magnitude, 10) * 1)
    return round(aggregate_index, 2), verified, unverified, exp_magnitude

st.markdown('<div class="main-header">RESUMEPARSER PRO</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">AI Resume Analysis & Candidate Ranking System</div>', unsafe_allow_html=True)

layout_left, layout_right = st.columns(2)
with layout_left:
    st.subheader("System Input")
    jd_input = st.text_area("Job Description / Technical Specification", height=200)
    manual_spec = st.text_input("Mandatory Skill Constraints (Comma Separated)", "Docker, AWS, Kubernetes")
with layout_right:
    st.subheader("Asset Upload")
    document_assets = st.file_uploader("Source Files (PDF)", type=["pdf"], accept_multiple_files=True)

if st.button("INITIALIZE ANALYSIS"):
    if jd_input and document_assets:
        spec_list = [s.strip() for s in manual_spec.split(",") if s.strip()]
        processed_matrix = []
        for asset in document_assets:
            content_buffer = extract_document_text(asset)
            score, verified, unverified, exp = execute_neural_match(jd_input, content_buffer, spec_list)
            if score >= 80:
                classification, indicator = "OPTIMAL COMPATIBILITY", "🟢"
            elif score >= 50:
                classification, indicator = "PROVISIONAL STATUS", "🟡"
            else:
                classification, indicator = "NON-COMPLIANT", "🔴"
            processed_matrix.append({
                "Identity": asset.name,
                "Neural Score": score,
                "Tenure": f"{exp} YRS",
                "Compliance": f"{indicator} {classification}",
                "Verified Tech": ", ".join(verified),
                "Missing Nodes": ", ".join(unverified)
            })
        analytics_df = pd.DataFrame(processed_matrix).sort_values("Neural Score", ascending=False).reset_index(drop=True)
        analytics_df.insert(0, "Rank", range(1, len(analytics_df) + 1))
        st.markdown("---")
        st.subheader("Ranking Intelligence Output")
        st.dataframe(analytics_df, use_container_width=True, hide_index=True)
        st.subheader("Performance Metrics Visualization")
        st.bar_chart(analytics_df.set_index("Identity")["Neural Score"])
        csv_payload = analytics_df.to_csv(index=False).encode('utf-8')
        st.download_button("EXPORT SYSTEM REPORT", data=csv_payload, file_name="ResumeParser_Pro_Report.csv", mime="text/csv")
    else:
        st.error("Protocol Error: Input fields require data for processing.")

st.markdown("---")
st.markdown("<p style='text-align: right; font-family: Orbitron; font-size: 10px; color: #444;'>ENGINE STATUS: OPERATIONAL | PR AV</p>", unsafe_allow_html=True)
