#!/usr/bin/env python3
"""
FULL AUTOMATION PIPELINE v2.0
Scraping → Tailoring → Aplicação

Zero Human-in-the-Loop
STAR Methodology
Antifrágil com Self-Healing
"""

import json
import os
import re
import hashlib
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass

# Imports internos
from scraper import scrape_jobs, Job
from pipeline import (
    LLMOrchestrator, 
    extract_keywords, 
    load_master_cv,
    validate_ats_match,
    inject_missing_keywords
)

try:
    from jinja2 import Template
    import requests
except ImportError:
    import subprocess
    subprocess.run(["pip", "install", "jinja2", "requests", "-q"])
    from jinja2 import Template
    import requests

try:
    from weasyprint import HTML
    HAS_WEASYPRINT = True
except ImportError:
    HAS_WEASYPRINT = False


BASE_DIR = Path(__file__).parent
TEMPLATES_DIR = BASE_DIR / "templates"
OUTPUT_DIR = BASE_DIR / "output"
JOBS_DIR = BASE_DIR / "jobs"


# ============== STAR FORMATTER ==============

def format_star_bullet(star: Dict) -> str:
    """Formata bullet STAR para HTML"""
    action = star.get("action", "")
    result = star.get("result", "")
    
    # Extrai métricas do result
    result_with_metrics = result
    metrics = re.findall(r'(\d+[%$MK]?(?:\s*[\+\-]?\d*[%$MK]?)?)', result)
    for metric in metrics:
        result_with_metrics = result_with_metrics.replace(
            metric, 
            f"<span class='metric'>{metric}</span>"
        )
    
    # Formata keywords
    keywords = star.get("keywords", [])
    for kw in keywords[:3]:  # Máximo 3 keywords por bullet
        if kw.lower() in action.lower():
            action = re.sub(
                rf'\b({re.escape(kw)})\b',
                r"<span class='keyword'>\1</span>",
                action,
                flags=re.IGNORECASE,
                count=1
            )
    
    return f"{action} <strong>Result:</strong> {result_with_metrics}"


def build_experience_from_star(exp: Dict, keywords: List[str]) -> Dict:
    """Constrói experiência formatada a partir de STAR"""
    bullets = []
    
    for star in exp.get("bullets_star", [])[:4]:
        # Verifica relevância para keywords da vaga
        star_text = json.dumps(star, ensure_ascii=False).lower()
        relevance = sum(1 for kw in keywords if kw.lower() in star_text)
        
        if relevance > 0 or len(bullets) < 2:  # Mínimo 2 bullets
            bullets.append({
                "html": format_star_bullet(star),
                "relevance": relevance
            })
    
    # Ordena por relevância e pega os top
    bullets.sort(key=lambda x: x["relevance"], reverse=True)
    
    return {
        "empresa": exp["empresa"],
        "cargo": exp.get("cargo_alternativo", {}).get("gpm_ai", exp["cargo"]),
        "periodo": exp["periodo"],
        "scope": exp.get("escopo", ""),
        "bullets": [b["html"] for b in bullets[:4]]
    }


def build_projects_from_star(projects: List[Dict]) -> List[Dict]:
    """Formata projetos AI com STAR"""
    formatted = []
    for proj in projects[:4]:
        formatted.append({
            "nome": proj["nome"],
            "descricao": f"{proj.get('action', '')} Result: {proj.get('result', '')}",
            "stack": " • ".join(proj.get("stack", []))
        })
    return formatted


# ============== TAILORING ENGINE v2 ==============

