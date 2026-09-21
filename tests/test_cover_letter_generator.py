from agents.cover_letter_generator import CoverLetterGenerator
from tests.conftest import FakeLLMClient


def test_generate_returns_letter_text(sample_profile, sample_job_analysis):
    letter_text = "Dear Hiring Manager,\n\nI'm excited to apply..."
    client = FakeLLMClient(responses=[letter_text])
    generator = CoverLetterGenerator(client)

    result = generator.generate(sample_profile, sample_job_analysis)

    assert result == letter_text
    assert client.calls[0]["config"]["temperature"] == 0.7
