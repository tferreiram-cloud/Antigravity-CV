#!/usr/bin/env python3
"""
Taylor-Made Resume Generator v2
Gera currículos personalizados usando LLM custo zero (Ollama/Groq)
"""

import json
import os
import argparse
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Optional

try:
    from jinja2 import Template
except ImportError:
    print("❌ Jinja2 não instalado. Execute: pip install jinja2")
    exit(1)

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

try:
    from weasyprint import HTML
    HAS_WEASYPRINT = True
except ImportError:
    HAS_WEASYPRINT = False


# Diretório base do projeto
BASE_DIR = Path(__file__).parent
TEMPLATES_DIR = BASE_DIR / "templates"
OUTPUT_DIR = BASE_DIR / "output"


# ============== LLM BACKENDS (Custo Zero) ==============

def check_ollama_available() -> bool:
    """Verifica se Ollama está rodando"""
    try:
        result = subprocess.run(["ollama", "list"], capture_output=True, timeout=5)
        return result.returncode == 0
    except:
        return False


def call_ollama(prompt: str, model: str = "gemma3:4b") -> Optional[str]:
    """Chama Ollama local"""
    if not HAS_REQUESTS:
        print("⚠️  requests não instalado")
        return None
    
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.7}
            },
            timeout=120
        )
        if response.status_code == 200:
            return response.json().get("response", "")
    except Exception as e:
        print(f"⚠️  Erro Ollama: {e}")
    return None


def call_groq(prompt: str, model: str = "llama-3.3-70b-versatile") -> Optional[str]:
    """Chama Groq API (free tier)"""
    if not HAS_REQUESTS:
        return None
    
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return None
    
    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": "Você retorna apenas JSON válido, sem markdown ou explicações."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 2500
            },
            timeout=60
        )
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"⚠️  Erro Groq: {e}")
    return None


