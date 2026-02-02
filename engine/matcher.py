#!/usr/bin/env python3
"""
ANTIGRAVITY TAILOR - CV Matcher
Matching engine: compara vaga contra Master CV e seleciona melhores matches.

REGRAS:
- Prioriza experiências CORE sobre CONTEXTUAL
- Calcula match score objetivo
- Seleciona headline mais adequada
- NÃO inventa informações
"""

import json
import re
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.models import (
    Job, Language, Seniority, MatchTier,
    ExperienceMatch, MatchResult, ResumeOutput
)
from core.config import MASTER_CV_PT, MASTER_CV_EN, MASTER_CV_JUNIOR, config


# ============== MASTER CV LOADER ==============

class MasterCV:
    """
    Wrapper para o Master CV JSON.
    Fonte única da verdade - NUNCA modificar.
    """
    
    def __init__(self, data: Dict):
        self.data = data
        self._parse()
    
    def _parse(self):
        """Parse data into convenient attributes"""
        self.candidato = self.data.get("candidato", self.data.get("candidate", {}))
        self.headlines = self.data.get("headlines", self.data.get("headlines_variants", {}))
        self.summaries = self.data.get("summaries", self.data.get("summaries_variants", {}))
        self.experiencias = self.data.get("experiencias", self.data.get("experience", []))
        self.formacao = self.data.get("formacao", self.data.get("education", []))
        self.skills = self.data.get("skills", {})
        self.projetos_ai = self.data.get("projetos_ai", self.data.get("ai_projects", []))
    
    @classmethod
    def load(cls, language: Language = Language.PT, junior_mode: bool = False) -> "MasterCV":
        """Carrega Master CV do arquivo"""
        if junior_mode:
            path = MASTER_CV_JUNIOR
        else:
            path = MASTER_CV_PT if language == Language.PT else MASTER_CV_EN
        
        if not path.exists():
            raise FileNotFoundError(f"Master CV não encontrado: {path}")
        
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        return cls(data)
    
    def get_all_keywords(self) -> List[str]:
        """Retorna todas as keywords do CV para matching"""
        keywords = []
        
        # Skills
        for skill_category in self.skills.values():
            if isinstance(skill_category, list):
                for skill in skill_category:
                    if isinstance(skill, str):
                        keywords.append(skill.lower())
                    elif isinstance(skill, dict) and "name" in skill:
                        keywords.append(skill["name"].lower())
        
        # Keywords de experiências
        for exp in self.experiencias:
            if "keywords" in exp:
                keywords.extend([k.lower() for k in exp["keywords"]])
            if "stack_tecnica" in exp:
                keywords.extend([s.lower() for s in exp.get("stack_tecnica", [])])
        
        return list(set(keywords))
    
    def get_experience_keywords(self, exp: Dict) -> List[str]:
        """Retorna keywords de uma experiência específica"""
        keywords = []
        
        # Keywords explícitas
        if "keywords" in exp:
            keywords.extend([k.lower() for k in exp["keywords"]])
        
        # Stack técnica
        if "stack_tecnica" in exp:
            keywords.extend([s.lower() for s in exp["stack_tecnica"]])
        
        # Bullets text
        bullets = exp.get("bullets", exp.get("bullets_execution_first", []))
        for bullet in bullets:
            if isinstance(bullet, str):
                # Extrair termos relevantes do bullet
                words = re.findall(r'\b[a-zA-Z]{3,}\b', bullet.lower())
                keywords.extend(words)
        
        return list(set(keywords))


# ============== MATCHER CLASS ==============

