#!/usr/bin/env python3
"""
ANTIGRAVITY TAILOR - Job Interpreter
Análise semântica da vaga: extração de keywords, senioridade, tipo

NÃO inventa dados. Apenas extrai o que está explícito.
"""

import re
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.models import Job, Language, Seniority, JobValidation


# ============== KEYWORD PATTERNS ==============

HARD_SKILLS_PATTERNS = {
    # Marketing / Growth
    "gtm": ["gtm", "go-to-market", "go to market"],
    "crm": ["crm", "hubspot", "salesforce", "pipedrive"],
    "marketing_automation": ["marketing automation", "automação de marketing", "automation"],
    "seo": ["seo", "search engine optimization"],
    "sem": ["sem", "search engine marketing", "paid search"],
    "google_ads": ["google ads", "adwords", "google advertising"],
    "meta_ads": ["meta ads", "facebook ads", "instagram ads", "fb ads"],
    "analytics": ["analytics", "ga4", "google analytics", "data analytics"],
    "ab_testing": ["a/b testing", "ab testing", "teste ab", "split testing"],
    "cro": ["cro", "conversion rate optimization", "otimização de conversão"],
    "growth": ["growth", "growth hacking", "growth marketing"],
    "brandformance": ["brandformance", "brand performance"],
    "revops": ["revops", "revenue operations"],
    "abm": ["abm", "account based marketing"],
    "demand_gen": ["demand generation", "demand gen", "geração de demanda"],
    "lead_gen": ["lead generation", "lead gen", "geração de leads"],
    "inbound": ["inbound", "inbound marketing"],
    "outbound": ["outbound", "outbound marketing"],
    "content_marketing": ["content marketing", "marketing de conteúdo"],
    "influencer": ["influencer", "influenciador"],
    "branding": ["branding", "brand strategy", "marca"],
    "positioning": ["positioning", "posicionamento"],
    "product_marketing": ["product marketing", "pmm", "marketing de produto"],
    
    # AI / Tech
    "ai": ["ai", "artificial intelligence", "inteligência artificial", "ia"],
    "llm": ["llm", "large language model", "gpt", "claude", "gemini"],
    "ml": ["ml", "machine learning", "aprendizado de máquina"],
    "python": ["python"],
    "sql": ["sql", "mysql", "postgresql", "postgres"],
    "docker": ["docker", "container"],
    "n8n": ["n8n", "n8n.io"],
    "make": ["make", "integromat"],
    "zapier": ["zapier"],
    "rag": ["rag", "retrieval augmented"],
    "prompt_engineering": ["prompt engineering", "engenharia de prompt"],
    
    # Data
    "data_analysis": ["data analysis", "análise de dados", "data-driven"],
    "dashboard": ["dashboard", "dashboards", "tableau", "power bi", "looker"],
    "excel": ["excel", "planilhas", "spreadsheet"],
    "bi": ["bi", "business intelligence"],
    
    # Management
    "project_management": ["project management", "gestão de projetos", "pm"],
    "agile": ["agile", "ágil", "scrum", "kanban"],
    "okrs": ["okr", "okrs", "objectives and key results"],
    "kpis": ["kpi", "kpis", "indicadores"],
    "p_and_l": ["p&l", "p/l", "profit and loss", "lucros e perdas"],
    "budget": ["budget", "orçamento", "budget management"],
}

SOFT_SKILLS_PATTERNS = {
    "leadership": ["liderança", "leadership", "líder", "leader", "liderar"],
    "communication": ["comunicação", "communication", "apresentação", "presentation"],
    "teamwork": ["trabalho em equipe", "teamwork", "equipe", "team"],
    "stakeholder": ["stakeholder", "stakeholders", "partes interessadas"],
    "negotiation": ["negociação", "negotiation", "negociar"],
    "strategic": ["estratégico", "strategic", "estratégia", "strategy"],
    "analytical": ["analítico", "analytical", "análise crítica"],
    "problem_solving": ["resolução de problemas", "problem solving"],
    "proactive": ["proativo", "proactive", "iniciativa"],
    "adaptable": ["adaptável", "adaptable", "flexível", "flexible"],
}

