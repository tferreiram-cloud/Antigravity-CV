#!/usr/bin/env python3
"""
ANTIGRAVITY TAILOR - Main Pipeline (Refactored)

Sistema de geração de currículos com:
- Scraping seguro com validação
- Matching inteligente contra Master CV
- Preview antes de geração
- Modos de falha elegantes

USO:
    python tailor.py https://empresa.com/vaga
    python tailor.py --text "Descrição da vaga..."
    python tailor.py vaga.txt
"""

import sys
import json
import argparse
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Optional, Tuple

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from core import (
    Job, Language, Seniority, OutputFormat,
    MatchResult, ResumeOutput, PipelineState,
    OUTPUT_DIR, JOBS_DIR, config
)
from engine import (
    JobInterpreter, CVMatcher, MasterCV,
    create_job_from_scrape, build_resume
)


# ============== SCRAPER (Simplified) ==============

def scrape_url(url: str) -> Tuple[str, str, str, str]:
    """
    Scrape básico de URL.
    Retorna (title, company, description, location)
    """
    import requests
    from bs4 import BeautifulSoup
    
    headers = config.scraping.headers
    
    try:
        response = requests.get(url, headers=headers, timeout=config.scraping.timeout_seconds)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Tentar extrair título
        title = ""
        title_selectors = [
            "h1.topcard__title",  # LinkedIn
            "h1.titulo-vaga",     # Gupy
            "h1",                  # Generic
            ".job-title",
            "[data-testid='job-title']"
        ]
        for selector in title_selectors:
            elem = soup.select_one(selector)
            if elem:
                title = elem.get_text(strip=True)
                break
        
        # Tentar extrair empresa
        company = ""
        company_selectors = [
            "a.topcard__org-name-link",  # LinkedIn
            ".company-name",
            "[data-testid='company-name']"
        ]
        for selector in company_selectors:
            elem = soup.select_one(selector)
            if elem:
                company = elem.get_text(strip=True)
                break
        
        # Extrair descrição (corpo principal)
        description = ""
        desc_selectors = [
            ".description__text",        # LinkedIn
            ".job-description",
            ".description",
            "article",
            "main"
        ]
        for selector in desc_selectors:
            elem = soup.select_one(selector)
            if elem:
                description = elem.get_text(separator="\n", strip=True)
                break
        
        # Fallback: pegar todo o texto
        if not description:
            description = soup.get_text(separator="\n", strip=True)
        
        return title, company, description, ""
        
    except Exception as e:
        print(f"⚠️ Erro no scraping: {e}")
        return "", "", "", ""


# ============== PIPELINE STEPS ==============

def step_input(args) -> PipelineState:
    """
    STEP 1: Input
    Lê vaga de URL, arquivo ou texto direto
    """
    state = PipelineState(step="input")
    
    # Determinar source
    if args.text:
        # Texto direto
        title = args.title or "Vaga Manual"
        company = args.company or "Empresa"
        description = args.text
        url = ""
        source = "manual"
    elif args.job.startswith("http"):
        # URL
        print(f"🔍 Scraping: {args.job}")
        title, company, description, location = scrape_url(args.job)
        url = args.job
        source = "url"
    elif Path(args.job).exists():
        # Arquivo
        with open(args.job, "r", encoding="utf-8") as f:
            description = f.read()
        title = Path(args.job).stem
        company = ""
        url = ""
        source = "file"
    else:
        # Texto inline
        description = args.job
        title = "Vaga"
        company = ""
        url = ""
        source = "inline"
    
    # Criar Job com validação
    job, validation = create_job_from_scrape(
        title=title,
        company=company,
        description=description,
        url=url,
        source=source
    )
    
    state.job = job
    
    # Checar validação
    if not validation.is_valid:
        print("\n⚠️ Não consegui ler a vaga com segurança.")
        print("Checklist:")
        print(validation.to_checklist_str())
        print("\nPor favor cole o texto completo ou tente outro link.")
        state.add_error("Validação de scraping falhou")
        return state
    
    print(f"\n✅ Vaga carregada: {job.title} @ {job.company}")
    print(f"   Idioma: {job.language.value}")
    print(f"   Senioridade: {job.seniority.value if job.seniority else 'N/A'}")
    print(f"   Tipo: {job.job_type}")
    
    return state