def tailor_resume_star(master_cv: Dict, job: Job, llm: Optional[LLMOrchestrator] = None) -> Dict:
    """
    Gera currículo tailored usando STAR methodology
    """
    candidato = master_cv["candidato"]
    
    # Extrai keywords da vaga
    keywords = extract_keywords(job.description, llm)
    print(f"   Keywords: {', '.join(keywords[:8])}...")
    
    # Determina tipo de vaga
    job_type = "gpm_ai"  # Default
    job_lower = job.title.lower() + job.description.lower()
    
    if "product manager" in job_lower and "ai" in job_lower:
        job_type = "gpm_ai"
    elif "marketing" in job_lower:
        job_type = "marketing_lead"
    elif "ai" in job_lower or "data" in job_lower:
        job_type = "ai_lead"
    else:
        job_type = "product_manager"
    
    # Headline e Summary dinâmicos
    headline = candidato.get("headlines_por_vaga", {}).get(job_type, candidato["headline_master"])
    summary = candidato.get("summary_por_vaga", {}).get(job_type, "")
    
    # Keywords string
    keywords_str = " • ".join(keywords[:12])
    
    # Experiências com STAR
    experiences = master_cv.get("experiencias_star", [])
    
    # Score e seleciona experiências mais relevantes
    scored_exp = []
    for exp in experiences:
        exp_text = json.dumps(exp, ensure_ascii=False).lower()
        score = sum(1 for kw in keywords if kw.lower() in exp_text)
        scored_exp.append((exp, score))
    
    scored_exp.sort(key=lambda x: x[1], reverse=True)
    selected_exp = [build_experience_from_star(exp, keywords) for exp, score in scored_exp[:6]]
    
    # Projetos AI
    projects = build_projects_from_star(master_cv.get("projetos_ai", []))
    
    # Skills organizadas por relevância
    skills_data = master_cv.get("skills", {})
    skills_formatted = []
    
    for key, skill_cat in skills_data.items():
        if not isinstance(skill_cat, dict):
            continue
        
        skills_list = []
        for kw in skill_cat.get("keywords", [])[:6]:
            is_critical = kw.lower() in job_lower or skill_cat.get("critical", False)
            skills_list.append({
                "name": kw,
                "class": "critical" if is_critical else ""
            })
        
        if skills_list:
            skills_formatted.append({
                "name": skill_cat.get("label", key),
                "skills_list": skills_list
            })
    
    # Educação
    education = []
    for edu in master_cv.get("formacao", [])[:4]:
        education.append({
            "titulo": edu.get("programa", ""),
            "instituicao": edu["instituicao"],
            "ano": edu.get("ano", "")
        })
    
    return {
        "nome": candidato["nome_completo"],
        "email": candidato.get("email", ""),
        "linkedin": candidato.get("linkedin", ""),
        "headline": headline,
        "summary": summary,
        "keywords": keywords_str,
        "experience": selected_exp,
        "projects": projects,
        "skills": skills_formatted,
        "education": education,
        "languages": candidato.get("idiomas", []),
        "_job": job.to_dict(),
        "_keywords": keywords
    }


# ============== PDF GENERATOR ==============

def generate_pdf(data: Dict, output_name: str) -> str:
    """Gera PDF do currículo"""
    template_path = TEMPLATES_DIR / "resume_sota.html"
    
    with open(template_path, "r", encoding="utf-8") as f:
        template = Template(f.read())
    
    html = template.render(**data)
    
    # Self-healing ATS
    keywords = data.get("_keywords", [])
    if keywords:
        score, missing = validate_ats_match(html, keywords)
        print(f"   ATS Score: {score:.1f}%")
        
        healing_rounds = 0
        while score < 85 and healing_rounds < 3 and missing:
            data = inject_missing_keywords(data, missing)
            html = template.render(**data)
            score, missing = validate_ats_match(html, keywords)
            healing_rounds += 1
        
        if healing_rounds > 0:
            print(f"   ⚡ Self-healed to {score:.1f}%")
    
    # Salva
    OUTPUT_DIR.mkdir(exist_ok=True)
    html_path = OUTPUT_DIR / f"{output_name}.html"
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)
    
    if HAS_WEASYPRINT:
        pdf_path = OUTPUT_DIR / f"{output_name}.pdf"
        HTML(string=html).write_pdf(pdf_path)
        return str(pdf_path)
    
    return str(html_path)


# ============== APPLICATION ENGINE ==============

def apply_to_job(job: Job, resume_path: str) -> bool:
    """
    Aplica para uma vaga automaticamente
    (Placeholder - precisa ser customizado por plataforma)
    """
    print(f"\n   📤 Aplicando para: {job.title} @ {job.company}")
    
    # Gupy - via API ou Selenium
    if job.source == "gupy":
        print(f"   ⚠️ Gupy requer login. URL: {job.url}")
        # Aqui entraria automação com Selenium/Playwright
        return False
    
    # LinkedIn Easy Apply (requer Selenium)
    if job.source == "linkedin":
        print(f"   ⚠️ LinkedIn Easy Apply requer Selenium. URL: {job.url}")
        return False
    
    return False