class CVMatcher:
    """
    Engine de matching entre Job e Master CV.
    
    Algoritmo:
    1. Extrai keywords da vaga
    2. Compara com keywords de cada experiência
    3. Calcula score de overlap
    4. Prioriza CORE (1.5x) sobre CONTEXTUAL
    5. Seleciona top N experiências
    6. Escolhe headline mais adequada
    """
    
    def __init__(self, master: MasterCV, debug: bool = False):
        self.master = master
        self.debug = debug
        self.config = config.matching
    
    def match(self, job: Job) -> MatchResult:
        """
        Executa matching completo.
        Retorna MatchResult com score, experiências selecionadas, headline, etc.
        """
        # 1. Coletar keywords da vaga
        job_keywords = self._get_job_keywords(job)
        
        if self.debug:
            print(f"\n🔍 Job keywords ({len(job_keywords)}): {', '.join(job_keywords[:15])}")
        
        # 2. Pontuar experiências
        exp_scores = self._score_experiences(job_keywords)
        
        # 3. Selecionar top experiências
        selected_exps = self._select_experiences(exp_scores)
        
        # 4. Calcular score total
        total_score, covered, missing = self._calculate_coverage(job_keywords, selected_exps)
        
        # 5. Determinar tier
        tier = self._get_tier(total_score)
        
        # 6. Selecionar headline e summary
        headline_id, headline = self._select_headline(job)
        summary = self._select_summary(headline_id)
        
        # 7. Selecionar skills
        skills = self._select_skills(job_keywords)
        
        # 8. Warnings
        warnings = self._generate_warnings(job, total_score, missing)
        
        return MatchResult(
            total_score=total_score,
            total_percentage=int(total_score * 100),
            tier=tier,
            selected_headline=headline,
            headline_id=headline_id,
            selected_summary=summary,
            selected_experiences=selected_exps,
            selected_skills=skills,
            keywords_covered=covered,
            keywords_missing=missing,
            warnings=warnings
        )
    
    def _get_job_keywords(self, job: Job) -> List[str]:
        """Coleta todas as keywords relevantes da vaga"""
        keywords = []
        
        # Do interpreter
        keywords.extend(job.hard_skills)
        keywords.extend(job.keywords_ats)
        
        # Normalizar
        keywords = [k.lower().replace("_", " ") for k in keywords]
        
        return list(set(keywords))
    
    def _score_experiences(self, job_keywords: List[str]) -> List[Tuple[Dict, float, List[str]]]:
        """
        Pontua cada experiência contra keywords da vaga.
        Retorna lista de (experiência, score, keywords_matched)
        """
        scores = []
        
        for exp in self.master.experiencias:
            exp_keywords = self.master.get_experience_keywords(exp)
            
            # Calcular overlap
            matched = [k for k in job_keywords if any(k in ek or ek in k for ek in exp_keywords)]
            
            # Score base = overlap / total keywords
            if job_keywords:
                base_score = len(matched) / len(job_keywords)
            else:
                base_score = 0
            
            # Multiplicador por tier
            tier = exp.get("tier", "contextual")
            if tier == "core":
                score = base_score * self.config.core_weight
            else:
                score = base_score * self.config.contextual_weight
            
            scores.append((exp, score, matched))
            
            if self.debug:
                company = exp.get("empresa", exp.get("company", "?"))
                print(f"   {company}: {score:.2%} ({len(matched)} keywords)")
        
        return scores
    
    def _select_experiences(self, exp_scores: List[Tuple[Dict, float, List[str]]]) -> List[ExperienceMatch]:
        """
        Seleciona top experiências por score, garantindo que as CORE mais recentes
        SEMPRE entrem (Densidade Histórica).
        """
        # 1. Separar CORE e Contextual
        core_exps = [e for e in exp_scores if e[0].get("tier") == "core"]
        contextual_exps = [e for e in exp_scores if e[0].get("tier") != "core"]
        
        # 2. Ordenar CORE por recência (ID maior costuma ser mais recente no nosso JSON)
        # e Contextual por Score
        core_exps = sorted(core_exps, key=lambda x: x[0].get("id", 0), reverse=True)
        contextual_exps = sorted(contextual_exps, key=lambda x: x[1], reverse=True)
        
        # 3. Seleção Híbrida
        selected_raw = []
        
        # Sempre incluir as Top 3 CORE (se existirem) para manter o corpo do CV
        selected_raw.extend(core_exps[:3])
        
        # Preencher o resto com os melhores matches (CORE ou Contextual)
        remaining_slots = self.config.max_experiences - len(selected_raw)
        others = [e for e in (core_exps[3:] + contextual_exps) if e not in selected_raw]
        others = sorted(others, key=lambda x: x[1], reverse=True)
        
        selected_raw.extend(others[:remaining_slots])
        
        # 4. Converter para ExperienceMatch
        selected = []
        for exp, score, matched in selected_raw:
            # Match Threshold Logic (Relaxed)
            # Only filter if we have plenty of good candidates. 
            # If we are short on experiences, we take what we have.
            is_mandatory_core = any(exp['id'] == c[0]['id'] for c in core_exps[:3])
            
            # If it's mandatory core, always keep.
            # If it's not matches threshold, keep.
            # If we don't have enough EXPs yet (< max_experiences), keep it anyway to fill the CV.
            should_keep = is_mandatory_core or (score >= self.config.minimum_match_threshold) or (len(selected) < self.config.max_experiences)

            if not should_keep:
                continue
            
            bullets = exp.get("bullets", exp.get("bullets_execution_first", []))
            # NÃO truncar aqui. Deixar a AI decidir ou truncar apenas na renderização final se necessário.
            selected_bullets = bullets 
            
            match = ExperienceMatch(
                experience_id=exp.get("id", 0),
                company=exp.get("empresa", exp.get("company", "")),
                role=exp.get("cargo", exp.get("role", "")),
                tier=exp.get("tier", "contextual"),
                score=score,
                matched_keywords=matched,
                selected_bullets=selected_bullets
            )
            selected.append(match)
        
        # Sort final selection chronologically
        selected = sorted(selected, key=lambda x: x.experience_id, reverse=True)
        
        return selected
    
    def _calculate_coverage(
        self, 
        job_keywords: List[str], 
        selected_exps: List[ExperienceMatch]
    ) -> Tuple[float, List[str], List[str]]:
        """Calcula cobertura total de keywords"""
        # Keywords cobertas pelas experiências selecionadas
        covered = set()
        for exp in selected_exps:
            covered.update(exp.matched_keywords)
        
        # Keywords faltantes
        missing = [k for k in job_keywords if k not in covered]
        
        # Score = covered / total
        if job_keywords:
            score = len(covered) / len(job_keywords)
        else:
            score = 0
        
        return score, list(covered), missing
    
    def _get_tier(self, score: float) -> MatchTier:
        """Determina tier do match"""
        if score >= self.config.high_match_threshold:
            return MatchTier.HIGH
        elif score >= self.config.medium_match_threshold:
            return MatchTier.MEDIUM
        else:
            return MatchTier.LOW
    
    def _select_headline(self, job: Job) -> Tuple[str, str]:
        """Seleciona headline mais adequada para a vaga"""
        # Mapping job_type -> headline_id
        type_to_headline = {
            "marketing": "marketing_manager",
            "growth": "growth_lead",
            "branding": "branding",
            "ai_ops": "ai_lead",
            "product": "product_manager",
            "revops": "revops",
            "content": "content_strategy",
            "crm": "customer_success",
            "b2b": "b2b_marketing",
        }
        
        # Ajuste por senioridade
        seniority_preference = {
            Seniority.LEAD: ["gpm_ai", "martech_lead", "growth_lead"],
            Seniority.MANAGER: ["marketing_manager", "product_manager", "pmm"],
            Seniority.SENIOR: ["growth_cro", "branding", "media_trafego"],
            Seniority.PLENO: ["marketing_manager", "growth_cro"],
            Seniority.JUNIOR: ["marketing_manager"],
        }
        
        # Determinar headline_id
        headline_id = type_to_headline.get(job.job_type, "marketing_manager")
        
        # Ajustar por senioridade se disponível
        if job.seniority and job.seniority in seniority_preference:
            preferred = seniority_preference[job.seniority]
            if preferred:
                headline_id = preferred[0]
        
        # Buscar headline text
        headline = self.master.headlines.get(headline_id, "")
        if not headline and self.master.headlines:
            # Fallback para primeira disponível
            headline_id = list(self.master.headlines.keys())[0]
            if headline_id.startswith("_"):
                headline_id = list(self.master.headlines.keys())[1]
            headline = self.master.headlines[headline_id]
        
        return headline_id, headline
    
    def _select_summary(self, headline_id: str) -> str:
        """Seleciona summary correspondente à headline"""
        summary = self.master.summaries.get(headline_id, "")
        if not summary and self.master.summaries:
            # Fallback
            for key, val in self.master.summaries.items():
                if not key.startswith("_"):
                    return val
        return summary
    
    def _select_skills(self, job_keywords: List[str]) -> List[str]:
        """Seleciona skills mais relevantes"""
        all_skills = []
        
        # Flatten skills
        for category, skills in self.master.skills.items():
            if category.startswith("_"):
                continue
            if isinstance(skills, list):
                for skill in skills:
                    if isinstance(skill, str):
                        all_skills.append(skill)
                    elif isinstance(skill, dict) and "name" in skill:
                        all_skills.append(skill["name"])
        
        # Priorizar skills que matcham keywords
        prioritized = []
        others = []
        
        for skill in all_skills:
            skill_lower = skill.lower()
            if any(k in skill_lower or skill_lower in k for k in job_keywords):
                prioritized.append(skill)
            else:
                others.append(skill)
        
        # Combinar mantendo ordem
        result = prioritized + others
        
        return result[:self.config.max_skills]
    
    def _generate_warnings(self, job: Job, score: float, missing: List[str]) -> List[str]:
        """Gera warnings para o usuário"""
        warnings = []
        
        if score < self.config.medium_match_threshold:
            warnings.append(f"⚠️ Match baixo ({int(score*100)}%). Esta vaga pode não ser ideal.")
        
        if len(missing) > 5:
            warnings.append(f"⚠️ {len(missing)} requisitos não cobertos pelo CV.")
        
        if job.seniority in [Seniority.LEAD, Seniority.MANAGER]:
            warnings.append("ℹ️ Vaga de liderança - bullets estratégicos priorizados.")
        
        return warnings


