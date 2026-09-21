from agents.job_analyzer import JobAnalyzer
from tests.conftest import FakeLLMClient


def test_analyze_returns_structured_result(sample_job_analysis):
    client = FakeLLMClient(responses=[sample_job_analysis])
    analyzer = JobAnalyzer(client)

    result = analyzer.analyze("We are hiring a Senior Backend Engineer at Globex...")

    assert result["role_info"]["title"] == "Senior Backend Engineer"
    assert "Python" in result["requirements"]["must_have_skills"]


def test_analyze_resets_hallucinated_company_name():
    raw_text = "We are hiring a Backend Engineer. Location: Remote."
    hallucinated = {
        "role_info": {"title": "Backend Engineer", "company": "TotallyMadeUpCo", "location": "Remote", "level": "Mid"},
        "requirements": {"must_have_skills": [], "nice_to_have_skills": [], "education": "", "years_experience": ""},
        "keywords": {"ats_keywords": [], "soft_skills": []},
        "summary": "",
    }
    client = FakeLLMClient(responses=[hallucinated])
    analyzer = JobAnalyzer(client)

    result = analyzer.analyze(raw_text)

    assert result["role_info"]["company"] == "Unknown"


def test_analyze_keeps_company_name_found_in_text():
    raw_text = "We are hiring a Backend Engineer at Globex. Location: Remote."
    analysis = {
        "role_info": {"title": "Backend Engineer", "company": "Globex", "location": "Remote", "level": "Mid"},
        "requirements": {"must_have_skills": [], "nice_to_have_skills": [], "education": "", "years_experience": ""},
        "keywords": {"ats_keywords": [], "soft_skills": []},
        "summary": "",
    }
    client = FakeLLMClient(responses=[analysis])
    analyzer = JobAnalyzer(client)

    result = analyzer.analyze(raw_text)

    assert result["role_info"]["company"] == "Globex"