# ============== MAIN PIPELINE ==============

def run_full_pipeline(
    query: str = "Product Manager AI",
    gupy_companies: List[str] = None,
    apply: bool = False,
    limit: int = 5
) -> Dict:
    """
    Pipeline completo:
    1. Scraping de vagas
    2. Tailoring de currículo (STAR)
    3. Geração de PDF
    4. Aplicação automática (opcional)
    """
    print("\n" + "=" * 70)
    print("🚀 FULL AUTOMATION PIPELINE v2.0 - STAR METHODOLOGY")
    print("=" * 70)
    
    results = {
        "jobs_found": 0,
        "resumes_generated": [],
        "applications_sent": [],
        "errors": []
    }
    
    # 1. SCRAPING
    print("\n📋 [1/4] SCRAPING VAGAS...")
    print("-" * 50)
    
    if gupy_companies is None:
        gupy_companies = ["ifood", "nubank", "mercadolivre"]
    
    try:
        jobs = scrape_jobs(query, gupy_companies, save=True)
        results["jobs_found"] = len(jobs)
    except Exception as e:
        print(f"   ❌ Erro no scraping: {e}")
        results["errors"].append(f"Scraping: {e}")
        jobs = []
    
    if not jobs:
        print("   ⚠️ Nenhuma vaga encontrada. Usando vagas salvas...")
        # Fallback para vagas salvas
        for f in JOBS_DIR.glob("*.json"):
            try:
                with open(f) as jf:
                    job_data = json.load(jf)
                    jobs.append(Job(**job_data))
            except:
                pass
    
    # 2. INICIALIZAÇÃO
    print("\n🤖 [2/4] INICIALIZANDO...")
    print("-" * 50)
    
    llm = LLMOrchestrator()
    master_cv = load_master_cv()
    
    # 3. TAILORING + PDF
    print("\n✨ [3/4] GERANDO CURRÍCULOS (STAR)...")
    print("-" * 50)
    
    for i, job in enumerate(jobs[:limit], 1):
        print(f"\n   [{i}/{min(len(jobs), limit)}] {job.title}")
        print(f"       @ {job.company}")
        
        try:
            # Tailor
            data = tailor_resume_star(master_cv, job, llm)
            
            # Generate
            slug = re.sub(r'[^a-z0-9]', '_', f"{job.company}_{job.title}"[:40].lower())
            timestamp = datetime.now().strftime("%Y%m%d")
            output_name = f"{slug}_{timestamp}"
            
            pdf_path = generate_pdf(data, output_name)
            print(f"   ✅ PDF: {pdf_path}")
            
            results["resumes_generated"].append({
                "job_id": job.id,
                "job_title": job.title,
                "company": job.company,
                "pdf_path": pdf_path
            })
            
            # 4. APLICAÇÃO (se habilitado)
            if apply:
                if apply_to_job(job, pdf_path):
                    results["applications_sent"].append(job.id)
            
        except Exception as e:
            print(f"   ❌ Erro: {e}")
            results["errors"].append(f"{job.id}: {e}")
    
    # SUMMARY
    print("\n" + "=" * 70)
    print("📊 RESUMO")
    print("=" * 70)
    print(f"   Vagas encontradas: {results['jobs_found']}")
    print(f"   Currículos gerados: {len(results['resumes_generated'])}")
    print(f"   Aplicações enviadas: {len(results['applications_sent'])}")
    print(f"   Erros: {len(results['errors'])}")
    print("=" * 70 + "\n")
    
    return results


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Full Automation Pipeline")
    parser.add_argument("-q", "--query", default="Product Manager AI", help="Termo de busca")
    parser.add_argument("-c", "--companies", nargs="*", default=None, help="Slugs Gupy")
    parser.add_argument("-l", "--limit", type=int, default=5, help="Limite de vagas")
    parser.add_argument("--apply", action="store_true", help="Aplicar automaticamente")
    
    args = parser.parse_args()
    
    run_full_pipeline(
        query=args.query,
        gupy_companies=args.companies,
        limit=args.limit,
        apply=args.apply
    )