def step_interpret(state: PipelineState) -> PipelineState:
    """
    STEP 2: Interpretar vaga
    Extrai keywords, senioridade, tipo
    """
    if state.has_errors():
        return state
    
    state.step = "interpret"
    
    job = state.job
    print(f"\n🔍 Interpretando vaga...")
    print(f"   Hard skills: {len(job.hard_skills)} encontradas")
    print(f"   Keywords ATS: {len(job.keywords_ats)} encontradas")
    
    if config.debug_mode:
        print(f"   Skills: {', '.join(job.hard_skills[:10])}")
    
    return state


def step_match(state: PipelineState, language: Language, junior_mode: bool = False) -> PipelineState:
    """
    STEP 3: Match contra Master CV
    Calcula score e seleciona experiências
    """
    if state.has_errors():
        return state
    
    state.step = "match"
    
    # Carregar Master CV
    print(f"\n📊 Carregando Master CV ({language.value})...")
    try:
        master = MasterCV.load(language=language, junior_mode=junior_mode)
    except FileNotFoundError as e:
        state.add_error(str(e))
        return state
    
    # Fazer matching
    matcher = CVMatcher(master, debug=config.debug_mode)
    match_result = matcher.match(state.job)
    state.match_result = match_result
    
    # Output
    print(f"\n{'='*50}")
    print(f"📊 MATCH SCORE: {match_result.total_percentage}%")
    print(f"{'='*50}")
    print(f"\n✅ Headline: {match_result.headline_id}")
    print(f"   {match_result.selected_headline}")
    print(f"\n📋 Experiências selecionadas ({len(match_result.selected_experiences)}):")
    for exp in match_result.selected_experiences:
        print(f"   • {exp.company} ({exp.tier}) - {exp.score:.0%} match")
    
    print(f"\n✅ Keywords cobertas ({len(match_result.keywords_covered)}):")
    print(f"   {', '.join(match_result.keywords_covered[:10])}")
    
    if match_result.keywords_missing:
        print(f"\n⚠️ Keywords não cobertas ({len(match_result.keywords_missing)}):")
        print(f"   {', '.join(match_result.keywords_missing[:5])}")
    
    for warning in match_result.warnings:
        print(f"\n{warning}")
    
    # Verificar se deve continuar
    if not match_result.should_proceed():
        print(f"\n⚠️ Match baixo ({match_result.total_percentage}%).")
        print("Esta vaga pode não ser um bom match para o perfil atual.")
        if not config.debug_mode:
            response = input("Deseja gerar mesmo assim? [s/N] ")
            if response.lower() != "s":
                state.add_error("Usuário cancelou por baixo match")
                return state
    
    return state


def step_build(state: PipelineState, language: Language, junior_mode: bool = False) -> PipelineState:
    """
    STEP 4: Construir currículo
    """
    if state.has_errors():
        return state
    
    state.step = "build"
    
    master = MasterCV.load(language=language, junior_mode=junior_mode)
    resume = build_resume(master, state.match_result, state.job)
    state.resume = resume
    
    print(f"\n✅ Currículo construído")
    print(f"   Experiências: {len(resume.experiences)}")
    print(f"   Skills: {len(resume.skills)}")
    
    return state


