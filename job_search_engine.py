#!/usr/bin/env python3
"""
ANTIGRAVITY JOB SEARCH ENGINE v2.0
==================================
Powered by JobSpy - Multi-source job aggregator.
Replaces legacy scraper.py with resilient job board scraping.

Usage:
    python job_search_engine.py --query "Product Manager AI" --location "Brazil"
"""

import json
import sys
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
import warnings

# Suppress version warnings - we handle compatibility manually
warnings.filterwarnings("ignore")

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    from jobspy import scrape_jobs
    JOBSPY_AVAILABLE = True
except ImportError as e:
    JOBSPY_AVAILABLE = False
    # If not in path, try adding current dir if jobspy was cloned here
    if (PROJECT_ROOT / "temp_jobspy").exists():
        sys.path.insert(0, str(PROJECT_ROOT / "temp_jobspy"))
        try:
            from jobspy import scrape_jobs
            JOBSPY_AVAILABLE = True
        except:
            pass
    if not JOBSPY_AVAILABLE:
        print(f"⚠️ JobSpy not available via pip or local clone: {e}")

from engine.matcher_utils import match_job_to_profile, SCRAPER_MATCH_THRESHOLD


# ============== CONFIG ==============

OUTPUT_DIR = PROJECT_ROOT / "jobs"
OUTPUT_FILE = OUTPUT_DIR / "scraped_jobs.json"

DEFAULT_SEARCH_TERMS = [
    "Product Manager AI",
    "Product Manager Generative AI", 
    "GTM Manager",
    "Growth Manager AI"
]

DEFAULT_COUNTRIES = {
    "linkedin": None,  # LinkedIn doesn't need country code
    "indeed": "Brazil",
    "glassdoor": "Brazil"
}


# ============== SELF-HEALING ENGINE ==============

