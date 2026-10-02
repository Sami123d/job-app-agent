"""End-to-end check of the Streamlit demo (streamlit_app.py) with a fake LLM."""
import json
import unittest.mock as mock
from pathlib import Path

import pytest

from tests.conftest import FakeLLMClient

st_testing = pytest.importorskip("streamlit.testing.v1")
ROOT = Path(__file__).resolve().parent.parent


def test_streamlit_demo_generates_documents(monkeypatch):
    profile = json.loads((ROOT / "data" / "demo_profile.json").read_text(encoding="utf-8"))
    analysis = {
        "role_info": {"title": "Senior Python Developer", "company": "FutureTech AI"},
        "requirements": {"must_have_skills": ["Python", "FastAPI"], "nice_to_have_skills": ["Redis"]},
        "keywords": {"ats_keywords": ["Python", "FastAPI"], "soft_skills": []},
        "summary": "Build APIs and agent systems.",
    }
    cv = {k: profile[k] for k in ("personal_info", "summary", "skills", "experience", "education")}
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")

    with mock.patch("utils.llm_factory.create_llm_client",
                    lambda provider=None: FakeLLMClient([analysis, cv, "Dear Hiring Manager, ..."])):
        at = st_testing.AppTest.from_file(str(ROOT / "streamlit_app.py"), default_timeout=60)
        at.run()
        at.button[0].click().run()   # "Use a sample job description"
        at.button[1].click().run()   # "Analyze & generate"

    assert not at.exception
    assert not at.error
    assert any("FutureTech AI" in s.value for s in at.subheader)
    assert [m.label for m in at.metric][0] == "Overall match"
