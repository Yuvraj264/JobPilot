from typing import Dict, List, Tuple
from app.models.profile import UserProfile
from app.schemas.profile import ProfileCompletenessResponse, ProfileSummaryResponse


class CompletenessService:
    """
    Backend service calculating profile completeness percentage and missing section identifiers.
    Deterministic (non-AI).
    """

    @staticmethod
    def calculate_completeness(profile: UserProfile) -> ProfileCompletenessResponse:
        if not profile:
            return ProfileCompletenessResponse(
                percentage=0,
                missing_sections=[
                    "basic_information",
                    "professional_information",
                    "education",
                    "skills",
                    "projects",
                    "certifications",
                    "job_preferences",
                ],
            )

        score = 0
        missing: List[str] = []

        # 1. Basic Information (20 points max)
        basic_fields = [profile.full_name, profile.email, profile.phone, profile.current_city, profile.current_country]
        filled_basic = sum(1 for f in basic_fields if f and str(f).strip())
        score += int((filled_basic / 5) * 20)
        if filled_basic < 5:
            missing.append("basic_information")

        # 2. Professional Information (15 points max)
        prof_fields = [profile.professional_summary, profile.current_role, profile.employment_status]
        filled_prof = sum(1 for f in prof_fields if f and str(f).strip())
        # years_of_experience is always float, so valid
        if profile.years_of_experience is not None:
            filled_prof += 1
        score += int((filled_prof / 4) * 15)
        if filled_prof < 4 or not profile.professional_summary:
            missing.append("professional_summary")

        # 3. Education (15 points max)
        if profile.education and len(profile.education) > 0:
            score += 15
        else:
            missing.append("education")

        # 4. Skills (15 points max)
        skill_count = len(profile.skills) if profile.skills else 0
        if skill_count >= 3:
            score += 15
        elif skill_count > 0:
            score += int((skill_count / 3) * 15)
            missing.append("skills")
        else:
            missing.append("skills")

        # 5. Projects (15 points max)
        if profile.projects and len(profile.projects) > 0:
            score += 15
        else:
            missing.append("projects")

        # 6. Certifications (5 points max)
        if profile.certifications and len(profile.certifications) > 0:
            score += 5
        else:
            missing.append("certifications")

        # 7. Job Preferences (15 points max)
        pref = profile.job_preference
        if pref:
            pref_score = 0
            if pref.target_roles and len(pref.target_roles) > 0:
                pref_score += 5
            if pref.preferred_locations and len(pref.preferred_locations) > 0:
                pref_score += 5
            if pref.min_expected_salary or pref.max_expected_salary:
                pref_score += 5
            score += pref_score
            if pref_score < 15:
                missing.append("job_preferences")
        else:
            missing.append("job_preferences")

        # Clamp between 0 and 100
        final_percentage = max(0, min(100, score))

        return ProfileCompletenessResponse(
            percentage=final_percentage,
            missing_sections=missing,
        )

    @staticmethod
    def generate_summary(profile: UserProfile) -> ProfileSummaryResponse:
        """
        Returns a compact structured representation of the profile for matching engine / AI layer.
        """
        if not profile:
            return ProfileSummaryResponse(
                name="Unknown User",
                roles=[],
                locations=[],
                skills=[],
                experience_years=0.0,
                education_count=0,
                projects_count=0,
                certifications_count=0,
                profile_completeness=0,
            )

        completeness = CompletenessService.calculate_completeness(profile)
        roles = profile.job_preference.target_roles if profile.job_preference and profile.job_preference.target_roles else []
        locations = profile.job_preference.preferred_locations if profile.job_preference and profile.job_preference.preferred_locations else []
        skill_names = [s.name for s in profile.skills] if profile.skills else []

        return ProfileSummaryResponse(
            name=profile.full_name,
            roles=roles,
            locations=locations,
            skills=skill_names,
            experience_years=profile.years_of_experience,
            education_count=len(profile.education) if profile.education else 0,
            projects_count=len(profile.projects) if profile.projects else 0,
            certifications_count=len(profile.certifications) if profile.certifications else 0,
            profile_completeness=completeness.percentage,
        )
