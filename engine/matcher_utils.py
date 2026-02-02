#!/usr/bin/env python3
"""
ANTIGRAVITY TAILOR - Matcher Utils
Utilities for matching jobs against Master CV profile.
"""

import re
import json
from pathlib import Path
from typing import List, Set, Optional
from dataclasses import dataclass

# Optional: Ollama for smarter keyword extraction
try:
    import requests
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False


# ============== CONFIG ==============

MASTER_PROFILE_PATH = Path(__file__).parent.parent / "master_profile_v8.json"
SCRAPER_MATCH_THRESHOLD = 0.30  # Minimum match score to keep a job (significantly lowered)

# Explicit Log for Source of Truth
print(f"🔒 [SYSTEM] Enforcing Source of Truth: {MASTER_PROFILE_PATH.name}")
if not MASTER_PROFILE_PATH.exists():
    print(f"❌ [CRITICAL] Master Profile NOT FOUND at {MASTER_PROFILE_PATH}")
else:
    print(f"✅ [SYSTEM] Master Profile loaded successfully ({MASTER_PROFILE_PATH.stat().st_size} bytes)")


# ============== STOPWORDS ==============

STOPWORDS_PT = {
    "de", "da", "do", "das", "dos", "em", "no", "na", "nos", "nas",
    "para", "com", "por", "uma", "um", "que", "ser", "ter", "como",
    "sua", "seu", "suas", "seus", "esta", "este", "ou", "ao", "aos",
    "pela", "pelo", "sobre", "entre", "mais", "muito", "bem", "bom",
    "nosso", "nossa", "nossos", "nossas", "voce", "você", "vocês"
}

STOPWORDS_EN = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "as", "is", "was", "are", "were", "been",
    "be", "have", "has", "had", "do", "does", "did", "will", "would",
    "could", "should", "may", "might", "must", "shall", "can", "this",
    "that", "these", "those", "it", "its", "they", "them", "their",
    "we", "us", "our", "you", "your", "who", "which", "what", "when",
    "where", "how", "why", "all", "each", "every", "both", "few", "more",
    "most", "other", "some", "such", "no", "not", "only", "own", "same"
}

STOPWORDS_ALL = STOPWORDS_PT | STOPWORDS_EN


# ============== KEYWORD EXTRACTION ==============

def extract_keywords_from_text(text: str, use_ollama: bool = False) -> List[str]:
    """
    Extract relevant keywords from job description text.
    Uses Ollama if available and enabled, otherwise regex fallback.
    
    Returns:
        List of normalized keywords (lowercase, no duplicates order preserved)
    """
    if use_ollama and OLLAMA_AVAILABLE:
        keywords = _extract_keywords_ollama(text)
        if keywords:
            return keywords
    
    # Fallback: regex-based extraction
    return _extract_keywords_regex(text)


def _extract_keywords_regex(text: str) -> List[str]:
    """Regex-based keyword extraction (fallback)"""
    # Normalize text
    text = text.lower()
    
    # Common tech/business terms patterns
    patterns = [
        # Tech skills with versions/variations
        r'\b(?:python|java|javascript|typescript|sql|nosql|react|vue|angular|node\.?js|docker|kubernetes|aws|gcp|azure|terraform|ci/cd)\b',
        r'\b(?:machine\s*learning|deep\s*learning|nlp|llm|rag|ai|ml|data\s*science)\b',
        r'\b(?:agile|scrum|kanban|jira|confluence)\b',
        r'\b(?:product\s*manager|product\s*owner|pm|po|gpm|tpm)\b',
        r'\b(?:gtm|go[\s\-]?to[\s\-]?market|b2b|b2c|saas|crm|erp)\b',
        r'\b(?:api|rest|graphql|microservices|sdk)\b',
        r'\b(?:kpi|okr|roi|cac|ltv|mrr|arr)\b',
        r'\b(?:marketing|growth|branding|performance|analytics)\b',
        r'\b(?:stakeholder|roadmap|strategy|planning)\b',
        r'\b(?:hubspot|salesforce|meta\s*ads|google\s*ads|analytics)\b',
    ]
    
    keywords = set()
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        keywords.update(m.lower().strip() for m in matches)
    
    # Also extract capitalized multi-word terms (likely proper nouns / technologies)
    capitalized_terms = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
    for term in capitalized_terms:
        if len(term) > 2 and term.lower() not in STOPWORDS_ALL:
            keywords.add(term.lower())
    
    # Extract words that look like skills (alphanumeric, 3+ chars)
    words = re.findall(r'\b[a-zA-Z][a-zA-Z0-9\+\#\.]{2,}\b', text.lower())
    for word in words:
        if word not in STOPWORDS_ALL and len(word) >= 3:
            keywords.add(word)
    
    return list(keywords)


def _extract_keywords_ollama(text: str, model: str = "llama3.2") -> Optional[List[str]]:
    """Use local Ollama for smarter keyword extraction"""
    try:
        prompt = f"""Extract the most important skills, technologies, and requirements from this job description.
Return ONLY a JSON array of keywords, nothing else.

Job Description:
{text[:2000]}

Example output: ["python", "machine learning", "product management", "stakeholder management"]
"""
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": model, "prompt": prompt, "stream": False},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json().get("response", "")
            # Extract JSON array from response
            match = re.search(r'\[.*?\]', result, re.DOTALL)
            if match:
                keywords = json.loads(match.group())
                return [k.lower().strip() for k in keywords if isinstance(k, str)]
    except Exception:
        pass
    
    return None


# ============== PROFILE LOADING ==============

