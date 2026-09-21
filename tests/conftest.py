import json
import sys
from pathlib import Path

import pytest

# Allow `from utils...` / `from agents...` imports when running pytest from repo root.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.llm_client import LLMClient


class FakeLLMClient(LLMClient):
    """
    Test double for LLMClient. Returns pre-scripted responses in call order,
    so tests never hit a real LLM API.
    """

    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def generate_content(self, prompt, system_instruction="", config=None):
        self.calls.append({
            "prompt": prompt,
            "system_instruction": system_instruction,
            "config": config,
        })
        if not self.responses:
            raise AssertionError("FakeLLMClient ran out of scripted responses")
        response = self.responses.pop(0)
        return json.dumps(response) if isinstance(response, dict) else response


@pytest.fixture
def sample_profile():
    return {
        "personal_info": {
            "name": "Alex Candidate",
            "email": "alex@example.com",
            "phone": "+1 555 0100",
            "linkedin": "linkedin.com/in/alexcandidate",
            "location": "Remote",
        },
        "summary": "Backend engineer focused on distributed systems.",
        "skills": {
            "Technical": ["Python", "PostgreSQL", "Docker"],
            "Soft Skills": ["Communication"],
        },
        "experience": [
            {
                "company": "Acme Corp",
                "title": "Backend Engineer",
                "dates": "2022 - Present",
                "location": "Remote",
                "achievements": [
                    "Reduced API latency by 40% through query optimization.",
                    "Led migration from monolith to microservices.",
                ],
            }
        ],
        "education": [
            {"school": "State University", "degree": "B.Sc. Computer Science", "dates": "2018-2022"}
        ],
    }


@pytest.fixture
def sample_job_analysis():
    return {
        "role_info": {
            "title": "Senior Backend Engineer",
            "company": "Globex",
            "location": "Remote",
            "level": "Senior",
        },
        "requirements": {
            "must_have_skills": ["Python", "PostgreSQL", "Docker"],
            "nice_to_have_skills": ["Kubernetes"],
            "education": "Bachelor's degree",
            "years_experience": "3+ years",
        },
        "keywords": {
            "ats_keywords": ["Python", "PostgreSQL", "Docker", "Microservices"],
            "soft_skills": ["Communication"],
        },
        "summary": "Senior backend role focused on distributed systems at Globex.",
    }