def step_render(state: PipelineState, output_format: OutputFormat, output_name: Optional[str] = None) -> Path:
    """
    STEP 5: Renderizar output
    Gera PDF/HTML/Markdown
    """
    if state.has_errors():
        return None
    
    state.step = "render"
    
    resume = state.resume
    
    # Nome do arquivo
    if output_name:
        name = output_name
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        company = state.job.company.lower().replace(" ", "_")[:20]
        name = f"{company}_{timestamp}"
    
    # Renderizar HTML
    html_content = render_html(resume)
    html_path = OUTPUT_DIR / f"{name}.html"
    html_path.write_text(html_content, encoding="utf-8")
    
    # Gerar PDF se solicitado
    if output_format == OutputFormat.PDF:
        try:
            from weasyprint import HTML
            pdf_path = OUTPUT_DIR / f"{name}.pdf"
            HTML(string=html_content).write_pdf(pdf_path)
            print(f"\n📄 PDF gerado: {pdf_path}")
            return pdf_path
        except ImportError:
            print("⚠️ WeasyPrint não instalado. Gerando apenas HTML.")
            output_format = OutputFormat.HTML
    
    if output_format == OutputFormat.HTML:
        print(f"\n📄 HTML gerado: {html_path}")
        return html_path
    
    return html_path


def render_html(resume: ResumeOutput) -> str:
    """Renderiza HTML do currículo"""
    # Template inline simples
    template = """<!DOCTYPE html>
<html lang="{lang}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{name} - Resume</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: 'Segoe UI', Tahoma, sans-serif;
            font-size: 11pt;
            line-height: 1.5;
            color: #333;
            padding: 40px;
            max-width: 800px;
            margin: 0 auto;
        }}
        h1 {{ font-size: 24pt; font-weight: 700; margin-bottom: 5px; }}
        h2 {{ font-size: 12pt; font-weight: 600; color: #444; margin: 20px 0 10px; border-bottom: 1px solid #ddd; padding-bottom: 5px; }}
        h3 {{ font-size: 11pt; font-weight: 600; margin-bottom: 3px; }}
        .header {{ margin-bottom: 20px; }}
        .contact {{ font-size: 10pt; color: #666; margin-bottom: 10px; }}
        .headline {{ font-size: 12pt; font-weight: 500; color: #555; margin-bottom: 10px; }}
        .summary {{ font-size: 10pt; color: #555; margin-bottom: 15px; }}
        .experience {{ margin-bottom: 15px; }}
        .exp-header {{ display: flex; justify-content: space-between; }}
        .exp-company {{ font-weight: 600; }}
        .exp-period {{ font-size: 10pt; color: #666; }}
        .exp-role {{ font-style: italic; margin-bottom: 5px; }}
        .exp-scope {{ font-size: 9pt; color: #777; margin-bottom: 5px; }}
        ul {{ margin-left: 20px; }}
        li {{ margin-bottom: 3px; font-size: 10pt; }}
        .skills {{ display: flex; flex-wrap: wrap; gap: 8px; }}
        .skill {{ background: #f0f0f0; padding: 3px 8px; border-radius: 3px; font-size: 9pt; }}
        /* footer removed - internal data */
    </style>
</head>
<body>
    <div class="header">
        <h1>{name}</h1>
        <div class="contact">{location} | {email} | {linkedin} | {phone}</div>
        <div class="headline">{headline}</div>
        <div class="summary">{summary}</div>
    </div>
    
    <h2>Professional Experience</h2>
    {experiences_html}
    
    <h2>Education</h2>
    {education_html}
    
    <h2>Skills</h2>
    <div class="skills">{skills_html}</div>
</body>
</html>"""
    
    # Experiências
    exp_html = ""
    for exp in resume.experiences:
        bullets = "".join(f"<li>{b}</li>" for b in exp.get("bullets", []))
        exp_html += f"""
        <div class="experience">
            <div class="exp-header">
                <span class="exp-company">{exp.get('company', '')}</span>
                <span class="exp-period">{exp.get('period', '')}</span>
            </div>
            <div class="exp-role">{exp.get('role', '')}</div>
            <div class="exp-scope">{exp.get('scope', '')}</div>
            <ul>{bullets}</ul>
        </div>"""
    
    # Educação
    edu_html = "<ul>"
    for edu in resume.education:
        highlight = f" - {edu.get('highlight', '')}" if edu.get('highlight') else ""
        edu_html += f"<li><strong>{edu.get('institution', '')}</strong> - {edu.get('program', '')} ({edu.get('year', '')}){highlight}</li>"
    edu_html += "</ul>"
    
    # Skills
    skills_html = "".join(f'<span class="skill">{s}</span>' for s in resume.skills)
    
    return template.format(
        lang=resume.language.value,
        name=resume.name,
        location=resume.location,
        email=resume.email,
        linkedin=resume.linkedin,
        phone=resume.phone,
        headline=resume.headline,
        summary=resume.summary,
        experiences_html=exp_html,
        education_html=edu_html,
        skills_html=skills_html
    )