def get_profile_skills(master_cv_path: Path = None) -> Set[str]:
    """
    Extract all skills from the Master CV profile.
    
    Returns:
        Set of normalized skill names
    """
    if master_cv_path is None:
        master_cv_path = MASTER_PROFILE_PATH
    
    if not master_cv_path.exists():
        return set()
    
    with open(master_cv_path, 'r', encoding='utf-8') as f:
        profile = json.load(f)
    
    skills = set()
    
    # Extract from skills sections
    skills_data = profile.get('skills', {})
    for category in skills_data.values():
        if isinstance(category, list):
            for item in category:
                if isinstance(item, dict):
                    name = item.get('name', '').lower().strip()
                    if name:
                        skills.add(name)
                elif isinstance(item, str):
                    skills.add(item.lower().strip())
    
    # Extract from headlines_variants (attack angles)
    headlines = profile.get('headlines_variants', {})
    for key, headline in headlines.items():
        if key.startswith('_'):  # Skip comments
            continue
        if isinstance(headline, str):
            # Extract all meaningful words from headlines (not just capitalized)
            words = re.findall(r'\b[a-zA-Z][a-zA-Z\+\-]{2,}\b', headline)
            for word in words:
                word_lower = word.lower()
                if word_lower not in STOPWORDS_ALL and len(word_lower) >= 3:
                    skills.add(word_lower)
    
    # Extract keywords from experience STAR bullets
    experiences = profile.get('experiencias', [])
    for exp in experiences:
        stars = exp.get('stars', [])
        for star in stars:
            keywords = star.get('keywords', [])
            for kw in keywords:
                skills.add(kw.lower().strip())
    
    # Extract from stack_tecnica
    for exp in experiences:
        stack = exp.get('stack_tecnica', [])
        for tech in stack:
            skills.add(tech.lower().strip())
    
    return skills


# ============== MATCHING ==============

def calculate_match_score(job_keywords: List[str], profile_skills: Set[str]) -> float:
    """
    Calculate match score between job keywords and profile skills.
    Uses weighted Jaccard-like similarity.
    
    Returns:
        Float between 0.0 and 1.0
    """
    if not job_keywords:
        return 0.0
    
    job_set = set(kw.lower().strip() for kw in job_keywords)
    profile_lower = {s.lower() for s in profile_skills}
    
    # Direct matches
    direct_matches = job_set & profile_lower
    
    # Partial matches (substring matching for compound terms)
    partial_matches = set()
    for job_kw in job_set:
        for profile_skill in profile_lower:
            if job_kw in profile_skill or profile_skill in job_kw:
                if job_kw not in direct_matches:
                    partial_matches.add(job_kw)
                    break
    
    # Weighted score: direct matches worth 1.0, partial worth 0.5
    match_count = len(direct_matches) + (len(partial_matches) * 0.5)
    
    # Score relative to job requirements, but cap denominator to be less punishing
    # for long job descriptions with many incidental keywords
    denominator = len(job_set)
    if denominator > 15:
        denominator = 15
    
    if denominator == 0:
        return 0.0
    
    score = match_count / denominator
    
    # Cap at 1.0
    return min(1.0, score)


@dataclass
class MatchResult:
    """Result of matching a job against profile"""
    score: float
    matched_keywords: List[str]
    missing_keywords: List[str]
    total_keywords: int
    
    @property
    def is_above_threshold(self) -> bool:
        return self.score >= SCRAPER_MATCH_THRESHOLD
    
    def to_dict(self) -> dict:
        return {
            "score": round(self.score, 3),
            "matched": self.matched_keywords,
            "missing": self.missing_keywords,
            "total": self.total_keywords,
            "above_threshold": self.is_above_threshold
        }


def match_job_to_profile(
    job_description: str,
    master_cv_path: Path = None,
    use_ollama: bool = False
) -> MatchResult:
    """
    Main function: Match a job description against the Master CV profile.
    
    Args:
        job_description: Full text of job posting
        master_cv_path: Path to master CV JSON (uses default if None)
        use_ollama: Whether to try Ollama for keyword extraction
    
    Returns:
        MatchResult with score and keyword details
    """
    # Extract keywords from job
    job_keywords = extract_keywords_from_text(job_description, use_ollama=use_ollama)
    
    # Get profile skills
    profile_skills = get_profile_skills(master_cv_path)
    
    # Calculate score
    score = calculate_match_score(job_keywords, profile_skills)
    
    # Determine matched and missing
    job_set = set(kw.lower().strip() for kw in job_keywords)
    profile_lower = {s.lower() for s in profile_skills}
    
    matched = []
    missing = []
    
    for kw in job_keywords:
        kw_lower = kw.lower().strip()
        if kw_lower in profile_lower:
            matched.append(kw)
        else:
            # Check partial match
            found = False
            for ps in profile_lower:
                if kw_lower in ps or ps in kw_lower:
                    matched.append(kw)
                    found = True
                    break
            if not found:
                missing.append(kw)
    
    return MatchResult(
        score=score,
        matched_keywords=matched,
        missing_keywords=missing,
        total_keywords=len(job_keywords)
    )


# ============== CLI ==============

if __name__ == "__main__":
    # Quick test
    test_description = """
    We're looking for a Senior Product Manager to lead our AI initiatives.
    You'll work with Python, machine learning, and LLM technologies.
    Experience with GTM strategy, stakeholder management, and data-driven decision making required.
    Nice to have: n8n, Docker, SQL, marketing automation.
    """
    
    print("🔍 Testing matcher_utils...")
    print(f"Profile skills: {len(get_profile_skills())} loaded")
    
    result = match_job_to_profile(test_description)
    print(f"\n📊 Match Result:")
    print(f"   Score: {result.score:.0%}")
    print(f"   Above threshold ({SCRAPER_MATCH_THRESHOLD:.0%}): {result.is_above_threshold}")
    print(f"   Matched: {result.matched_keywords[:10]}...")
    print(f"   Missing: {result.missing_keywords[:10]}...")
