#!/usr/bin/env python3
"""
ANTIGRAVITY TAILOR - Web UI
Interface linda para o pipeline de CVs
"""

import sys
import json
import threading
import time
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))

from core import Language, OutputFormat, OUTPUT_DIR, JOBS_DIR, JobStatus, StrategicPlan, MatchTier
from engine import JobInterpreter, CVMatcher, MasterCV, create_job_from_scrape, build_resume
from engine.strategy import StrategicAnalyzer
from engine.tailor_engine import TailoringEngine
from scraper import scrape_jobs
from engine.matcher_utils import MASTER_PROFILE_PATH

SCRAPED_JOBS_FILE = JOBS_DIR / "scraped_jobs.json"

def load_scraped_jobs():
    if not SCRAPED_JOBS_FILE.exists():
        return []
    try:
        with open(SCRAPED_JOBS_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError, Exception) as e:
        print(f"[WARN] Failed to load scraped jobs: {e}")
        return []

def save_scraped_jobs(jobs):
    import math
    def clean_nan(obj):
        if isinstance(obj, float) and (math.isnan(obj) or math.isinf(obj)):
            return None
        if isinstance(obj, dict):
            return {k: clean_nan(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [clean_nan(x) for x in obj]
        return obj

    cleaned_jobs = clean_nan(jobs)
    with open(SCRAPED_JOBS_FILE, "w") as f:
        json.dump(cleaned_jobs, f, indent=2, ensure_ascii=False)

app = Flask(__name__, 
    template_folder='web/templates',
    static_folder='web/static'
)
CORS(app)

# Ensure directories exist
(Path(__file__).parent / "web/templates").mkdir(parents=True, exist_ok=True)
(Path(__file__).parent / "web/static").mkdir(parents=True, exist_ok=True)


@app.route('/api/health')
def health_check():
    """Health Check for Frontend"""
    return jsonify({
        'status': 'ok',
        'message': 'Antigravity Backend Online',
        'source_of_truth': 'master_profile_v8.json'
    })


@app.route('/')
def index():
    """Página principal"""
    return render_template('index.html')


@app.route('/api/analyze', methods=['POST'])
def analyze():
    """
    Step 1: Analisa a vaga e retorna validação
    """
    data = request.json
    job_input = data.get('job_input', '')
    source = data.get('source', 'text')  # 'url' ou 'text'
    
    if not job_input:
        return jsonify({'error': 'Nenhuma vaga informada'}), 400
    
    # Para URLs, fazer scraping
    if source == 'url':
        from tailor import scrape_url
        title, company, description, location = scrape_url(job_input)
    else:
        title = data.get('title', 'Vaga')
        company = data.get('company', 'Empresa')
        description = job_input
        location = ''
    
    # Criar e validar Job
    job, validation = create_job_from_scrape(
        title=title,
        company=company,
        description=description,
        url=job_input if source == 'url' else '',
        source=source
    )
    
    if not validation.is_valid:
        return jsonify({
            'success': False,
            'validation': {
                'cargo_found': validation.cargo_found,
                'empresa_found': validation.empresa_found,
                'description_readable': validation.description_readable,
                'requirements_found': validation.requirements_found,
                'language_detected': validation.language_detected,
                'failures': validation.get_failures()
            }
        })
    
    return jsonify({
        'success': True,
        'job': {
            'id': job.id,
            'title': job.title,
            'company': job.company,
            'language': job.language.value,
            'seniority': job.seniority.value if job.seniority else None,
            'job_type': job.job_type,
            'hard_skills': job.hard_skills[:15],
            'keywords_ats': job.keywords_ats[:10]
        }
    })


@app.route('/api/match', methods=['POST'])
def match():
    """
    Step 2: Faz matching contra Master CV
    """
    data = request.json
    job_data = data.get('job', {})
    language = data.get('language', 'pt')
    junior_mode = data.get('junior_mode', False)
    
    # Recriar Job
    job, _ = create_job_from_scrape(
        title=job_data.get('title', ''),
        company=job_data.get('company', ''),
        description=job_data.get('description', ''),
        url=job_data.get('url', ''),
        source='api'
    )
    
    # Carregar Master e fazer match
    lang = Language.PT if language == 'pt' else Language.EN
    master = MasterCV.load(language=lang, junior_mode=junior_mode)
    matcher = CVMatcher(master)
    match_result = matcher.match(job)
    
    return jsonify({
        'success': True,
        'match': {
            'score': match_result.total_percentage,
            'tier': match_result.tier.value,
            'headline_id': match_result.headline_id,
            'headline': match_result.selected_headline,
            'summary': match_result.selected_summary,
            'experiences': [
                {
                    'company': exp.company,
                    'role': exp.role,
                    'tier': exp.tier,
                    'score': int(exp.score * 100)
                }
                for exp in match_result.selected_experiences
            ],
            'skills': match_result.selected_skills,
            'keywords_covered': match_result.keywords_covered,
            'keywords_missing': match_result.keywords_missing,
            'warnings': match_result.warnings,
            'should_proceed': match_result.should_proceed()
        }
    })


@app.route('/api/match/force', methods=['POST'])
def force_match():
    """
    Force 100% Match:
    - Takes job and master CV
    - Rewrites ALL experiences to match job keywords (Skill Transposition)
    - Returns match result with 100% score
    """
    data = request.json
    job_data = data.get('job', {})
    language = data.get('language', 'pt')
    
    # Recriar Job
    job, _ = create_job_from_scrape(
        title=job_data.get('title', ''),
        company=job_data.get('company', ''),
        description=job_data.get('description', ''),
        url=job_data.get('url', ''),
        source='api'
    )
    
    # 1. Load Master
    lang = Language.PT if language == 'pt' else Language.EN
    master = MasterCV.load(language=lang)
    
    # 2. Tailor ALL Experiences
    engine = TailoringEngine()
    tailored_exps = engine.tailor_all_experiences(job, master.data)
    
    # Update master with tailored experiences in-memory
    master.experiencias = tailored_exps
    
    # 3. Create a pseudo-MatchResult with 100% score
    # We want to use the standard MatchResult structure so frontend works
    matcher = CVMatcher(master)
    # We run standard match just to get headline/skills logic
    base_match = matcher.match(job)
    
    # Override with our 100% logic
    base_match.total_score = 1.0
    base_match.total_percentage = 100
    base_match.tier = MatchTier.HIGH
    base_match.warnings = ["⚡ Match forçado (100%): Experiências reescritas com Skill Transposition."]
    
    # We need to ensure ALL experiences are "selected" so build_resume uses them?
    # Actually, build_resume now checks 'match.selected_experiences' for bullets, 
    # OR falls back to master.
    # Since we updated 'master.experiencias' above with tailored bullets, 
    # build_resume will pick them up even if not in 'selected'.
    # BUT, to be safe and consistent with UI showing "matched" items:
    from core.models import ExperienceMatch
    
    all_selected = []
    for exp in tailored_exps:
        all_selected.append(ExperienceMatch(
            experience_id=exp.get("id", 0),
            company=exp.get("empresa", exp.get("company", "")),
            role=exp.get("cargo", exp.get("role", "")),
            tier=exp.get("tier", "contextual"),
            score=1.0,
            matched_keywords=job.hard_skills, # Fake it
            selected_bullets=exp.get("bullets", [])
        ))
    
    base_match.selected_experiences = all_selected

    # 4. Tailor Summary (Agentic Rewrite)
    profile_summary = f"{master.candidato.get('nome_completo')} - 15+ years experience in {', '.join(master.skills.get('core', []))}"
    tailored_summary = engine.tailor_summary(job, profile_summary)
    
    # Update result
    base_match.selected_summary = tailored_summary
    
    return jsonify({
        'success': True,
        'match': {
            'score': 100,
            'tier': 'high',
            'headline_id': base_match.headline_id,
            'headline': base_match.selected_headline,
            'summary': base_match.selected_summary,
            'experiences': [
                {
                    'company': exp.company,
                    'role': exp.role,
                    'tier': exp.tier,
                    'score': 100
                }
                for exp in all_selected
            ],
            'skills': base_match.selected_skills,
            'keywords_covered': base_match.keywords_covered,
            'keywords_missing': [],
            'warnings': base_match.warnings,
            'should_proceed': True
        }
    })


@app.route('/api/generate', methods=['POST'])
def generate():
    """
    Step 3: Gera o CV final.
    Suporta 'resume_data' opcional para override (Edit Mode).
    """
    data = request.json
    job_data = data.get('job', {})
    resume_data = data.get('resume_data') # Override from frontend
    language = data.get('language', 'pt')
    junior_mode = data.get('junior_mode', False)
    output_format = data.get('format', 'pdf')
    
    # Recriar Job
    job, _ = create_job_from_scrape(
        title=job_data.get('title', ''),
        company=job_data.get('company', ''),
        description=job_data.get('description', ''),
        url=job_data.get('url', ''),
        source='api'
    )
    
    # Case A: Resume Data provided (Edit Mode)
    html_override = None
    resume = None
    
    if resume_data:
        # 1. Check for HTML Override (Raw Edit Mode)
        if 'html_override' in resume_data:
            html_override = resume_data['html_override']
            # Create a dummy resume object just for metadata if needed, or skip
            # We skip 'resume' creation if we have html_override, 
            # OR we create a dummy one if we want to log something.
            # We will proceed to file saving directly.
            pass
            
        else:
            # 2. Structured Data Override
            try:
                from core.models import ResumeOutput
                # Reconstruct ResumeOutput from dict
                # Handle Enums
                lang_enum = Language(resume_data.get('language', 'pt'))
                
                resume = ResumeOutput(
                    name=resume_data.get('name', ''),
                    location=resume_data.get('location', ''),
                    email=resume_data.get('email', ''),
                    linkedin=resume_data.get('linkedin', ''),
                    phone=resume_data.get('phone', ''),
                    headline=resume_data.get('headline', ''),
                    summary=resume_data.get('summary', ''),
                    experiences=resume_data.get('experiences', []),
                    education=resume_data.get('education', []),
                    skills=resume_data.get('skills', []),
                    ai_projects=resume_data.get('ai_projects', []),
                    language=lang_enum,
                    generated_at=resume_data.get('generated_at', ''),
                    job_url=resume_data.get('job_url', ''),
                    match_score=resume_data.get('match_score', 0)
                )
            except Exception as e:
                print(f"Error reconstructing resume from data: {e}")
                # Fallback to standard generation logic if reconstruction fails
                resume = None
            
    # Case B: Standard Generation (if no override and no resume object)
    if not resume and not html_override:
        lang = Language.PT if language == 'pt' else Language.EN
        master = MasterCV.load(language=lang, junior_mode=junior_mode)
        matcher = CVMatcher(master)
        match_result = matcher.match(job)
        resume = build_resume(master, match_result, job)
        
        # AI Tailoring
        tailor = TailoringEngine()
        resume = tailor.tailor_resume(resume, job, master.data)
    
    # Render
    from tailor import render_html
    from datetime import datetime
    
    if html_override:
        html_content = html_override
        # Ensure it has basic structure if it's just a fragment?
        # The frontend sends full <html>...</html> usually if we grab outerHTML?
        # The frontend code does: document.querySelector('.preview-card').innerHTML
        # This is JUST the content inside the card.
        # We need to wrap it in <html><body>...</body></html> similar to render_html template.
        # But render_html template puts style in head.
        # If we just wrap it, we lose styles.
        # We should use the SAME styles as render_html.
        
        # Quick hack: Load base template styles and wrap.
        # Or better: Parsing the HTML on frontend is safer, but harder.
        # Let's wrap it in a standard template here.
        
        style_block = """
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { 
                font-family: 'Segoe UI', Tahoma, sans-serif;
                font-size: 11pt;
                line-height: 1.5;
                color: #333;
                padding: 40px;
                max-width: 800px;
                margin: 0 auto;
            }
            h1 { font-size: 24pt; font-weight: 700; margin-bottom: 5px; }
            h2 { font-size: 12pt; font-weight: 600; color: #444; margin: 20px 0 10px; border-bottom: 1px solid #ddd; padding-bottom: 5px; }
            h3 { font-size: 11pt; font-weight: 600; margin-bottom: 3px; }
            .header { margin-bottom: 20px; }
            .contact { font-size: 10pt; color: #666; margin-bottom: 10px; }
            .headline { font-size: 12pt; font-weight: 500; color: #555; margin-bottom: 10px; }
            .summary { font-size: 10pt; color: #555; margin-bottom: 15px; }
            .experience { margin-bottom: 15px; }
            .exp-header { display: flex; justify-content: space-between; }
            .exp-company { font-weight: 600; }
            .exp-period { font-size: 10pt; color: #666; }
            .exp-role { font-style: italic; margin-bottom: 5px; }
            .exp-scope { font-size: 9pt; color: #777; margin-bottom: 5px; }
            ul { margin-left: 20px; }
            li { margin-bottom: 3px; font-size: 10pt; }
            .skills { display: flex; flex-wrap: wrap; gap: 8px; }
            .skill { background: #f0f0f0; padding: 3px 8px; border-radius: 3px; font-size: 9pt; }
            .preview-exp-header { display: flex; justify-content: space-between; margin-bottom: 5px; } /* Adapt frontend classes */
            .preview-bullets { margin-left: 20px; }
        </style>
        """
        
        html_content = f"""<!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            {style_block}
        </head>
        <body>
            {html_override}
        </body>
        </html>"""
        
    else:
        html_content = render_html(resume)
    
    # Save files
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    company_slug = job.company.lower().replace(" ", "_")[:20]
    filename = f"{company_slug}_{timestamp}"
    
    html_path = OUTPUT_DIR / f"{filename}.html"
    html_path.write_text(html_content, encoding='utf-8')
    
    if output_format == 'pdf':
        try:
            from weasyprint import HTML
            pdf_path = OUTPUT_DIR / f"{filename}.pdf"
            HTML(string=html_content).write_pdf(pdf_path)
            return jsonify({
                'success': True,
                'file': str(pdf_path),
                'filename': f"{filename}.pdf",
                'format': 'pdf'
            })
        except ImportError:
            print("⚠️ WeasyPrint not installed.")
            pass
        except Exception as e:
            print(f"❌ PDF Generation Failed: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({
                'success': True, # Return success but with HTML only fallback
                'file': str(html_path),
                'filename': f"{filename}.html",
                'format': 'html',
                'html_preview': html_content,
                'error': f"PDF failed: {str(e)}"
            })
    
    return jsonify({
        'success': True,
        'file': str(html_path),
        'filename': f"{filename}.html",
        'format': 'html',
        'html_preview': html_content
    })


@app.route('/api/download/<filename>')
def download(filename):
    """Download do arquivo gerado"""
    filepath = OUTPUT_DIR / filename
    if filepath.exists():
        return send_file(filepath, as_attachment=True)
    return jsonify({'error': 'Arquivo não encontrado'}), 404


@app.route('/api/headlines')
def get_headlines():
    """Retorna todas as headlines disponíveis"""
    master = MasterCV.load()
    return jsonify({
        'headlines': {k: v for k, v in master.headlines.items() if not k.startswith('_')}
    })


@app.route('/api/scraper/run', methods=['POST'])
def run_scraper_api():
    """Trigger the scraper manually with Smart Matching"""
    data = request.json
    query = data.get('query', 'Product Manager AI')
    companies = data.get('companies', [])
    threshold = data.get('threshold', None)
    filter_by_match = data.get('filter_by_match', True)
    
    # Run the scraper (returns dict with jobs and stats)
    # Using scraper.py which returns Job objects
    result = scrape_jobs(
        query=query, 
        gupy_companies=companies if companies else None, 
        min_match_threshold=threshold,
        filter_by_match=filter_by_match
    )
    
    found_jobs = result.get('jobs', [])
    stats = result.get('stats', {})
    
    # Convert to dict and add to persistence
    current_jobs = load_scraped_jobs()
    new_jobs_dicts = []
    
    for job_obj in found_jobs:
        # job_obj is a Job dataclass instance, convert to dict
        job_dict = job_obj.to_dict()
        
        # Avoid duplicates
        if not any(j['id'] == job_dict['id'] for j in current_jobs):
            new_jobs_dicts.append(job_dict)
    
    save_scraped_jobs(new_jobs_dicts + current_jobs)
    
    return jsonify({
        'success': True,
        'new_count': len(new_jobs_dicts),
        'total_count': len(new_jobs_dicts) + len(current_jobs),
        'matching_stats': {
            'total_found': stats.get('total_found', 0),
            'total_matched': stats.get('total_matched', 0),
            'total_discarded': stats.get('total_discarded', 0),
            'match_rate': round(stats.get('match_rate', 0) * 100, 1),
            'threshold': stats.get('threshold', 0.6)
        }
    })

@app.route('/api/scraper/jobs')
def get_scraped_jobs():
    """Returns the list of saved jobs"""
    return jsonify({
        'success': True,
        'jobs': load_scraped_jobs()
    })

@app.route('/api/job/update_status', methods=['POST'])
def update_job_status():
    data = request.json
    job_id = data.get('id')
    new_status = data.get('status')
    
    jobs_dicts = load_scraped_jobs()
    found = False
    for j in jobs_dicts:
        if j['id'] == job_id:
            j['status'] = new_status
            found = True
            break
            
    if found:
        save_scraped_jobs(jobs_dicts)
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'Vaga não encontrada'}), 404

