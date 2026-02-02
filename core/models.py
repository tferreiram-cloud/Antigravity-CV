#!/usr/bin/env python3
"""
ANTIGRAVITY TAILOR - Core Models
Dataclasses e tipos para o pipeline
"""

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Any
from enum import Enum
from datetime import datetime


class Language(Enum):
    PT = "pt"
    EN = "en"


class Seniority(Enum):
    JUNIOR = "junior"
    PLENO = "pleno"
    SENIOR = "senior"
    MANAGER = "manager"
    LEAD = "lead"


class OutputFormat(Enum):
    PDF = "pdf"
    DOCX = "docx"
    MARKDOWN = "md"
    HTML = "html"


class MatchTier(Enum):
    HIGH = "high"      # >70% match
    MEDIUM = "medium"  # 40-70% match
    LOW = "low"        # <40% match


class JobStatus(Enum):
    TODO = "todo"
    STRATEGY = "strategy"
    TAILORING = "tailoring"
    APPLIED = "applied"
    REJECTED = "rejected"


@dataclass
class StrategicPlan:
    ghost_notes: List[str]
    vulnerability_report: List[str]
    anti_overqualification_applied: bool
    suggested_narrative_shift: str
    approved: bool = False


# ============== JOB MODELS ==============

@dataclass
class JobValidation:
    """Checklist de validação do scraping"""
    cargo_found: bool = False
    empresa_found: bool = False
    description_readable: bool = False
    requirements_found: bool = False
    language_detected: str = ""
    raw_length: int = 0
    
    @property
    def is_valid(self) -> bool:
        """Retorna True se scraping foi bem sucedido"""
        return all([
            self.cargo_found,
            self.empresa_found,
            self.description_readable,
            self.raw_length > 100
        ])
    
    def get_failures(self) -> List[str]:
        """Lista de falhas de validação"""
        failures = []
        if not self.cargo_found:
            failures.append("Cargo não identificado")
        if not self.empresa_found:
            failures.append("Empresa não identificada")
        if not self.description_readable:
            failures.append("Descrição não legível")
        if not self.requirements_found:
            failures.append("Requisitos não encontrados")
        if self.raw_length < 100:
            failures.append("Texto muito curto")
        return failures
    
    def to_checklist_str(self) -> str:
        """Retorna checklist formatado"""
        checks = [
            f"[{'✓' if self.cargo_found else '✗'}] Cargo identificado",
            f"[{'✓' if self.empresa_found else '✗'}] Empresa identificada",
            f"[{'✓' if self.description_readable else '✗'}] Descrição legível",
            f"[{'✓' if self.requirements_found else '✗'}] Requisitos explícitos",
            f"[{'✓' if self.language_detected else '✗'}] Idioma: {self.language_detected or 'N/A'}",
        ]
        return "\n".join(checks)


@dataclass
class Job:
    """Estrutura de uma vaga"""
    id: str
    title: str
    company: str
    description: str
    url: str = ""
    location: str = ""
    source: str = "manual"
    status: JobStatus = JobStatus.TODO
    
    # Detalhes extraídos
    language: Language = Language.PT
    seniority: Optional[Seniority] = None
    job_type: str = "general"
    hard_skills: List[str] = field(default_factory=list)
    soft_skills: List[str] = field(default_factory=list)
    keywords_ats: List[str] = field(default_factory=list)
    
    # Plano Estratégico
    strategic_plan: Optional[StrategicPlan] = None
    
    # Metadados
    scraped_at: str = field(default_factory=lambda: datetime.now().isoformat())
    validation: Optional[JobValidation] = None
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "title": self.title,
            "company": self.company,
            "description": self.description,
            "url": self.url,
            "location": self.location,
            "source": self.source,
            "status": self.status.value if self.status else "todo",
            "language": self.language.value,
            "seniority": self.seniority.value if self.seniority else None,
            "job_type": self.job_type,
            "hard_skills": self.hard_skills,
            "soft_skills": self.soft_skills,
            "keywords_ats": self.keywords_ats,
            "strategic_plan": asdict(self.strategic_plan) if self.strategic_plan else None,
            "scraped_at": self.scraped_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Job':
        # Lazy status conversion
        status_val = data.get("status", "todo")
        try:
            status = JobStatus(status_val)
        except:
            status = JobStatus.TODO
            
        # Strategic plan
        strat_data = data.get("strategic_plan")
        strat_plan = None
        if strat_data:
            strat_plan = StrategicPlan(**strat_data)
            
        return cls(
            id=data["id"],
            title=data.get("title") or "",
            company=data.get("company") or "",
            description=data.get("description") or "",
            url=data.get("url") or "",
            location=data.get("location") or "",
            source=data.get("source") or "manual",
            status=status,
            language=Language(data.get("language") or "pt"),
            seniority=Seniority(data["seniority"]) if data.get("seniority") else None,
            job_type=data.get("job_type") or "general",
            hard_skills=data.get("hard_skills") or [],
            soft_skills=data.get("soft_skills") or [],
            keywords_ats=data.get("keywords_ats") or [],
            strategic_plan=strat_plan,
            scraped_at=data.get("scraped_at", datetime.now().isoformat())
        )
    
    @property
    def is_valid(self) -> bool:
        return self.validation.is_valid if self.validation else False


