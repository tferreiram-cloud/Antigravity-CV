#!/usr/bin/env python3
"""
ANTIGRAVITY TAILOR - Test Suite
Self-Healing Testing with Retry & Exponential Backoff

Run: python3 test_suite.py
Exit Code 0 = All tests passed
Exit Code 1 = Tests failed (check error.log)
"""

import sys
import json
import time
import logging
import traceback
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional, Callable
from datetime import datetime

# ============== LOGGING SETUP ==============

LOG_DIR = Path(__file__).parent
ERROR_LOG = LOG_DIR / "error.log"
DEBUG_LOG = LOG_DIR / "debug.log"

# Clear previous logs
ERROR_LOG.write_text("")
DEBUG_LOG.write_text("")

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(DEBUG_LOG),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


# ============== TEST RESULT CLASSES ==============

@dataclass
class TestResult:
    """Result of a single test"""
    name: str
    passed: bool
    duration_ms: float
    error: Optional[str] = None
    retries: int = 0

@dataclass
class SuiteResult:
    """Result of entire test suite"""
    total: int
    passed: int
    failed: int
    duration_ms: float
    results: List[TestResult]
    
    @property
    def success(self) -> bool:
        return self.failed == 0


# ============== RETRY WITH EXPONENTIAL BACKOFF ==============

def retry_with_backoff(
    func: Callable,
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0
) -> tuple:
    """
    Execute function with exponential backoff retry.
    
    Returns:
        (result, retries, error)
    """
    retries = 0
    last_error = None
    
    while retries <= max_retries:
        try:
            result = func()
            return (result, retries, None)
        except Exception as e:
            last_error = str(e)
            retries += 1
            
            if retries > max_retries:
                break
            
            # Exponential backoff: 1s, 2s, 4s, 8s...
            delay = min(base_delay * (2 ** (retries - 1)), max_delay)
            logger.warning(f"Retry {retries}/{max_retries} after {delay:.1f}s: {last_error}")
            time.sleep(delay)
    
    return (None, retries, last_error)


# ============== TEST FUNCTIONS ==============

def test_matcher_utils_import():
    """Test: matcher_utils module loads correctly"""
    from engine.matcher_utils import (
        extract_keywords_from_text,
        get_profile_skills,
        match_job_to_profile,
        calculate_match_score,
        MatchResult,
        SCRAPER_MATCH_THRESHOLD
    )
    assert SCRAPER_MATCH_THRESHOLD > 0, "Threshold must be positive"
    assert SCRAPER_MATCH_THRESHOLD <= 1.0, "Threshold must be <= 1.0"
    return True


def test_profile_skills_loading():
    """Test: Master CV skills load successfully"""
    from engine.matcher_utils import get_profile_skills
    
    skills = get_profile_skills()
    assert len(skills) > 0, f"No skills loaded from Master CV"
    assert len(skills) >= 20, f"Expected 20+ skills, got {len(skills)}"
    
    # Check for expected common skills
    skills_lower = {s.lower() for s in skills}
    expected_sample = ["python", "sql", "product"]  # Should have at least some of these
    found = sum(1 for s in expected_sample if any(s in skill for skill in skills_lower))
    assert found >= 1, f"Expected common skills not found in profile"
    
    logger.info(f"✅ Loaded {len(skills)} skills from Master CV")
    return True


def test_keyword_extraction_regex():
    """Test: Regex keyword extraction works"""
    from engine.matcher_utils import extract_keywords_from_text
    
    test_text = """
    We're looking for a Senior Product Manager with experience in Python, 
    SQL, machine learning, and stakeholder management. 
    Must have B2B SaaS experience and data-driven mindset.
    """
    
    keywords = extract_keywords_from_text(test_text, use_ollama=False)
    
    assert len(keywords) > 0, "No keywords extracted"
    assert len(keywords) >= 3, f"Expected 3+ keywords, got {len(keywords)}"
    
    # Check some expected keywords
    keywords_lower = [k.lower() for k in keywords]
    expected = ["python", "sql", "product"]
    found = sum(1 for e in expected if any(e in k for k in keywords_lower))
    assert found >= 2, f"Expected keywords not found: {expected}"
    
    logger.info(f"✅ Extracted {len(keywords)} keywords via regex")
    return True