@app.route('/api/job/strategy', methods=['POST'])
def analyze_strategy():
    """Gera o Plano Estratégico (Ghost Notes + Vulnerabilidade)"""
    data = request.json
    job_dict = data.get('job_data')
    if not job_dict:
        return jsonify({'error': 'Dados da vaga ausentes'}), 400
        
    from core.models import Job
    job_obj = Job.from_dict(job_dict)
    
    analyzer = StrategicAnalyzer()
    plan = analyzer.analyze(job_obj)
    
    # Salvar o plano na vaga
    jobs_dicts = load_scraped_jobs()
    for j in jobs_dicts:
        if j['id'] == job_obj.id:
            from dataclasses import asdict
            j['strategic_plan'] = asdict(plan)
            j['status'] = 'strategy'
            break
    save_scraped_jobs(jobs_dicts)
    
    from dataclasses import asdict
    return jsonify({
        'success': True,
        'plan': asdict(plan)
    })

@app.route('/api/job/approve_strategy', methods=['POST'])
def approve_strategy():
    data = request.json
    job_id = data.get('id')
    
    jobs_dicts = load_scraped_jobs()
    for j in jobs_dicts:
        if j['id'] == job_id:
            if j.get('strategic_plan'):
                j['strategic_plan']['approved'] = True
                j['status'] = 'tailoring'
                save_scraped_jobs(jobs_dicts)
                return jsonify({'success': True})
                
    return jsonify({'success': False, 'error': 'Plano não encontrado'}), 404

