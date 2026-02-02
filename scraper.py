#!/usr/bin/env python3

"""
Job Scraper - Busca vagas automaticamente
Suporta: LinkedIn, Gupy, Glassdoor (via scraping ou API)
v2.0 - Com Smart Matching Filter
"""

import re
import json
import hashlib
import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict, field
from urllib.parse import quote_plus

try:
    import requests
    from bs4 import BeautifulSoup
    import pandas as pd
    from jobspy import scrape_jobs as jobspy_scrape
    SCRAPER_AVAILABLE = True
except ImportError as e:
    SCRAPER_AVAILABLE = False
    _IMPORT_ERROR = str(e)
    # User must run: pip install requests beautifulsoup4 python-jobspy pandas
    import warnings
    warnings.warn(
        f"Scraper dependencies not installed: {e}. "
        "Run: pip install requests beautifulsoup4 python-jobspy pandas"
    )

# Smart Matching
from engine.matcher_utils import match_job_to_profile, SCRAPER_MATCH_THRESHOLD


BASE_DIR = Path(__file__).parent
JOBS_DIR = BASE_DIR / "jobs"
JOBS_DIR.mkdir(exist_ok=True)


@dataclass
class Job:
    """Estrutura de uma vaga"""
    id: str
    title: str
    company: str
    location: str
    description: str
    url: str
    source: str
    scraped_at: str
    logo_url: Optional[str] = None
    salary_info: Optional[str] = None
    applied: bool = False
    resume_generated: bool = False
    keywords: List[str] = None
    match_score: float = 0.0
    matched_keywords: List[str] = field(default_factory=list)
    missing_keywords: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    def save(self):
        """Salva vaga como JSON"""
        path = JOBS_DIR / f"{self.id}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
        
        # Também salva descrição como txt para o pipeline
        txt_path = JOBS_DIR / f"{self.id}.txt"
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(f"{self.title} - {self.company}\n\n")
            f.write(self.description)
        
        return path



class JobSpyScraper:
    """Scraper robusto multi-fonte via JobSpy (LinkedIn, Indeed, Glassdoor)"""
    
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
    ]
    
    def search(self, 
               query: str, 
               location: str = "Brazil", 
               limit: int = 20,
               sources: List[str] = None) -> List[Job]:
        """Busca vagas usando JobSpy com tentativas e rotação de UA"""
        if not SCRAPER_AVAILABLE:
            print(f"   ⚠️ JobSpy não disponível: {_IMPORT_ERROR}")
            return []
            
        if sources is None:
            sources = ["linkedin", "indeed", "glassdoor"]
            
        jobs = []
        import random
        
        # Try with a random UA
        ua = random.choice(self.USER_AGENTS)
            
        try:
            print(f"   🚀 JobSpy: Buscando '{query}' em {sources}...")
            # JobSpy scrape_jobs returns a Pandas DataFrame
            jobs_df = jobspy_scrape(
                site_name=sources,
                search_term=query,
                location=location,
                results_wanted=limit,
                hours_old=168,  # last 7 days
                country_indeed='brazil',
                country_glassdoor='brazil',
                linkedin_fetch_description=True,
                description_format="markdown",
                offset=0
                # user_agent=ua # JobSpy handles this better internally often, but we can pass kwargs if needed
            )
            
            if jobs_df is None or jobs_df.empty:
                print("   ⚠️ JobSpy: Nenhum resultado encontrado.")
                return []
                
            for _, row in jobs_df.iterrows():
                # Generate unique ID
                job_url = row.get('job_url', '')
                job_id_hash = hashlib.md5(f"{row.get('title', '')}{row.get('company', '')}{job_url}".encode()).hexdigest()[:12]
                
                # Cleanup description (JobSpy usually provides it)
                description = row.get('description', '')
                if not isinstance(description, str):
                    description = ""
                
                if not description or len(description) < 50:
                    description = f"Vaga: {row.get('title')}\nEmpresa: {row.get('company')}\nLocal: {row.get('location')}\n\nDescrição não capturada automaticamente. Confira no link: {job_url}"

                job = Job(
                    id=f"{row.get('site', 'js')}_{job_id_hash}",
                    title=str(row.get('title', '')),
                    company=str(row.get('company', '')),
                    location=str(row.get('location', '')),
                    description=description,
                    url=job_url,
                    source=str(row.get('site', 'unknown')),
                    scraped_at=datetime.now().isoformat(),
                    logo_url=row.get('company_url_direct', None),
                    salary_info=f"{row.get('min_amount', '')} - {row.get('max_amount', '')} {row.get('currency', '')}" if row.get('min_amount') else None
                )
                jobs.append(job)
            
            return jobs
            
        except Exception as e:
            print(f"   ❌ Erro JobSpy: {e}")
            import traceback
            traceback.print_exc()
            return []