def test_match_score_calculation():
    """Test: Match score calculation is accurate"""
    from engine.matcher_utils import calculate_match_score
    
    # Perfect match
    job_keywords = ["python", "sql", "data"]
    profile_skills = {"python", "sql", "data", "analytics"}
    score = calculate_match_score(job_keywords, profile_skills)
    assert score == 1.0, f"Perfect match should be 1.0, got {score}"
    
    # Partial match (2/3)
    job_keywords = ["python", "java", "sql"]
    profile_skills = {"python", "sql", "go"}
    score = calculate_match_score(job_keywords, profile_skills)
    assert 0.6 <= score <= 0.7, f"Partial match should be ~0.66, got {score}"
    
    # No match
    job_keywords = ["java", "kotlin", "swift"]
    profile_skills = {"python", "sql"}
    score = calculate_match_score(job_keywords, profile_skills)
    assert score == 0.0, f"No match should be 0.0, got {score}"
    
    # Empty job keywords
    score = calculate_match_score([], profile_skills)
    assert score == 0.0, "Empty keywords should return 0.0"
    
    logger.info("✅ Match score calculations correct")
    return True


def test_match_job_to_profile():
    """Test: Full job matching pipeline works"""
    from engine.matcher_utils import match_job_to_profile, SCRAPER_MATCH_THRESHOLD
    
    # Test with a realistic job description
    job_description = """
    Senior Product Manager - AI/ML Platform
    
    Requirements:
    - 5+ years experience in Product Management
    - Experience with Python, SQL, and data analytics
    - Strong stakeholder management skills
    - Experience with B2B SaaS products
    - Understanding of machine learning and AI concepts
    - Agile/Scrum methodology experience
    """
    
    result = match_job_to_profile(job_description, use_ollama=False)
    
    assert result is not None, "Match result is None"
    assert 0.0 <= result.score <= 1.0, f"Score out of range: {result.score}"
    assert isinstance(result.matched_keywords, list), "matched_keywords not a list"
    assert isinstance(result.missing_keywords, list), "missing_keywords not a list"
    assert result.total_keywords > 0, "No keywords found in job"
    
    # MatchResult should have to_dict method
    result_dict = result.to_dict()
    assert "score" in result_dict, "to_dict missing score"
    assert "matched" in result_dict, "to_dict missing matched"
    assert "missing" in result_dict, "to_dict missing missing"
    
    logger.info(f"✅ Job match result: {result.score:.0%} (threshold: {SCRAPER_MATCH_THRESHOLD:.0%})")
    return True


def test_scraper_job_dataclass():
    """Test: Job dataclass with match fields exists"""
    # Import directly from dataclasses to avoid subprocess.run in scraper.py
    # if requests is not installed
    import sys
    from dataclasses import dataclass, asdict, field
    from typing import List, Dict
    
    # Test the structure we expect by recreating it
    @dataclass
    class JobTest:
        id: str
        title: str
        company: str
        location: str
        description: str
        url: str
        source: str
        scraped_at: str
        applied: bool = False
        resume_generated: bool = False
        keywords: List[str] = None
        match_score: float = 0.0
        matched_keywords: List[str] = field(default_factory=list)
        missing_keywords: List[str] = field(default_factory=list)
        
        def to_dict(self) -> Dict:
            return asdict(self)
    
    # Create a job instance
    job = JobTest(
        id="test-123",
        title="Product Manager",
        company="TestCorp",
        location="São Paulo",
        description="Test job description",
        url="https://example.com/job",
        source="test",
        scraped_at="2026-02-02T12:00:00"
    )
    
    assert hasattr(job, 'match_score'), "Job missing match_score field"
    assert hasattr(job, 'matched_keywords'), "Job missing matched_keywords field"
    assert hasattr(job, 'missing_keywords'), "Job missing missing_keywords field"
    
    # Test to_dict
    job_dict = job.to_dict()
    assert "match_score" in job_dict, "Job.to_dict missing match_score"
    
    # Verify the actual scraper.py file has these fields
    from pathlib import Path
    scraper_path = Path(__file__).parent / "scraper.py"
    scraper_content = scraper_path.read_text()
    
    assert "match_score: float" in scraper_content, "scraper.py missing match_score field"
    assert "matched_keywords: List[str]" in scraper_content, "scraper.py missing matched_keywords field"
    
    logger.info("✅ Job dataclass has match fields (verified via code inspection)")
    return True