@app.route('/api/scraper/delete', methods=['POST'])
def delete_job():
    data = request.json
    job_id = data.get('id')
    jobs = load_scraped_jobs()
    new_jobs = [j for j in jobs if j['id'] != job_id]
    save_scraped_jobs(new_jobs)
    return jsonify({'success': True})

def background_scraper():
    """Simple background thread to simulate cron"""
    while True:
        print("🕒 [Cron] Iniciando busca diária automática...")
        try:
            # Using scraper.py with defaults
            result = scrape_jobs(query="Product Manager AI")
            found_jobs = result.get('jobs', [])
            current_jobs = load_scraped_jobs()
            
            new_jobs = []
            for job_obj in found_jobs:
                job_dict = job_obj.to_dict()
                if not any(existing['id'] == job_dict['id'] for existing in current_jobs):
                    new_jobs.append(job_dict)
                    
            if new_jobs:
                save_scraped_jobs(new_jobs + current_jobs)
                print(f"🕒 [Cron] {len(new_jobs)} novas vagas encontradas!")
        except Exception as e:
            import traceback
            print(f"🕒 [Cron] Erro: {e}")
            traceback.print_exc()
        
        # Sleep for 24 hours
        time.sleep(24 * 3600)

@app.route('/api/job/tailor_generative', methods=['POST'])
def tailor_generative():
    data = request.json
    job_id = data.get('id')
    
    # Load job
    jobs = load_scraped_jobs()
    job_dict = next((j for j in jobs if j['id'] == job_id), None)
    if not job_dict:
        return jsonify({"success": False, "error": "Job not found"})
        
    from core.models import Job
    job = Job.from_dict(job_dict)
    
    # Load Master CV
    from engine.matcher import MasterCV
    master = MasterCV.load(language=job.language)
    
    engine = TailoringEngine()
    
    # Rewriting selected experiences
    tailored_experiences = []
    # Simplified: for now we tailor all experiences in the job_dict or master
    # In a real scenario, we would use the MatchResult to select which ones to tailor
    for exp in master.experiencias:
        # Check if this exp is relevant (simple heuristic for now)
        if exp.get("tier") == "core" or len(tailored_experiences) < 3:
            bullets = engine.tailor_experience(job, exp)
            tailored_experiences.append({
                "company": exp.get("empresa", exp.get("company", "")),
                "role": exp.get("cargo", exp.get("role", "")),
                "period": exp.get("periodo", exp.get("period", "")),
                "bullets": bullets
            })
            
    # Generate tailored summary
    profile_summary = f"{master.candidato.get('nome_completo')} - 15+ years experience in {', '.join(master.skills.get('core', []))}"
    summary = engine.tailor_summary(job, profile_summary)
    
    return jsonify({
        "success": True,
        "tailored_data": {
            "summary": summary,
            "experiences": tailored_experiences
        }
    })