class SelfHealingJobSearch:
    """
    Gold Standard Job Search Engine.
    Respects site-specific limitations (Indeed/LinkedIn) and implements
    a robust self-healing loop with query broadening and proxy/UA rotation.
    """
    
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
    ]

    def __init__(self):
        self.output_dir = OUTPUT_DIR
        self.output_file = OUTPUT_FILE
        self.output_dir.mkdir(exist_ok=True)

    def _validate_job(self, job: Dict) -> bool:
        """Checks if a job has minimal required data and isn't a duplicate/trash."""
        required = ['title', 'company', 'description', 'url']
        has_required = all(job.get(k) and len(str(job.get(k))) > 1 for k in required)
        
        # Quality filter: description must have meat
        if has_required and len(job['description']) < 200:
            return False
            
        return has_required

    def _get_site_specific_kwargs(self, site: str, base_kwargs: Dict) -> Dict:
        """
        Handles JobSpy/Board limitations. 
        Indeed/LinkedIn only allow ONE from specific lists.
        """
        kwargs = base_kwargs.copy()
        kwargs["site_name"] = [site]
        
        if site == "indeed":
            # Indeed: Only one from [hours_old, (job_type & is_remote), easy_apply]
            if kwargs.get("is_remote") or kwargs.get("job_type"):
                kwargs.pop("hours_old", None)
                kwargs.pop("easy_apply", None)
            elif kwargs.get("hours_old"):
                kwargs.pop("is_remote", None)
                kwargs.pop("job_type", None)
                kwargs.pop("easy_apply", None)
        
        elif site == "linkedin":
            # LinkedIn: Only one from [hours_old, easy_apply]
            if kwargs.get("hours_old"):
                kwargs.pop("easy_apply", None)
                
        return kwargs

    def search_with_retry(
        self,
        query: str,
        location: str = "Brazil",
        sites: List[str] = None,
        max_retries: int = 3,
        **kwargs
    ) -> Dict:
        """
        Gold Standard Search Loop.
        1. Explores queries (Advanced Indeed syntax support)
        2. Respects API limitations per board
        3. Self-heals by broadening search terms
        """
        sites = sites or ["linkedin", "indeed", "glassdoor"]
        current_query = query
        all_matched = []
        all_discarded = []
        search_stats = []
        
        print(f"\n🌟 [GOLD STANDARD] Iniciando Antigravity Search: '{query}'")
        
        for attempt in range(max_retries):
            print(f"   🔄 Tentativa {attempt + 1}/{max_retries} (UA Rotation)...")
            ua = self.USER_AGENTS[attempt % len(self.USER_AGENTS)]
            
            base_kwargs = {
                "search_term": current_query,
                "location": location,
                "results_wanted": kwargs.get("results_wanted", 20),
                "hours_old": kwargs.get("hours_old", 72),
                "country_indeed": "brazil",
                "linkedin_fetch_description": True,
                "description_format": "markdown",
                "user_agent": ua,
                "verbose": 0
            }
            
            if kwargs.get("is_remote"): base_kwargs["is_remote"] = True
            if kwargs.get("job_type"): base_kwargs["job_type"] = kwargs["job_type"]

            # Scraping per site to avoid parameter collisions
            current_attempt_jobs = []
            
            for site in sites:
                try:
                    site_kwargs = self._get_site_specific_kwargs(site, base_kwargs)
                    print(f"      📡 Scraping {site.upper()}...")
                    df = scrape_jobs(**site_kwargs)
                    
                    if not df.empty:
                        res = self._process_dataframe(df, kwargs.get("threshold", SCRAPER_MATCH_THRESHOLD))
                        current_attempt_jobs.extend(res["jobs"])
                        all_discarded.extend(res["discarded"])
                        print(f"      ✅ {site.upper()}: {len(res['jobs'])} matches found.")
                    else:
                        print(f"      ⚠️ {site.upper()}: No results.")
                        
                except Exception as e:
                    print(f"      ❌ {site.upper()} Error: {e}")

            # Self-Healing: If 0 matches, broaden query
            if not current_attempt_jobs and attempt < max_retries - 1:
                print(f"   ⚠️ Sem matches. Aplicando Self-Healing: Broadening Query...")
                # Remove quotes or specific qualifiers
                broad_query = current_query.replace('"', "").split(" OR ")[0]
                if broad_query == current_query and " " in current_query:
                    # Remove last word
                    current_query = " ".join(current_query.split(" ")[:-1])
                else:
                    current_query = broad_query
                print(f"   💡 Nova Query: '{current_query}'")
                continue
            
            # Filter and deduplicate
            for job in current_attempt_jobs:
                if self._validate_job(job):
                    # Dedup by URL
                    if not any(j['url'] == job['url'] for j in all_matched):
                        all_matched.append(job)
                else:
                    all_discarded.append(job)
            
            if all_matched: break

        stats = {
            "query": query,
            "final_query": current_query,
            "attempts": attempt + 1,
            "total_found": len(all_matched) + len(all_discarded),
            "total_matched": len(all_matched),
            "match_rate": len(all_matched) / (len(all_matched) + len(all_discarded)) if (all_matched or all_discarded) else 0
        }
        
        print(f"\n🏆 BUSCA CONCLUÍDA: {stats['total_matched']} vagas filtradas com Gold Standard.")
        return {"jobs": all_matched, "discarded": all_discarded, "stats": stats}

    def _process_dataframe(self, df: pd.DataFrame, threshold: float) -> Dict:
        """Converts DataFrame to Job dicts and performs matching."""
        matched_jobs = []
        discarded_jobs = []
        safe_threshold = float(threshold) if threshold is not None else SCRAPER_MATCH_THRESHOLD
        
        # Clean NaN values which break JSON
        import numpy as np
        df = df.replace({np.nan: None})
        
        for idx, row in df.iterrows():
            job_data = {
                "id": f"js_{row.get('id', idx)}_{datetime.now().strftime('%H%M%S')}",
                "title": str(row.get("title", "N/A")),
                "company": str(row.get("company", row.get("company_name", "N/A"))),
                "location": str(row.get("location", "N/A")),
                "description": str(row.get("description", "")),
                "url": str(row.get("job_url", "")),
                "source": str(row.get("site", "unknown")),
                "scraped_at": datetime.now().isoformat(),
                "job_type": str(row.get("job_type", "")),
                "status": "todo"
            }
            
            if job_data["description"] and len(job_data["description"]) > 100:
                m_result = match_job_to_profile(job_data["description"])
                job_data["match_score"] = m_result.score
                job_data["matched_keywords"] = m_result.matched_keywords
                job_data["missing_keywords"] = m_result.missing_keywords
                
                if m_result.score >= safe_threshold:
                    matched_jobs.append(job_data)
                else:
                    discarded_jobs.append(job_data)
            else:
                job_data["match_score"] = 0.0
                discarded_jobs.append(job_data)
                
        return {"jobs": matched_jobs, "discarded": discarded_jobs, "stats": {}}