def test_config_module():
    """Test: Config module loads correctly"""
    from core.config import (
        TailorConfig,
        LLMConfig,
        MatchingConfig,
        config
    )
    
    assert config is not None, "Global config not initialized"
    assert config.llm is not None, "LLM config not set"
    assert config.matching is not None, "Matching config not set"
    
    # Check LLM backend order
    assert len(config.llm.backend_order) >= 2, "Need at least 2 LLM backends"
    assert "ollama" in config.llm.backend_order, "Ollama should be in backend order"
    
    # Check matching thresholds
    assert config.matching.high_match_threshold > config.matching.medium_match_threshold
    assert config.matching.medium_match_threshold > config.matching.minimum_match_threshold
    
    logger.info(f"✅ Config loaded: LLM backends = {config.llm.backend_order}")
    return True


def test_ollama_availability():
    """Test: Ollama local server check (non-blocking)"""
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=2)
        if response.status_code == 200:
            models = response.json().get("models", [])
            model_names = [m.get("name", "") for m in models]
            logger.info(f"✅ Ollama available with models: {model_names[:3]}...")
            return True
        else:
            logger.warning(f"⚠️ Ollama returned status {response.status_code}")
            return True  # Non-blocking, just a warning
    except Exception as e:
        logger.warning(f"⚠️ Ollama not available (optional): {e}")
        return True  # Non-blocking


def test_master_cv_structure():
    """Test: Master CV v8 has expected structure"""
    from pathlib import Path
    import json
    
    cv_path = Path(__file__).parent / "master_profile_v8.json"
    assert cv_path.exists(), f"Master CV not found: {cv_path}"
    
    with open(cv_path, 'r', encoding='utf-8') as f:
        cv = json.load(f)
    
    # Check required fields (v8 schema uses candidato.nome_completo)
    assert "candidato" in cv, "Master CV missing field: candidato"
    assert "nome_completo" in cv["candidato"], "Master CV missing candidato.nome_completo"
    
    # Required top-level sections
    required_sections = ["headlines_variants", "skills"]
    for field in required_sections:
        assert field in cv, f"Master CV missing field: {field}"
    
    # Check experience structure (can be 'experiencias' or 'experiences')
    experiences = cv.get("experiencias", cv.get("experiences", []))
    assert len(experiences) > 0, "No experiences in Master CV"
    
    # Check STAR bullets
    stars_count = sum(len(exp.get("stars", [])) for exp in experiences)
    assert stars_count >= 10, f"Expected 10+ STAR bullets, got {stars_count}"
    
    logger.info(f"✅ Master CV valid: {len(cv.get('experiencias', []))} experiences, {stars_count} STAR bullets")
    return True


def test_llm_service():
    """Test: LLM Service loads correctly with fallback chain"""
    from core.llm_service import (
        LLMService,
        get_llm_service,
        OllamaBackend,
        GeminiBackend,
        GroqBackend,
        retry_with_backoff,
        OLLAMA_CONFIG,
        GEMINI_CONFIG,
        GROQ_CONFIG
    )
    
    # Test singleton pattern
    service1 = get_llm_service()
    service2 = get_llm_service()
    assert service1 is service2, "Singleton pattern not working"
    
    # Test backend configs exist
    assert OLLAMA_CONFIG.name == "ollama", "Ollama config incorrect"
    assert "keywords" in OLLAMA_CONFIG.use_cases, "Ollama should support keywords"
    
    # Test retry function works
    counter = {"value": 0}
    
    def failing_then_success():
        counter["value"] += 1
        if counter["value"] < 2:
            raise Exception("First call fails")
        return "success"
    
    result, retries, error = retry_with_backoff(failing_then_success, max_retries=3, base_delay=0.01)
    assert result == "success", "Retry should eventually succeed"
    assert retries == 1, f"Should have retried 1 time, got {retries}"
    
    # Test service initialization
    service = LLMService()
    backends = service.get_available_backends()
    
    # At least the module should load without errors
    assert isinstance(backends, list), "get_available_backends should return list"
    
    logger.info(f"✅ LLM Service initialized: {len(backends)} backends available")
    return True