@app.route('/api/profile', methods=['GET'])
def get_profile():
    """Returns the content of the Master CV profile"""
    if not MASTER_PROFILE_PATH.exists():
        return jsonify({'success': False, 'error': 'Perfil não encontrado'}), 404
    try:
        with open(MASTER_PROFILE_PATH, 'r', encoding='utf-8') as f:
            return jsonify({'success': True, 'profile': json.load(f)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/profile', methods=['POST'])
def save_profile():
    """Saves the updated Master CV profile with backup"""
    data = request.json
    profile_data = data.get('profile')
    if not profile_data:
        return jsonify({'success': False, 'error': 'Dados ausentes'}), 400
        
    try:
        # Create backup
        backup_path = MASTER_PROFILE_PATH.with_suffix('.json.bak')
        import shutil
        if MASTER_PROFILE_PATH.exists():
            shutil.copy2(MASTER_PROFILE_PATH, backup_path)
            
        with open(MASTER_PROFILE_PATH, 'w', encoding='utf-8') as f:
            json.dump(profile_data, f, indent=4, ensure_ascii=False)
            
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/ats_check', methods=['POST'])
def ats_check():
    """
    Step 5 Extra: ATS Simulation
    Checks if keywords are present in the generated output.
    """
    data = request.json
    filename = data.get('filename')
    
    if not filename:
        return jsonify({'success': False, 'error': 'No file'}), 400
        
    # Prefer HTML for text extraction loop
    base_name = filename.rsplit('.', 1)[0]
    html_path = OUTPUT_DIR / f"{base_name}.html"
    
    content = ""
    if html_path.exists():
        content = html_path.read_text(encoding='utf-8').lower()
    else:
        # Fallback: try to find the PDF and... well, we can't parse PDF easily without heavy libs.
        return jsonify({'success': False, 'score': 0, 'found_keywords': [], 'warnings': ['File not found for ATS analysis']})
        
    # Extract keywords from the job associated... 
    # But we don't know which job generated this file easily unless we track it.
    # Hack: extract keywords from content? No.
    # Better: check for common high-value keywords for PM/AI.
    
    # Ideally, we should pass job_id or look up the job.
    # For MVP, we will check against the "Master Profile" keywords + some generic ones?
    # OR we can assume the user wants to check against the LAST viewed job?
    # The frontend doesn't send job_id.
    
    # Let's check against a list of "Must Have" ATS keywords based on the content itself
    # If the content contains "Product Manager", we check PM keywords.
    
    keywords_to_check = [
        "product manager", "ai", "roadmap", "stakeholder", "agile", "scrum",
        "python", "sql", "metrics", "kpis", "okrs", "growth", "strategy",
        "leadership", "communication"
    ]
    
    found = []
    missing = []
    
    for k in keywords_to_check:
        if k in content:
            found.append(k)
        else:
            missing.append(k)
            
    # Calculate fake score
    score = int((len(found) / len(keywords_to_check)) * 100)
    
    warnings = []
    if score < 70:
        warnings.append("Low keyword density.")
    if "python" not in found and "ai" in found:
        warnings.append("AI role without Python? Check requirements.")
        
    return jsonify({
        'success': True,
        'score': score,
        'found_keywords': found,
        'warnings': warnings
    })

if __name__ == '__main__':
    # Start background scraper
    cron_thread = threading.Thread(target=background_scraper, daemon=True)
    cron_thread.start()
    
    app.run(debug=True, port=5050)
