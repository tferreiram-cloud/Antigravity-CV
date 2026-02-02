#!/usr/bin/env python3
"""
ANTIGRAVITY TAILOR - Configuration
Configurações centralizadas do pipeline
"""

from pathlib import Path
from dataclasses import dataclass
from typing import List
import os

# Load .env file FIRST before anything else
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")


# ============== PATHS ==============

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR
OUTPUT_DIR = BASE_DIR / "output"
JOBS_DIR = BASE_DIR / "jobs"
TEMPLATES_DIR = BASE_DIR / "templates"

# Create dirs if not exist
OUTPUT_DIR.mkdir(exist_ok=True)
JOBS_DIR.mkdir(exist_ok=True)


# ============== MASTER CV PATHS ==============

MASTER_CV_PT = DATA_DIR / "master_cv_pt.json"
MASTER_CV_EN = DATA_DIR / "master_cv_en.json"
MASTER_CV_JUNIOR = DATA_DIR / "master_cv_junior.json"


# ============== LLM BACKENDS ==============

@dataclass
class LLMConfig:
    """Configuração de backends LLM"""
    # API Keys (loaded from environment)
    api_key: str = None
    model_name: str = "gemini-2.0-flash"
    
    # Model configs
    ollama_model: str = "gemma2:9b"
    ollama_url: str = "http://localhost:11434"
    groq_model: str = "llama-3.3-70b-versatile"
    gemini_model: str = "gemini-2.0-flash"
    
    # Ordem de fallback
    backend_order: List[str] = None
    
    def __post_init__(self):
        if self.backend_order is None:
            self.backend_order = ["ollama", "groq", "gemini"]
        # Load API key from environment if not set
        if self.api_key is None:
            self.api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")


# ============== MATCHING CONFIG ==============

@dataclass
class MatchingConfig:
    """Configuração do engine de matching"""
    # Thresholds
    high_match_threshold: float = 0.70
    medium_match_threshold: float = 0.40
    minimum_match_threshold: float = 0.10
    
    # Seleção
    max_experiences: int = 7  # Aumentado para perfis sêniores
    max_bullets_per_exp: int = 12  # Aumentado para permitir densidade máxima antes da IA
    max_skills: int = 20
    
    # Priorização
    core_weight: float = 1.5  # Multiplicador para experiências CORE
    contextual_weight: float = 1.0
    
    # Keywords
    min_keyword_length: int = 3
    common_words_to_ignore: List[str] = None
    
    def __post_init__(self):
        if self.common_words_to_ignore is None:
            self.common_words_to_ignore = [
                "the", "and", "for", "with", "you", "are", "our", "will",
                "que", "com", "para", "uma", "seu", "sua", "nos", "das", "dos"
            ]


# ============== OUTPUT CONFIG ==============

@dataclass
class OutputConfig:
    """Configuração de output"""
    default_format: str = "pdf"
    include_ai_projects: bool = True
    include_education: bool = True
    max_pages: int = 2
    
    # PDF
    pdf_margin: str = "1cm"
    
    # Footer
    include_footer: bool = True
    footer_text: str = "Gerado via Antigravity Tailor"


# ============== SCRAPING CONFIG ==============

@dataclass
class ScrapingConfig:
    """Configuração de scraping"""
    timeout_seconds: int = 30
    retry_attempts: int = 3
    user_agent: str = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    
    # Validação mínima
    min_description_length: int = 100
    max_description_length: int = 20000
    
    # Headers
    headers: dict = None
    
    def __post_init__(self):
        if self.headers is None:
            self.headers = {
                "User-Agent": self.user_agent,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
            }


# ============== GLOBAL CONFIG ==============

@dataclass
class TailorConfig:
    """Configuração global do Tailor"""
    llm: LLMConfig = None
    matching: MatchingConfig = None
    output: OutputConfig = None
    scraping: ScrapingConfig = None
    
    # Debug
    debug_mode: bool = False
    verbose: bool = False
    
    def __post_init__(self):
        if self.llm is None:
            self.llm = LLMConfig()
        if self.matching is None:
            self.matching = MatchingConfig()
        if self.output is None:
            self.output = OutputConfig()
        if self.scraping is None:
            self.scraping = ScrapingConfig()


# ============== DEFAULT INSTANCE ==============

config = TailorConfig()
