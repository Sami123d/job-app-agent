from utils.match_calculator import MatchCalculator


def test_calculate_match_score_counts_required_skill_matches(sample_profile, sample_job_analysis):
    calculator = MatchCalculator()

    result = calculator.calculate_match_score(sample_profile, sample_job_analysis)

    assert result["required_skills_matched"] == 3  # Python, PostgreSQL, Docker
    assert result["required_skills_total"] == 3
    assert result["required_skills_score"] == 100.0
    assert result["overall_score"] > 0


def test_calculate_match_score_reports_missing_required_skills(sample_profile):
    job_analysis = {
        "requirements": {
            "must_have_skills": ["Python", "Rust", "Kubernetes"],
            "nice_to_have_skills": [],
        },
        "keywords": {"ats_keywords": []},
    }
    calculator = MatchCalculator()

    result = calculator.calculate_match_score(sample_profile, job_analysis)

    assert "rust" in result["missing_required_skills"] or "kubernetes" in result["missing_required_skills"]
    assert result["required_skills_matched"] < result["required_skills_total"]


def test_calculate_match_score_handles_no_requirements():
    calculator = MatchCalculator()
    result = calculator.calculate_match_score({}, {})

    assert result["overall_score"] == 100
