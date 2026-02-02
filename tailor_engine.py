#!/usr/bin/env python3
"""
TAYLOR-MADE RESUME ENGINE v2.0
Motor de Transformação Semântica

NÃO é um gerador genérico. É um sistema de POSICIONAMENTO ESTRATÉGICO:
- Detecta DOR LATENTE da vaga
- Aplica NARRATIVE SHIFT baseado no contexto
- Neutraliza OVERQUALIFIED traduindo para execução
- Gera MENSAGEM DE NETWORKING personalizada

Posicionamento: "Arquiteto de Crescimento" (menos slide, mais código e margem)
"""

import re
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field

# --- SETUP ---
def setup_env():
    import subprocess, sys
    for pkg in ["jinja2", "weasyprint"]:
        try: __import__(pkg)
        except: subprocess.check_call([sys.executable, "-m", "pip", "install", pkg, "-q"])
setup_env()

from jinja2 import Template, Environment
try:
    from weasyprint import HTML
    HAS_WEASYPRINT = True
except:
    HAS_WEASYPRINT = False

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)


# ============================================================================
# MASTER CONTEXT - O que o mercado precisa ver
# ============================================================================

MASTER_CONTEXT = {
    "nome": "Thiago Ferreira Moraes",
    "email": "thiago@email.com",
    "linkedin": "linkedin.com/in/thiagomkt",
    "location": "São Paulo, Brazil",
    
    # POSICIONAMENTO ESTRATÉGICO
    "positioning": {
        "role": "Arquiteto de Crescimento",
        "mindset": "Hands-on executioner who organizes chaos",
        "differentiator": "Onde a marca vira performance. IA + Automação + P/L",
        "target_salary": "15k-25k CLT"
    },
    
    # NARRATIVA POR CONTEXTO (Narrative Shift)
    "narrative_shifts": {
        "lead_manager": {
            "hide_titles": ["Partner Marketing Lead", "Senior Marketing Manager"],
            "show_as": "Growth & Automation Specialist",
            "focus": "execução técnica"
        },
        "specialist_analyst": {
            "hide_titles": ["Partner Marketing Lead"],
            "show_as": "MarTech Specialist",
            "focus": "hands-on delivery"
        },
        "product_ai": {
            "hide_titles": [],
            "show_as": "AI Product Lead",
            "focus": "product development + LLM"
        }
    },
    
    # TRADUÇÃO OVERQUALIFIED -> EXECUTOR
    "term_translations": {
        # Termos abstratos -> Termos de execução
        "Liderança de times": "Coordenação de squads multidisciplinares",
        "Visão Estratégica": "Arquitetura de dados e automações",
        "Gestão Executiva": "Gestão de P/L e margem operacional",
        "Transformação Digital": "Automação de processos com n8n/Python",
        "Inovação": "Implementação de IA generativa em produção",
        "Direcionamento Estratégico": "Otimização de CAC/LTV com dados",
        "Desenvolvimento de Negócios": "Geração de pipeline via automação de SDR",
        "Stakeholder Management": "Interface técnica com áreas de negócio"
    },
    
    # EXPERIÊNCIAS COM CONTEXTO SEMÂNTICO
    "experiences": [
        {
            "id": "lorinz",
            "empresa": "Lorinz Consulting",
            "cargo_original": "AI & Automation Lead",
            "cargo_executor": "Growth & Automation Specialist",
            "periodo": "Dez 2022 – Presente",
            "duracao": "2+ anos",
            "tipo": "own_business",
            "semantic_context": {
                "prova_de": ["automação", "margem", "p/l", "hands-on", "ia"],
                "keyword_meta": "Gestão de P/L e sobrevivência",
                "keyword_display": "Margem de Contribuição • Automação Low-cost"
            },
            "bullets_modelo_cam": [  # CONTEXTO -> ALAVANCA -> MÉTRICA
                {
                    "contexto": "E-commerce com 40% de abandono de carrinho e atendimento manual",
                    "alavanca": "Arquitetei workflows de IA agentic com n8n, Docker e PostgreSQL",
                    "metrica": "80% automação, 15% recuperação de carrinhos, 98% precisão",
                    "tags": ["agentic_ai", "n8n", "docker", "automação"]
                },
                {
                    "contexto": "Marketing produzindo conteúdo manualmente, semanas por campanha",
                    "alavanca": "Implementei pipeline de IA local: ComfyUI + Ollama + Eleven Labs",
                    "metrica": "40% menos tempo, 3x mais campanhas/mês",
                    "tags": ["prompt_engineering", "ai_content", "produtividade"]
                },
                {
                    "contexto": "Dados de vendas e marketing em silos, sem visão unificada",
                    "alavanca": "Construí stack RevOps conectando CRM, ads e analytics",
                    "metrica": "25% aumento de receita, 20% redução de CAC",
                    "tags": ["revops", "sql", "data", "cac"]
                },
                {
                    "contexto": "1000+ stakeholders precisando de treinamento em novas ferramentas",
                    "alavanca": "Criei programa de certificação com currículo estruturado",
                    "metrica": "95% satisfação, 80% adoção em 3 meses",
                    "tags": ["enablement", "scale", "training"]
                }
            ],
            "stack": "n8n • Docker • PostgreSQL • Python • SQL • LangChain • OpenAI API"
        },
        {
            "id": "meta",
            "empresa": "Meta (Facebook)",
            "cargo_original": "Partner Marketing Lead",
            "cargo_executor": "Growth Strategy Specialist",
            "periodo": "Dez 2021 – Dez 2022",
            "duracao": "1 ano",
            "tipo": "bigtech",
            "semantic_context": {
                "prova_de": ["escala", "dados", "incrementalidade", "stakeholders"],
                "keyword_meta": "Escala com IA e Dados",
                "keyword_display": "Incrementalidade • Atribuição • GTM"
            },
            "bullets_modelo_cam": [
                {
                    "contexto": "Partners não aproveitando Discovery Commerce, receita na mesa",
                    "alavanca": "Desenhei GTM cross-continental com case studies e enablement",
                    "metrica": "US$85M impacto via campanhas partner-driven",
                    "tags": ["gtm", "revenue", "latam", "scale"]
                },
                {
                    "contexto": "Agências sem path claro para usar produtos Meta",
                    "alavanca": "Criei Canva Creative Journey e Commerce Performance Series",
                    "metrica": "50%+ da receita partner-driven na região",
                    "tags": ["product", "enablement", "certification"]
                },
                {
                    "contexto": "C-level precisando de visibilidade do ecossistema de partners",
                    "alavanca": "Montei dashboards e apresentei QBRs executivos",
                    "metrica": "Investimento adicional aprovado para programas",
                    "tags": ["c-level", "stakeholders", "data"]
                }
            ],
            "stack": "Meta Ads • Data Analytics • Cross-functional Coordination"
        },
        {
            "id": "telium",
            "empresa": "Telium Networks",
            "cargo_original": "Senior Marketing Manager",
            "cargo_executor": "Growth Lead (Report to CEO)",
            "periodo": "Nov 2020 – Dez 2021",
            "duracao": "1 ano 2 meses",
            "tipo": "startup_b2b",
            "semantic_context": {
                "prova_de": ["growth", "rebranding", "automação", "conversão"],
                "keyword_meta": "Eficiência Operacional",
                "keyword_display": "Growth Hacking • MQL Automation"
            },
            "bullets_modelo_cam": [
                {
                    "contexto": "Crescimento estagnado em 20% YoY",
                    "alavanca": "Liderei rebrand (AllWaysON) + automação de marketing",
                    "metrica": "Crescimento acelerou de 20% para 30% YoY",
                    "tags": ["growth", "branding", "automation"]
                },
                {
                    "contexto": "Sales lutando com qualidade de leads",
                    "alavanca": "Implementei lead scoring e qualificação automatizada",
                    "metrica": "+25% conversão, -20% ciclo de vendas",
                    "tags": ["sales_enablement", "conversion", "automation"]
                }
            ],
            "stack": "Marketing Automation • CRM • B2B Growth"
        },
        {
            "id": "ambev",
            "empresa": "Ambev (ABInBev)",
            "cargo_original": "Internal Communications Specialist",
            "cargo_executor": "Campaign Lead (LATAM Scope)",
            "periodo": "Jun 2018 – Nov 2019",
            "duracao": "1 ano 6 meses",
            "tipo": "multinational",
            "semantic_context": {
                "prova_de": ["campanhas", "escala", "influenciadores", "viral"],
                "keyword_meta": "Processos e Eficiência",
                "keyword_display": "Gestão de Stakeholders • Orçamento"
            },
            "bullets_modelo_cam": [
                {
                    "contexto": "Campanha anual de responsabilidade precisando de breakthrough",
                    "alavanca": "Liderei 'Dia de Responsa' com Anitta e Wesley Safadão",
                    "metrica": "Trending Twitter, elogio CEO global, 10M+ impressões",
                    "tags": ["campaign", "influencer", "viral", "scale"]
                },
                {
                    "contexto": "Comunicação interna fragmentada no Workplace",
                    "alavanca": "Unifiquei storytelling e treinei times regionais",
                    "metrica": "+50% engajamento de funcionários",
                    "tags": ["internal_comms", "engagement", "training"]
                }
            ],
            "stack": "Workplace • Social Media • Agency Management"
        },
        {
            "id": "dow",
            "empresa": "Dow Chemical",
            "cargo_original": "Senior Marketing Specialist",
            "cargo_executor": "Demand Gen Specialist (B2B)",
            "periodo": "2017 – 2019",
            "duracao": "2 anos",
            "tipo": "multinational",
            "semantic_context": {
                "prova_de": ["b2b", "pipeline", "conteúdo técnico", "demanda"],
                "keyword_meta": "Processos e Eficiência",
                "keyword_display": "Pipeline B2B • Lead Nurturing"
            },
            "bullets_modelo_cam": [
                {
                    "contexto": "Divisão industrial sem pipeline de marketing",
                    "alavanca": "Construí estratégia de content marketing B2B",
                    "metrica": "US$5M pipeline, +30% MQLs",
                    "tags": ["b2b", "content", "pipeline", "demand_gen"]
                }
            ],
            "stack": "Content Marketing • Marketing Automation • Technical Writing"
        },
        {
            "id": "suzano",
            "empresa": "Suzano",
            "cargo_original": "Marketing Coordinator",
            "cargo_executor": "M&A Brand Integration Lead",
            "periodo": "2015 – 2017",
            "duracao": "2 anos",
            "tipo": "multinational",
            "semantic_context": {
                "prova_de": ["rebranding", "m&a", "change_management"],
                "keyword_meta": "Processos e Eficiência",
                "keyword_display": "M&A Integration • Change Management"
            },
            "bullets_modelo_cam": [
                {
                    "contexto": "Pós-fusão com duas identidades de marca conflitantes",
                    "alavanca": "Liderei rebranding e integração cultural",
                    "metrica": "+25% brand recall, integração bem-sucedida",
                    "tags": ["rebranding", "m&a", "change"]
                }
            ],
            "stack": "Brand Strategy • M&A Communications"
        },
        {
            "id": "fastshop",
            "empresa": "Fast Shop",
            "cargo_original": "Trade Marketing Analyst",
            "cargo_executor": "Retail Analytics Specialist",
            "periodo": "2013 – 2015",
            "duracao": "2 anos",
            "tipo": "retail",
            "semantic_context": {
                "prova_de": ["varejo", "analytics", "promoções", "roi"],
                "keyword_meta": "Gestão de P/L",
                "keyword_display": "Trade Analytics • Promotional ROI"
            },
            "bullets_modelo_cam": [
                {
                    "contexto": "Campanhas promocionais sem otimização, ROI inconsistente",
                    "alavanca": "Construí framework de analytics e modelos preditivos",
                    "metrica": "+18% vendas promocionais, 15% otimização de spend",
                    "tags": ["analytics", "retail", "roi", "data"]
                }
            ],
            "stack": "Analytics • Trade Marketing • Data Analysis"
        }
    ],
    
    # PROJETOS AI (prova de hands-on técnico)
    "ai_projects": [
        {
            "nome": "E-commerce Agentic Workflow",
            "problema": "Abandono de carrinho + atendimento manual",
            "solucao": "Agentes autônomos para recuperação e triage",
            "resultado": "98% precisão, 80% automação, 15% recovery",
            "stack": "n8n • Docker • PostgreSQL • WAHA Bot"
        },
        {
            "nome": "RAG Product Assistant",
            "problema": "SAC sobrecarregado com dúvidas de produto",
            "solucao": "Chatbot WhatsApp com RAG e embeddings",
            "resultado": "70% mais rápido, 85% resolução first-contact",
            "stack": "Python • LangChain • ChromaDB • OpenAI"
        },
        {
            "nome": "Local AI Content Pipeline",
            "problema": "Produção de conteúdo manual e lenta",
            "solucao": "Pipeline end-to-end com LLMs locais",
            "resultado": "40% mais rápido, 3x output",
            "stack": "ComfyUI • Ollama • Eleven Labs • n8n"
        },
        {
            "nome": "RevOps Automation Stack",
            "problema": "Dados de vendas/marketing em silos",
            "solucao": "Pipeline unificado CRM-Ads-Analytics",
            "resultado": "25% receita, -20% CAC",
            "stack": "n8n • GoHighLevel • SQL"
        }
    ],
    
    # FORMAÇÃO
    "education": [
        {"program": "MSc Communications", "institution": "USP", "year": "2024–Present", "focus": "Psicologia Analítica"},
        {"program": "MBA Marketing Director", "institution": "NEXT MBA", "year": "2024", "focus": "Philip Kotler"},
        {"program": "Neuroscience Spec.", "institution": "Mackenzie", "year": "2018–2020", "focus": "Neuromarketing"},
        {"program": "BA Marketing", "institution": "ESPM", "year": "2007–2011", "focus": "Research Assistant"}
    ],
    
    "languages": ["Português (Nativo)", "English (Fluent - IELTS)", "Español (Avanzado)"]
}