class GupyScraper:
    """Scraper para Gupy (principal ATS do Brasil)"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        })
    
    def search_company(self, company_slug: str, limit: int = 10) -> List[Job]:
        """Busca vagas de uma empresa específica no Gupy"""
        jobs = []
        
        api_url = f"https://{company_slug}.gupy.io/api/job"
        
        try:
            response = self.session.get(api_url, timeout=30)
            if response.status_code != 200:
                print(f"   ⚠️ Gupy {company_slug} retornou {response.status_code}")
                return jobs
            
            data = response.json()
            
            for item in data.get("data", [])[:limit]:
                job_id = f"gupy_{item.get('id', '')}"
                
                job = Job(
                    id=job_id,
                    title=item.get("name", ""),
                    company=company_slug,
                    location=item.get("city", "Remote"),
                    description=self._clean_description(item.get("description", "")),
                    url=f"https://{company_slug}.gupy.io/jobs/{item.get('id')}",
                    source="gupy",
                    scraped_at=datetime.now().isoformat()
                )
                jobs.append(job)
            
        except Exception as e:
            print(f"   ❌ Erro scraping Gupy {company_slug}: {e}")
        
        return jobs
    
    def _clean_description(self, html: str) -> str:
        """Remove HTML da descrição"""
        soup = BeautifulSoup(html, "html.parser")
        return soup.get_text(separator="\n", strip=True)


class JobAggregator:
    """Agregador de múltiplas fontes"""
    
    def __init__(self):
        self.jobspy = JobSpyScraper()
        self.gupy = GupyScraper()
    
    def search(self, 
               query: str, 
               location: str = "Brazil",
               gupy_companies: List[str] = None,
               limit_per_source: int = 10) -> List[Job]:
        """Busca vagas em múltiplas fontes"""
        
        all_jobs = []
        
        # JobSpy (LinkedIn, Indeed, Glassdoor)
        print(f"   🔍 Buscando no JobSpy (LI, Indeed, GD): '{query}'")
        jobspy_jobs = self.jobspy.search(query, location, limit_per_source)
        all_jobs.extend(jobspy_jobs)
        print(f"   ✓ JobSpy: {len(jobspy_jobs)} vagas encontradas")
        
        # Gupy (empresas específicas)
        if gupy_companies:
            for company in gupy_companies:
                print(f"   🔍 Buscando no Gupy: {company}")
                gupy_jobs = self.gupy.search_company(company, limit_per_source)
                all_jobs.extend(gupy_jobs)
                print(f"   ✓ Gupy {company}: {len(gupy_jobs)} vagas")
        
        # Filtra por query (apenas para Gupy, JobSpy já vem filtrado)
        query_lower = query.lower()
        filtered = []
        native_filtered_sources = ['linkedin', 'indeed', 'glassdoor', 'zip_recruiter']
        
        for j in all_jobs:
            if j.source in native_filtered_sources:
                filtered.append(j)
            elif query_lower in j.title.lower() or query_lower in j.description.lower():
                filtered.append(j)
        
        return filtered


def scrape_jobs(query: str = "Product Manager AI", 
                gupy_companies: List[str] = None,
                save: bool = True,
                filter_by_match: bool = True,
                min_match_threshold: float = None) -> Dict:
    """
    Função principal de scraping com Smart Matching Filter
    
    Args:
        query: Termo de busca
        gupy_companies: Lista de slugs Gupy (ex: ["ifood", "nubank", "mercadolivre"])
        save: Se deve salvar as vagas em arquivos
        filter_by_match: Se deve filtrar por match score
        min_match_threshold: Threshold mínimo (usa SCRAPER_MATCH_THRESHOLD se None)
    
    Returns:
        Dict com jobs, stats de matching
    """
    print("\n" + "=" * 60)
    print("🔎 JOB SCRAPER v2.0 - Smart Matching")
    print("=" * 60)
    
    threshold = min_match_threshold or SCRAPER_MATCH_THRESHOLD
    
    
    if gupy_companies is None:
        gupy_companies = [] # Disabled momentarily due to API changes: ["ifood", "nubank", "mercadolivre", "stone", "vtex"]
    
    
    aggregator = JobAggregator()
    raw_jobs = aggregator.search(query, gupy_companies=gupy_companies)
    
    print(f"\n📊 Analisando {len(raw_jobs)} vagas contra seu perfil...")
    
    # Calculate match score for each job
    matched_jobs = []
    discarded_jobs = []
    
    for job in raw_jobs:
        result = match_job_to_profile(job.description)
        job.match_score = result.score
        job.matched_keywords = result.matched_keywords
        job.missing_keywords = result.missing_keywords
        job.keywords = result.matched_keywords + result.missing_keywords
        
        if filter_by_match and result.score < threshold:
            discarded_jobs.append(job)
            print(f"   ✗ {job.title[:40]}... [{result.score:.0%}] DESCARTADA")
        else:
            matched_jobs.append(job)
            print(f"   ✓ {job.title[:40]}... [{result.score:.0%}]")
    
    print(f"\n📈 Resultado do Matching:")
    print(f"   ✅ Relevantes: {len(matched_jobs)} ({len(matched_jobs)/len(raw_jobs)*100:.0f}%)" if raw_jobs else "   Nenhuma vaga encontrada")
    print(f"   ❌ Descartadas: {len(discarded_jobs)}")
    print(f"   📏 Threshold: {threshold:.0%}")
    
    if save and matched_jobs:
        print("\n📁 Salvando vagas relevantes...")
        for job in matched_jobs:
            path = job.save()
            print(f"   ✓ {job.id}: {job.title[:50]}... [{job.match_score:.0%}]")
    
    print("\n" + "=" * 60)
    
    return {
        "jobs": matched_jobs,
        "discarded": discarded_jobs,
        "stats": {
            "total_found": len(raw_jobs),
            "total_matched": len(matched_jobs),
            "total_discarded": len(discarded_jobs),
            "match_rate": len(matched_jobs) / len(raw_jobs) if raw_jobs else 0,
            "threshold": threshold
        }
    }


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Job Scraper v2.0 - Smart Matching")
    parser.add_argument("-q", "--query", default="Product Manager AI", help="Termo de busca")
    parser.add_argument("-c", "--companies", nargs="*", default=None, help="Slugs Gupy (ex: ifood nubank)")
    parser.add_argument("-t", "--threshold", type=float, default=None, help="Threshold mínimo de match (0.0-1.0)")
    parser.add_argument("--no-filter", action="store_true", help="Não filtrar por match")
    
    args = parser.parse_args()
    
    result = scrape_jobs(
        args.query, 
        args.companies,
        filter_by_match=not args.no_filter,
        min_match_threshold=args.threshold
    )
    
    print(f"\n📋 Vagas salvas em: {JOBS_DIR}")
    print(f"\n🏆 Top vagas por match:")
    for job in sorted(result['jobs'], key=lambda j: j.match_score, reverse=True)[:5]:
        print(f"   • [{job.match_score:.0%}] {job.title} @ {job.company}")
