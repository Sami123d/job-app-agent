"""
Streamlit front end for the AI Job Application Agent (public demo).

Runs the same pipeline as the Flask app (app.py):
JobAnalyzer -> MatchCalculator -> CVCustomizer -> CoverLetterGenerator,
then builds the CV and cover letter as DOCX + PDF.

The demo always uses the fictional profile in data/demo_profile.json.
On Streamlit Community Cloud set GEMINI_API_KEY under Settings -> Secrets.
"""

import html
import json
import os
import re
import tempfile
from pathlib import Path

import sys

import streamlit as st

# Make agent progress prints show up in the Streamlit Cloud logs right away.
try:
    sys.stdout.reconfigure(line_buffering=True)
except Exception:
    pass

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

st.set_page_config(page_title="AI Job Application Agent · Tailored CV in seconds", page_icon="🎯", layout="wide")


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
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Plus+Jakarta+Sans:wght@600;700;800&display=swap');
    :root { --brand:#4F46E5; --brand-2:#7C3AED; --brand-soft:#EEF2FF; --bg:#F7F8FC; --surface:#FFFFFF; --border:#E5E7EB;
            --text:#0F172A; --muted:#64748B; --ok:#059669; --warn:#D97706;
            --shadow: 0 1px 2px rgba(15,23,42,.04), 0 8px 24px -10px rgba(15,23,42,.12); }
    .stApp { background: radial-gradient(1100px 500px at 85% -10%, rgba(124,58,237,.08), transparent 60%),
                         radial-gradient(900px 500px at -10% 0%, rgba(79,70,229,.08), transparent 60%), var(--bg);
             color: var(--text); font-family: 'Inter', system-ui, sans-serif; }
    h1,h2,h3,h4 { font-family:'Plus Jakarta Sans','Inter',sans-serif; color:var(--text); letter-spacing:-.02em; }
    .block-container { padding-top: 2.2rem; max-width: 1150px; }
    #MainMenu, footer { visibility:hidden; } header[data-testid="stHeader"] { background:transparent; }

    [data-testid="stSidebar"] { background:var(--surface); border-right:1px solid var(--border); }
    .brand { display:flex; align-items:center; gap:.6rem; padding:.25rem 0 1.25rem; border-bottom:1px solid var(--border); margin-bottom:1.1rem; }
    .brand-mark { width:36px; height:36px; border-radius:10px; display:grid; place-items:center; color:#fff; font-weight:800;
                  background:linear-gradient(135deg,var(--brand),var(--brand-2)); box-shadow:0 6px 16px -6px rgba(79,70,229,.6); }
    .brand-name { font-family:'Plus Jakarta Sans',sans-serif; font-weight:800; font-size:1.02rem; line-height:1.1; color:var(--text); }
    .brand-sub { font-size:.75rem; color:var(--muted); }
    .side-label { font-size:.7rem; font-weight:700; letter-spacing:.08em; text-transform:uppercase; color:var(--muted); margin:1.1rem 0 .55rem; }
    .card { background:var(--surface); border:1px solid var(--border); border-radius:14px; padding:1rem 1.1rem; box-shadow:var(--shadow); margin-bottom:.7rem; }
    .person { display:flex; gap:.7rem; align-items:center; }
    .avatar { width:40px; height:40px; border-radius:50%; background:var(--brand-soft); color:var(--brand); display:grid; place-items:center; font-weight:700; }
    .muted { color:var(--muted); font-size:.8rem; }
    .steps-side { list-style:none; padding:0; margin:0; }
    .steps-side li { display:flex; gap:.55rem; align-items:center; font-size:.85rem; padding:.3rem 0; color:var(--text); }
    .num { width:22px; height:22px; border-radius:7px; background:var(--brand-soft); color:var(--brand); font-size:.72rem; font-weight:700; display:grid; place-items:center; }

    .hero-badge { display:inline-flex; gap:.4rem; align-items:center; padding:.3rem .75rem; border-radius:999px; background:var(--surface);
                  border:1px solid var(--border); font-size:.78rem; font-weight:600; color:var(--brand); box-shadow:var(--shadow); }
    .hero-title { font-size:2.6rem; font-weight:800; margin:.8rem 0 .35rem; line-height:1.1; font-family:'Plus Jakarta Sans',sans-serif; color:var(--text); }
    .hero-title span { background:linear-gradient(135deg,var(--brand),var(--brand-2)); -webkit-background-clip:text; background-clip:text; color:transparent; }
    .hero-sub { color:var(--muted); font-size:1.05rem; max-width:740px; margin-bottom:1.3rem; }
    .how { display:grid; grid-template-columns:repeat(3,1fr); gap:.75rem; margin-bottom:1.4rem; }
    .how .card { margin:0; }
    .how .t { font-weight:700; font-size:.92rem; margin-top:.35rem; }
    .how .d { color:var(--muted); font-size:.82rem; }
    @media (max-width: 900px) { .how { grid-template-columns:1fr; } .hero-title { font-size:2rem; } }

    [data-testid="stTextArea"] textarea { background:var(--surface); border-radius:12px; font-size:.92rem; }
    .stButton > button, .stDownloadButton > button { border-radius:10px; font-weight:600; border:1px solid var(--border); box-shadow:var(--shadow); }
    .stButton > button[kind="primary"] { background:linear-gradient(135deg,var(--brand),var(--brand-2)); border:none; color:#fff; padding:.55rem 1.4rem; }
    .stButton > button[kind="primary"]:hover { filter:brightness(1.05); }
    .stDownloadButton > button { background:var(--surface); color:var(--text); width:100%; }
    .stDownloadButton > button:hover { border-color:var(--brand); color:var(--brand); }

    .result-head { margin:1.6rem 0 .8rem; }
    .result-head h2 { margin:0; font-size:1.6rem; }
    .metrics { display:grid; grid-template-columns:repeat(4,1fr); gap:.75rem; margin-bottom:1rem; }
    .metric { background:var(--surface); border:1px solid var(--border); border-radius:14px; padding:1rem 1.1rem; box-shadow:var(--shadow); }
    .metric .l { color:var(--muted); font-size:.78rem; font-weight:600; text-transform:uppercase; letter-spacing:.05em; }
    .metric .v { font-family:'Plus Jakarta Sans',sans-serif; font-size:1.7rem; font-weight:800; color:var(--text); }
    .bar { height:6px; background:#E2E8F0; border-radius:99px; overflow:hidden; margin-top:.45rem; }
    .bar > div { height:100%; background:linear-gradient(90deg,var(--brand),var(--brand-2)); }
    @media (max-width: 900px) { .metrics { grid-template-columns:repeat(2,1fr); } }
    .chips { display:flex; flex-wrap:wrap; gap:.35rem; margin:.3rem 0 .8rem; }
    .chip { padding:.22rem .6rem; border-radius:999px; font-size:.76rem; font-weight:600; background:var(--brand-soft); color:var(--brand); }
    .chip.gap { background:#FFF7ED; color:#C2410C; }
    .chip.soft { background:#F1F5F9; color:#334155; }
    .letter { white-space:pre-wrap; font-size:.92rem; line-height:1.65; color:#1E293B; }
    .section-title { font-weight:700; font-size:.78rem; text-transform:uppercase; letter-spacing:.06em; color:var(--muted); margin-bottom:.35rem; }
</style>
""", unsafe_allow_html=True)


def esc(text) -> str:
    return html.escape(str(text or ""))


profile = load_profile()
info = profile.get("personal_info", {})
initials = "".join(w[0] for w in (info.get("name") or "JL").split()[:2]).upper()

with st.sidebar:
    st.markdown(f"""
        <div class="brand"><div class="brand-mark">🎯</div>
          <div><div class="brand-name">Job Application Agent</div><div class="brand-sub">Multi-agent CV generator</div></div></div>
        <div class="side-label">Demo candidate</div>
        <div class="card"><div class="person"><div class="avatar">{esc(initials)}</div>
          <div><b>{esc(info.get('name'))}</b><div class="muted">{esc(info.get('location'))}</div></div></div>
          <div class="muted" style="margin-top:.6rem">Fictional profile, so the demo runs without anyone's real data.</div></div>
    """, unsafe_allow_html=True)
    with st.expander("View full profile"):
        st.json(profile, expanded=False)
    st.markdown("""
        <div class="side-label">Agent pipeline</div>
        <ul class="steps-side">
          <li><span class="num">1</span>Job Analyzer</li><li><span class="num">2</span>Match Calculator</li>
          <li><span class="num">3</span>CV Customizer</li><li><span class="num">4</span>Cover Letter Generator</li>
        </ul>
        <div class="side-label">Good to know</div>
        <div class="muted">Runs on the Gemini free tier: a full run takes 20-60 seconds.</div>
    """, unsafe_allow_html=True)
    st.markdown("[View source on GitHub](https://github.com/Sami123d/job-app-agent-extended)")

if not (os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or os.getenv("DEEPSEEK_API_KEY")):
    st.warning('No AI key configured. Add `GEMINI_API_KEY = "..."` under Settings → Secrets.')

st.markdown("""
    <div class="hero-badge">⚡ Multi-agent AI · ATS-optimized</div>
    <div class="hero-title">Turn any job post into a <span>tailored CV and cover letter</span></div>
    <div class="hero-sub">Paste a job description. The agents pull out the must-have skills and ATS keywords,
    score the candidate against the role, then rewrite the CV and draft a cover letter, ready as PDF and DOCX.</div>
    <div class="how">
      <div class="card"><div>🔍</div><div class="t">1 · Analyze the role</div><div class="d">Skills, seniority and ATS keywords extracted from the post.</div></div>
      <div class="card"><div>📊</div><div class="t">2 · Score the match</div><div class="d">Must-have, nice-to-have and keyword coverage, plus the gaps.</div></div>
      <div class="card"><div>📄</div><div class="t">3 · Write the documents</div><div class="d">Tailored CV and cover letter, downloadable as PDF and DOCX.</div></div>
    </div>
""", unsafe_allow_html=True)

if "jd" not in st.session_state:
    st.session_state.jd = ""

top_l, top_r = st.columns([3, 1])
with top_l:
    st.markdown('<div class="section-title" style="margin-top:.55rem">Job description</div>', unsafe_allow_html=True)
with top_r:
    if st.button("✨ Use a sample job post", use_container_width=True):
        st.session_state.jd = SAMPLE_JD_PATH.read_text(encoding="utf-8")

jd = st.text_area("Job description", key="jd", height=240, label_visibility="collapsed",
                  placeholder="Paste the full job posting here (at least 50 characters)...")

if st.button("Analyze & generate  →", type="primary", disabled=len(jd.strip()) < 50):
    with st.status("Running the agents...", expanded=True) as status:
        try:
            st.session_state.result = run_pipeline(jd.strip(), profile, status)
            status.update(label="Done: documents are ready", state="complete", expanded=False)
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
    req = analysis.get("requirements", {}) or {}
    kw = analysis.get("keywords", {}) or {}

    def pct(a, b):
        return int(round(100 * a / b)) if b else 0

    overall = match.get("overall_score", 0) or 0
    m_req = (match.get("required_skills_matched", 0), match.get("required_skills_total", 0))
    m_nice = (match.get("nice_to_have_matched", 0), match.get("nice_to_have_total", 0))
    m_kw = (match.get("keywords_matched", 0), match.get("keywords_total", 0))

    st.subheader(f"{role.get('title') or 'Role'} · {role.get('company') or 'Company'}")
    st.markdown(f"""
        <div class="metrics">
          <div class="metric"><div class="l">Overall match</div><div class="v">{overall:g}%</div><div class="bar"><div style="width:{min(overall, 100)}%"></div></div></div>
          <div class="metric"><div class="l">Must-have skills</div><div class="v">{m_req[0]}/{m_req[1]}</div><div class="bar"><div style="width:{pct(*m_req)}%"></div></div></div>
          <div class="metric"><div class="l">Nice-to-have</div><div class="v">{m_nice[0]}/{m_nice[1]}</div><div class="bar"><div style="width:{pct(*m_nice)}%"></div></div></div>
          <div class="metric"><div class="l">ATS keywords</div><div class="v">{m_kw[0]}/{m_kw[1]}</div><div class="bar"><div style="width:{pct(*m_kw)}%"></div></div></div>
        </div>
    """, unsafe_allow_html=True)

    f = result["files"]
    d1, d2, d3, d4 = st.columns(4)
    d1.download_button("⬇  CV · PDF", f["cv_pdf"][1], f["cv_pdf"][0], "application/pdf", use_container_width=True)
    d2.download_button("⬇  CV · DOCX", f["cv_docx"][1], f["cv_docx"][0], use_container_width=True)
    d3.download_button("⬇  Cover letter · PDF", f["cl_pdf"][1], f["cl_pdf"][0], "application/pdf", use_container_width=True)
    d4.download_button("⬇  Cover letter · DOCX", f["cl_docx"][1], f["cl_docx"][0], use_container_width=True)

    def chips(items, cls=""):
        items = [esc(i) for i in (items or []) if i]
        if not items:
            return '<div class="muted" style="margin-bottom:.8rem">None</div>'
        return '<div class="chips">' + "".join(f'<span class="chip {cls}">{i}</span>' for i in items) + "</div>"

    left, right = st.columns([3, 2])
    with left:
        st.markdown(f'<div class="card"><div class="section-title">Cover letter</div><div class="letter">{esc(result["letter"])}</div></div>',
                    unsafe_allow_html=True)
    with right:
        recs = "".join(f'<div class="muted" style="margin-top:.35rem">{esc(r)}</div>' for r in (match.get("recommendations") or []))
        st.markdown(f"""
            <div class="card"><div class="section-title">Role summary</div><div style="font-size:.9rem">{esc(analysis.get("summary"))}</div></div>
            <div class="card"><div class="section-title">Must-have skills</div>{chips(req.get("must_have_skills"))}
              <div class="section-title">Nice-to-have</div>{chips(req.get("nice_to_have_skills"), "soft")}
              <div class="section-title">ATS keywords</div>{chips(kw.get("ats_keywords"), "soft")}
              <div class="section-title">Gaps to address</div>{chips(match.get("missing_required_skills"), "gap")}{recs}</div>
        """, unsafe_allow_html=True)
