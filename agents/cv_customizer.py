"""
CV Customizer Agent
Role: Tailor the master profile to match specific job requirements.
"""

from typing import Dict, Any, List
from utils.llm_client import LLMClient
import json

class CVCustomizer:
    """
    Agent responsible for rewriting CV content to target a specific job.
    """

    def __init__(self, client: LLMClient):
        self.client = client
        self.system_instruction = """
        You are an expert Career Coach and Professional Resume Writer.
        Your goal is to rewrite candidate profiles to perfectly align with target job descriptions.
        You use the STAR method (Situation, Task, Action, Result) to quantify achievements.
        You ensure high ATS compliance by naturally integrating keywords.
        Return raw JSON only.
        """

    def customize(self, profile: Dict[str, Any], job_analysis: Dict[str, Any], relevant_snippets: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Customize the candidate profile for the analyzed job.
        
        Args:
            profile: Candidates base profile
            job_analysis: Structured analysis of the target job
            relevant_snippets: (Optional) High-relevance snippets retrieved via RAG
            
        Returns:
            Customized profile dictionary ready for document generation
        """
        print("🎨 Customizing candidate profile using RAG contexts...")
        
        # Format snippets for prompt
        rag_context = ""
        if relevant_snippets:
            rag_context = "\nPRIORITY CONTEXT (Top Relevant Experience):\n" + json.dumps(relevant_snippets, indent=2)

        prompt = f"""
        Tailor this candidate's profile to match the job requirements perfectly.
        {rag_context}

        CANDIDATE BASE PROFILE:
        {json.dumps(profile, indent=2)}

        JOB ANALYSIS:
        {json.dumps(job_analysis, indent=2)}

        TASK:
        1. Rewrite the "Professional Summary" to highlight relevant experience for THIS job (2-3 sentences only, no repetition).
        2. Reorder and filter "Core Skills" to prioritize the job's "must_have_skills". Remove duplicates.
        3. Select ONLY the top 3-4 most relevant "Work Experience" entries that match the job requirements.
        4. For each selected role, rewrite bullet points to:
           - Use keywords from the job description
           - Emphasize overlapping skills
           - Use STAR method (Situation, Task, Action, Result) where possible
           - Keep only 3-4 most impactful achievements per role (no repetition)
        5. Include ALL education entries (but only once, no duplicates).
        6. DO NOT repeat the same information in different sections.
        7. If an experience/education appears multiple times, include it only once.
        
        OUTPUT FORMAT (JSON):
        {{
            "personal_info": {{ ...keep original... }},
            "summary": "Tailored summary...",
            "skills": {{
                "Technical": ["..."],
                "Soft Skills": ["..."]
            }},
            "experience": [
                {{
                    "company": "...",
                    "title": "...",
                    "dates": "...",
                    "achievements": [
                        "Optimized bullet point 1...",
                        "Optimized bullet point 2..."
                    ]
                }}
            ],
            "education": [ ...keep original... ]
        }}

        CRITICAL RULES:
        1. Do NOT invent experiences. Only reframe existing ones.
        2. Use EXACT vocabulary from the job analysis where applicable.
        3. Focus on impact and metrics (STAR method).
        4. Maintain a professional, executive tone.
        5. NO REPETITION: Each piece of information should appear only once.
        6. NO DUPLICATES: If the same experience/education appears multiple times in input, include it only once.
        7. BE CONCISE: Summary should be 2-3 sentences, not repeating what's in experience section.
        8. FILTER WISELY: Only include experiences that are relevant to the job. Skip irrelevant ones.
        """

        # Temperature 0.5 for a balance of creativity and adherence to facts
        return self.client.generate_json(prompt, system_instruction=self.system_instruction, temperature=0.5)
