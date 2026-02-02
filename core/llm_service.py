#!/usr/bin/env python3
"""
ANTIGRAVITY TAILOR - LLM Service
Unified LLM Backend with Fallback Chain + Exponential Backoff

Hierarchy (Cost-Efficiency):
1. Ollama (Local) - $0 - Keywords, Scoring, Filtering
2. Gemini Flash   - Free Tier - Synthesis, Tailoring
3. Groq           - Free Tier - Fallback

Usage:
    from core.llm_service import LLMService
    
    llm = LLMService()
    response = llm.generate("Extract keywords from: ...")
"""

import os
import time
import json
import logging
from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass, field
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


# ============== CONFIG ==============

@dataclass
class LLMBackendConfig:
    """Configuration for a single LLM backend"""
    name: str
    enabled: bool = True
    model: str = ""
    base_url: str = ""
    api_key_env: str = ""  # Environment variable name for API key
    timeout_seconds: int = 30
    max_tokens: int = 2000
    temperature: float = 0.7
    
    # Use cases this backend is suited for
    use_cases: List[str] = field(default_factory=list)


# Default configuration
OLLAMA_CONFIG = LLMBackendConfig(
    name="ollama",
    model="gemma3:4b",
    base_url="http://localhost:11434",
    use_cases=["keywords", "scoring", "filtering", "analysis", "synthesis", "tailoring", "cv_generation"]
)

GEMINI_CONFIG = LLMBackendConfig(
    name="gemini",
    model="gemini-2.0-flash",
    base_url="https://generativelanguage.googleapis.com/v1beta",
    api_key_env="GEMINI_API_KEY",
    use_cases=["synthesis", "tailoring", "cv_generation"]
)

GROQ_CONFIG = LLMBackendConfig(
    name="groq",
    model="llama-3.3-70b-versatile",
    base_url="https://api.groq.com/openai/v1",
    api_key_env="GROQ_API_KEY",
    use_cases=["fallback", "synthesis", "analysis"]
)

CLAUDE_CONFIG = LLMBackendConfig(
    name="claude",
    model="claude-sonnet-4-20250514",
    base_url="https://api.anthropic.com/v1",
    api_key_env="ANTHROPIC_API_KEY",
    max_tokens=4096,
    temperature=0.7,
    use_cases=["synthesis", "tailoring", "cv_generation", "analysis", "keywords"]
)


# ============== RETRY WITH EXPONENTIAL BACKOFF ==============

def retry_with_backoff(
    func: Callable,
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    exceptions: tuple = (Exception,)
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
        except exceptions as e:
            last_error = str(e)
            retries += 1
            
            if retries > max_retries:
                break
            
            # Exponential backoff: 1s, 2s, 4s, 8s...
            delay = min(base_delay * (2 ** (retries - 1)), max_delay)
            logger.warning(f"Retry {retries}/{max_retries} after {delay:.1f}s: {last_error}")
            time.sleep(delay)
    
    return (None, retries, last_error)


# ============== BACKEND ABSTRACT CLASS ==============

class LLMBackend(ABC):
    """Abstract base class for LLM backends"""
    
    def __init__(self, config: LLMBackendConfig):
        self.config = config
        self.available = False
        self._check_availability()
    
    @abstractmethod
    def _check_availability(self) -> bool:
        """Check if backend is available"""
        pass
    
    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> Optional[str]:
        """Generate text from prompt"""
        pass
    
    def supports_use_case(self, use_case: str) -> bool:
        """Check if backend supports a specific use case"""
        return use_case in self.config.use_cases or "fallback" in self.config.use_cases


# ============== OLLAMA BACKEND ==============

class OllamaBackend(LLMBackend):
    """Local Ollama backend - $0 cost"""

    def _check_availability(self) -> bool:
        try:
            import requests
            # First check if Ollama server is running
            response = requests.get(
                f"{self.config.base_url}/api/tags",
                timeout=2
            )
            if response.status_code == 200:
                # Try to verify model exists via /api/show (more reliable than /api/tags)
                try:
                    show_response = requests.post(
                        f"{self.config.base_url}/api/show",
                        json={"name": self.config.model},
                        timeout=5
                    )
                    if show_response.status_code == 200:
                        self.available = True
                        logger.info(f"✅ Ollama available with model: {self.config.model}")
                        return True
                except Exception:
                    pass

                # Fallback: check /api/tags list
                models = response.json().get("models", [])
                model_names = [m.get("name", "") for m in models]
                model_base = self.config.model.split(":")[0]
                self.available = any(model_base in name for name in model_names)

                if self.available:
                    logger.info(f"✅ Ollama available with model: {self.config.model}")
                else:
                    # Last resort: assume available if server responds (will fail gracefully on generate)
                    self.available = True
                    logger.info(f"✅ Ollama server running, assuming model {self.config.model} available")
                return self.available
        except Exception as e:
            logger.debug(f"Ollama not available: {e}")

        self.available = False
        return False
    
    def generate(self, prompt: str, **kwargs) -> Optional[str]:
        if not self.available:
            return None
        
        try:
            import requests
            
            def _request():
                response = requests.post(
                    f"{self.config.base_url}/api/generate",
                    json={
                        "model": self.config.model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": kwargs.get("temperature", self.config.temperature),
                            "num_predict": kwargs.get("max_tokens", self.config.max_tokens)
                        }
                    },
                    timeout=self.config.timeout_seconds
                )
                response.raise_for_status()
                return response.json().get("response", "")
            
            result, retries, error = retry_with_backoff(_request, max_retries=2)
            
            if error:
                logger.error(f"Ollama generation failed: {error}")
                return None
            
            return result
            
        except Exception as e:
            logger.error(f"Ollama error: {e}")
            return None