# ============== CLI & INTEGRATION ==============

def search_jobs(**kwargs) -> Dict:
    engine = SelfHealingJobSearch()
    # Normalize keys from app.py
    query = kwargs.get("search_term", kwargs.get("query", "Product Manager AI"))
    return engine.search_with_retry(
        query=query,
        location=kwargs.get("location", "Brazil"),
        sites=kwargs.get("sites"),
        results_wanted=kwargs.get("results", kwargs.get("results_wanted", 20)),
        hours_old=kwargs.get("hours", kwargs.get("hours_old", 72)),
        is_remote=kwargs.get("is_remote", kwargs.get("remote", False)),
        threshold=kwargs.get("min_match_threshold", kwargs.get("threshold", SCRAPER_MATCH_THRESHOLD))
    )

def save_jobs(jobs: List[Dict], append: bool = True) -> Path:
    """Save jobs to JSON file, optionally appending to existing."""
    if not OUTPUT_FILE.parent.exists():
        OUTPUT_FILE.parent.mkdir(parents=True)
        
    existing_jobs = []
    if append and OUTPUT_FILE.exists():
        try:
            with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
                existing_jobs = json.load(f)
        except:
            existing_jobs = []
    
    # Merge without duplicates (by URL)
    existing_urls = {j.get("url") for j in existing_jobs}
    new_jobs = [j for j in jobs if j.get("url") not in existing_urls]
    
    all_jobs = existing_jobs + new_jobs
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_jobs, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 Saved {len(new_jobs)} new jobs (total: {len(all_jobs)}) to {OUTPUT_FILE}")
    return OUTPUT_FILE


def run_full_search(
    queries: List[str] = None,
    location: str = "Brazil",
    save: bool = True
) -> Dict:
    """Run search for multiple queries and aggregate results."""
    queries = queries or DEFAULT_SEARCH_TERMS
    all_results = []
    
    for q in queries:
        res = search_jobs(query=q, location=location)
        all_results.extend(res["jobs"])
    
    if save:
        save_jobs(all_results)
    
    return {"jobs": all_results}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Antigravity Gold Standard Search v2.1")
    parser.add_argument("-q", "--query", type=str, default="Product Manager AI")
    parser.add_argument("-l", "--location", type=str, default="Brazil")
    parser.add_argument("--sites", type=str, nargs="+", default=["linkedin", "indeed", "glassdoor"])
    parser.add_argument("--results", type=int, default=20)
    parser.add_argument("--hours", type=int, default=72)
    parser.add_argument("--threshold", type=float, default=None)
    parser.add_argument("--full", action="store_true")
    
    args = parser.parse_args()
    
    if args.full:
        result = run_full_search(location=args.location)
    else:
        result = search_jobs(
            query=args.query,
            location=args.location,
            sites=args.sites,
            results=args.results,
            hours=args.hours,
            threshold=args.threshold
        )
        save_jobs(result["jobs"])
    
    print("\n📤 Final Stats:")
    print(json.dumps(result.get("stats", {}), indent=2))