# ============================================================================
# DOR LATENTE DETECTOR
# ============================================================================

@dataclass
class PainPoint:
    """Dor latente identificada na vaga"""
    category: str  # cac, automation, branding, scale, margem
    keywords: List[str]
    solution_tags: List[str]
    messaging_hook: str

PAIN_POINT_PATTERNS = {
    "cac_alto": PainPoint(
        category="cac",
        keywords=["cac", "custo de aquisição", "roi", "roas", "otimização", "performance"],
        solution_tags=["cac", "data", "automation", "revops"],
        messaging_hook="redução de CAC via automação e dados"
    ),
    "falta_automacao": PainPoint(
        category="automation",
        keywords=["automação", "automatizar", "processos", "eficiência", "escala", "manual"],
        solution_tags=["automation", "n8n", "pipeline", "workflow"],
        messaging_hook="automação de processos que antes levavam semanas"
    ),
    "branding_nao_converte": PainPoint(
        category="branding",
        keywords=["marca", "branding", "posicionamento", "awareness", "conversão", "performance"],
        solution_tags=["branding", "growth", "gtm", "conversion"],
        messaging_hook="conexão entre branding e conversão mensurável"
    ),
    "escala": PainPoint(
        category="scale",
        keywords=["escala", "scale", "crescimento", "growth", "expansão", "latam"],
        solution_tags=["scale", "latam", "gtm", "enablement"],
        messaging_hook="operações em escala LATAM com eficiência"
    ),
    "dados_silos": PainPoint(
        category="data",
        keywords=["dados", "data", "analytics", "bi", "dashboard", "métricas", "kpi"],
        solution_tags=["data", "analytics", "sql", "pipeline"],
        messaging_hook="unificação de dados fragmentados para decisões ágeis"
    ),
    "ia_generativa": PainPoint(
        category="ai",
        keywords=["ai", "ia", "llm", "generativa", "machine learning", "ml", "chatbot", "agente"],
        solution_tags=["agentic_ai", "prompt_engineering", "ai_content", "automation"],
        messaging_hook="implementação de IA generativa em produção"
    ),
    "margem": PainPoint(
        category="margin",
        keywords=["margem", "p/l", "pl", "custo", "cmv", "lucratividade", "rentabilidade"],
        solution_tags=["roi", "cac", "revops", "automation"],
        messaging_hook="otimização de margem via automação low-cost"
    )
}