# ============== MAIN PIPELINE ==============

def run_pipeline(
    job_input: str,
    language: str = "pt",
    seniority: str = None,
    output_format: str = "pdf",
    output_name: str = None,
    debug: bool = False,
    text: str = None,
    title: str = None,
    company: str = None
) -> Optional[Path]:
    """
    Executa pipeline completo.
    
    Args:
        job_input: URL, arquivo ou texto da vaga
        language: pt ou en
        seniority: junior, manager, senior, lead
        output_format: pdf, html, md
        output_name: Nome do arquivo de saída
        debug: Modo debug
        text: Texto direto da vaga (alternativa a job_input)
        title: Título da vaga (para input manual)
        company: Empresa (para input manual)
    
    Returns:
        Path do arquivo gerado ou None se falhou
    """
    # Config
    config.debug_mode = debug
    lang = Language.PT if language == "pt" else Language.EN
    out_fmt = OutputFormat[output_format.upper()]
    junior_mode = seniority == "junior" if seniority else False
    
    # Criar args-like object
    class Args:
        pass
    args = Args()
    args.job = job_input
    args.text = text
    args.title = title
    args.company = company
    
    print(f"\n{'='*50}")
    print(f"🚀 ANTIGRAVITY TAILOR")
    print(f"{'='*50}")
    
    # Pipeline
    state = step_input(args)
    state = step_interpret(state)
    state = step_match(state, lang, junior_mode)
    state = step_build(state, lang, junior_mode)
    result = step_render(state, out_fmt, output_name)
    
    if state.has_errors():
        print(f"\n❌ Pipeline falhou:")
        for err in state.errors:
            print(f"   • {err}")
        return None
    
    print(f"\n✅ Pipeline concluído com sucesso!")
    return result


# ============== CLI ==============

def main():
    parser = argparse.ArgumentParser(
        description="Antigravity Tailor - Resume Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python tailor.py https://empresa.com/vaga
  python tailor.py vaga.txt --lang en
  python tailor.py --text "Descrição da vaga..." --title "PM Sênior" --company "Empresa"
  python tailor.py https://vaga.com --seniority junior --debug
        """
    )
    
    parser.add_argument("job", nargs="?", default="", help="URL, arquivo ou texto da vaga")
    parser.add_argument("--text", "-t", help="Texto direto da vaga")
    parser.add_argument("--title", help="Título da vaga (para input manual)")
    parser.add_argument("--company", help="Empresa (para input manual)")
    parser.add_argument("--lang", "-l", default="pt", choices=["pt", "en"], help="Idioma do CV")
    parser.add_argument("--seniority", "-s", choices=["junior", "pleno", "senior", "manager", "lead"], help="Nível de senioridade")
    parser.add_argument("--output", "-o", help="Nome do arquivo de saída")
    parser.add_argument("--format", "-f", default="pdf", choices=["pdf", "html", "md"], help="Formato de saída")
    parser.add_argument("--debug", "-d", action="store_true", help="Modo debug")
    
    args = parser.parse_args()
    
    # Validar input
    if not args.job and not args.text:
        parser.error("Informe uma URL, arquivo ou use --text para texto direto")
    
    # Executar
    result = run_pipeline(
        job_input=args.job,
        language=args.lang,
        seniority=args.seniority,
        output_format=args.format,
        output_name=args.output,
        debug=args.debug,
        text=args.text,
        title=args.title,
        company=args.company
    )
    
    return 0 if result else 1


if __name__ == "__main__":
    sys.exit(main())
