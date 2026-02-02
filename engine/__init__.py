#!/usr/bin/env python3
"""
ANTIGRAVITY TAILOR - Engine Package
"""

from .interpreter import (
    JobInterpreter,
    validate_job_scraping,
    create_job_from_scrape,
    HARD_SKILLS_PATTERNS,
    SOFT_SKILLS_PATTERNS,
    SENIORITY_PATTERNS,
    JOB_TYPE_PATTERNS
)

from .matcher import (
    MasterCV,
    CVMatcher,
    build_resume
)

__all__ = [
    # Interpreter
    "JobInterpreter",
    "validate_job_scraping",
    "create_job_from_scrape",
    "HARD_SKILLS_PATTERNS",
    "SOFT_SKILLS_PATTERNS",
    "SENIORITY_PATTERNS",
    "JOB_TYPE_PATTERNS",
    # Matcher
    "MasterCV",
    "CVMatcher",
    "build_resume"
]
