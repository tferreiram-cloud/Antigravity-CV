#!/usr/bin/env python3
"""
ANTIGRAVITY TAILOR - Generative Tailoring Engine
Synthesizes custom narratives from Master CV STAR facts.

Now uses unified LLMService with Claude as primary backend.
"""

import json
import logging
from typing import List, Dict, Optional
from core.models import Job, ExperienceMatch, ResumeOutput, Seniority
from core.config import config
from core.llm_service import get_llm_service, LLMService

logger = logging.getLogger(__name__)


class TailoringEngine:
    """
    Engine that uses LLM to bridge gaps between Candidate Facts (STAR) and Job Requirements.
    Uses unified LLMService with fallback chain: Claude → Ollama → Gemini → Groq
    """

    def __init__(self, llm_service: Optional[LLMService] = None):
        """
        Initialize TailoringEngine with LLMService.

        Args:
            llm_service: Optional LLMService instance. If None, uses singleton.
        """
        self.llm = llm_service or get_llm_service()
        self.available = bool(self.llm.get_available_backends())

        if self.available:
            backends = self.llm.get_available_backends()
            logger.info(f"✅ TailoringEngine initialized with backends: {backends}")
        else:
            logger.warning("⚠️ TailoringEngine: No LLM backends available. Using fallback mode.")

    def _generate(self, prompt: str, use_case: str = "tailoring", **kwargs) -> Optional[str]:
        """
        Generate text using LLMService with proper error handling.
        """
        if not self.available:
            return None

        try:
            result = self.llm.generate(
                prompt,
                use_case=use_case,
                temperature=kwargs.get("temperature", 0.7),
                max_tokens=kwargs.get("max_tokens", 2000)
            )
            return result
        except Exception as e:
            logger.error(f"LLM generation error: {e}")
            return None

    def _extract_json(self, text: str) -> Optional[List[str]]:
        """
        Extract JSON array from LLM response.
        """
        if not text:
            return None

        try:
            # Handle markdown code blocks
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]

            # Try to find JSON array
            import re
            match = re.search(r'\[.*?\]', text, re.DOTALL)
            if match:
                return json.loads(match.group())

            return json.loads(text.strip())
        except (json.JSONDecodeError, Exception) as e:
            logger.warning(f"Failed to parse JSON: {e}")
            return None

    def tailor_summary(self, job: Job, candidate_facts: str) -> str:
        """
        Generates a tailored summary based on the job and candidate profile.
        """
        prompt = f"""Você é um Career Agent Sênior especializado em currículos de alto impacto.
Escreva um Resumo Profissional (Summary) de 3-4 linhas para este candidato, focado nesta vaga.

VAGA: {job.title} em {job.company}
REQUISITOS: {', '.join(job.hard_skills[:10]) if job.hard_skills else 'Não especificados'}

CANDIDATO:
{candidate_facts}

REGRAS:
1. Primeira pessoa, profissional e direto
2. Destacar fit cultural e técnico
3. Usar métricas quando disponíveis
4. Idioma: {job.language.value.upper()}

Retorne APENAS o texto do resumo, sem explicações."""

        result = self._generate(prompt, use_case="cv_generation")

        if result:
            return result.strip()

        # Fallback
        return "Experienced professional with strong background in technology and leadership, delivering measurable results across multiple industries."

    def tailor_experience(self, job: Job, experience: Dict) -> List[str]:
        """
        Rewrites experience bullets to highlight missing keywords while staying 100% factual.
        """
        raw_facts = "\n".join(experience.get("bullets_execution_first", experience.get("bullets", [])))

        if not raw_facts:
            return []

        prompt = f"""Você é um Career Agent Sênior especializado em GTM e Performance.
Seu objetivo é REESCREVER os fatos (STAR) abaixo para maximizar o match com a vaga, sem inventar dados.

VAGA: {job.title} em {job.company}
SKILLS DESEJADAS: {', '.join(job.hard_skills + job.keywords_ats) if (job.hard_skills or job.keywords_ats) else 'Gerais'}
DESCRIÇÃO: {job.description[:1000] if job.description else 'Não disponível'}

FATOS BRUTOS (STAR):
{raw_facts}

REGRAS DE OURO:
1. Mantenha os números e resultados intactos
2. Bridge the Gap: Se a vaga pede 'Excel' ou 'KPIs' e o fato original descreve análise de dados, mencione explicitamente as ferramentas
3. Foco em Execução: Use verbos de ação fortes (Arquitetou, Implementou, Tracionou)
4. Tamanho: Retorne exatamente 3-4 bullets curtos e impactantes
5. Idioma: {job.language.value.upper()}

Retorne APENAS a lista de bullets em formato JSON: ["bullet 1", "bullet 2", ...]"""

        result = self._generate(prompt, use_case="tailoring")
        bullets = self._extract_json(result)

        if bullets:
            return bullets

        # Fallback to original bullets
        return experience.get("bullets_execution_first", experience.get("bullets", []))[:3]

    def tailor_experience_enriched(self, job: Job, experience: Dict, rules: Dict) -> List[str]:
        """
        Enhanced version of tailor_experience that respects anti-overqualification rules.
        """
        facts = "\n".join(experience.get("bullets", []))

        if not facts:
            return []

        prompt = f"""Você é um Career Agent Sênior especializado em perfis High-End (GTM, Meta, Ambev).
Sintetize os fatos da experiência '{experience.get('company', 'N/A')}' para a vaga abaixo.

VAGA: {job.title} em {job.company}
SENIORIDADE: {job.seniority.value if job.seniority else 'Sênior'}
REQUISITOS: {', '.join(job.hard_skills[:15]) if job.hard_skills else 'Não especificados'}

REGRAS DE CALIBRAÇÃO:
- Verbos preferidos: {', '.join(rules.get('usar_verbos', ['Implementei', 'Arquitetei', 'Tracionei']))}
- Foco: {rules.get('foco', 'Resultados mensuráveis e execução')}
- Proporção: {rules.get('proporcao_bullets', '70% execução, 30% estratégia')}

FATOS BRUTOS:
{facts}

INSTRUÇÕES:
1. Reescreva em 5-7 bullets DENSOS (2-3 linhas cada)
2. Se vaga técnica: foque em 'how-to'. Se gestão: foque em 'impacto/P&L'
3. Nunca invente números. Use verbos de impacto qualitativo se não houver métricas
4. Preserve stack técnica e ferramentas mencionadas
5. Idioma: {job.language.value.upper()}

Retorne APENAS JSON: ["bullet 1", ...]"""

        result = self._generate(prompt, use_case="cv_generation", max_tokens=3000)
        bullets = self._extract_json(result)

        if bullets:
            return bullets

        return experience.get("bullets", [])[:8]

    def tailor_resume(self, resume: ResumeOutput, job: Job, master_cv: Dict) -> ResumeOutput:
        """
        Main entry point for High-Density AI Synthesis.
        Rewrites Summary and Experiences in a single context-aware pass.
        """
        if not self.available:
            logger.warning("No LLM backends available. Returning original resume.")
            return resume

        anti_ov = master_cv.get("anti_overqualification", {})
        calib_type = "calibracao_senior" if job.seniority in [Seniority.SENIOR, Seniority.LEAD, Seniority.MANAGER] else "calibracao_manager"
        rules = anti_ov.get(calib_type, anti_ov.get("calibracao_manager", {}))

        # 1. Tailor Summary
        candidate_facts = f"15+ years experience. Core Skills: {', '.join(resume.skills[:10])}"
        resume.summary = self.tailor_summary(job, candidate_facts)

        # 2. Tailor each experience using the enriched prompt
        tailored_exps = []
        for exp in resume.experiences:
            bullets = self.tailor_experience_enriched(job, exp, rules)
            exp["bullets"] = bullets
            tailored_exps.append(exp)

        resume.experiences = tailored_exps

        logger.info(f"✅ Resume tailored for {job.company} - {job.title}")
        return resume

    def tailor_all_experiences(self, job: Job, master_cv: Dict) -> List[Dict]:
        """
        Force 100% Match: Rewrites ALL experiences using Skill Transposition.
        Focus: Translate user's experience into job's terminology without inventing facts.
        """
        if not self.available:
            return master_cv.get("experiencias", [])

        tailored_exps = []
        
        # Sort experiences first to ensure context (optional, but good for processing)
        # We process all of them
        all_exps = master_cv.get("experiencias", [])
        
        for exp in all_exps:
            # Deep copy to avoid mutating original structure too much if not needed
            new_exp = exp.copy()
            
            # Use specific prompt for Skill Transposition
            prompt = f"""Você é um Expert em Recrutamento e Engenharia de Currículos.
Sua missão: Realizar 'Skill Transposition' para alinhar a experiência do candidato à vaga.

VAGA ALVO: {job.title} em {job.company}
KEYWORDS DA VAGA: {', '.join(job.hard_skills + job.keywords_ats)}

EXPERIÊNCIA ORIGINAL:
Empresa: {exp.get('empresa', exp.get('company'))}
Cargo: {exp.get('cargo', exp.get('role'))}
Bullets Atuais:
{chr(10).join(exp.get('bullets_execution_first', exp.get('bullets', [])))}

DIRETRIZES:
1. Analise os bullets originais e veja se alguma realização prova competência nas Keywords da Vaga.
2. Se provar, REESCREVA o bullet usando a terminologia da vaga (ex: se fez 'análise de vendas', e a vaga pede 'Revenue Operations', use 'Revenue Operations' se for tecnicamente correto).
3. SE NÃO HOUVER CORRELAÇÃO, MANTENHA O BULLET ORIGINAL OU O MELHORE APENAS PARA CLAREZA.
4. NÃO INVENTE FATOS. Apenas refrações de perspectiva.
5. Mantenha números e métricas.
6. Idioma: {job.language.value.upper()}

Retorne APENAS a lista de bullets (JSON array of strings)."""

            result = self._generate(prompt, use_case="tailoring")
            new_bullets = self._extract_json(result)
            
            if new_bullets:
                new_exp["bullets"] = new_bullets
                new_exp["bullets_execution_first"] = new_bullets # Updates priority bullets
            
            tailored_exps.append(new_exp)
            
        return tailored_exps

    def generate_headline(self, job: Job, candidate_skills: List[str]) -> str:
        """
        Generate a tailored headline for the job.
        """
        prompt = f"""Crie um headline profissional de 1 linha para este candidato, alinhado com a vaga.

VAGA: {job.title} em {job.company}
SKILLS DO CANDIDATO: {', '.join(candidate_skills[:15])}

REGRAS:
1. Máximo 10 palavras
2. Destaque o diferencial técnico
3. Use termos da vaga quando possível
4. Idioma: {job.language.value.upper()}

Retorne APENAS o headline, sem aspas ou explicações."""

        result = self._generate(prompt, use_case="tailoring", max_tokens=100)

        if result:
            return result.strip().strip('"').strip("'")

        return "Senior Product & Growth Professional | AI & Data-Driven"