# ============== MATCH MODELS ==============

@dataclass
class ExperienceMatch:
    """Match de uma experiência com a vaga"""
    experience_id: int
    company: str
    role: str
    tier: str  # core ou contextual
    score: float  # 0.0 a 1.0
    matched_keywords: List[str] = field(default_factory=list)
    selected_bullets: List[str] = field(default_factory=list)


@dataclass
class MatchResult:
    """Resultado do matching CV vs Vaga"""
    total_score: float  # 0.0 a 1.0
    total_percentage: int  # 0 a 100
    tier: MatchTier
    
    # Seleções
    selected_headline: str
    headline_id: str
    selected_summary: str
    selected_experiences: List[ExperienceMatch] = field(default_factory=list)
    selected_skills: List[str] = field(default_factory=list)
    
    # Cobertura
    keywords_covered: List[str] = field(default_factory=list)
    keywords_missing: List[str] = field(default_factory=list)
    
    # Warnings
    warnings: List[str] = field(default_factory=list)
    
    def get_coverage_report(self) -> str:
        """Relatório de cobertura para o usuário"""
        covered = len(self.keywords_covered)
        total = covered + len(self.keywords_missing)
        
        report = [
            f"📊 Match Score: {self.total_percentage}%",
            f"",
            f"✅ Requisitos cobertos ({covered}):",
        ]
        for kw in self.keywords_covered[:10]:
            report.append(f"   • {kw}")
        
        if self.keywords_missing:
            report.append(f"")
            report.append(f"⚠️ Não cobertos ({len(self.keywords_missing)}):")
            for kw in self.keywords_missing[:5]:
                report.append(f"   • {kw}")
        
        return "\n".join(report)
    
    def should_proceed(self) -> bool:
        """Retorna True se match é bom o suficiente"""
        return self.total_percentage >= 60


# ============== OUTPUT MODELS ==============

@dataclass
class ResumeOutput:
    """Currículo gerado"""
    # Header
    name: str
    location: str
    email: str
    linkedin: str
    phone: str
    
    # Content
    headline: str
    summary: str
    experiences: List[Dict[str, Any]] = field(default_factory=list)
    education: List[Dict[str, Any]] = field(default_factory=list)
    skills: List[str] = field(default_factory=list)
    ai_projects: List[Dict[str, Any]] = field(default_factory=list)
    
    # Metadata
    language: Language = Language.PT
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    job_url: str = ""
    match_score: int = 0
    
    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "location": self.location,
            "email": self.email,
            "linkedin": self.linkedin,
            "phone": self.phone,
            "headline": self.headline,
            "summary": self.summary,
            "experiences": self.experiences,
            "education": self.education,
            "skills": self.skills,
            "ai_projects": self.ai_projects,
            "language": self.language.value,
            "generated_at": self.generated_at,
            "job_url": self.job_url,
            "match_score": self.match_score
        }


# ============== PIPELINE STATE ==============

@dataclass
class PipelineState:
    """Estado do pipeline para tracking"""
    step: str = "init"
    job: Optional[Job] = None
    match_result: Optional[MatchResult] = None
    resume: Optional[ResumeOutput] = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    def add_error(self, error: str):
        self.errors.append(error)
    
    def add_warning(self, warning: str):
        self.warnings.append(warning)
    
    def has_errors(self) -> bool:
        return len(self.errors) > 0