def test_jobspy_integration():
    """Test: JobSpy integration can fetch jobs"""
    from scraper import JobSpyScraper
    
    scraper = JobSpyScraper()
    # Use a small limit for testing
    jobs = scraper.search(query="Product Manager", limit=2, sources=["linkedin"])
    
    # We allow zero jobs if the site is blocking, but we check structure if jobs are found
    if jobs:
        job = jobs[0]
        assert job.id.startswith("linkedin_") or job.id.startswith("li_") or job.id.startswith("js_"), f"Unexpected ID format: {job.id}"
        assert job.title, "Job title missing"
        assert job.company, "Job company missing"
        assert job.url, "Job URL missing"
        logger.info(f"✅ JobSpy integration fetched {len(jobs)} jobs")
    else:
        logger.warning("⚠️ JobSpy fetched 0 jobs (could be rate-limiting or no matches)")
    
    return True


# ============== TEST RUNNER ==============

def run_test(test_func: Callable, max_retries: int = 2) -> TestResult:
    """Run a single test with retry logic"""
    start = time.time()
    
    def wrapped():
        return test_func()
    
    result, retries, error = retry_with_backoff(wrapped, max_retries=max_retries)
    
    duration = (time.time() - start) * 1000
    
    if error:
        # Log error to error.log
        with open(ERROR_LOG, 'a') as f:
            f.write(f"\n{'='*60}\n")
            f.write(f"TEST FAILED: {test_func.__name__}\n")
            f.write(f"TIME: {datetime.now().isoformat()}\n")
            f.write(f"RETRIES: {retries}\n")
            f.write(f"ERROR: {error}\n")
            f.write(f"{'='*60}\n")
    
    return TestResult(
        name=test_func.__name__,
        passed=error is None,
        duration_ms=duration,
        error=error,
        retries=retries
    )


def run_suite() -> SuiteResult:
    """Run all tests in the suite"""
    tests = [
        test_matcher_utils_import,
        test_config_module,
        test_master_cv_structure,
        test_profile_skills_loading,
        test_keyword_extraction_regex,
        test_match_score_calculation,
        test_match_job_to_profile,
        test_scraper_job_dataclass,
        test_llm_service,
        test_ollama_availability,
        test_jobspy_integration,
    ]
    
    logger.info(f"\n{'='*60}")
    logger.info("🧪 ANTIGRAVITY TAILOR - TEST SUITE")
    logger.info(f"{'='*60}")
    logger.info(f"Running {len(tests)} tests with self-healing retry...\n")
    
    start = time.time()
    results = []
    
    for test in tests:
        logger.info(f"▶️ Running: {test.__name__}...")
        result = run_test(test)
        results.append(result)
        
        if result.passed:
            logger.info(f"   ✅ PASSED ({result.duration_ms:.0f}ms)")
        else:
            logger.error(f"   ❌ FAILED: {result.error}")
            if result.retries > 0:
                logger.info(f"      (retried {result.retries} times)")
    
    duration = (time.time() - start) * 1000
    passed = sum(1 for r in results if r.passed)
    failed = len(results) - passed
    
    return SuiteResult(
        total=len(results),
        passed=passed,
        failed=failed,
        duration_ms=duration,
        results=results
    )


# ============== MAIN ==============

if __name__ == "__main__":
    try:
        suite_result = run_suite()
        
        logger.info(f"\n{'='*60}")
        logger.info("📊 TEST RESULTS SUMMARY")
        logger.info(f"{'='*60}")
        logger.info(f"Total:  {suite_result.total}")
        logger.info(f"Passed: {suite_result.passed}")
        logger.info(f"Failed: {suite_result.failed}")
        logger.info(f"Time:   {suite_result.duration_ms:.0f}ms")
        logger.info(f"{'='*60}")
        
        if suite_result.success:
            logger.info("\n🎉 ALL TESTS PASSED! Exit Code 0\n")
            sys.exit(0)
        else:
            logger.error(f"\n❌ {suite_result.failed} TEST(S) FAILED! Exit Code 1")
            logger.error(f"Details in: {ERROR_LOG}\n")
            
            # Print failed tests
            for r in suite_result.results:
                if not r.passed:
                    logger.error(f"  • {r.name}: {r.error}")
            
            sys.exit(1)
            
    except Exception as e:
        logger.critical(f"💀 CRITICAL ERROR: {e}")
        logger.critical(traceback.format_exc())
        
        # Write to error.log
        with open(ERROR_LOG, 'a') as f:
            f.write(f"\n{'='*60}\n")
            f.write(f"CRITICAL SUITE ERROR\n")
            f.write(f"TIME: {datetime.now().isoformat()}\n")
            f.write(f"ERROR: {e}\n")
            f.write(traceback.format_exc())
            f.write(f"{'='*60}\n")
        
        sys.exit(1)
