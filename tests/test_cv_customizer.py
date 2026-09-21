from agents.cv_customizer import CVCustomizer
from tests.conftest import FakeLLMClient


def test_customize_returns_parsed_cv(sample_profile, sample_job_analysis):
    customized = {
        "personal_info": sample_profile["personal_info"],
        "summary": "Tailored summary for Globex.",
        "skills": {"Technical": ["Python", "PostgreSQL"], "Soft Skills": []},
        "experience": [sample_profile["experience"][0]],
        "education": sample_profile["education"],
    }
    client = FakeLLMClient(responses=[customized])
    customizer = CVCustomizer(client)

    result = customizer.customize(sample_profile, sample_job_analysis)

    assert result["summary"] == "Tailored summary for Globex."
    assert "Python" in result["skills"]["Technical"]


def test_customize_includes_rag_snippets_in_prompt(sample_profile, sample_job_analysis):
    client = FakeLLMClient(responses=[{"summary": "ok"}])
    customizer = CVCustomizer(client)
    snippets = [{"content": "Reduced API latency by 40%.", "metadata": {"company": "Acme Corp"}}]

    customizer.customize(sample_profile, sample_job_analysis, relevant_snippets=snippets)

    prompt = client.calls[0]["prompt"]
    assert "Reduced API latency by 40%" in prompt
