#!/usr/bin/env python3
"""
SOTA Resume Generator - Currículo otimizado para ATS
Gera currículo completo com todas experiências e keywords mapeadas
"""

import json
from pathlib import Path
from datetime import datetime

try:
    from jinja2 import Template
except ImportError:
    print("❌ Jinja2 não instalado. Execute: pip install jinja2")
    exit(1)

try:
    from weasyprint import HTML
    HAS_WEASYPRINT = True
except ImportError:
    HAS_WEASYPRINT = False


BASE_DIR = Path(__file__).parent
TEMPLATES_DIR = BASE_DIR / "templates"
OUTPUT_DIR = BASE_DIR / "output"


def load_master_profile() -> dict:
    with open(BASE_DIR / "master_profile.json", "r", encoding="utf-8") as f:
        return json.load(f)


def generate_sota_ifood_ai():
    """Gera currículo SOTA para vaga iFood IA Generativa"""
    
    profile = load_master_profile()
    candidato = profile["candidato"]
    
    # ============== DADOS TAILORED PARA VAGA iFOOD GPM IA ==============
    
    data = {
        "nome": candidato["nome_completo"],
        "email": "thiago@email.com",  # UPDATE COM EMAIL REAL
        "linkedin": candidato["linkedin"],
        
        # HEADLINE: Match direto com título da vaga
        "headline": "Group Product Manager (GPM) | IA Generativa & LLM Products | Ex-Meta | Agentic AI & Automation at Scale",
        
        # SUMMARY: Keywords críticas da vaga
        "summary": """Group Product Manager with 15+ years in high-complexity environments (Meta, Ambev, Dow, Suzano) now focused on IA Generativa and AI/ML product development at scale. 
Currently building production-grade agentes autônomos and LLM-powered automation for marketplaces using n8n, Docker, Python, and SQL. 
Proven track record leading cross-functional teams, defining product roadmaps, and managing C-level stakeholders in LATAM operations at escala. 
Unique edge: Neuroscience background (USP/Mackenzie) combined with hands-on experience in Agentic Flows, RAG implementations, and Prompt Engineering.""",

        # KEYWORDS SECTION: Todas as keywords críticas da vaga
        "keywords": "GPM • IA Generativa • LLM Orchestration • Agentic AI • Agentes Autônomos • RAG • Prompt Engineering • Product Roadmap • Marketplace Operations at Scale • C-Level Stakeholder Management • Data Science • ML Engineering • Python • SQL • n8n • Docker • Langchain",
        
        # EXPERIÊNCIAS: Todas relevantes com bullets ATS-optimized
        "experience": [
            {
                "empresa": "Lorinz Consulting",
                "cargo": "AI & Automation Lead | Senior Consultant",
                "periodo": "Dec 2022 - Present",
                "scope": "AI Strategy & Implementation for Enterprise Clients (360 Dialog, Borelli, JEM Systems)",
                "bullets": [
                    "Architected and deployed <span class='keyword'>Agentic AI workflows</span> using <span class='keyword'>n8n</span>, Docker, and PostgreSQL for e-commerce automation, achieving <span class='metric'>80% reduction</span> in manual customer service operations",
                    "Developed <span class='keyword'>LLM-powered chatbots</span> with <span class='keyword'>RAG</span> implementation for product recommendation, integrating Nuvemshop and Shopify APIs for real-time inventory queries",
                    "Led <span class='keyword'>Prompt Engineering</span> initiatives for content generation pipelines using ComfyUI, Eleven Labs, and local LLMs, reducing production time by <span class='metric'>40%</span>",
                    "Designed <span class='keyword'>RevOps automation</span> stack connecting sales and marketing data, enabling <span class='keyword'>data-driven</span> decisions that increased client revenue by <span class='metric'>25%</span>",
                    "Managed <span class='keyword'>stakeholder</span> education programs for 1,000+ participants with <span class='metric'>95% satisfaction rate</span>"
                ]
            },
            {
                "empresa": "Meta (Facebook)",
                "cargo": "Partner Marketing Lead",
                "periodo": "Dec 2021 - Dec 2022",
                "scope": "LATAM & North America | Partner Ecosystem | $116.6B Revenue Portfolio",
                "bullets": [
                    "Led <span class='keyword'>Go-to-Market strategy</span> for Discovery Commerce across LATAM, generating <span class='metric'>US$85M revenue impact</span> through data-driven partner campaigns featured in AdWeek and Meio & Mensagem",
                    "Created Canva Creative Journey and Commerce Performance Series programs, contributing to <span class='metric'>50%+ of Meta's partner-driven revenue</span> in the region",
                    "Managed <span class='keyword'>C-level stakeholders</span> and cross-functional teams across 3 continents, aligning product marketing roadmaps with business objectives",
                    "Co-led Disability@ ERG initiatives, developing AI-powered accessibility chatbot highlighted by executive leadership",
                    "Applied <span class='keyword'>A/B testing</span> and experimentation frameworks to optimize partner activation campaigns"
                ]
            },
            {
                "empresa": "Telium Networks",
                "cargo": "Senior Marketing Manager",
                "periodo": "Nov 2020 - Dec 2021",
                "scope": "Reporting to CEO | B2B Technology | Growth & Brand Strategy",
                "bullets": [
                    "Defined and executed <span class='keyword'>product roadmap</span> for marketing technology stack, increasing company growth from <span class='metric'>20% to 30% YoY</span>",
                    "Implemented <span class='keyword'>marketing automation</span> and sales methodologies, achieving <span class='metric'>+25% conversion rate</span> in 3 months",
                    "Led brand repositioning initiative (AllWaysON), translating technical capabilities into market positioning"
                ]
            },
            {
                "empresa": "Ambev (ABInBev)",
                "cargo": "Internal Communications Specialist",
                "periodo": "Jun 2018 - Nov 2019",
                "scope": "LATAM & Global Scope | Cross-functional Projects",
                "bullets": [
                    "Managed 'Dia de Responsa' campaign recognized by global CEO Carlos Brito, trending on Twitter with influencer participation (Anitta, Wesley Safadão)",
                    "Led agency management for events and video production across Latin America",
                    "Supervised Workplace campaigns on sustainability and product launches at <span class='keyword'>scale</span>"
                ]
            },
            {
                "empresa": "Dow Chemical",
                "cargo": "Senior Marketing Specialist",
                "periodo": "2017 - 2019",
                "scope": "B2B Industrial | Demand Generation",
                "bullets": [
                    "Structured B2B content marketing strategy generating <span class='metric'>US$5M pipeline</span> in marketing-originated opportunities",
                    "Translated technical requirements into marketing specifications for industrial division"
                ]
            },
            {
                "empresa": "Suzano Papel e Celulose",
                "cargo": "Marketing Coordinator",
                "periodo": "2015 - 2017",
                "scope": "Post-M&A Brand Integration",
                "bullets": [
                    "Coordinated rebranding and institutional communication post-merger, increasing brand awareness by <span class='metric'>25%</span> in unaided recall"
                ]
            }
        ],
        
        # PROJETOS AI: Crítico para vaga de IA
        "projects": [
            {
                "nome": "E-commerce Agentic Workflow",
                "descricao": "Autonomous AI agents for cart recovery and customer triage with 98% accuracy",
                "stack": "n8n • Docker • PostgreSQL • WAHA Bot • LLM API"
            },
            {
                "nome": "RAG-Powered Product Assistant",
                "descricao": "WhatsApp chatbot with retrieval-augmented generation for product recommendations",
                "stack": "Python • LangChain • Vector DB • Nuvemshop API"
            },
            {
                "nome": "Local AI Content Pipeline",
                "descricao": "End-to-end content generation with local LLMs, image generation, and voice synthesis",
                "stack": "ComfyUI • Ollama • Eleven Labs • Python"
            },
            {
                "nome": "RevOps Automation Stack",
                "descricao": "Unified sales-marketing data pipeline reducing CAC and increasing LTV",
                "stack": "n8n • GoHighLevel • SQL • Webhooks"
            }
        ],
        
        # SKILLS: Organizadas por relevância para vaga
        "skills": [
            {
                "name": "AI & LLM",
                "skills_list": [
                    {"name": "LLM Orchestration", "class": "critical"},
                    {"name": "Agentic AI", "class": "critical"},
                    {"name": "RAG", "class": "critical"},
                    {"name": "Prompt Engineering", "class": "critical"},
                    {"name": "Fine-tuning", "class": "highlight"},
                    {"name": "LangChain", "class": "highlight"}
                ]
            },
            {
                "name": "Infrastructure",
                "skills_list": [
                    {"name": "n8n", "class": "critical"},
                    {"name": "Docker", "class": "critical"},
                    {"name": "Python", "class": "critical"},
                    {"name": "SQL/PostgreSQL", "class": "critical"},
                    {"name": "API Design", "class": ""},
                    {"name": "MCP Servers", "class": ""}
                ]
            },
            {
                "name": "Product & Data",
                "skills_list": [
                    {"name": "Product Roadmap", "class": "critical"},
                    {"name": "A/B Testing", "class": "highlight"},
                    {"name": "Data Science", "class": "highlight"},
                    {"name": "ML Engineering", "class": "highlight"},
                    {"name": "Agile/Scrum", "class": ""},
                    {"name": "Backlog Mgmt", "class": ""}
                ]
            },
            {
                "name": "Leadership",
                "skills_list": [
                    {"name": "C-Level Stakeholders", "class": "critical"},
                    {"name": "Cross-functional", "class": ""},
                    {"name": "GTM Strategy", "class": ""},
                    {"name": "Team Leadership", "class": ""},
                    {"name": "Remote Teams", "class": ""},
                    {"name": "Agency Mgmt", "class": ""}
                ]
            }
        ],
        
        # EDUCAÇÃO
        "education": [
            {
                "titulo": "MSc Communications",
                "instituicao": "USP - Univ. São Paulo",
                "ano": "2024 - Present"
            },
            {
                "titulo": "MBA Marketing Director",
                "instituicao": "NEXT MBA (Philip Kotler)",
                "ano": "2024"
            },
            {
                "titulo": "Neuroscience Specialization",
                "instituicao": "Mackenzie University",
                "ano": "2018 - 2020"
            },
            {
                "titulo": "BA Marketing & Advertising",
                "instituicao": "ESPM",
                "ano": "2007 - 2011"
            }
        ],
        
        # IDIOMAS
        "languages": [
            {"idioma": "Portuguese", "nivel": "Native"},
            {"idioma": "English", "nivel": "Fluent (IELTS)"},
            {"idioma": "Spanish", "nivel": "Advanced"}
        ]
    }
    
    # Gerar HTML
    with open(TEMPLATES_DIR / "resume_sota.html", "r", encoding="utf-8") as f:
        template = Template(f.read())
    
    html = template.render(**data)
    
    # Salvar
    OUTPUT_DIR.mkdir(exist_ok=True)
    
    html_path = OUTPUT_DIR / "ifood_sota.html"
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"✅ HTML salvo: {html_path}")
    
    if HAS_WEASYPRINT:
        pdf_path = OUTPUT_DIR / "ifood_sota.pdf"
        HTML(string=html).write_pdf(pdf_path)
        print(f"✅ PDF salvo: {pdf_path}")
    
    print("\n📊 ATS KEYWORD MATCH:")
    print("=" * 50)
    keywords_vaga = [
        "GPM", "IA Generativa", "LLM", "RAG", "Fine-tuning", 
        "Prompt Engineering", "Agentic AI", "ML Engineering", 
        "Data Science", "stakeholders C-level", "roadmap",
        "n8n", "Langchain", "marketplaces", "escala", "agentes"
    ]
    
    html_lower = html.lower()
    for kw in keywords_vaga:
        found = "✅" if kw.lower() in html_lower else "❌"
        print(f"  {found} {kw}")
    
    print("=" * 50)
    print("🎯 Currículo SOTA gerado com sucesso!")


if __name__ == "__main__":
    generate_sota_ifood_ai()