# ============== RESUME BUILDER ==============

def build_resume(master: MasterCV, match: MatchResult, job: Job) -> ResumeOutput:
    """
    Constrói o ResumeOutput a partir do match result.
    """
    candidato = master.candidato
    
    # Header
    name = candidato.get("nome_completo", candidato.get("full_name", ""))
    location = candidato.get("localizacao", candidato.get("location", {}))
    if isinstance(location, dict):
        location_str = location.get("display", f"{location.get('cidade', '')}, {location.get('estado', '')}")
    else:
        location_str = str(location)
    
    contato = candidato.get("contato", candidato.get("contact", {}))
    email = contato.get("email", "")
    linkedin = contato.get("linkedin", "")
    phone = contato.get("telefone", contato.get("phone", ""))
    
    # Experiências formatadas
    experiences = []
    
    # Extract end year helper
    def extract_end_year(period_str):
        if not period_str:
            return 0
        if "Presente" in period_str or "Atual" in period_str or "Current" in period_str:
            return 2026 # Always top
        import re
        years = re.findall(r'\d{4}', period_str)
        return int(years[-1]) if years else 0

    # 1. First, map selected matches to experiences
    # formatting them as needed
    processed_exps = []
    
    # We want ALL experiences from Master CV, but we want to use the "selected_bullets" 
    # from the match result if available (which might have been tailored).
    # If not in match result, we take the original.
    
    # Create a lookup for matched experiences
    match_lookup = {exp.company: exp for exp in match.selected_experiences}
    
    for orig_exp in master.experiencias:
        company = orig_exp.get("empresa", orig_exp.get("company", ""))
        
        # Determine bullets: use matched version if exists (tailored/selected), else original
        if company in match_lookup:
            bullets = match_lookup[company].selected_bullets
        else:
            bullets = orig_exp.get("bullets_execution_first", orig_exp.get("bullets", []))
            
        processed_exps.append({
            "company": company,
            "role": orig_exp.get("cargo", orig_exp.get("role", "")),
            "period": orig_exp.get("periodo", orig_exp.get("period", "")),
            "location": orig_exp.get("localizacao", orig_exp.get("location", "")),
            "scope": orig_exp.get("scope", ""),
            "bullets": bullets
        })

    # 2. Sort by Date Descending (Golden Rule: Timeline Integrity)
    experiences = sorted(processed_exps, key=lambda x: extract_end_year(x['period']), reverse=True)
    
    # Formação
    education = []
    for edu in master.formacao:
        if edu.get("tier") == "core":
            education.append({
                "institution": edu.get("instituicao", edu.get("institution", "")),
                "program": edu.get("programa", edu.get("program", "")),
                "year": edu.get("ano", edu.get("year", "")),
                "highlight": edu.get("destaque", edu.get("highlight", ""))
            })
    
    # AI Projects (se relevante)
    ai_projects = []
    for proj in master.projetos_ai:
        ai_projects.append({
            "name": proj.get("nome", proj.get("name", "")),
            "bullet": proj.get("bullet", ""),
        })
    
    return ResumeOutput(
        name=name,
        location=location_str,
        email=email,
        linkedin=linkedin,
        phone=phone,
        headline=match.selected_headline,
        summary=match.selected_summary,
        experiences=experiences,
        education=education,
        skills=match.selected_skills,
        ai_projects=ai_projects,
        language=job.language,
        job_url=job.url,
        match_score=match.total_percentage
    )