def detect_pain_points(job_description: str) -> List[PainPoint]:
    """Detecta dores latentes no job description"""
    jd_lower = job_description.lower()
    detected = []
    
    for name, pain in PAIN_POINT_PATTERNS.items():
        score = sum(1 for kw in pain.keywords if kw in jd_lower)
        if score >= 1:
            detected.append((pain, score))
    
    # Ordena por score e retorna top 3
    detected.sort(key=lambda x: x[1], reverse=True)
    return [p[0] for p in detected[:3]]


# ============================================================================
# NARRATIVE SHIFT ENGINE
# ============================================================================

def determine_narrative_shift(job_description: str) -> str:
    """Determina qual narrativa usar baseado na vaga"""
    jd_lower = job_description.lower()
    
    # Detecta nível/tipo da vaga
    if any(kw in jd_lower for kw in ["gpm", "product manager", "product lead", "ai product"]):
        return "product_ai"
    elif any(kw in jd_lower for kw in ["lead", "manager", "coordenador", "head"]):
        return "lead_manager"
    else:
        return "specialist_analyst"


def apply_narrative_shift(exp: Dict, shift_type: str) -> Dict:
    """Aplica transformação de narrativa na experiência"""
    shift = MASTER_CONTEXT["narrative_shifts"].get(shift_type, {})
    
    # Cria cópia para não mutar original
    transformed = exp.copy()
    
    # Se cargo original deve ser escondido, usa o executor
    if exp.get("cargo_original") in shift.get("hide_titles", []):
        transformed["cargo_display"] = exp.get("cargo_executor", exp["cargo_original"])
    else:
        transformed["cargo_display"] = exp.get("cargo_original")
    
    return transformed


