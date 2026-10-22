from __future__ import annotations

import re

from config.resume_profile import (
    GENERIC_ENGINEERING_TITLES,
    ROLE_FAMILY_KEYWORDS,
    SENIORITY_BLACKLIST,
    STRONG_MATCH_KEYWORDS,
    SUPPORTING_MATCH_KEYWORDS,
)


def _normalize(text: str) -> str:
    return " ".join(text.lower().split())


def _matched_keywords(text: str, keywords: list[str]) -> list[str]:
    normalized_text = _normalize(text)
    matched = set()
    for keyword in keywords:
        normalized_keyword = _normalize(keyword)
        if " " not in normalized_keyword and len(normalized_keyword) <= 3:
            pattern = rf"(?<![a-z0-9]){re.escape(normalized_keyword)}(?![a-z0-9])"
            if re.search(pattern, normalized_text):
                matched.add(keyword)
        elif normalized_keyword in normalized_text:
            matched.add(keyword)
    return sorted(matched)


def evaluate_job_title(title: str, allowed_job_titles: list[str]) -> tuple[bool, bool, str]:
    normalized_title = _normalize(title)

    seniority_hits = _matched_keywords(normalized_title, SENIORITY_BLACKLIST)
    if seniority_hits:
        reason = f"Title indicates role level beyond target range: {', '.join(seniority_hits[:2])}"
        return True, False, reason

    title_hits = _matched_keywords(normalized_title, allowed_job_titles)
    if title_hits:
        reason = f"Direct title match: {', '.join(title_hits[:3])}"
        return False, True, reason

    return False, False, "No direct title match; checking description against resume profile"


def evaluate_job_fit(
    title: str,
    description: str,
    allowed_job_titles: list[str],
) -> tuple[bool, str]:
    combined_text = _normalize(f"{title}\n{description}")
    title_text = _normalize(title)

    seniority_hits = _matched_keywords(title_text, SENIORITY_BLACKLIST)
    if seniority_hits:
        return False, f"Title indicates role level beyond target range: {', '.join(seniority_hits[:2])}"

    title_hits = _matched_keywords(title_text, allowed_job_titles)
    generic_title_hits = _matched_keywords(title_text, GENERIC_ENGINEERING_TITLES)
    role_hits = _matched_keywords(combined_text, ROLE_FAMILY_KEYWORDS)
    strong_skill_hits = _matched_keywords(combined_text, STRONG_MATCH_KEYWORDS)
    supporting_skill_hits = _matched_keywords(combined_text, SUPPORTING_MATCH_KEYWORDS)

    if title_hits and (len(strong_skill_hits) >= 1 or len(role_hits) >= 1 or len(supporting_skill_hits) >= 1):
        matched = ", ".join((title_hits + strong_skill_hits + role_hits)[:5])
        return True, f"Title and skills align with resume profile ({matched})"

    if generic_title_hits and (len(strong_skill_hits) >= 1 or len(role_hits) >= 1):
        matched = ", ".join((generic_title_hits + strong_skill_hits + supporting_skill_hits)[:5])
        return True, f"Generic engineering title matched by backend/AI overlap ({matched})"

    if len(role_hits) >= 1 and (len(strong_skill_hits) >= 2 or (len(strong_skill_hits) >= 1 and len(supporting_skill_hits) >= 1)):
        matched = ", ".join((role_hits + strong_skill_hits + supporting_skill_hits)[:6])
        return True, f"Description strongly overlaps with resume profile ({matched})"

    if "python" in combined_text and (len(strong_skill_hits) >= 1 or len(role_hits) >= 1):
        matched = ", ".join((strong_skill_hits + role_hits)[:4])
        return True, f"Python/AI backend stack matched ({matched})"

    total_hits = role_hits + strong_skill_hits + supporting_skill_hits
    if total_hits:
        matched = ", ".join(total_hits[:6])
        return False, f"Insufficient overlap with resume profile ({matched})"

    return False, "No meaningful AI/backend/software overlap found in the description"
