"""
Streamlit front end for the AI Job Application Agent (public demo).

Runs the same pipeline as the Flask app (app.py):
JobAnalyzer -> MatchCalculator -> CVCustomizer -> CoverLetterGenerator,
then builds the CV and cover letter as DOCX + PDF.

The demo always uses the fictional profile in data/demo_profile.json.
On Streamlit Community Cloud set GEMINI_API_KEY under Settings -> Secrets.
"""

import json
import os
import re
import tempfile
from pathlib import Path

import streamlit as st

# Copy secrets into the environment before the LLM factory reads them.
for _k in ("GEMINI_API_KEY", "GOOGLE_API_KEY", "DEEPSEEK_API_KEY", "LLM_PROVIDER",
           "GEMINI_MODEL", "GEMINI_FALLBACK_MODEL"):
    try:
        if _k in st.secrets and not os.getenv(_k):
            os.environ[_k] = str(st.secrets[_k]).strip()
    except Exception:
        pass  # no secrets.toml when running locally
if not os.getenv("LLM_PROVIDER"):
    os.environ["LLM_PROVIDER"] = "gemini" if (os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")) else "deepseek"

from agents.job_analyzer import JobAnalyzer
from agents.cv_customizer import CVCustomizer
from agents.cover_letter_generator import CoverLetterGenerator
from utils.document_builder import DocumentBuilder
from utils.llm_factory import create_llm_client
from utils.match_calculator import MatchCalculator
from utils.profile_deduplicator import ProfileDeduplicator

ROOT = Path(__file__).resolve().parent
PROFILE_PATH = ROOT / "data" / "demo_profile.json"
SAMPLE_JD_PATH = ROOT / "sample_job_description.txt"

st.set_page_config(page_title="AI Job Application Agent", page_icon="🎯", layout="wide")


@st.cache_resource
def get_agents():
    client = create_llm_client()
    return JobAnalyzer(client), CVCustomizer(client), CoverLetterGenerator(client)


@st.cache_data
def load_profile():
    with open(PROFILE_PATH, encoding="utf-8") as f:
        return ProfileDeduplicator.deduplicate_profile(json.load(f))


def safe_name(text: str) -> str:
    return re.sub(r"[^\w\-]+", "_", text or "").strip("_")[:40] or "Role"


def run_pipeline(job_description: str, profile: dict, status) -> dict:
    job_analyzer, cv_customizer, cover_letter_generator = get_agents()

    status.write("🔍 Job Analyzer: extracting skills and ATS keywords...")
    analysis = job_analyzer.analyze(job_description)

    status.write("📊 Match Calculator: scoring the profile against the role...")
    match = MatchCalculator().calculate_match_score(profile, analysis)

    status.write("✍️ CV Customizer: tailoring the CV...")
    cv = ProfileDeduplicator.remove_repetitive_content(cv_customizer.customize(profile, analysis))

    status.write("💌 Cover Letter Generator: drafting the letter...")
    letter = cover_letter_generator.generate(profile, analysis)

    status.write("📄 Building DOCX and PDF files...")
    role = analysis.get("role_info", {}) or {}
    base = f"{safe_name(role.get('company'))}_{safe_name(role.get('title'))}"
    files = {}
    with tempfile.TemporaryDirectory() as tmp:
        paths = {
            "cv_docx": os.path.join(tmp, f"CV_{base}.docx"),
            "cv_pdf": os.path.join(tmp, f"CV_{base}.pdf"),
            "cl_docx": os.path.join(tmp, f"CoverLetter_{base}.docx"),
            "cl_pdf": os.path.join(tmp, f"CoverLetter_{base}.pdf"),
        }
        DocumentBuilder().create_cv(cv, paths["cv_docx"])
        DocumentBuilder().create_cv_pdf(cv, paths["cv_pdf"])
        DocumentBuilder().create_cover_letter(letter, profile, paths["cl_docx"])
        DocumentBuilder().create_cover_letter_pdf(letter, profile, paths["cl_pdf"])
        for key, path in paths.items():
            with open(path, "rb") as f:
                files[key] = (os.path.basename(path), f.read())

    return {"analysis": analysis, "match": match, "letter": letter, "files": files}


# ---------------------------------------------------------------- UI
profile = load_profile()

st.title("🎯 AI Job Application Agent")
st.caption("Paste a job description. Three AI agents analyze it, score the match, and write a "
           "tailored, ATS-optimized CV and cover letter (DOCX + PDF).")

with st.sidebar:
    st.subheader("Demo profile")
    info = profile.get("personal_info", {})
    st.markdown(f"**{info.get('name', '')}**  \n{info.get('location', '')}")
    st.caption("A fictional candidate, so the demo can run without anyone's real data.")
    with st.expander("View full profile"):
        st.json(profile, expanded=False)
    st.divider()
    st.markdown("**Pipeline**\n1. Job Analyzer\n2. Match Calculator\n3. CV Customizer\n4. Cover Letter Generator")
    st.caption("Runs on the Gemini free tier, so a run takes 20-60 seconds and can occasionally hit rate limits.")
    st.markdown("[Source on GitHub](https://github.com/Sami123d/job-app-agent-extended)")

if not (os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or os.getenv("DEEPSEEK_API_KEY")):
    st.warning('No AI key configured. Add `GEMINI_API_KEY = "..."` under Settings → Secrets.')

if "jd" not in st.session_state:
    st.session_state.jd = ""
if st.button("Use a sample job description"):
    st.session_state.jd = SAMPLE_JD_PATH.read_text(encoding="utf-8")

jd = st.text_area("Job description", key="jd", height=260,
                  placeholder="Paste the full job posting here (at least 50 characters)...")

if st.button("Analyze & generate", type="primary", disabled=len(jd.strip()) < 50):
    with st.status("Running the agents...", expanded=True) as status:
        try:
            st.session_state.result = run_pipeline(jd.strip(), profile, status)
            status.update(label="Done", state="complete", expanded=False)
        except Exception as e:  # show a readable error instead of a traceback
            st.session_state.pop("result", None)
            status.update(label="Something went wrong", state="error")
            msg = str(e)
            if "503" in msg or "429" in msg or "high demand" in msg.lower():
                st.error("The free Gemini tier is busy right now. Please try again in a minute.")
            else:
                st.error(f"Generation failed: {msg[:300]}")

result = st.session_state.get("result")
if result:
    analysis, match = result["analysis"], result["match"]
    role = analysis.get("role_info", {}) or {}
    st.subheader(f"{role.get('title') or 'Role'} · {role.get('company') or 'Company'}")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Overall match", f"{match.get('overall_score', 0)}%")
    c2.metric("Must-have skills", f"{match.get('required_skills_matched', 0)}/{match.get('required_skills_total', 0)}")
    c3.metric("Nice-to-have", f"{match.get('nice_to_have_matched', 0)}/{match.get('nice_to_have_total', 0)}")
    c4.metric("ATS keywords", f"{match.get('keywords_matched', 0)}/{match.get('keywords_total', 0)}")

    f = result["files"]
    d1, d2, d3, d4 = st.columns(4)
    d1.download_button("⬇️ CV (PDF)", f["cv_pdf"][1], f["cv_pdf"][0], "application/pdf")
    d2.download_button("⬇️ CV (DOCX)", f["cv_docx"][1], f["cv_docx"][0])
    d3.download_button("⬇️ Cover letter (PDF)", f["cl_pdf"][1], f["cl_pdf"][0], "application/pdf")
    d4.download_button("⬇️ Cover letter (DOCX)", f["cl_docx"][1], f["cl_docx"][0])

    left, right = st.columns(2)
    with left:
        st.markdown("#### Cover letter")
        st.write(result["letter"])
    with right:
        st.markdown("#### What the analyzer found")
        req = analysis.get("requirements", {}) or {}
        kw = analysis.get("keywords", {}) or {}
        if analysis.get("summary"):
            st.write(analysis["summary"])
        st.markdown("**Must-have:** " + ", ".join(req.get("must_have_skills") or []) or "-")
        st.markdown("**Nice-to-have:** " + ", ".join(req.get("nice_to_have_skills") or []) or "-")
        st.markdown("**ATS keywords:** " + ", ".join(kw.get("ats_keywords") or []) or "-")
        if match.get("missing_required_skills"):
            st.markdown("**Gaps:** " + ", ".join(match["missing_required_skills"]))
        for rec in match.get("recommendations") or []:
            st.caption("💡 " + str(rec))