def call_gemini(prompt: str) -> Optional[str]:
    """Chama Google Gemini API (free tier)"""
    if not HAS_REQUESTS:
        return None
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None
    
    try:
        response = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}",
            headers={"Content-Type": "application/json"},
            json={
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.7, "maxOutputTokens": 2500}
            },
            timeout=60
        )
        if response.status_code == 200:
            return response.json()["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        print(f"⚠️  Erro Gemini: {e}")
    return None


# ============== CORE LOGIC ==============

def load_master_profile() -> dict:
    """Carrega o perfil master do candidato"""
    with open(BASE_DIR / "master_profile.json", "r", encoding="utf-8") as f:
        return json.load(f)


def load_job_description(job_path: str) -> str:
    """Carrega descrição da vaga de arquivo ou retorna string direta"""
    if os.path.exists(job_path):
        with open(job_path, "r", encoding="utf-8") as f:
            return f.read()
    return job_path


def get_tailoring_prompt(profile: dict, job_description: str) -> str:
    """Retorna o prompt para tailoring via LLM"""
    return f"""Você é um especialista em currículos para posições de Staff/GPM em tecnologia.

METODOLOGIA AIM:
Cada bullet point DEVE seguir: [Verbo de Ação Forte] + [Desafio Técnico] + [Impacto Mensurável com métrica]

CANDIDATO (Master Profile):
{json.dumps(profile['candidato'], indent=2, ensure_ascii=False)}

EXPERIÊNCIAS DISPONÍVEIS:
{json.dumps(profile['experiencias'][:4], indent=2, ensure_ascii=False)}

PROJETOS AI:
{json.dumps(profile.get('projetos_ai_automation', {}), indent=2, ensure_ascii=False)}

VAGA ALVO:
{job_description}

TAREFA:
1. Analise a vaga e identifique keywords críticas
2. Escolha o headline mais adequado das opções disponíveis ou crie um novo
3. Reescreva o summary (máx 2 frases) focando no match com a vaga
4. Selecione as 3-4 experiências mais relevantes
5. Para cada experiência, reescreva 2-3 bullets usando AIM
6. Use <span class="metric">valor</span> para destacar métricas

OUTPUT (JSON válido):
{{
  "headline": "headline tailored",
  "summary": "summary tailored (2 frases máx)",
  "experience": [
    {{
      "empresa": "Nome",
      "cargo": "Cargo tailored",
      "periodo": "YYYY - YYYY",
      "bullets": ["bullet 1", "bullet 2", "bullet 3"]
    }}
  ],
  "skills": {{
    "ai": ["skill1", "skill2", "skill3", "skill4", "skill5", "skill6"],
    "data": ["skill1", "skill2", "skill3", "skill4"],
    "product": ["skill1", "skill2", "skill3", "skill4"]
  }}
}}

REGRAS CRÍTICAS:
- Priorize experiências com AI, n8n, Docker, SQL, automação
- NÃO INVENTE dados - use apenas o que está no perfil
- Tom técnico, terminologia de produto/engenharia
- Retorne APENAS o JSON, sem explicações
"""


def tailor_with_llm(profile: dict, job_description: str, backend: str = "auto") -> Optional[dict]:
    """Usa LLM para tailoring do currículo"""
    prompt = get_tailoring_prompt(profile, job_description)
    response = None
    
    if backend == "auto":
        # Tenta Ollama primeiro (local), depois Groq, depois Gemini
        if check_ollama_available():
            print("🤖 Usando Ollama (local)...")
            response = call_ollama(prompt)
        
        if not response and os.getenv("GROQ_API_KEY"):
            print("🤖 Usando Groq API...")
            response = call_groq(prompt)
        
        if not response and os.getenv("GEMINI_API_KEY"):
            print("🤖 Usando Gemini API...")
            response = call_gemini(prompt)
    
    elif backend == "ollama":
        print("🤖 Usando Ollama (local)...")
        response = call_ollama(prompt)
    
    elif backend == "groq":
        print("🤖 Usando Groq API...")
        response = call_groq(prompt)
    
    elif backend == "gemini":
        print("🤖 Usando Gemini API...")
        response = call_gemini(prompt)
    
    if not response:
        print("⚠️  Nenhum LLM disponível. Usando perfil base.")
        return None
    
    # Parse JSON com fallback robusto
    try:
        content = response.strip()
        # Limpa possível markdown
        if content.startswith("```"):
            lines = content.split("\n")
            content = "\n".join(lines[1:])
            if "```" in content:
                content = content.split("```")[0]
        
        # Tenta encontrar JSON delimitado por { }
        start = content.find("{")
        end = content.rfind("}") + 1
        if start >= 0 and end > start:
            content = content[start:end]
        
        return json.loads(content)
    except json.JSONDecodeError as e:
        print(f"⚠️  Erro parsing JSON: {e}")
        print("   Usando perfil base como fallback.")
        return None



def build_default_resume_data(profile: dict) -> dict:
    """Constrói dados do currículo sem LLM (fallback)"""
    candidato = profile["candidato"]
    
    # Handle Summary Source
    summary_map = candidato.get("summary_por_vaga", {})
    # Get first available summary or empty string
    default_summary = next(iter(summary_map.values())) if summary_map else ""
    summary = candidato.get("summary_master", default_summary)
    
    # Handle Experience Source
    experiments_source = profile.get("experiencias_star", profile.get("experiencias", []))
    
    experience = []
    for exp in experiments_source[:4]:
        bullets = []
        # Try finding bullets in different formats
        raw_bullets = exp.get("bullets_star", exp.get("bullets_detalhados", exp.get("bullets", [])))
        
        for b in raw_bullets[:3]:
            if isinstance(b, dict):
                # Format: STAR (Situation, Task, Action, Result)
                # We want: Action + Task/Situation + Result
                action = b.get('action', '')
                result = b.get('result', '')
                bullet = f"{action}. Result: {result}"
                bullets.append(bullet)
            elif isinstance(b, str):
                bullets.append(b)
        
        if bullets:
            experience.append({
                "empresa": exp.get("empresa", ""),
                "cargo": exp.get("cargo", ""),
                "periodo": exp.get("periodo", ""),
                "bullets": bullets,
                "tech_stack": exp.get("stack_tecnica", exp.get("stack", []))
            })
    
    # Skills mapping (support v3 structure)
    skills = profile.get("skills", {})
    # If skills is dict of dicts (v3), flatten keys or extract keywords
    ai_skills = skills.get("ai_llm", {}).get("keywords", []) or skills.get("ai_infrastructure", {}).get("keywords", [])
    data_skills = skills.get("data", {}).get("keywords", []) or skills.get("data_analytics", {}).get("keywords", [])
    prod_skills = skills.get("product", {}).get("keywords", []) or skills.get("product_marketing", {}).get("keywords", [])

    return {
        "headline": candidato.get("headline_master", "Professional"),
        "summary": summary,
        "experience": experience,
        "skills": {
            "ai": ai_skills[:6],
            "data": data_skills[:4],
            "product": prod_skills[:4]
        },
        "projects": profile.get("projetos_ai", []) # Pass projects if available
    }



def generate_html(profile: dict, tailored_data: dict, template_name: str = "resume.html") -> str:
    """Gera HTML do currículo usando template específico"""
    candidato = profile["candidato"]
    
    template_path = TEMPLATES_DIR / template_name
    if not template_path.exists():
        print(f"⚠️ Template {template_name} não encontrado. Usando resume.html")
        template_path = TEMPLATES_DIR / "resume.html"

    with open(template_path, "r", encoding="utf-8") as f:
        template = Template(f.read())
    
    # Prepara educação (top 4)
    education = []
    for edu in profile.get("formacao", [])[:4]:
        education.append({
            "titulo": edu.get("programa", edu.get("titulo", "")),
            "instituicao": edu["instituicao"],
            "periodo": edu.get("periodo", edu.get("ano", edu.get("status", ""))),
            "curso": edu.get("curso", edu.get("programa", ""))
        })
    
    html = template.render(
        profile=profile,
        tailored=tailored_data,
        candidato=candidato, # legacy support
        headline=tailored_data["headline"], # legacy support
        email=candidato.get("email", ""), # legacy support
        linkedin=candidato.get("linkedin", ""), # legacy support
        summary=tailored_data["summary"], # legacy support
        experience=tailored_data["experience"], # legacy support
        skills=tailored_data["skills"], # legacy support
        education=education, # legacy support
        languages=candidato.get("idiomas", []) # legacy support
    )
    
    return html


def save_output(html: str, output_path: Path, generate_pdf: bool = True):
    """Salva HTML e opcionalmente PDF no caminho especificado"""
    OUTPUT_DIR.mkdir(exist_ok=True)
    
    # Salva HTML
    with open(output_path.with_suffix(".html"), "w", encoding="utf-8") as f:
        f.write(html)
    print(f"✅ HTML salvo: {output_path.with_suffix('.html')}")
    
    # Gera PDF se possível e solicitado
    if generate_pdf:
        if HAS_WEASYPRINT:
            pdf_path = output_path.with_suffix(".pdf")
            HTML(string=html).write_pdf(pdf_path)
            print(f"✅ PDF salvo: {pdf_path}")
        else:
            print("⚠️  WeasyPrint não instalado. Abra o HTML no navegador → Print → Save as PDF")


def main():
    parser = argparse.ArgumentParser(
        description="Taylor-Made Resume Generator (Custo Zero)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python generate_resume.py -j examples/ifood_ai_job.txt
  python generate_resume.py -j vaga.txt --backend ollama
  
Configuração LLM:
  Ollama: Instale e rode 'ollama run gemma3:4b'
  Groq:   export GROQ_API_KEY="gsk_..."
  Gemini: export GEMINI_API_KEY="..."
        """
    )
    parser.add_argument("--job", "-j", required=True, help="Arquivo com descrição da vaga")
    parser.add_argument("--output", "-o", default=None, help="Nome do arquivo de saída (base)")
    parser.add_argument("--backend", "-b", choices=["auto", "ollama", "groq", "gemini"], 
                        default="auto", help="Backend LLM (default: auto)")
    parser.add_argument("--no-llm", action="store_true", help="Não usar LLM (usa perfil base)")
    parser.add_argument("--legacy", action="store_true", help="Usar templates legados (single file)")
    
    args = parser.parse_args()
    
    print("📄 Taylor-Made Resume Generator v2 (Premium Edition)")
    print("=" * 40)
    
    # Carrega dados
    profile = load_master_profile()
    job_description = load_job_description(args.job)
    
    print(f"👤 Candidato: {profile['candidato']['nome_completo']}")
    print(f"📋 Vaga: {args.job}")
    print(f"🔧 Backend: {args.backend}")
    
    # Tailoring
    if args.no_llm:
        tailored_data = build_default_resume_data(profile)
    else:
        tailored_data = tailor_with_llm(profile, job_description, args.backend)
        if tailored_data is None:
            tailored_data = build_default_resume_data(profile)
    
    # Define base name
    if args.output:
        base_name = args.output.replace(".pdf", "").replace(".html", "")
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        company_slug = tailored_data.get("experience", [{}])[0].get("empresa", "Job").lower().replace(" ", "_")[:15]
        # Tenta pegar empresa da vaga se possível (não temos extraído structured ainda aqui, simplificação)
        base_name = f"cv_{timestamp}"

    # Generate Outputs
    if args.legacy:
        # Legacy Mode: One file for both
        html = generate_html(profile, tailored_data, "resume.html")
        save_output(html, OUTPUT_DIR / base_name, generate_pdf=True)
    else:
        # Premium Mode: Two Artifacts
        print("\n🎨 Gerando Artifacts Premium...")
        
        # 1. Web Version ("Visual")
        html_web = generate_html(profile, tailored_data, "premium_web.html")
        save_output(html_web, OUTPUT_DIR / f"{base_name}_web", generate_pdf=False)
        
        # 2. ATS Version ("Technical")
        html_ats = generate_html(profile, tailored_data, "premium_ats.html")
        save_output(html_ats, OUTPUT_DIR / f"{base_name}_ats", generate_pdf=True)
    
    print("=" * 40)
    print("🎯 Sucesso! Arquivos gerados em output/")


if __name__ == "__main__":
    main()

