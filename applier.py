#!/usr/bin/env python3
import os
import json
import time
import asyncio
import random
from pathlib import Path
from playwright.async_api import async_playwright
import google.generativeai as genai
from dotenv import load_dotenv

# Load Env
load_dotenv()

# Config
BASE_DIR = Path(__file__).parent
MASTER_PROFILE_PATH = BASE_DIR / "master_profile_v8.json"
PREFERENCES_PATH = BASE_DIR / "preferences.json"
# Default path for Chrome on macOS
CHROME_PATH = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
USER_DATA_DIR = os.path.expanduser("~/Library/Application Support/Google/Chrome")

# LLM Config
try:
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    model = genai.GenerativeModel('gemini-2.0-flash')
except Exception as e:
    print(f"⚠️ [SYSTEM] Gemini Config Error: {e}")

class LinkedInApplier:
    def __init__(self, user_data_dir=None):
        print("🚀 [APPLIER] Starting LinkedIn Easy Apply Bot...")
        self.profile = self._load_json(MASTER_PROFILE_PATH)
        self.preferences = self._load_json(PREFERENCES_PATH)
        self.user_data_dir = user_data_dir or USER_DATA_DIR
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

    def _load_json(self, path):
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        print(f"⚠️ [APPLIER] File not found: {path}")
        return {}

    async def init_browser(self):
        print(f"🌐 [APPLIER] Launching Chrome Context from: {self.user_data_dir}")
        self.playwright = await async_playwright().start()
        
        try:
            # Launch persistent context to keep login session
            # IMPORTANT: Chrome must be closed for this to work due to lock
            self.context = await self.playwright.chromium.launch_persistent_context(
                user_data_dir=self.user_data_dir,
                executable_path=CHROME_PATH,
                headless=False,
                args=["--no-sandbox", "--disable-blink-features=AutomationControlled"],
                viewport={"width": 1280, "height": 800}
            )
            self.page = self.context.pages[0] if self.context.pages else await self.context.new_page()
            print("✅ [APPLIER] Browser initialized (Persistent Profile).")
        except Exception as e:
            print(f"❌ [APPLIER] Browser init failed: {e}")
            print("⚠️ Tip: Make sure Google Chrome is completely closed before running this script.")
            await self.shutdown()

    async def human_type(self, element, text):
        """Simulate human typing speed"""
        await element.click()
        for char in text:
            await self.page.keyboard.type(char)
            await asyncio.sleep(random.uniform(0.05, 0.15))

    async def get_ai_answer(self, question_text, question_type="text"):
        print(f"🧠 [AI] Answering: {question_text[:50]}...")
        prompt = f"""
        INSTRUÇÃO DE RESPOSTA: Você é um assistente de preenchimento de vagas do LinkedIn.
        Responda à pergunta baseando-se nos fatos reais do perfil e preferências do candidato.

        PERFIL (RESUMO):
        - Nome: {self.profile.get('candidato', {}).get('nome_completo')}
        - Experiência: 15+ anos (Meta, Ambev, Dow)
        - Stack Martech: HubSpot, Salesforce, GoHighLevel, n8n, Python, SQL
        - Idiomas: Português (Nativo), Inglês (Fluente), Espanhol (Avançado)
        - Localização: São Paulo (Remoto disponível)

        PREFERÊNCIAS:
        {json.dumps(self.preferences, indent=2)}

        REGRAS:
        1. Fatos Reais: Use os 15 anos de experiência e a passagem pela Meta para validar números.
        2. Contexto Técnico: Para ferramentas, cite HubSpot e CRM conforme documentado no perfil.
        3. Tom de Voz: Profissional e direto. 
        4. Se a pergunta for Sim/Não, responda apenas 'Yes' ou 'No' baseado na compatibilidade.
        5. Se for um número (ex: anos de experiência), responda apenas o número.
        6. Se for texto curto, seja extremamente conciso (max 10-15 palavras).

        PERGUNTA DO LINKEDIN: "{question_text}"
        TIPO: {question_type}

        RESPOSTA FINAL (APENAS O VALOR):
        """
        try:
            response = model.generate_content(prompt)
            answer = response.text.strip().strip('"').strip("'")
            print(f"✅ [AI] Answer: {answer}")
            return answer
        except Exception as e:
            print(f"❌ [AI] Error generating answer: {e}")
            return "Contact candidate"

    async def process_form(self):
        """Scan page for questions and fill them"""
        # Common LinkedIn Selectors for questions
        labels = await self.page.query_selector_all(".fb-dash-form-element__label, label")
        
        for label in labels:
            text = await label.inner_text()
            text = text.strip()
            if not text or len(text) < 3: continue

            # Avoid common non-question labels
            if text in ["First name", "Last name", "Email address", "Phone country code", "Mobile phone number"]:
                continue

            # Try to find the associated input/select
            for_attr = await label.get_attribute("for")
            target = None
            if for_attr:
                target = await self.page.query_selector(f"#{for_attr}")
            
            if not target:
                # Try sibling or parent-child relationship
                parent = await label.query_selector("xpath=..")
                target = await parent.query_selector("input, select, textarea")

            if target:
                tag_name = await target.evaluate("el => el.tagName.toLowerCase()")
                input_type = await target.get_attribute("type")

                if tag_name == "input" and input_type in ["text", "number"]:
                    # Check if already filled
                    val = await target.get_attribute("value")
                    if not val:
                        answer = await self.get_ai_answer(text, "text")
                        await self.human_type(target, answer)
                
                elif tag_name == "select":
                    answer = await self.get_ai_answer(text, "select")
                    # Select by visible text or value (AI should return the best match)
                    await target.select_option(label=answer)
                
                elif tag_name == "textarea":
                    answer = await self.get_ai_answer(text, "textarea")
                    await self.human_type(target, answer)

    async def next_or_submit(self):
        """Click 'Next', 'Review', or 'Submit application'"""
        buttons = await self.page.query_selector_all("button")
        for btn in buttons:
            text = await btn.inner_text()
            if any(word in text.lower() for word in ["next", "review", "submit"]):
                print(f"🖱️ [APPLIER] Clicking: {text}")
                await btn.click()
                await asyncio.sleep(2)
                return True
        return False

    async def run(self, job_url):
        await self.init_browser()
        await self.page.goto(job_url)
        print(f"📍 [APPLIER] Navigated to job: {job_url}")
        
        # Wait for "Easy Apply" or the form to appear
        # If Easy Apply button exists, click it
        easy_apply_btn = await self.page.query_selector("button:has-text('Easy Apply')")
        if easy_apply_btn:
            await easy_apply_btn.click()
            await asyncio.sleep(2)

        # Loop through pages of the application
        max_steps = 10
        for i in range(max_steps):
            print(f"📝 [APPLIER] Processing step {i+1}...")
            await self.process_form()
            
            # Check for deal-breaker logic here if needed
            # ...

            success = await self.next_or_submit()
            if not success:
                print("🏁 [APPLIER] No more buttons found or application finished.")
                break
            
            # Check if we are done (Submit clicked)
            # LinkedIn often shows a "Your application was sent" message
            if "submitted" in await self.page.content():
                print("🎉 [APPLIER] Application submitted successfully!")
                break

    async def shutdown(self):
        if self.context:
            await self.context.close()
        if self.playwright:
            await self.playwright.stop()
        print("🛑 [APPLIER] Bot stopped.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="LinkedIn Easy Apply Bot")
    parser.add_argument("url", nargs="?", help="LinkedIn Job URL")
    parser.add_argument("--profile-dir", help="Custom Chrome User Data Dir")
    args = parser.parse_args()

    if not args.url:
        print("❌ Please provide a Job URL.")
        print("Example: python applier.py https://www.linkedin.com/jobs/view/...")
        exit(1)

    applier = LinkedInApplier(user_data_dir=args.profile_dir)
    try:
        asyncio.run(applier.run(args.url))
    except KeyboardInterrupt:
        pass
