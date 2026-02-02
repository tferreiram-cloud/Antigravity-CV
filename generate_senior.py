#!/usr/bin/env python3
"""
Senior Resume Generator - Currículo completo para 15+ anos de experiência
Ordem cronológica reversa, conteúdo expandido, formatação profissional
"""

import json
from pathlib import Path
from datetime import datetime

try:
    from jinja2 import Template
except ImportError:
    import subprocess
    subprocess.run(["pip", "install", "jinja2", "-q"])
    from jinja2 import Template

try:
    from weasyprint import HTML
    HAS_WEASYPRINT = True
except ImportError:
    HAS_WEASYPRINT = False


BASE_DIR = Path(__file__).parent
TEMPLATES_DIR = BASE_DIR / "templates"
OUTPUT_DIR = BASE_DIR / "output"


def format_star_to_bullet(star: dict) -> str:
    """Converte STAR em bullet profissional"""
    action = star.get("action", "")
    result = star.get("result", "")
    
    # Destaca métricas
    import re
    for metric in re.findall(r'(\d+[%$MK+\-]?\s*(?:reduction|increase|improvement|growth|revenue|pipeline)?)', result, re.I):
        result = result.replace(metric, f"<span class='metric'>{metric}</span>")
    
    # Bullet completo STAR
    bullet = f"{action}"
    if result:
        bullet += f" <strong>→</strong> {result}"
    
    return bullet


