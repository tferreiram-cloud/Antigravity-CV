# ANTIGRAVITY TAILOR - PLANO ESTRATÉGICO (PLAN.md)

**CTO & Arquiteto-Chefe**: Antigravity Agent  
**Última Atualização**: 2026-02-02  
**Status**: ✅ FASE MVP EM ANDAMENTO

---

## 📍 VISÃO GERAL DO PROJETO

**Objetivo**: Sistema antifrágil de geração de currículos taylor-made usando **IA Generativa real** (não blocos Lego de JavaScript). O pipeline:
1. Master CV como **banco de dados RAG** de experiências STAR
2. Scraper inteligente que busca vagas alinhadas ao perfil
3. Engine de tailoring com LLM que **sintetiza** narrativas (não apenas seleciona)
4. Storage organizado de CVs gerados para envio

---

## 🔍 ANÁLISE DE ESTADO ATUAL

### O que já existe (Inventário)

| Componente | Arquivo(s) | Status | Avaliação |
|------------|-----------|--------|-----------|
| Master CV Database | `master_profile_v8.json` | ✅ Maduro | 986 linhas, 15 headlines, STAR completo |
| Pipeline Principal | `pipeline.py`, `full_pipeline.py` | ✅ Funcional | Antifrágil com fallback LLM |
| Tailoring Engine | `engine/tailor_engine.py` | ✅ Real AI | Gemini integration, prompts STAR |
| Web UI | `app.py` + `web/` | ✅ Flask | 19 endpoints, CORS enabled |
| Scraper | `scraper.py` | ⚠️ Parcial | LinkedIn + Gupy, mas sem filtro inteligente |
| Output Storage | `output/` | ✅ Funcional | 46 CVs gerados (HTML + PDF) |
| Jobs Storage | `jobs/` | ✅ Funcional | 30 vagas scraped |

### Gaps Identificados (AIM: Impact)

| Gap | Impact se resolvido | Prioridade |
|-----|---------------------|------------|
| Scraper não filtra por match com perfil | CVs irrelevantes, esforço desperdiçado | 🔴 ALTA |
| Sem storage persistente centralizado | CVs espalhados, difícil tracking | 🟡 MÉDIA |
| Dependência alta de Gemini API | Custo acumulativo em escala | 🟡 MÉDIA |
| Falta UI de gestão de CVs enviados | Tracking manual | 🟢 BAIXA |

---

## 📋 ROADMAP MVP (AIM Methodology)

### Phase 1: Smart Scraper Filter [CONCLUÍDO ✅]
- **Objetivo**: Filtrar ruído e focar em vagas de alto match (Product/AI).
- **Entregáveis**:
    - [x] Integração com JobSpy (Substituindo scraper legado).
    - [x] Engine de Matching (Jaccard Weighted).
    - [x] Filtro dinâmico por match score (Threshold: 0.30).
    - [x] API de estatísticas de matching.
- Tempo de review por vaga: <2min

**Implementação**:
```python
# scraper.py - Adicionar
def match_job_to_profile(job: Job, master_cv: dict) -> float:
    """Retorna score de match 0-1 entre vaga e perfil"""
    # Extrai keywords da vaga
    job_keywords = extract_keywords_ats(job.description)
    # Compara com skills do master CV
    profile_skills = master_cv.get('skills', {})
    # Score = intersection / union
    return calculate_jaccard_similarity(job_keywords, profile_skills)
```

### FASE 2: OLLAMA LOCAL FIRST 🟡 PRIORIDADE MÉDIA

**Action**: Configurar Ollama como LLM primário para processamento de dados (keyword extraction, scoring). Gemini apenas para synthesis de alta complexidade.

**Impact**:
- Custo zero para 80% das operações
- Latência reduzida (local)
- Fallback chain: Ollama → Gemini Free → Groq

**Metric**:
- ≥80% das chamadas LLM executadas localmente
- Custo mensal de API: <$5