SENIORITY_PATTERNS = {
    Seniority.JUNIOR: ["junior", "júnior", "jr", "entry level", "iniciante", "trainee", "estágio", "estagiário"],
    Seniority.PLENO: ["pleno", "mid", "mid-level", "intermediário"],
    Seniority.SENIOR: ["senior", "sênior", "sr", "experienced", "experiente"],
    Seniority.MANAGER: ["manager", "gerente", "coordenador", "coordinator", "supervisor"],
    Seniority.LEAD: ["lead", "head", "diretor", "director", "principal", "vp", "vice president"],
}

JOB_TYPE_PATTERNS = {
    "marketing": ["marketing", "mkt", "comunicação"],
    "growth": ["growth", "aquisição", "acquisition", "performance"],
    "branding": ["branding", "brand", "marca"],
    "ai_ops": ["ai", "ia", "automation", "automação", "llm"],
    "product": ["produto", "product", "pm", "apm", "gpm"],
    "revops": ["revops", "revenue", "sales ops", "operações"],
    "content": ["content", "conteúdo", "editorial", "mídias sociais"],
    "crm": ["crm", "lifecycle", "retention", "retenção"],
    "b2b": ["b2b", "enterprise", "corporativo"],
}


# ============== INTERPRETER CLASS ==============

class JobInterpreter:
    """
    Interpreta uma vaga e extrai informações estruturadas.
    
    REGRAS:
    - NÃO inventa requisitos
    - NÃO infere tecnologias não citadas
    - Usa APENAS o que está explícito no texto
    """
    
    def __init__(self, debug: bool = False):
        self.debug = debug
    
    def interpret(self, job: Job) -> Job:
        """
        Interpreta a vaga e preenche campos estruturados.
        Modifica o Job in-place e retorna.
        """
        text = f"{job.title} {job.description}".lower()
        
        # Extrair informações
        job.hard_skills = self._extract_hard_skills(text)
        job.soft_skills = self._extract_soft_skills(text)
        job.keywords_ats = self._extract_ats_keywords(text)
        job.seniority = self._detect_seniority(text)
        job.job_type = self._detect_job_type(text)
        job.language = self._detect_language(text)
        
        if self.debug:
            self._print_debug(job)
        
        return job
    
    def _extract_hard_skills(self, text: str) -> List[str]:
        """Extrai hard skills do texto"""
        found = []
        for skill_id, patterns in HARD_SKILLS_PATTERNS.items():
            for pattern in patterns:
                if re.search(rf'\b{re.escape(pattern)}\b', text, re.IGNORECASE):
                    found.append(skill_id)
                    break
        return list(set(found))
    
    def _extract_soft_skills(self, text: str) -> List[str]:
        """Extrai soft skills do texto"""
        found = []
        for skill_id, patterns in SOFT_SKILLS_PATTERNS.items():
            for pattern in patterns:
                if re.search(rf'\b{re.escape(pattern)}\b', text, re.IGNORECASE):
                    found.append(skill_id)
                    break
        return list(set(found))
    
    def _extract_ats_keywords(self, text: str) -> List[str]:
        """Extrai keywords para ATS matching"""
        # Combina hard + soft + palavras específicas encontradas
        keywords = []
        
        # Add hard skills
        keywords.extend(self._extract_hard_skills(text))
        
        # Buscar padrões específicos comuns em vagas
        ats_patterns = [
            r'\b(kpi|roi|cac|ltv|mrr|arr|nps|csat)\b',
            r'\b(\d+\s*anos?\s*de\s*experiência|\d+\s*years?\s*experience)\b',
            r'\b(inglês|english|espanhol|spanish)\s*(fluente|avançado|advanced|native)\b',
            r'\b(remote|remoto|híbrido|hybrid|presencial|onsite)\b',
        ]
        
        for pattern in ats_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            keywords.extend([m if isinstance(m, str) else m[0] for m in matches])
        
        return list(set(keywords))
    
    def _detect_seniority(self, text: str) -> Optional[Seniority]:
        """Detecta senioridade da vaga"""
        # Prioridade: LEAD > MANAGER > SENIOR > PLENO > JUNIOR
        priority_order = [Seniority.LEAD, Seniority.MANAGER, Seniority.SENIOR, Seniority.PLENO, Seniority.JUNIOR]
        
        for seniority in priority_order:
            patterns = SENIORITY_PATTERNS[seniority]
            for pattern in patterns:
                if re.search(rf'\b{re.escape(pattern)}\b', text, re.IGNORECASE):
                    return seniority
        
        return None
    
    def _detect_job_type(self, text: str) -> str:
        """Detecta tipo da vaga"""
        scores = {}
        
        for job_type, patterns in JOB_TYPE_PATTERNS.items():
            score = 0
            for pattern in patterns:
                matches = len(re.findall(rf'\b{re.escape(pattern)}\b', text, re.IGNORECASE))
                score += matches
            if score > 0:
                scores[job_type] = score
        
        if scores:
            return max(scores, key=scores.get)
        return "marketing"  # default
    
    def _detect_language(self, text: str) -> Language:
        """Detecta idioma predominante"""
        # Palavras exclusivas de cada idioma
        pt_words = ["você", "será", "nosso", "nossa", "equipe", "empresa", "requisitos", "responsabilidades"]
        en_words = ["you", "will", "our", "team", "company", "requirements", "responsibilities"]
        
        pt_count = sum(1 for word in pt_words if word in text)
        en_count = sum(1 for word in en_words if word in text)
        
        return Language.EN if en_count > pt_count else Language.PT
    
    def _print_debug(self, job: Job):
        """Print debug info"""
        print(f"\n{'='*50}")
        print(f"🔍 DEBUG: Job Interpretation")
        print(f"{'='*50}")
        print(f"Title: {job.title}")
        print(f"Company: {job.company}")
        print(f"Language: {job.language.value}")
        print(f"Seniority: {job.seniority.value if job.seniority else 'N/A'}")
        print(f"Type: {job.job_type}")
        print(f"Hard Skills ({len(job.hard_skills)}): {', '.join(job.hard_skills[:10])}")
        print(f"Soft Skills ({len(job.soft_skills)}): {', '.join(job.soft_skills)}")
        print(f"ATS Keywords ({len(job.keywords_ats)}): {', '.join(job.keywords_ats[:10])}")


