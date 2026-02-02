#!/usr/bin/env python3
"""
ANTIFRAGILE Resume Pipeline v1.0
Sistema autônomo com self-healing e múltiplos fallbacks
Zero human-in-the-loop - roda do começo ao fim

FLUXO:
1. Carrega Master CV
2. Extrai keywords da vaga (regex ou LLM)
3. Seleciona experiências relevantes
4. Gera currículo tailored
5. Valida ATS match
6. Self-heal se match < 80%
7. Gera PDF
8. Notifica via webhook (opcional)
"""

import json
import re
import os
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict
import hashlib

try:
    from jinja2 import Template
except ImportError:
    subprocess.run(["pip", "install", "jinja2", "-q"])
    from jinja2 import Template

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    subprocess.run(["pip", "install", "requests", "-q"])
    import requests
    HAS_REQUESTS = True

try:
    from weasyprint import HTML
    HAS_WEASYPRINT = True
except ImportError:
    HAS_WEASYPRINT = False


BASE_DIR = Path(__file__).parent
TEMPLATES_DIR = BASE_DIR / "templates"
OUTPUT_DIR = BASE_DIR / "output"
JOBS_DIR = BASE_DIR / "jobs"


# ============== SELF-HEALING LLM LAYER ==============

class LLMOrchestrator:
    """Orquestrador antifrágil de LLMs com fallback automático"""
    
    def __init__(self):
        self.backends = []
        self._detect_backends()
    
    def _detect_backends(self):
        """Auto-detecta backends disponíveis"""
        # Ollama
        try:
            r = requests.get("http://localhost:11434/api/tags", timeout=2)
            if r.status_code == 200:
                models = [m["name"] for m in r.json().get("models", [])]
                for model in models:
                    self.backends.append(("ollama", model))
        except:
            pass
        
        # Groq
        if os.getenv("GROQ_API_KEY"):
            self.backends.append(("groq", "llama-3.3-70b-versatile"))
        
        # Gemini
        if os.getenv("GEMINI_API_KEY"):
            self.backends.append(("gemini", "gemini-1.5-flash"))
        
        print(f"🔧 LLM Backends detectados: {len(self.backends)}")
        for b in self.backends:
            print(f"   ✓ {b[0]}:{b[1]}")
    
    def call(self, prompt: str, max_retries: int = 3) -> Optional[str]:
        """Chama LLM com fallback automático"""
        for backend, model in self.backends:
            for attempt in range(max_retries):
                try:
                    if backend == "ollama":
                        return self._call_ollama(prompt, model)
                    elif backend == "groq":
                        return self._call_groq(prompt, model)
                    elif backend == "gemini":
                        return self._call_gemini(prompt)
                except Exception as e:
                    print(f"   ⚠️ {backend}:{model} tentativa {attempt+1} falhou: {e}")
        return None
    
    def _call_ollama(self, prompt: str, model: str) -> str:
        r = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": model, "prompt": prompt, "stream": False},
            timeout=120
        )
        return r.json().get("response", "")
    
    def _call_groq(self, prompt: str, model: str) -> str:
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {os.getenv('GROQ_API_KEY')}"},
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7
            },
            timeout=60
        )
        return r.json()["choices"][0]["message"]["content"]
    
    def _call_gemini(self, prompt: str) -> str:
        r = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={os.getenv('GEMINI_API_KEY')}",
            json={"contents": [{"parts": [{"text": prompt}]}]},
            timeout=60
        )
        return r.json()["candidates"][0]["content"]["parts"][0]["text"]


# ============== KEYWORD EXTRACTION (Self-healing) ==============

