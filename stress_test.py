#!/usr/bin/env python3
"""
STRESS TEST - LinkedIn Marketing Jobs
Busca vagas das últimas 24h e gera currículo tailor-made para cada uma
"""

import re
import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import List, Dict
import time

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    import subprocess
    subprocess.run(["pip", "install", "requests", "beautifulsoup4", "-q"])
    import requests
    from bs4 import BeautifulSoup

from tailor_engine import generate_tailored_resume

BASE_DIR = Path(__file__).parent
JOBS_DIR = BASE_DIR / "jobs"
JOBS_DIR.mkdir(exist_ok=True)
OUTPUT_DIR = BASE_DIR / "output"


class LinkedInScraper24h:
    """Scraper LinkedIn focado em vagas das últimas 24h"""
    
    BASE_URL = "https://www.linkedin.com/jobs/search"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9,pt-BR;q=0.8"
        })
    
    def search(self, query: str, location: str = "Brazil", limit: int = 10) -> List[Dict]:
        """Busca vagas das últimas 24h"""
        jobs = []
        
        params = {
            "keywords": query,
            "location": location,
            "f_TPR": "r86400",  # Últimas 24 horas
            "position": 1,
            "pageNum": 0,
            "sortBy": "DD"  # Date descending
        }
        
        print(f"\n🔍 Buscando: '{query}' em {location} (últimas 24h)")
        
        try:
            response = self.session.get(self.BASE_URL, params=params, timeout=30)
            print(f"   Status: {response.status_code}")
            
            if response.status_code != 200:
                return jobs
            
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Encontra job cards
            job_cards = soup.find_all("div", class_="base-card")[:limit]
            print(f"   Cards encontrados: {len(job_cards)}")
            
            for i, card in enumerate(job_cards):
                try:
                    title_elem = card.find("h3", class_="base-search-card__title")
                    company_elem = card.find("h4", class_="base-search-card__subtitle")
                    location_elem = card.find("span", class_="job-search-card__location")
                    link_elem = card.find("a", class_="base-card__full-link")
                    
                    if not all([title_elem, company_elem]):
                        continue
                    
                    title = title_elem.text.strip()
                    company = company_elem.text.strip()
                    loc = location_elem.text.strip() if location_elem else "Remote"
                    url = link_elem.get("href", "").split("?")[0] if link_elem else ""
                    
                    # ID único
                    job_id = hashlib.md5(f"{title}{company}".encode()).hexdigest()[:10]
                    
                    # Busca descrição
                    print(f"   [{i+1}] Buscando: {title[:40]}...")
                    description = self._get_description(url) if url else f"Vaga de {title} na {company}"
                    
                    # Delay gentil
                    time.sleep(0.5)
                    
                    job = {
                        "id": f"li_{job_id}",
                        "title": title,
                        "company": company,
                        "location": loc,
                        "url": url,
                        "description": description,
                        "scraped_at": datetime.now().isoformat()
                    }
                    jobs.append(job)
                    
                    # Salva como arquivo
                    self._save_job(job)
                    
                except Exception as e:
                    print(f"   ⚠️ Erro no card: {e}")
                    continue
            
        except Exception as e:
            print(f"   ❌ Erro geral: {e}")
        
        return jobs
    
    def _get_description(self, url: str) -> str:
        """Extrai descrição da vaga"""
        try:
            resp = self.session.get(url, timeout=20)
            soup = BeautifulSoup(resp.text, "html.parser")
            
            # Múltiplos seletores
            for selector in ["show-more-less-html__markup", "description__text", "job-details"]:
                elem = soup.find(class_=selector)
                if elem:
                    text = elem.get_text(separator="\n", strip=True)
                    if len(text) > 100:
                        return text[:3000]  # Limita
            
        except Exception as e:
            pass
        
        return "Descrição não disponível via scraping. Contém requisitos padrão de marketing."
    
    def _save_job(self, job: Dict):
        """Salva job como JSON e TXT"""
        job_path = JOBS_DIR / f"{job['id']}.json"
        with open(job_path, "w", encoding="utf-8") as f:
            json.dump(job, f, indent=2, ensure_ascii=False)
        
        txt_path = JOBS_DIR / f"{job['id']}.txt"
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(f"{job['title']} - {job['company']}\n\n")
            f.write(job['description'])


def run_stress_test(query: str = "marketing", limit: int = 5):
    """
    Executa stress test completo:
    1. Scrape vagas das últimas 24h
    2. Gera currículo tailor-made para cada
    """
    
    print("\n" + "=" * 70)
    print("🚀 STRESS TEST - LinkedIn Marketing Jobs (24h)")
    print("=" * 70)
    
    results = {
        "jobs_found": 0,
        "resumes_generated": 0,
        "errors": [],
        "output_files": []
    }
    
    # 1. SCRAPING
    print("\n📋 FASE 1: SCRAPING LINKEDIN")
    print("-" * 50)
    
    scraper = LinkedInScraper24h()
    jobs = scraper.search(query, location="Brazil", limit=limit)
    results["jobs_found"] = len(jobs)
    
    if not jobs:
        print("\n⚠️ Nenhuma vaga encontrada no scraping.")
        print("   Usando vagas de exemplo salvas...")
        
        # Fallback para arquivos existentes
        for f in list(JOBS_DIR.glob("*.json"))[:limit]:
            try:
                with open(f) as jf:
                    jobs.append(json.load(jf))
            except:
                pass
    
    print(f"\n✅ {len(jobs)} vagas para processar")
    
    # 2. GERAÇÃO DE CURRÍCULOS
    print("\n📄 FASE 2: GERANDO CURRÍCULOS TAILOR-MADE")
    print("-" * 50)
    
    for i, job in enumerate(jobs, 1):
        print(f"\n[{i}/{len(jobs)}] {job['title'][:45]}")
        print(f"        @ {job['company']}")
        
        try:
            pdf_path, networking_msg = generate_tailored_resume(
                job_description=job['description'],
                company=job['company'],
                role=job['title'],
                output_name=f"stress_{job['id']}"
            )
            
            results["resumes_generated"] += 1
            results["output_files"].append({
                "job": job['title'],
                "company": job['company'],
                "pdf": pdf_path,
                "message": networking_msg[:100] + "..."
            })
            
        except Exception as e:
            print(f"   ❌ Erro: {e}")
            results["errors"].append(f"{job['id']}: {e}")
    
    # 3. RELATÓRIO
    print("\n" + "=" * 70)
    print("📊 RELATÓRIO STRESS TEST")
    print("=" * 70)
    print(f"""
   Vagas encontradas:     {results['jobs_found']}
   Currículos gerados:    {results['resumes_generated']}
   Erros:                 {len(results['errors'])}
   Taxa de sucesso:       {results['resumes_generated']/max(len(jobs),1)*100:.0f}%
""")
    
    if results['output_files']:
        print("📁 ARQUIVOS GERADOS:")
        for out in results['output_files']:
            print(f"   • {out['company']}: {out['job'][:40]}")
            print(f"     PDF: {out['pdf']}")
    
    print("\n" + "=" * 70)
    
    return results


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Stress Test LinkedIn Jobs")
    parser.add_argument("-q", "--query", default="marketing manager", help="Query de busca")
    parser.add_argument("-l", "--limit", type=int, default=5, help="Limite de vagas")
    
    args = parser.parse_args()
    
    run_stress_test(args.query, args.limit)