def validate_job_scraping(title: str, company: str, description: str, url: str) -> JobValidation:
    """
    Valida se o scraping foi bem sucedido.
    
    CHECKLIST:
    [ ] Cargo identificado
    [ ] Empresa identificada
    [ ] Descrição legível
    [ ] Requisitos explícitos
    [ ] Idioma identificado
    """
    validation = JobValidation()
    
    # Cargo
    validation.cargo_found = bool(title and len(title) > 3)
    
    # Empresa
    validation.empresa_found = bool(company and len(company) > 2)
    
    # Descrição
    validation.description_readable = bool(description and len(description) > 100)
    validation.raw_length = len(description) if description else 0
    
    # Requisitos
    requirements_keywords = ["requisitos", "requirements", "qualificações", "qualifications", 
                           "experiência", "experience", "skills", "habilidades"]
    validation.requirements_found = any(kw in description.lower() for kw in requirements_keywords) if description else False
    
    # Idioma
    if description:
        pt_count = sum(1 for w in ["você", "nosso", "será", "equipe"] if w in description.lower())
        en_count = sum(1 for w in ["you", "our", "will", "team"] if w in description.lower())
        validation.language_detected = "en" if en_count > pt_count else "pt"
    
    return validation


def create_job_from_scrape(
    title: str,
    company: str, 
    description: str,
    url: str,
    location: str = "",
    source: str = "manual"
) -> Tuple[Job, JobValidation]:
    """
    Cria um Job a partir de dados scraped.
    Retorna (Job, ValidationResult).
    
    Se validação falhar, Job.is_valid será False.
    """
    import hashlib
    
    # Validar
    validation = validate_job_scraping(title, company, description, url)
    
    # Criar ID único
    job_id = hashlib.md5(f"{title}{company}{url}".encode()).hexdigest()[:12]
    
    # Criar Job
    job = Job(
        id=job_id,
        title=title or "Unknown",
        company=company or "Unknown",
        location=location,
        description=description or "",
        url=url,
        source=source,
        validation=validation
    )
    
    # Interpretar se válido
    if validation.is_valid:
        interpreter = JobInterpreter()
        interpreter.interpret(job)
    
    return job, validation