def extract_keywords_regex(job_text: str) -> List[str]:
    """Extrai keywords usando regex (fallback sem LLM)"""
    # Keywords conhecidas de vagas tech/AI
    known_keywords = [
        "GPM", "Product Manager", "Product Management", "IA Generativa", "AI",
        "LLM", "RAG", "Fine-tuning", "Prompt Engineering", "Agentic",
        "ML Engineering", "Machine Learning", "Data Science", "Python",
        "SQL", "Docker", "n8n", "Langchain", "stakeholders", "roadmap",
        "GTM", "Go-to-Market", "A/B Testing", "agile", "scrum",
        "marketplace", "escala", "scale", "agentes", "agents",
        "C-level", "liderança", "leadership", "squad", "cross-functional"
    ]
    
    found = []
    job_lower = job_text.lower()
    for kw in known_keywords:
        if kw.lower() in job_lower:
            found.append(kw)
    
    return found


def extract_keywords_llm(job_text: str, llm: LLMOrchestrator) -> List[str]:
    """Extrai keywords usando LLM"""
    prompt = f"""Extraia as 20 keywords mais importantes desta vaga para otimização ATS.
Retorne APENAS uma lista JSON de strings, sem explicações.

VAGA:
{job_text}

FORMATO: ["keyword1", "keyword2", ...]"""
    
    response = llm.call(prompt)
    if response:
        try:
            # Tenta extrair JSON da resposta
            match = re.search(r'\[.*\]', response, re.DOTALL)
            if match:
                return json.loads(match.group())
        except:
            pass
    return []


def extract_keywords(job_text: str, llm: Optional[LLMOrchestrator] = None) -> List[str]:
    """Extração antifrágil - tenta LLM, fallback para regex"""
    keywords = []
    
    # Tenta LLM primeiro
    if llm:
        keywords = extract_keywords_llm(job_text, llm)
        if keywords:
            print(f"   ✓ LLM extraiu {len(keywords)} keywords")
    
    # Fallback regex
    if not keywords:
        keywords = extract_keywords_regex(job_text)
        print(f"   ✓ Regex extraiu {len(keywords)} keywords")
    
    return keywords


# ============== MASTER CV LOADER ==============

def load_master_cv() -> Dict:
    """Carrega Master CV com validação"""
    path = BASE_DIR / "master_profile.json"
    if not path.exists():
        raise FileNotFoundError(f"Master CV não encontrado: {path}")
    
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # Validação básica
    assert "candidato" in data, "Master CV inválido: falta 'candidato'"
    assert "experiencias" in data or "experiencias_star" in data, "Master CV inválido: falta 'experiencias' ou 'experiencias_star'"
    
    print(f"   ✓ Master CV carregado: {data['candidato']['nome_completo']}")
    exp_count = len(data.get('experiencias', data.get('experiencias_star', [])))
    print(f"   ✓ {exp_count} experiências disponíveis")
    
    return data


# ============== TAILORING ENGINE ==============

def score_experience(exp: Dict, keywords: List[str]) -> int:
    """Pontua experiência baseado em match de keywords"""
    exp_text = json.dumps(exp, ensure_ascii=False).lower()
    score = 0
    for kw in keywords:
        if kw.lower() in exp_text:
            score += 1
    return score


def select_best_experiences(master_cv: Dict, keywords: List[str], max_exp: int = 6) -> List[Dict]:
    """Seleciona experiências mais relevantes para a vaga"""
    experiences = master_cv.get("experiencias", [])
    
    # Pontua cada experiência
    scored = [(exp, score_experience(exp, keywords)) for exp in experiences]
    scored.sort(key=lambda x: x[1], reverse=True)
    
    # Seleciona top N
    selected = [exp for exp, score in scored[:max_exp]]
    
    print(f"   ✓ Selecionadas {len(selected)} experiências mais relevantes")
    
    return selected


def format_experience_bullets(exp: Dict) -> List[str]:
    """Formata bullets de uma experiência"""
    bullets = []
    for b in exp.get("bullets_detalhados", [])[:4]:
        bullet = b.get("descricao", "")
        if b.get("metrica"):
            bullet += f" <span class='metric'>{b['metrica']}</span>"
        bullets.append(bullet)
    return bullets