# ============== GEMINI BACKEND ==============

class GeminiBackend(LLMBackend):
    """Google Gemini backend - Free tier"""
    
    def _check_availability(self) -> bool:
        api_key = os.environ.get(self.config.api_key_env)
        self.available = bool(api_key)
        if self.available:
            self.api_key = api_key
            logger.info(f"✅ Gemini available with model: {self.config.model}")
        else:
            logger.debug(f"Gemini not available: {self.config.api_key_env} not set")
        return self.available
    
    def generate(self, prompt: str, **kwargs) -> Optional[str]:
        if not self.available:
            return None
        
        try:
            import requests
            
            def _request():
                url = f"{self.config.base_url}/models/{self.config.model}:generateContent"
                
                response = requests.post(
                    url,
                    params={"key": self.api_key},
                    json={
                        "contents": [{"parts": [{"text": prompt}]}],
                        "generationConfig": {
                            "temperature": kwargs.get("temperature", self.config.temperature),
                            "maxOutputTokens": kwargs.get("max_tokens", self.config.max_tokens)
                        }
                    },
                    timeout=self.config.timeout_seconds
                )
                response.raise_for_status()
                
                data = response.json()
                candidates = data.get("candidates", [])
                if candidates:
                    content = candidates[0].get("content", {})
                    parts = content.get("parts", [])
                    if parts:
                        return parts[0].get("text", "")
                return ""
            
            result, retries, error = retry_with_backoff(_request, max_retries=2)
            
            if error:
                logger.error(f"Gemini generation failed: {error}")
                return None
            
            return result
            
        except Exception as e:
            logger.error(f"Gemini error: {e}")
            return None


# ============== GROQ BACKEND ==============

class GroqBackend(LLMBackend):
    """Groq backend - Free tier, fast inference"""

    def _check_availability(self) -> bool:
        api_key = os.environ.get(self.config.api_key_env)
        self.available = bool(api_key)
        if self.available:
            self.api_key = api_key
            logger.info(f"✅ Groq available with model: {self.config.model}")
        else:
            logger.debug(f"Groq not available: {self.config.api_key_env} not set")
        return self.available

    def generate(self, prompt: str, **kwargs) -> Optional[str]:
        if not self.available:
            return None

        try:
            import requests

            def _request():
                response = requests.post(
                    f"{self.config.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.config.model,
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": kwargs.get("temperature", self.config.temperature),
                        "max_tokens": kwargs.get("max_tokens", self.config.max_tokens)
                    },
                    timeout=self.config.timeout_seconds
                )
                response.raise_for_status()

                data = response.json()
                choices = data.get("choices", [])
                if choices:
                    return choices[0].get("message", {}).get("content", "")
                return ""

            result, retries, error = retry_with_backoff(_request, max_retries=2)

            if error:
                logger.error(f"Groq generation failed: {error}")
                return None

            return result

        except Exception as e:
            logger.error(f"Groq error: {e}")
            return None


# ============== CLAUDE BACKEND ==============

class ClaudeBackend(LLMBackend):
    """Anthropic Claude backend - Premium quality for CV generation"""

    def _check_availability(self) -> bool:
        api_key = os.environ.get(self.config.api_key_env)
        self.available = bool(api_key)
        if self.available:
            self.api_key = api_key
            logger.info(f"✅ Claude available with model: {self.config.model}")
        else:
            logger.debug(f"Claude not available: {self.config.api_key_env} not set")
        return self.available

    def generate(self, prompt: str, **kwargs) -> Optional[str]:
        if not self.available:
            return None

        try:
            import requests

            def _request():
                response = requests.post(
                    f"{self.config.base_url}/messages",
                    headers={
                        "x-api-key": self.api_key,
                        "anthropic-version": "2023-06-01",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.config.model,
                        "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
                        "messages": [{"role": "user", "content": prompt}]
                    },
                    timeout=self.config.timeout_seconds
                )
                response.raise_for_status()

                data = response.json()
                content = data.get("content", [])
                if content:
                    # Claude returns content as array of blocks
                    text_blocks = [c.get("text", "") for c in content if c.get("type") == "text"]
                    return "".join(text_blocks)
                return ""

            result, retries, error = retry_with_backoff(_request, max_retries=2)

            if error:
                logger.error(f"Claude generation failed: {error}")
                return None

            return result

        except Exception as e:
            logger.error(f"Claude error: {e}")
            return None


