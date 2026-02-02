import sys
import json
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

from core.models import Language
from engine import create_job_from_scrape, CVMatcher, MasterCV

def test_match():
    print("Testing match logic...")
    
    # Mock data directly from frontend payload structure
    job_data = {
        "title": "Senior Product Manager",
        "company": "Tech Corp",
        "description": "We are looking for a Senior PM with experience in AI, Python, and GTM strategy. Must have 5+ years of experience leading teams.",
        "url": "http://example.com/job"
    }
    
    try:
        # Step 1: Create Job
        print("Creating job...")
        job, validation = create_job_from_scrape(
            title=job_data.get('title', ''),
            company=job_data.get('company', ''),
            description=job_data.get('description', ''),
            url=job_data.get('url', ''),
            source='api'
        )
        print(f"Job created: {job.id} (Valid: {validation.is_valid})")
        
        # Step 2: Load Master CV
        print("Loading Master CV...")
        master = MasterCV.load(language=Language.PT, junior_mode=False)
        print("Master CV loaded.")
        
        # Step 3: Match
        print("Running Matcher...")
        matcher = CVMatcher(master)
        match_result = matcher.match(job)
        
        print(f"Match success! Score: {match_result.total_percentage}%")
        print(f"Headline: {match_result.selected_headline}")
        print(f"Experiences: {len(match_result.selected_experiences)}")
        
    except Exception as e:
        print(f"\n❌ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_match()
