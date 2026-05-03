import streamlit as st
import pdfplumber
import docx
import re
import spacy

# Load NLP model
nlp = spacy.load("en_core_web_sm")

# Define marketing categories mapping
CATEGORY_MAPPING = {
    "social media": ["facebook", "instagram", "tiktok", "social media", "ads", "marketing"],
    "content creation": ["copywriting", "content writing", "blog", "creative writing"],
    "e-commerce": ["seo", "sem", "shopify", "woocommerce", "e-commerce", "analytics"],
    "affiliate data": ["excel", "data analysis", "data entry", "reporting", "statistics"]
}

def extract_text_from_pdf(file_path):
    text = ""
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() + "\n"
    return text

def extract_text_from_docx(file_path):
    doc = docx.Document(file_path)
    return "\n".join([p.text for p in doc.paragraphs])

def analyze_cv(text):
    text = text.lower()
    doc = nlp(text)
    skills = set()
    for token in doc:
        if token.text in ["facebook","instagram","tiktok","ads","copywriting","seo","sem","excel","analytics"]:
            skills.add(token.text)
    return skills

def recommend_categories(skills):
    categories = []
    for category, keywords in CATEGORY_MAPPING.items():
        for skill in skills:
            if skill in keywords:
                categories.append(category)
                break
    return list(set(categories))

st.title("Affiliance CV Analyzer 🤖")

uploaded_file = st.file_uploader("Upload your CV (PDF / DOCX)", type=["pdf","docx"])

if uploaded_file:
    file_path = uploaded_file.name
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    # Extract text
    if file_path.endswith(".pdf"):
        text = extract_text_from_pdf(file_path)
    else:
        text = extract_text_from_docx(file_path)
    
    st.subheader("Extracted Text:")
    st.text_area("", text, height=200)
    
    # Analyze CV
    skills = analyze_cv(text)
    st.subheader("Detected Skills:")
    st.write(", ".join(skills))
    
    categories = recommend_categories(skills)
    st.subheader("Recommended Marketing Categories:")
    st.write(", ".join(categories))