def generate_senior_resume_ifood():
    """
    Gera currículo COMPLETO para vaga iFood GPM IA
    TODAS as experiências em ordem cronológica reversa
    Conteúdo expandido para perfil sênior
    """
    
    # Dados completos do candidato
    data = {
        "nome": "Thiago Ferreira Moraes",
        "headline": "Group Product Manager (GPM) | AI & LLM Products | Ex-Meta | 15+ Years", 
        "email": "thiago@email.com",
        "linkedin": "linkedin.com/in/thiagomkt",
        "location": "São Paulo, Brazil",
        
        "summary": """Strategic Product and Marketing Leader with 15+ years of progressive experience across Fortune 500 companies (Meta, Ambev, Dow, Suzano) 
and high-growth tech startups. Currently focused on AI/ML product development, building production-grade Agentic AI workflows and LLM-powered 
automation systems. Proven track record of driving $85M+ revenue impact at Meta LATAM through Go-to-Market excellence and C-level stakeholder 
management. Unique combination of Neuroscience background (USP/Mackenzie) and hands-on technical skills in n8n, Docker, Python, and SQL. 
Passionate about translating complex AI capabilities into business value at scale across marketplaces and enterprise operations.""",

        "keywords": "LLM Orchestration • Agentic AI • RAG • Prompt Engineering • Product Roadmap • Go-to-Market • C-Level Stakeholder Management • Python • SQL • n8n • Docker • Data Science • ML Engineering • LATAM Scale",
        
        # EXPERIÊNCIAS EM ORDEM CRONOLÓGICA REVERSA (mais recente primeiro)
        "experience": [
            # 1. LORINZ (2022 - Present)
            {
                "empresa": "Lorinz Consulting",
                "cargo": "AI & Automation Lead | Senior Marketing Consultant",
                "periodo": "December 2022 – Present",
                "localizacao": "São Paulo, Brazil (Remote)",
                "escopo": "Enterprise AI Strategy & Implementation • Clients: 360 Dialog, Borelli, JEM Systems (global enterprise)",
                "bullets": [
                    "Architected and deployed production-grade <span class='keyword'>Agentic AI workflows</span> using n8n, Docker, and PostgreSQL for e-commerce clients, achieving <span class='metric'>80% automation</span> of customer service operations and <span class='metric'>15% recovery</span> of abandoned carts",
                    "Developed LLM-powered chatbots with <span class='keyword'>RAG (Retrieval-Augmented Generation)</span> for product recommendations, integrating Nuvemshop and Shopify APIs for real-time inventory queries with <span class='metric'>98% accuracy</span>",
                    "Led <span class='keyword'>Prompt Engineering</span> initiatives for AI content pipelines using ComfyUI, Eleven Labs, and local LLMs, reducing content production time by <span class='metric'>40%</span> and enabling <span class='metric'>3x campaign output</span>",
                    "Built RevOps automation stack connecting CRM, advertising, and analytics platforms, driving <span class='metric'>25% revenue increase</span> and <span class='metric'>20% CAC reduction</span> for clients",
                    "Managed stakeholder education programs for 1,000+ participants across marketing and sales teams, achieving <span class='metric'>95% satisfaction rate</span> and <span class='metric'>80% tool adoption</span> within 3 months"
                ],
                "stack": "n8n • Docker • PostgreSQL • Python • SQL • OpenAI API • LangChain • ComfyUI • Eleven Labs • GoHighLevel"
            },
            
            # 2. META (2021 - 2022)
            {
                "empresa": "Meta (Facebook)",
                "cargo": "Partner Marketing Lead",
                "periodo": "December 2021 – December 2022",
                "localizacao": "São Paulo, Brazil",
                "escopo": "LATAM & North America • Partner Ecosystem • $116.6B Revenue Portfolio",
                "bullets": [
                    "Designed and executed <span class='keyword'>Go-to-Market strategy</span> for Discovery Commerce across Latin America, generating <span class='metric'>US$85M revenue impact</span> through partner-driven campaigns featured in AdWeek and Meio & Mensagem",
                    "Created flagship programs including Canva Creative Journey and Commerce Performance Series, contributing to <span class='metric'>50%+ of Meta's partner-driven revenue</span> in the region with programs later scaled globally",
                    "Managed <span class='keyword'>C-level stakeholder</span> communication and cross-functional coordination across 3 continents, presenting quarterly business reviews and securing additional investment in partner programs",
                    "Coordinated product, sales, and partner teams for campaign execution, developing case studies and enablement materials that became standard resources across LATAM",
                    "Co-led Disability@ ERG initiatives including AI-powered chatbot for accessibility awareness, featured by executive leadership with <span class='metric'>50% increase</span> in ERG membership"
                ],
                "stack": "Meta Ads Platform • Workplace • Data Analytics • Cross-functional Leadership"
            },
            
            # 3. TELIUM (2020 - 2021)
            {
                "empresa": "Telium Networks",
                "cargo": "Senior Marketing Manager",
                "periodo": "November 2020 – December 2021",
                "localizacao": "São Paulo, Brazil",
                "escopo": "Reporting to CEO • B2B Technology • Full Marketing Leadership",
                "bullets": [
                    "Led comprehensive <span class='keyword'>growth strategy</span> and brand repositioning (AllWaysON), accelerating company growth from <span class='metric'>20% to 30% YoY</span> and increasing brand awareness by <span class='metric'>40%</span>",
                    "Implemented <span class='keyword'>marketing automation</span> and lead scoring infrastructure, achieving <span class='metric'>+25% conversion rate</span> in 3 months and <span class='metric'>20% reduction</span> in sales cycle",
                    "Managed agency relationships and budget allocation, redesigned corporate website, and trained sales team on new qualification criteria"
                ],
                "stack": "Marketing Automation • CRM • Google Analytics • B2B Marketing"
            },
            
            # 4. AMBEV (2018 - 2019)
            {
                "empresa": "Ambev (ABInBev)",
                "cargo": "Internal Communications Specialist",
                "periodo": "June 2018 – November 2019",
                "localizacao": "São Paulo, Brazil",
                "escopo": "LATAM & Global Scope • Cross-functional Projects • Agency Management",
                "bullets": [
                    "Led creative development and execution of 'Dia de Responsa' campaign with influencer partnerships (Anitta, Wesley Safadão), achieving <span class='metric'>Trending on Twitter</span> status and recognition from global CEO Carlos Brito",
                    "Generated <span class='metric'>10M+ social impressions</span> through strategic social media campaign, managing agencies for events, video production, and influencer coordination across Latin America",
                    "Unified internal communications across Workplace platform, achieving <span class='metric'>50% increase</span> in employee engagement and consistent brand voice across LATAM operations"
                ],
                "stack": "Workplace • Social Media • Agency Management • Video Production"
            },
            
            # 5. DOW CHEMICAL (2017 - 2019) - Paralelo com Ambev
            {
                "empresa": "Dow Chemical",
                "cargo": "Senior Marketing Specialist",
                "periodo": "2017 – 2019",
                "localizacao": "São Paulo, Brazil",
                "escopo": "B2B Industrial Marketing • Demand Generation • Content Strategy",
                "bullets": [
                    "Built <span class='keyword'>B2B content marketing strategy</span> for industrial division, generating <span class='metric'>US$5M pipeline</span> from marketing-originated leads and <span class='metric'>30% increase</span> in MQLs",
                    "Audited complete buyer journey and created technical content (whitepapers, webinars, case studies), implementing lead nurturing workflows with marketing automation",
                    "Translated complex technical product capabilities into compelling marketing specifications, bridging engineering and commercial teams"
                ],
                "stack": "Content Marketing • Marketing Automation • B2B Strategy • Technical Writing"
            },
            
            # 6. SUZANO (2015 - 2017)
            {
                "empresa": "Suzano Papel e Celulose",
                "cargo": "Marketing Coordinator",
                "periodo": "2015 – 2017",
                "localizacao": "São Paulo, Brazil",
                "escopo": "Post-M&A Brand Integration • Corporate Rebranding",
                "bullets": [
                    "Led <span class='keyword'>post-merger rebranding</span> initiative following major acquisition, coordinating with C-level leadership on brand strategy and developing new visual identity",
                    "Created comprehensive internal and external communication plan, achieving <span class='metric'>25% increase</span> in unaided brand recall and successful cultural integration across merged organization",
                    "Managed cross-functional teams for institutional communication and sustainability storytelling"
                ],
                "stack": "Brand Strategy • M&A Communications • Change Management"
            },
            
            # 7. FAST SHOP (2013 - 2015)
            {
                "empresa": "Fast Shop",
                "cargo": "Trade Marketing Analyst",
                "periodo": "2013 – 2015",
                "localizacao": "São Paulo, Brazil",
                "escopo": "Premium Retail • Trade Marketing • Analytics",
                "bullets": [
                    "Built <span class='keyword'>analytics framework</span> for promotional optimization, analyzing historical data and creating predictive models for promotional success",
                    "Drove <span class='metric'>18% sales increase</span> during promotional periods and <span class='metric'>15% optimization</span> of promotional spend through data-driven campaign planning",
                    "Coordinated with suppliers and store operations for trade marketing activations across retail network"
                ],
                "stack": "Analytics • Trade Marketing • Retail Operations • Excel/Data Analysis"
            }
        ],
        
        # PROJETOS AI
        "projects": [
            {
                "nome": "E-commerce Agentic Workflow",
                "descricao": "Autonomous AI agents for cart recovery & customer triage. 98% accuracy, 80% automation, 15% cart recovery.",
                "stack": "n8n • Docker • PostgreSQL • WAHA Bot • LLM API"
            },
            {
                "nome": "RAG-Powered Product Assistant",
                "descricao": "WhatsApp chatbot with retrieval-augmented generation. 70% faster response, 85% first-contact resolution.",
                "stack": "Python • LangChain • ChromaDB • OpenAI • Nuvemshop API"
            },
            {
                "nome": "Local AI Content Pipeline",
                "descricao": "End-to-end content generation with local LLMs. 40% faster production, 3x content output.",
                "stack": "ComfyUI • Ollama • Eleven Labs • Python • n8n"
            },
            {
                "nome": "RevOps Automation Stack",
                "descricao": "Unified sales-marketing data pipeline. 25% revenue increase, 20% CAC reduction.",
                "stack": "n8n • GoHighLevel • SQL • Webhooks"
            }
        ],
        
        # SKILLS
        "skills": [
            {
                "name": "AI & LLM",
                "skills_list": [
                    {"name": "LLM Orchestration", "primary": True},
                    {"name": "Agentic AI", "primary": True},
                    {"name": "RAG", "primary": True},
                    {"name": "Prompt Engineering", "primary": True},
                    {"name": "Fine-tuning", "primary": False},
                    {"name": "LangChain", "primary": False}
                ]
            },
            {
                "name": "Infrastructure",
                "skills_list": [
                    {"name": "n8n", "primary": True},
                    {"name": "Docker", "primary": True},
                    {"name": "Python", "primary": True},
                    {"name": "SQL/PostgreSQL", "primary": True},
                    {"name": "APIs", "primary": False}
                ]
            },
            {
                "name": "Product & Data",
                "skills_list": [
                    {"name": "Product Roadmap", "primary": True},
                    {"name": "Go-to-Market", "primary": True},
                    {"name": "A/B Testing", "primary": False},
                    {"name": "Data Science", "primary": False},
                    {"name": "Agile/Scrum", "primary": False}
                ]
            },
            {
                "name": "Leadership",
                "skills_list": [
                    {"name": "C-Level Stakeholders", "primary": True},
                    {"name": "Cross-functional Teams", "primary": False},
                    {"name": "Agency Management", "primary": False},
                    {"name": "Remote Leadership", "primary": False}
                ]
            }
        ],
        
        # EDUCAÇÃO
        "education": [
            {
                "programa": "MSc Communications",
                "instituicao": "USP - Universidade de São Paulo",
                "ano": "2024 – Present",
                "destaque": "Analytical Psychology & Consumer Behavior"
            },
            {
                "programa": "MBA Marketing Director",
                "instituicao": "NEXT MBA",
                "ano": "2024",
                "destaque": "With Philip Kotler"
            },
            {
                "programa": "Neuroscience Specialization",
                "instituicao": "Mackenzie University",
                "ano": "2018 – 2020",
                "destaque": "Neuromarketing & Cognitive Processes"
            },
            {
                "programa": "BA Marketing & Advertising",
                "instituicao": "ESPM",
                "ano": "2007 – 2011",
                "destaque": "Research Assistant"
            }
        ],
        
        # IDIOMAS
        "languages": [
            {"idioma": "Portuguese", "nivel": "Native", "certificacao": None},
            {"idioma": "English", "nivel": "Fluent", "certificacao": "IELTS"},
            {"idioma": "Spanish", "nivel": "Advanced", "certificacao": None}
        ]
    }
    
    # Carregar template
    with open(TEMPLATES_DIR / "senior_resume.html", "r", encoding="utf-8") as f:
        template = Template(f.read())
    
    # Renderizar
    html = template.render(**data)
    
    # Salvar
    OUTPUT_DIR.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_name = f"ifood_senior_{timestamp}"
    
    html_path = OUTPUT_DIR / f"{output_name}.html"
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"✅ HTML: {html_path}")
    
    if HAS_WEASYPRINT:
        pdf_path = OUTPUT_DIR / f"{output_name}.pdf"
        HTML(string=html).write_pdf(pdf_path)
        print(f"✅ PDF: {pdf_path}")
    
    # Stats
    print("\n📊 RESUMO DO CURRÍCULO:")
    print(f"   • {len(data['experience'])} experiências (ordem cronológica reversa)")
    print(f"   • {sum(len(e['bullets']) for e in data['experience'])} bullets totais")
    print(f"   • {len(data['projects'])} projetos AI")
    print(f"   • {len(data['keywords'].split('•'))} keywords ATS")
    
    return html_path if not HAS_WEASYPRINT else pdf_path


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("📄 SENIOR RESUME GENERATOR")
    print("=" * 60 + "\n")
    
    generate_senior_resume_ifood()
    
    print("\n" + "=" * 60)
    print("✅ CURRÍCULO SÊNIOR COMPLETO GERADO!")
    print("=" * 60 + "\n")