def build_tailored_data(master_cv: Dict, keywords: List[str], job_title: str = "") -> Dict:
    """Constrói dados tailored para o template"""
    candidato = master_cv["candidato"]
    experiences = select_best_experiences(master_cv, keywords)
    
    # Headline dinâmico
    if "gpm" in job_title.lower() or "group product" in job_title.lower():
        headline = "Group Product Manager (GPM) | IA Generativa & LLM Products | Ex-Meta | Agentic AI at Scale"
    elif "ai" in job_title.lower() or "ia" in job_title.lower():
        headline = candidato.get("headlines_alternativas", {}).get("ai_product", candidato["headline_master"])
    else:
        headline = candidato["headline_master"]
    
    # Summary dinâmico
    summary = candidato.get("summary_alternativas", {}).get("ai_focused", candidato["summary_master"])
    
    # Keywords string
    keywords_str = " • ".join(keywords[:15])
    
    # Experiências formatadas
    formatted_exp = []
    for exp in experiences:
        formatted_exp.append({
            "empresa": exp["empresa"],
            "cargo": exp["cargo"],
            "periodo": exp.get("periodo", ""),
            "scope": exp.get("escopo", exp.get("scope", "")),
            "bullets": format_experience_bullets(exp)
        })
    
    # Projetos AI
    projects = []
    if "projetos_ai_automation" in master_cv:
        for proj in master_cv["projetos_ai_automation"].get("projetos", [])[:4]:
            projects.append({
                "nome": proj["nome"],
                "descricao": proj["descricao"],
                "stack": " • ".join(proj.get("stack", []))
            })
    
    # Skills organizadas por relevância
    skills = master_cv.get("skills", {})
    skills_formatted = [
        {
            "name": "AI & LLM",
            "skills_list": [
                {"name": kw, "class": "critical"} 
                for kw in skills.get("ai_infrastructure", {}).get("keywords", [])[:6]
            ]
        },
        {
            "name": "Data & Infra",
            "skills_list": [
                {"name": kw, "class": ""} 
                for kw in skills.get("data_analytics", {}).get("keywords", [])[:6]
            ]
        },
        {
            "name": "Product",
            "skills_list": [
                {"name": kw, "class": ""} 
                for kw in skills.get("product_marketing", {}).get("keywords", [])[:6]
            ]
        },
        {
            "name": "Leadership",
            "skills_list": [
                {"name": kw, "class": ""} 
                for kw in skills.get("leadership", {}).get("keywords", [])[:6]
            ]
        }
    ]
    
    # Educação
    education = []
    for edu in master_cv.get("formacao", [])[:4]:
        education.append({
            "titulo": edu.get("programa", edu.get("titulo", "")),
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
        "experience": formatted_exp,
        "projects": projects,
        "skills": skills_formatted,
        "education": education,
        "languages": candidato.get("idiomas", [])
    }


# ============== ATS VALIDATION (Self-healing) ==============

def validate_ats_match(html: str, keywords: List[str]) -> tuple:
    """Valida match de keywords ATS, retorna (score, missing)"""
    html_lower = html.lower()
    found = []
    missing = []
    
    for kw in keywords:
        if kw.lower() in html_lower:
            found.append(kw)
        else:
            missing.append(kw)
    
    score = len(found) / len(keywords) * 100 if keywords else 0
    return score, missing


def inject_missing_keywords(data: Dict, missing: List[str]) -> Dict:
    """Self-healing: injeta keywords faltantes no currículo"""
    # Adiciona keywords faltantes na seção de keywords
    current_keywords = data.get("keywords", "")
    for kw in missing[:5]:  # Máximo 5 para não poluir
        if kw.lower() not in current_keywords.lower():
            current_keywords += f" • {kw}"
    
    data["keywords"] = current_keywords
    return data


# ============== MAIN PIPELINE ==============

def generate_resume(job_path: str, output_name: Optional[str] = None) -> str:
    """
    Pipeline antifrágil completo
    Retorna caminho do PDF gerado
    """
    print("\n" + "=" * 60)
    print("🚀 ANTIFRAGILE RESUME PIPELINE v1.0")
    print("=" * 60)
    
    # 1. Carrega vaga
    print("\n📋 [1/7] Carregando descrição da vaga...")
    if os.path.exists(job_path):
        with open(job_path, "r", encoding="utf-8") as f:
            job_text = f.read()
    else:
        job_text = job_path
    
    # Extrai título da vaga
    job_title = job_text.split("\n")[0] if job_text else ""
    print(f"   ✓ Vaga: {job_title[:60]}...")
    
    # 2. Inicializa LLM
    print("\n🤖 [2/7] Detectando backends LLM...")
    llm = LLMOrchestrator()
    
    # 3. Extrai keywords
    print("\n🔍 [3/7] Extraindo keywords...")
    keywords = extract_keywords(job_text, llm)
    print(f"   Keywords: {', '.join(keywords[:10])}...")
    
    # 4. Carrega Master CV
    print("\n📂 [4/7] Carregando Master CV...")
    master_cv = load_master_cv()
    
    # 5. Tailoring
    print("\n✨ [5/7] Gerando currículo tailored...")
    data = build_tailored_data(master_cv, keywords, job_title)
    
    # 6. Renderiza HTML
    print("\n📄 [6/7] Renderizando template...")
    template_path = TEMPLATES_DIR / "resume_sota.html"
    if not template_path.exists():
        template_path = TEMPLATES_DIR / "resume.html"
    
    with open(template_path, "r", encoding="utf-8") as f:
        template = Template(f.read())
    
    html = template.render(**data)
    
    # 7. Validação ATS + Self-healing
    print("\n🔧 [7/7] Validando ATS match...")
    score, missing = validate_ats_match(html, keywords)
    print(f"   Score inicial: {score:.1f}%")
    
    # Self-heal se score < 80%
    healing_rounds = 0
    while score < 80 and healing_rounds < 3 and missing:
        print(f"   ⚡ Self-healing round {healing_rounds + 1}: injetando {len(missing[:5])} keywords")
        data = inject_missing_keywords(data, missing)
        html = template.render(**data)
        score, missing = validate_ats_match(html, keywords)
        healing_rounds += 1
    
    print(f"   ✓ Score final: {score:.1f}%")
    if missing:
        print(f"   ⚠️ Keywords não incluídas: {', '.join(missing[:5])}")
    
    # Output
    OUTPUT_DIR.mkdir(exist_ok=True)
    
    if not output_name:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        slug = re.sub(r'[^a-z0-9]', '_', job_title.lower())[:30]
        output_name = f"{slug}_{timestamp}"
    
    html_path = OUTPUT_DIR / f"{output_name}.html"
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)
    
    pdf_path = OUTPUT_DIR / f"{output_name}.pdf"
    if HAS_WEASYPRINT:
        HTML(string=html).write_pdf(pdf_path)
        print(f"\n✅ PDF gerado: {pdf_path}")
    else:
        print(f"\n✅ HTML gerado: {html_path}")
        print("   ⚠️ WeasyPrint não disponível para PDF")
        pdf_path = html_path
    
    print("\n" + "=" * 60)
    print("🎯 PIPELINE COMPLETO - ZERO HUMAN IN THE LOOP")
    print("=" * 60 + "\n")
    
    return str(pdf_path)


# ============== CLI ==============

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Antifragile Resume Pipeline")
    parser.add_argument("job", help="Caminho para arquivo de vaga ou texto direto")
    parser.add_argument("-o", "--output", help="Nome do output (sem extensão)")
    
    args = parser.parse_args()
    
    generate_resume(args.job, args.output)
