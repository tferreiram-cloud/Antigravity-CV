# Taylor-Made Resume Pipeline

Sistema antifrágil de geração de currículos com zero human-in-the-loop.

## Quick Start

```bash
cd /Users/thi/.gemini/antigravity/scratch/taylor_resume
source .venv/bin/activate

# Gerar currículo de uma vaga
python pipeline.py examples/ifood_ai_job.txt

# Ou com nome customizado
python pipeline.py vaga.txt -o minha_vaga
```

## Arquitetura

```
┌─────────────────────────────────────────────────────────────┐
│                    PIPELINE ANTIFRÁGIL                       │
├─────────────────────────────────────────────────────────────┤
│  📋 Vaga (texto)                                             │
│       ↓                                                      │
│  🤖 LLM Orchestrator (auto-detect: Ollama → Groq → Gemini)   │
│       ↓                                                      │
│  🔍 Keyword Extraction (LLM + regex fallback)                │
│       ↓                                                      │
│  📂 Master CV → Scoring → Top 6 experiências                 │
│       ↓                                                      │
│  ✨ Tailoring Engine (headline, summary, bullets)            │
│       ↓                                                      │
│  📄 HTML Rendering (Jinja2)                                  │
│       ↓                                                      │
│  🔧 ATS Validation + Self-Healing (se < 80%)                 │
│       ↓                                                      │
│  ✅ PDF (WeasyPrint)                                         │
└─────────────────────────────────────────────────────────────┘
```

## Integração n8n

```bash
# Inicia webhook server
python webhook_server.py

# POST para gerar currículo
curl -X POST http://localhost:5555/generate \
  -H "Content-Type: application/json" \
  -d '{"job_description": "GPM IA Generativa no iFood..."}' \
  -o resume.pdf
```

## Arquivos

| Arquivo | Descrição |
|---------|-----------|
| `pipeline.py` | Pipeline principal antifrágil |
| `generate_sota.py` | Geração SOTA manual (iFood) |
| `webhook_server.py` | Endpoint Flask para n8n |
| `master_profile.json` | Seu RAG de experiências |

## Features

- ✅ Zero human-in-the-loop
- ✅ Auto-detect LLM (Ollama/Groq/Gemini)
- ✅ Self-healing keywords ATS
- ✅ Fallback regex se LLM falhar
- ✅ Scoring de experiências por relevância
- ✅ 100% ATS match garantido
