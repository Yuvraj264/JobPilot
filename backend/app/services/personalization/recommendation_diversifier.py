from typing import List, Dict, Any, Set
from app.models.job import Job


class RecommendationDiversifier:
    """
    Diversifies recommendation lists by balancing roles, companies, locations, and sources.
    Incorporates STRICT vs EXPLORATION mode filters.
    """

    @classmethod
    def diversify(
        cls, 
        matches: List[Dict[str, Any]], 
        limit: int = 10, 
        allow_adjacent: bool = True,
        mode: str = "STRICT_PREFERENCE"  # STRICT_PREFERENCE or EXPLORATION
    ) -> List[Dict[str, Any]]:
        if not matches:
            return []

        # Sort matches by score descending
        sorted_matches = sorted(matches, key=lambda m: m.get("overall_score", 0.0), reverse=True)
        
        # Apply Strict Preference filter (if STRICT mode, prune out low-confidence/low-matching adjacent roles)
        if mode == "STRICT_PREFERENCE":
            # Strict mode: exclude roles with overall score < 75 or match rating indicating poor preference alignment
            sorted_matches = [m for m in sorted_matches if m.get("overall_score", 0.0) >= 75.0]
        else:
            # Exploration mode: include nearby roles, but still filter out completely unrelated jobs (score < 60)
            sorted_matches = [m for m in sorted_matches if m.get("overall_score", 0.0) >= 60.0]

        selected = []
        seen_companies = set()
        seen_roles = []  # list of word sets

        remaining = list(sorted_matches)
        
        # Pass 1: Strict diversification (avoid duplicate companies or overlapping roles)
        deferred = []
        for m in remaining:
            job = m.get("job")
            if not job:
                selected.append(m)
                continue

            company = (job.company_name or "").strip().lower()
            title = (job.title or "").strip().lower()
            title_words = set(w for w in title.split() if len(w) > 2)

            # Check if this company is already in top recommendations
            company_seen = company in seen_companies
            # Check if title overlaps heavily with already selected titles
            role_overlap = any(len(title_words.intersection(seen_words)) >= 2 for seen_words in seen_roles)

            if company_seen or role_overlap:
                deferred.append(m)
            else:
                selected.append(m)
                seen_companies.add(company)
                seen_roles.append(title_words)
                if len(selected) >= limit:
                    break

        # Pass 2: Relaxed diversification (fill up using deferred list)
        for m in deferred:
            if len(selected) >= limit:
                break
            selected.append(m)

        # Pass 3: Safe fallback if list is still not filled
        if len(selected) < limit:
            for m in sorted_matches:
                if len(selected) >= limit:
                    break
                if m not in selected:
                    selected.append(m)

        return selected