# ============================================================================
# BULLET FORMATTER (CONTEXTO -> ALAVANCA -> MÉTRICA)
# ============================================================================

def format_cam_bullet(bullet: Dict, highlight_tags: List[str] = None) -> str:
    """Formata bullet no modelo CAM com highlighting"""
    contexto = bullet.get("contexto", "")
    alavanca = bullet.get("alavanca", "")
    metrica = bullet.get("metrica", "")
    
    # Destaca métricas
    metrica_highlighted = re.sub(
        r'(\d+[%$MBK+\-]?\s*(?:automação|recovery|precisão|redução|aumento|receita|pipeline)?)',
        r'<span class="metric">\1</span>',
        metrica,
        flags=re.IGNORECASE
    )
    
    # Monta bullet
    return f"{alavanca} → <strong>{metrica_highlighted}</strong>"


def select_relevant_bullets(exp: Dict, pain_points: List[PainPoint], max_bullets: int = 4) -> List[str]:
    """Seleciona bullets mais relevantes para as dores detectadas"""
    bullets = exp.get("bullets_modelo_cam", [])
    if not bullets:
        return []
    
    # Coleta tags das dores
    relevant_tags = set()
    for pain in pain_points:
        relevant_tags.update(pain.solution_tags)
    
    # Pontua cada bullet por relevância
    scored = []
    for bullet in bullets:
        bullet_tags = set(bullet.get("tags", []))
        score = len(bullet_tags & relevant_tags)
        scored.append((bullet, score))
    
    # Ordena e formata
    scored.sort(key=lambda x: x[1], reverse=True)
    formatted = [format_cam_bullet(b[0], list(relevant_tags)) for b in scored[:max_bullets]]
    
    return formatted