# ============== UNIFIED LLM SERVICE ==============

class LLMService:
    """
    Unified LLM Service with Fallback Chain

    Priority: Ollama (local, free) → Gemini (free tier) → Groq (free tier) → Claude (premium)
    """

    def __init__(self, backend_order: List[str] = None):
        self.backends: Dict[str, LLMBackend] = {}
        self.backend_order = backend_order or ["ollama", "gemini", "groq", "claude"]

        self._init_backends()

    def _init_backends(self):
        """Initialize all configured backends"""
        backend_configs = {
            "claude": (ClaudeBackend, CLAUDE_CONFIG),
            "ollama": (OllamaBackend, OLLAMA_CONFIG),
            "gemini": (GeminiBackend, GEMINI_CONFIG),
            "groq": (GroqBackend, GROQ_CONFIG)
        }
        
        for name in self.backend_order:
            if name in backend_configs:
                backend_class, config = backend_configs[name]
                try:
                    self.backends[name] = backend_class(config)
                except Exception as e:
                    logger.warning(f"Failed to initialize {name}: {e}")
        
        available = [n for n, b in self.backends.items() if b.available]
        logger.info(f"LLM backends available: {available}")
    
    def get_available_backends(self) -> List[str]:
        """Get list of available backend names"""
        return [n for n, b in self.backends.items() if b.available]
    
    def generate(
        self,
        prompt: str,
        use_case: str = "general",
        preferred_backend: str = None,
        **kwargs
    ) -> Optional[str]:
        """
        Generate text with fallback chain.
        
        Args:
            prompt: The prompt to send
            use_case: Type of task (keywords, synthesis, etc.)
            preferred_backend: Force a specific backend
            **kwargs: Additional params (temperature, max_tokens)
        
        Returns:
            Generated text or None if all backends fail
        """
        # Determine backend order
        if preferred_backend and preferred_backend in self.backends:
            order = [preferred_backend] + [b for b in self.backend_order if b != preferred_backend]
        else:
            # Prioritize backends that support the use case
            suited = [n for n in self.backend_order 
                     if n in self.backends and self.backends[n].supports_use_case(use_case)]
            others = [n for n in self.backend_order if n not in suited]
            order = suited + others
        
        # Try each backend in order
        for backend_name in order:
            backend = self.backends.get(backend_name)
            if not backend or not backend.available:
                continue
            
            logger.debug(f"Trying {backend_name} for use_case: {use_case}")
            
            result = backend.generate(prompt, **kwargs)
            if result:
                logger.info(f"✅ Generated via {backend_name}")
                return result
            
            logger.warning(f"⚠️ {backend_name} failed, trying next...")
        
        logger.error("❌ All LLM backends failed")
        return None
    
    def extract_keywords(self, text: str) -> List[str]:
        """
        Extract keywords from text using local LLM if available.
        
        Returns:
            List of keywords
        """
        prompt = f"""Extract the most important skills, technologies, and requirements from this job description.
Return ONLY a JSON array of keywords, nothing else. Do not include any explanation.

Text:
{text[:3000]}

Example output: ["python", "machine learning", "product management"]
"""
        
        result = self.generate(prompt, use_case="keywords", temperature=0.3)
        
        if result:
            try:
                # Extract JSON array from response
                import re
                match = re.search(r'\[.*?\]', result, re.DOTALL)
                if match:
                    keywords = json.loads(match.group())
                    return [k.lower().strip() for k in keywords if isinstance(k, str)]
            except (json.JSONDecodeError, Exception) as e:
                logger.warning(f"Failed to parse keywords JSON: {e}")
        
        return []


# ============== SINGLETON INSTANCE ==============

_llm_service: Optional[LLMService] = None

def get_llm_service() -> LLMService:
    """Get singleton LLM service instance"""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service


# ============== CLI ==============

if __name__ == "__main__":
    import sys
    
    logging.basicConfig(level=logging.INFO)
    
    print("\n" + "=" * 60)
    print("🤖 LLM SERVICE - Diagnostic Test")
    print("=" * 60)
    
    service = LLMService()
    
    print(f"\n📊 Available backends: {service.get_available_backends()}")
    
    # Test generation
    test_prompt = "Say 'Hello, I am working!' and nothing else."
    
    print("\n▶️ Testing generation...")
    result = service.generate(test_prompt, use_case="general")
    
    if result:
        print(f"✅ Response: {result[:100]}...")
        sys.exit(0)
    else:
        print("❌ All backends failed")
        sys.exit(1)
