#!/usr/bin/env python3
import asyncio
from applier import LinkedInApplier

async def test_llm():
    applier = LinkedInApplier()
    
    questions = [
        ("How many years of experience do you have in content creation & SEO?", "number"),
        ("Work with HubSpot or CRM?", "text"),
        ("Fluent in English?", "text"),
        ("Availability to start?", "text")
    ]
    
    print("\n--- Testing AI Answers ---")
    for q, qtype in questions:
        answer = await applier.get_ai_answer(q, qtype)
        print(f"Q: {q}")
        print(f"A: {answer}\n")

if __name__ == "__main__":
    asyncio.run(test_llm())
