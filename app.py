import streamlit as st
import PyPDF2
import pandas as pd
import re
import pytesseract
from pdf2image import convert_from_bytes
import io

# ---------------- 💎 PREMIUM UI ---------------- #
st.set_page_config(page_title="NeuroHire AI", layout="wide", page_icon="🎯")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Inter:wght@300;500;700&display=swap');
    .stTitle { font-family: 'Orbitron', sans-serif; color: #00d4ff; text-align: center; }
    .stSubheader { font-family: 'Inter', sans-serif; color: #f39c12; font-weight: 700; }
    </style>
    """, unsafe_allow_html=True)

# ---------------- ⚙️ HYBRID EXTRACTION ---------------- #

def extract_text(file):
    # Try Standard PDF Extraction first
    try:
        reader = PyPDF2.PdfReader(file)
        text = " ".join([p.extract_text() or "" for p in reader.pages]).strip()
    except:
        text = ""

    # If text is empty/short, it's a SCANNED PDF -> Use OCR
    if len(text) < 50:
        file.seek(0)
        images = convert_from_bytes(file.read())
        ocr_text = ""
        for img in images:
            ocr_text += pytesseract.image_to_string(img)
        return ocr_text.lower()
    
    return text.lower()

def clean_text(text):
    return re.sub(r'[^a-z0-9+#\s]', ' ', text.lower())

def analyze_match(jd, resume_text, skills_list):
    # Keyword Similarity
    jd_words = set(clean_text(jd).split())
    res_words = set(clean_text(resume_text).split())
    jd_words = {w for w in jd_words if len(w) > 2}
    
    keyword_score = (len(jd_words.intersection(res_words)) / len(jd_words)) * 100 if jd_words else 0

    # Skill Matching
    matched = [s.strip().upper() for s in skills_list if re.search(r'\b' + re.escape(s.lower().strip()) + r'\b', resume_text)]
    missing = [s.strip().upper() for s in skills_list if s.strip().upper() not in matched]
    
    # Experience
    exp_find = re.findall(r'(\d+)\+?\s*(years|yrs)', resume_text)
    exp = max([int(x[0]) for x in exp_find]) if exp_find else 0

    # Weighted Score: 40% Keywords, 50% Skills, 10% Experience
    final = (keyword_score * 0.4) + (len(matched)/len(skills_list) * 50) + (min(exp, 10) * 1)
    return round(final, 2), matched, missing, exp

# ---------------- 🖥️ INTERFACE ---------------- #

st.markdown("<h1 class='stTitle'>🧬 NEUROHIRE AI</h1>", unsafe_allow_html=True)
st.markdown("---")

c1, c2 = st.columns(2)
with c1:
    jd = st.text_area("Job Description", height=150)
    skills = st.text_input("Skills (comma separated)", "Python, SQL, AI")
with c2:
    files = st.file_uploader("Upload Resumes", type=["pdf"], accept_multiple_files=True)

if st.button("🚀 RUN ANALYSIS"):
    if jd and files:
        skill_arr = skills.split(",")
        data = []
        
        for f in files:
            raw = extract_text(f)
            score, m, mis, ex = analyze_match(jd, raw, skill_arr)
            
            tier = "🟢 PREMIER" if score > 75 else "🟡 MID" if score > 45 else "🔴 LOW"
            
            data.append({
                "Candidate": f.name,
                "Score": score,
                "Exp": ex,
                "Tier": tier,
                "Matched": ", ".join(m)
            })
            
        df = pd.DataFrame(data).sort_values("Score", ascending=False)
        st.dataframe(df, use_container_width=True)
        st.bar_chart(df.set_index("Candidate")["Score"])
    else:
        st.error("Please provide JD and Resumes")

st.markdown("<p style='text-align: right; color: grey;'>v2.1-OCR | PrAv</p>", unsafe_allow_html=True)