# ============================================================================
# NETWORKING MESSAGE GENERATOR
# ============================================================================

def generate_networking_message(
    company: str,
    role: str,
    pain_points: List[PainPoint]
) -> str:
    """Gera mensagem de networking baseada na dor identificada"""
    
    main_pain = pain_points[0] if pain_points else PAIN_POINT_PATTERNS["falta_automacao"]
    
    template = f"""Vi que a posição de {role} na {company} foca em {main_pain.messaging_hook}.

No meu tempo de Meta e varejo, percebi que o gargalo comum é a falta de conexão entre estratégia e execução técnica. 

Implementei automações que reduziram processos de semanas para horas. Posso te mostrar como aplicar isso na {company}?"""

    return template.strip()


# ============================================================================
# RESUME GENERATOR
# ============================================================================

def generate_tailored_resume(
    job_description: str,
    company: str = "Empresa",
    role: str = "Cargo",
    output_name: str = None
) -> Tuple[str, str]:
    """
    Gera currículo tailor-made para vaga específica.
    Retorna (path_pdf, networking_message)
    """
    
    print("\n" + "=" * 70)
    print("🎯 TAYLOR-MADE RESUME ENGINE v2.0")
    print("=" * 70)
    
    # 1. DETECTA DORES LATENTES
    print("\n📋 [1/5] Detectando Dores Latentes...")
    pain_points = detect_pain_points(job_description)
    print(f"   Dores: {', '.join([p.category for p in pain_points])}")
    
    # 2. DETERMINA NARRATIVA
    print("\n🎭 [2/5] Aplicando Narrative Shift...")
    shift_type = determine_narrative_shift(job_description)
    print(f"   Narrativa: {shift_type}")
    
    # 3. MONTA HEADLINE E SUMMARY
    print("\n✍️  [3/5] Gerando Headline e Summary...")
    
    # Keywords baseadas nas dores
    keywords = []
    for pain in pain_points:
        keywords.extend(pain.keywords[:2])
    keywords = list(set(keywords))[:5]
    
    headline = f"{role} | {MASTER_CONTEXT['positioning']['differentiator']}"
    
    summary = f"""Profissional com 15 anos de experiência (Meta, Ambev, Dow, Suzano) focado em {pain_points[0].messaging_hook if pain_points else 'crescimento'}. 
Mindset: {MASTER_CONTEXT['positioning']['mindset']}. 
Background técnico hands-on com n8n, Python, SQL e IA generativa. 
Histórico de impacto mensurável: US$85M na Meta, 30% growth na Telium, US$5M pipeline na Dow."""
    
    # 4. PROCESSA EXPERIÊNCIAS
    print("\n💼 [4/5] Selecionando Experiências Relevantes...")
    
    experiences = []
    for exp in MASTER_CONTEXT["experiences"]:
        # Aplica narrative shift
        transformed = apply_narrative_shift(exp, shift_type)
        
        # Seleciona bullets relevantes
        bullets = select_relevant_bullets(exp, pain_points, max_bullets=3)
        
        if not bullets:
            # Fallback: primeiro bullet
            if exp.get("bullets_modelo_cam"):
                bullets = [format_cam_bullet(exp["bullets_modelo_cam"][0])]
        
        experiences.append({
            "empresa": exp["empresa"],
            "cargo": transformed["cargo_display"],
            "periodo": exp["periodo"],
            "bullets": bullets,
            "stack": exp.get("stack", "")
        })
    
    print(f"   {len(experiences)} experiências processadas")
    
    # 5. GERA MENSAGEM DE NETWORKING
    print("\n📨 [5/5] Gerando Mensagem de Networking...")
    networking_msg = generate_networking_message(company, role, pain_points)
    
    # RENDERIZA HTML
    data = {
        "nome": MASTER_CONTEXT["nome"],
        "headline": headline,
        "email": MASTER_CONTEXT["email"],
        "linkedin": MASTER_CONTEXT["linkedin"],
        "location": MASTER_CONTEXT["location"],
        "summary": summary,
        "keywords": " • ".join(keywords),
        "experience": experiences,
        "projects": MASTER_CONTEXT["ai_projects"][:3],
        "education": MASTER_CONTEXT["education"],
        "languages": MASTER_CONTEXT["languages"]
    }
    
    # Template inline
    html_template = get_html_template()
    env = Environment()
    template = env.from_string(html_template)
    rendered = template.render(**data)
    
    # SALVA
    if output_name is None:
        slug = re.sub(r'[^a-z0-9]', '_', company.lower())[:20]
        output_name = f"tailored_{slug}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    html_path = OUTPUT_DIR / f"{output_name}.html"
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(rendered)
    
    pdf_path = html_path
    if HAS_WEASYPRINT:
        pdf_path = OUTPUT_DIR / f"{output_name}.pdf"
        HTML(string=rendered).write_pdf(pdf_path)
    
    print("\n" + "=" * 70)
    print(f"✅ CURRÍCULO: {pdf_path}")
    print("=" * 70)
    print("\n📨 MENSAGEM DE NETWORKING:\n")
    print(networking_msg)
    print("\n" + "=" * 70)
    
    return str(pdf_path), networking_msg


