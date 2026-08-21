import re
from typing import Dict, List, Any, Optional

COMMON_SKILLS = {
    "Programming": ["Python", "JavaScript", "TypeScript", "Java", "C++", "C#", "Go", "Rust", "Ruby", "PHP", "Swift", "Kotlin"],
    "Testing": ["Playwright", "Selenium", "Cypress", "PyTest", "JUnit", "Postman", "Appium", "Jest", "Manual Testing", "API Testing", "Jira"],
    "Database": ["PostgreSQL", "MySQL", "MongoDB", "SQLite", "Redis", "Oracle", "Elasticsearch", "SQL"],
    "Framework": ["FastAPI", "React", "Node.js", "Django", "Flask", "Express", "Spring Boot", "Next.js", "Angular", "Vue"],
    "Cloud": ["AWS", "Google Cloud", "Azure", "Docker", "Kubernetes", "Terraform", "Serverless"],
    "DevOps": ["Git", "GitHub Actions", "Jenkins", "CI/CD", "Linux", "Bash", "Docker Compose"],
    "Soft Skill": ["Communication", "Problem Solving", "Leadership", "Teamwork", "Agile", "Scrum"]
}


class DeterministicParser:
    """
    Layer 1 Deterministic Resume Parser.
    Extracts contact details, sections, skills, education, experience, projects, and certifications using regex & pattern heuristics.
    """

    @staticmethod
    def parse(text: str) -> Dict[str, Any]:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        
        contact = DeterministicParser.extract_contact(text, lines)
        sections = DeterministicParser.detect_sections(text)
        summary = DeterministicParser.extract_summary(sections, text)
        skills = DeterministicParser.extract_skills(text)
        education = DeterministicParser.extract_education(sections, text)
        experience = DeterministicParser.extract_experience(sections, text)
        projects = DeterministicParser.extract_projects(sections, text)
        certifications = DeterministicParser.extract_certifications(sections, text)

        return {
            "contact": contact,
            "summary": summary,
            "skills": skills,
            "education": education,
            "experience": experience,
            "projects": projects,
            "certifications": certifications,
        }

    @staticmethod
    def extract_contact(text: str, lines: List[str]) -> Dict[str, Optional[str]]:
        email_match = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)
        phone_match = re.search(r"(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}|\b\d{3}[-.\s]\d{4}\b", text)
        
        linkedin_match = re.search(r"(https?://)?(www\.)?linkedin\.com/in/[a-zA-Z0-9_-]+", text, re.IGNORECASE)
        github_match = re.search(r"(https?://)?(www\.)?github\.com/[a-zA-Z0-9_-]+", text, re.IGNORECASE)
        portfolio_match = re.search(r"(https?://)?(www\.)?[a-zA-Z0-9_-]+\.(io|dev|com|me)", text, re.IGNORECASE)

        # Name is usually the first non-empty line
        name = lines[0] if lines else "Unknown Candidate"
        # If first line contains email/phone, fall back to "Candidate"
        if email_match and email_match.group(0) in name:
            name = "Candidate"

        return {
            "name": name,
            "email": email_match.group(0) if email_match else None,
            "phone": phone_match.group(0) if phone_match else None,
            "location": None,
            "linkedin_url": linkedin_match.group(0) if linkedin_match else None,
            "github_url": github_match.group(0) if github_match else None,
            "portfolio_url": portfolio_match.group(0) if portfolio_match else None,
        }

    @staticmethod
    def detect_sections(text: str) -> Dict[str, str]:
        """
        Splits text by common section headers.
        """
        header_patterns = {
            "SUMMARY": r"(?:SUMMARY|PROFESSIONAL SUMMARY|OBJECTIVE|PROFILE)",
            "SKILLS": r"(?:SKILLS|TECHNICAL SKILLS|CORE COMPETENCIES|TECHNOLOGIES)",
            "EXPERIENCE": r"(?:EXPERIENCE|WORK EXPERIENCE|EMPLOYMENT|WORK HISTORY)",
            "EDUCATION": r"(?:EDUCATION|ACADEMIC BACKGROUND|QUALIFICATIONS)",
            "PROJECTS": r"(?:PROJECTS|KEY PROJECTS|PERSONAL PROJECTS)",
            "CERTIFICATIONS": r"(?:CERTIFICATIONS|LICENSES|CERTIFICATES)"
        }

        pattern = r"\n(?=(" + "|".join(header_patterns.values()) + r")[\s:]*\n)"
        splits = re.split(pattern, "\n" + text, flags=re.IGNORECASE)

        sections: Dict[str, str] = {}
        curr_key = "HEADER"
        for block in splits:
            if not block:
                continue
            block_upper = block.strip().upper()
            found_header = None
            for key, pat in header_patterns.items():
                if re.match(r"^" + pat + r"[\s:]*$", block_upper):
                    found_header = key
                    break

            if found_header:
                curr_key = found_header
            else:
                sections[curr_key] = sections.get(curr_key, "") + "\n" + block.strip()

        return sections

    @staticmethod
    def extract_summary(sections: Dict[str, str], text: str) -> Optional[str]:
        if "SUMMARY" in sections:
            return sections["SUMMARY"].strip()
        # Fallback heuristic: check early lines
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        for line in lines[1:5]:
            if len(line) > 50:
                return line
        return None

    @staticmethod
    def extract_skills(text: str) -> List[Dict[str, str]]:
        extracted = []
        seen = set()

        for category, skill_list in COMMON_SKILLS.items():
            for skill in skill_list:
                # Handle skills with special characters (like C++, C#, .NET, Node.js)
                escaped_skill = re.escape(skill)
                if skill.isalnum():
                    pattern = r"\b" + escaped_skill + r"\b"
                else:
                    pattern = r"(?:\s|^|,|/)" + escaped_skill + r"(?:\s|$|,|/|\.)"

                if re.search(pattern, text, re.IGNORECASE):
                    if skill.lower() not in seen:
                        seen.add(skill.lower())
                        extracted.append({"name": skill, "category": category})

        return extracted

    @staticmethod
    def extract_education(sections: Dict[str, str], text: str) -> List[Dict[str, Any]]:
        edu_text = sections.get("EDUCATION", text)
        results = []

        degrees = ["Bachelor", "B.S.", "B.Tech", "B.E.", "Master", "M.S.", "M.Tech", "Ph.D", "Associate", "Diploma"]
        for line in edu_text.splitlines():
            for deg in degrees:
                if deg.lower() in line.lower():
                    years = re.findall(r"\b(19\d{2}|20\d{2})\b", line)
                    start_yr = int(years[0]) if len(years) > 0 else None
                    end_yr = int(years[1]) if len(years) > 1 else (int(years[0]) if len(years) == 1 else None)
                    
                    results.append({
                        "institution": line.split(" - ")[0] if " - " in line else line[:100],
                        "degree": deg,
                        "field_of_study": line if len(line) < 100 else None,
                        "start_year": start_yr,
                        "end_year": end_yr,
                        "grade_or_cgpa": None,
                    })
                    break

        return results

    @staticmethod
    def extract_experience(sections: Dict[str, str], text: str) -> List[Dict[str, Any]]:
        exp_text = sections.get("EXPERIENCE", "")
        if not exp_text:
            return []

        results = []
        lines = [line.strip() for line in exp_text.splitlines() if line.strip()]
        for line in lines:
            if any(term in line.lower() for term in ["engineer", "developer", "analyst", "manager", "intern", "lead", "specialist"]):
                years = re.findall(r"\b(19\d{2}|20\d{2})\b", line)
                currently = "present" in line.lower() or "current" in line.lower()
                results.append({
                    "company": "Company / Organization",
                    "role": line[:150],
                    "location": None,
                    "start_date": years[0] if len(years) > 0 else None,
                    "end_date": "Present" if currently else (years[1] if len(years) > 1 else None),
                    "currently_working": currently,
                    "description": line,
                })

        return results

    @staticmethod
    def extract_projects(sections: Dict[str, str], text: str) -> List[Dict[str, Any]]:
        proj_text = sections.get("PROJECTS", "")
        if not proj_text:
            return []

        results = []
        lines = [line.strip() for line in proj_text.splitlines() if line.strip()]
        for line in lines:
            if len(line) > 5:
                results.append({
                    "name": line[:150],
                    "description": line,
                    "technologies": [],
                    "project_url": None,
                    "start_date": None,
                    "end_date": None,
                })
        return results[:5]  # Limit fallback to top 5

    @staticmethod
    def extract_certifications(sections: Dict[str, str], text: str) -> List[Dict[str, Any]]:
        cert_text = sections.get("CERTIFICATIONS", "")
        if not cert_text:
            return []

        results = []
        lines = [line.strip() for line in cert_text.splitlines() if line.strip()]
        for line in lines:
            if len(line) > 3:
                results.append({
                    "name": line[:150],
                    "issuing_organization": "Certifying Body",
                    "issue_date": None,
                    "expiry_date": None,
                    "credential_url": None,
                })
        return results[:5]