**Implementação**:
```python
# core/config.py - Adicionar
LLM_CHAIN = [
    {"name": "ollama", "model": "llama3.2", "for": ["keywords", "scoring"]},
    {"name": "gemini", "model": "gemini-1.5-flash", "for": ["synthesis"]},
]
```

### FASE 3: CV WAREHOUSE 🟡 PRIORIDADE MÉDIA

**Action**: Implementar sistema de storage com metadata para tracking de CVs gerados.

**Impact**:
- Histórico completo de CVs por vaga
- Status: Gerado → Enviado → Feedback
- Analytics: qual headline/summary converte melhor

**Metric**:
- 100% dos CVs com metadata completa
- Query time: <100ms

**Implementação**:
```
output/
├── index.json          # Índice de todos CVs
├── [company]_[date]/
│   ├── resume.pdf
│   ├── resume.html
│   └── metadata.json   # job_url, match_score, status, sent_at
```

### FASE 4: DASHBOARD DE TRACKING 🟢 PRIORIDADE BAIXA

**Action**: Adicionar UI para visualizar e gerenciar CVs enviados.

**Impact**:
- Visão consolidada de candidaturas
- Tracking de conversão por empresa/headline

**Metric**:
- Tempo para consultar status: <5s
- N/A até MVP validado

---

## ⚙️ STACK TÉCNICA APROVADA

### LLM Hierarchy (Custo-Eficiência)

| Tier | Provider | Use Case | Custo |
|------|----------|----------|-------|
| 1 | Ollama (Local) | Keywords, Scoring, Filtering | $0 |
| 2 | Gemini 1.5 Flash | Synthesis, Tailoring | Free Tier |
| 3 | Groq | Fallback se Gemini offline | Free Tier |
| 4 | GPT-4 | Raciocínio complexo (pós-MVP) | Pago |

### Self-Healing Loop (Já Implementado ✅)

```
[Job Input] → [LLM Extract Keywords]
     ↓ (se falhar)
[Regex Fallback]
     ↓
[Match vs Master CV]
     ↓ (se score < 80%)
[Self-Heal: Adjust Keywords]
     ↓
[Generate CV]
     ↓ (se ATS < 80%)
[Iterate: Add missing keywords]
```

---

## 🛡️ GOVERNANÇA

### Validação Real AI (Checklist)

Antes de qualquer deploy, verificar:

- [ ] CV gerado usa **síntese generativa**, não concatenação
- [ ] Bullets são reescritos mantendo fatos STAR originais
- [ ] Summary é único para cada vaga (não template fixo)
- [ ] Keywords ATS são bridge-the-gap (mencionam skills implícitas)

### Refactor Request Protocol

Se Back-end ou Front-end entregar código que:
1. Usa seleção hardcoded em vez de LLM synthesis
2. Não implementa fallback chain
3. Expõe API keys no código
4. Não valida inputs

→ Emitir `REFACTOR REQUEST` com:
```
ERROR_TYPE: Real AI violation / Security / Missing fallback
FILE: [path]
LINE: [n]
EXPECTED: [behavior]
ACTUAL: [behavior]
```

---

## 📊 MÉTRICAS DE SUCESSO MVP

| Métrica | Target | Atual |
|---------|--------|-------|
| CVs gerados automaticamente | 10+/semana | 46 total |
| Match score médio | ≥75% | TBD |
| Tempo por CV | <2min | ~3min |
| Custo LLM/mês | <$5 | ~$0 (Gemini Free) |
| Interviews obtidas | ≥2/mês | TBD |

---

## 🚀 PRÓXIMOS PASSOS IMEDIATOS

1. **[ESTA SPRINT]** Implementar Smart Scraper Filter (Fase 1)
2. **[PRÓXIMA]** Configurar Ollama local + fallback chain
3. **[BACKLOG]** CV Warehouse com metadata tracking
4. **[FUTURE]** Dashboard de candidaturas

---

## 📝 CHANGELOG

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-02-02 | Criação inicial do PLAN.md | CTO Agent |

---

> **Nota**: Este documento é a single source of truth para decisões arquiteturais. Qualquer mudança significativa deve ser documentada aqui antes de implementação.
