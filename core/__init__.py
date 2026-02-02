#!/usr/bin/env python3
"""
ANTIGRAVITY TAILOR - Core Package
"""

from .models import (
    Language,
    Seniority,
    OutputFormat,
    MatchTier,
    JobValidation,
    Job,
    JobStatus,
    StrategicPlan,
    ExperienceMatch,
    MatchResult,
    ResumeOutput,
    PipelineState
)

from .config import (
    BASE_DIR,
    DATA_DIR,
    OUTPUT_DIR,
    JOBS_DIR,
    TEMPLATES_DIR,
    MASTER_CV_PT,
    MASTER_CV_EN,
    MASTER_CV_JUNIOR,
    TailorConfig,
    config
)

__all__ = [
    # Enums
    "Language",
    "Seniority", 
    "OutputFormat",
    "MatchTier",
    # Models
    "JobValidation",
    "Job",
    "JobStatus",
    "StrategicPlan",
    "ExperienceMatch",
    "MatchResult",
    "ResumeOutput",
    "PipelineState",
    # Config
    "BASE_DIR",
    "DATA_DIR",
    "OUTPUT_DIR",
    "JOBS_DIR",
    "TEMPLATES_DIR",
    "MASTER_CV_PT",
    "MASTER_CV_EN",
    "MASTER_CV_JUNIOR",
    "TailorConfig",
    "config"
]
