import sys
import json
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

from core.models import Job, StrategicPlan
from engine.strategy import StrategicAnalyzer
from app import load_scraped_jobs

def test_strategy():
    print("Testing Strategy Analysis logic...")
    
    # 1. Load a real job from the cleaned file
    jobs = load_scraped_jobs()
    if not jobs:
        print("❌ No jobs found in scraped_jobs.json")
        return
        
    job_dict = jobs[0]
    print(f"Loaded Job: {job_dict['title']} at {job_dict['company']}")
    
    # 2. Convert to Job object
    try:
        job = Job.from_dict(job_dict)
        print("✅ Job object created successfully")
    except Exception as e:
        print(f"❌ Error creating Job object: {e}")
        return
        
    # 3. Analyze
    try:
        analyzer = StrategicAnalyzer(debug=True)
        plan = analyzer.analyze(job)
        print("\n✅ Strategy Analysis Successful!")
        print(f"Ghost Notes: {len(plan.ghost_notes)}")
        print(f"Vulnerabilities: {len(plan.vulnerability_report)}")
        print(f"Narrative Shift: {plan.suggested_narrative_shift}")
    except Exception as e:
        print(f"❌ Error in StrategicAnalyzer: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_strategy()