def get_html_template() -> str:
    """Template HTML profissional"""
    return """<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <style>
        :root { --primary: #1a365d; --accent: #c53030; --text: #2d3748; }
        @page { size: A4; margin: 12mm; }
        body { font-family: 'Helvetica Neue', sans-serif; color: var(--text); line-height: 1.45; font-size: 10px; }
        
        .header { text-align: center; border-bottom: 2px solid var(--primary); padding-bottom: 10px; margin-bottom: 12px; }
        .header h1 { font-size: 24px; color: var(--primary); margin: 0; }
        .header .headline { font-size: 11px; color: var(--text); margin: 4px 0; font-weight: 500; }
        .header .contact { font-size: 9px; color: #718096; }
        
        .summary { background: #f7fafc; padding: 10px; border-left: 3px solid var(--primary); margin-bottom: 12px; }
        .summary p { margin: 0; font-size: 10px; line-height: 1.5; }
        .keywords { margin-top: 6px; font-size: 9px; color: #4a5568; }
        
        h2 { color: var(--primary); text-transform: uppercase; font-size: 12px; letter-spacing: 1px; border-bottom: 1px solid #e2e8f0; padding-bottom: 3px; margin: 12px 0 8px; }
        
        .exp-item { margin-bottom: 10px; page-break-inside: avoid; }
        .exp-header { display: flex; justify-content: space-between; font-size: 11px; font-weight: 600; color: var(--primary); }
        .exp-title { font-size: 10px; color: var(--text); font-weight: 500; margin-bottom: 4px; }
        .exp-item ul { margin: 4px 0; padding-left: 16px; }
        .exp-item li { margin-bottom: 3px; font-size: 9.5px; line-height: 1.4; }
        .stack { font-size: 8px; color: #718096; font-style: italic; margin-top: 3px; }
        
        .metric { font-weight: 700; color: var(--primary); }
        
        .projects { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; }
        .project { background: #f7fafc; padding: 8px; border-left: 2px solid var(--primary); }
        .project h4 { font-size: 9px; color: var(--primary); margin: 0 0 3px; }
        .project p { font-size: 8px; color: var(--text); margin: 0; }
        .project .pstack { font-size: 7px; color: #718096; margin-top: 4px; }
        
        .education { display: grid; grid-template-columns: repeat(4, 1fr); gap: 6px; font-size: 9px; }
        .edu-item h4 { font-size: 10px; color: var(--primary); margin: 0; }
        .edu-item p { margin: 2px 0; color: #4a5568; }
        
        .languages { font-size: 9px; color: var(--text); }
    </style>
</head>
<body>
    <div class="header">
        <h1>{{ nome }}</h1>
        <div class="headline">{{ headline }}</div>
        <div class="contact">{{ email }} | {{ linkedin }} | {{ location }}</div>
    </div>
    
    <div class="summary">
        <p>{{ summary }}</p>
        <div class="keywords"><strong>Core:</strong> {{ keywords }}</div>
    </div>
    
    <h2>Professional Experience</h2>
    {% for exp in experience %}
    <div class="exp-item">
        <div class="exp-header">
            <span>{{ exp.empresa }}</span>
            <span>{{ exp.periodo }}</span>
        </div>
        <div class="exp-title">{{ exp.cargo }}</div>
        <ul>
            {% for bullet in exp.bullets %}
            <li>{{ bullet | safe }}</li>
            {% endfor %}
        </ul>
        {% if exp.stack %}<div class="stack">{{ exp.stack }}</div>{% endif %}
    </div>
    {% endfor %}
    
    <h2>AI & Automation Projects</h2>
    <div class="projects">
        {% for proj in projects %}
        <div class="project">
            <h4>{{ proj.nome }}</h4>
            <p>{{ proj.resultado }}</p>
            <div class="pstack">{{ proj.stack }}</div>
        </div>
        {% endfor %}
    </div>
    
    <h2>Education</h2>
    <div class="education">
        {% for edu in education %}
        <div class="edu-item">
            <h4>{{ edu.program }}</h4>
            <p>{{ edu.institution }} ({{ edu.year }})</p>
        </div>
        {% endfor %}
    </div>
    
    <h2>Languages</h2>
    <div class="languages">{{ languages | join(' • ') }}</div>
</body>
</html>"""


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Taylor-Made Resume Engine v2.0")
    parser.add_argument("-j", "--job", required=True, help="Arquivo com job description")
    parser.add_argument("-c", "--company", default="Empresa", help="Nome da empresa")
    parser.add_argument("-r", "--role", default="Cargo", help="Título da vaga")
    parser.add_argument("-o", "--output", default=None, help="Nome do output")
    
    args = parser.parse_args()
    
    # Carrega JD
    with open(args.job, "r", encoding="utf-8") as f:
        jd = f.read()
    
    # Gera
    pdf_path, msg = generate_tailored_resume(
        job_description=jd,
        company=args.company,
        role=args.role,
        output_name=args.output
    )
