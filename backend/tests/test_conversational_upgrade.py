import sys
import os
import ssl

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Disable Pinecone gRPC network calls & bypass local SSL verification for test environment
os.environ["PINECONE_API_KEY"] = ""
os.environ["PYTHONHTTPSVERIFY"] = "0"
os.environ["CURL_CA_BUNDLE"] = ""

try:
    ssl._create_default_https_context = ssl._create_unverified_context
except AttributeError:
    pass

from agents.supervisor import supervisor_chat
from graph.workflow import graph


def test_turn_by_turn_profile_progression():
    print("\n--- Test 0: Turn-by-Turn Profile Progression (Failure Mode #4) ---")
    state = {}
    
    # Turn 1: Initial Idea
    res1 = supervisor_chat(state, "Food delivery for college campuses")
    reply1 = res1["reply"]
    prof1 = res1["startup_profile"]
    assert "food delivery" in str(prof1.get("problem") or prof1.get("idea", "")).lower(), f"Turn 1 problem/idea not set: {prof1}"
    assert "target" in reply1.lower() or "customer" in reply1.lower() or "segment" in reply1.lower() or "wedge" in reply1.lower(), "Turn 1 did not ask for customer segment"
    
    # Turn 2: Select Customer Segment
    state2 = {"conversation": res1["conversation"], "startup_profile": prof1, "questions_asked": res1["questions_asked"]}
    res2 = supervisor_chat(state2, "B2B Enterprise")
    reply2 = res2["reply"]
    prof2 = res2["startup_profile"]
    print("Turn 2 Reply Snippet:", reply2[:150])
    assert "b2b" in str(prof2.get("target_customer", "")).lower() or "enterprise" in str(prof2.get("target_customer", "")).lower(), f"Turn 2 target_customer not set: {prof2}"
    assert reply2 != reply1, "Turn 2 repeated Turn 1 question verbatim!"
    assert "monetization" in reply2.lower() or "pricing" in reply2.lower() or "model" in reply2.lower() or "revenue" in reply2.lower(), "Turn 2 did not advance to business model"
    
    # Turn 3: Select Revenue Model
    state3 = {"conversation": res2["conversation"], "startup_profile": prof2, "questions_asked": res2["questions_asked"]}
    res3 = supervisor_chat(state3, "Subscription (SaaS)")
    reply3 = res3["reply"]
    prof3 = res3["startup_profile"]
    print("Turn 3 Reply Snippet:", reply3[:150])
    assert "subscription" in str(prof3.get("business_model", "")).lower() or "saas" in str(prof3.get("business_model", "")).lower(), f"Turn 3 business_model not set: {prof3}"
    assert reply3 != reply2, "Turn 3 repeated Turn 2 question verbatim!"
    
    print("PASSED: Profile updated turn-to-turn with zero repeated questions!")


def test_competitor_direct_answer():
    print("\n--- Test 1: Direct Competitor Query in Germany (Failure Mode #1) ---")
    query = "competition for car dealer industry in germany"
    state = {}
    
    result = supervisor_chat(state, query)
    
    assert result["mode"] == "research", f"Expected mode 'research', got '{result.get('mode')}'"
    assert "reply" in result, "Result missing 'reply'"
    
    reply = result["reply"]
    print("Supervisor Reply Snippet:")
    print(reply[:300] + "...\n")
    
    assert len(reply) > 20, "Reply is too short"
    assert not reply.startswith("To help us validate"), "Response gated with stock questionnaire"
    print("PASSED: Direct competitor research executed without gating questionnaire.")


def test_no_raw_scrape_dump():
    print("\n--- Test 2: Car Resale Query - No Raw Scrape Output (Failure Mode #3) ---")
    query = "car resale in germany"
    state = {}
    
    result = supervisor_chat(state, query)
    reply = result["reply"]
    
    # Assert raw scrape text format is NOT directly returned to the user
    assert "• Title:" not in reply, "Raw Tavily search output dumped to user"
    assert "Content: http" not in reply, "Raw URL scrape output dumped to user"
    print("PASSED: Research query synthesized properly without dumping raw scrape output.")


def test_no_fake_examples_or_leaked_headers():
    print("\n--- Test 3: Vague Query - No Fake Examples or Meta Headers (Failure Mode #2) ---")
    query = "market condition for my IT startup"
    state = {}
    
    result = supervisor_chat(state, query)
    reply = result["reply"]
    
    assert "meal planning software" not in reply.lower(), "Invented fake hypothetical example"
    assert "**Follow-up:**" not in reply, "Leaked internal meta header **Follow-up:**"
    assert "**Strategic Verdict:**" not in reply, "Leaked internal meta header **Strategic Verdict:**"
    print("PASSED: Vague query handled without fabricated examples or leaked headers.")


def test_full_validation_workflow():
    print("\n--- Test 4: Full Validation Pipeline Workflow ---")
    initial_state = {
        "user_query": "AI co-pilot for automotive car dealerships in Germany to automate inventory pricing and lead generation",
        "startup_profile": {
            "industry": "Automotive / E-commerce",
            "geography": "Germany",
            "target_customer": "Car dealerships & automotive groups"
        }
    }
    
    res = graph.invoke(initial_state)
    
    assert "market_analysis" in res and res["market_analysis"], "Market analysis missing"
    assert "competitor_analysis" in res and res["competitor_analysis"], "Competitor analysis missing"
    assert "business_analysis" in res and res["business_analysis"], "Business analysis missing"
    assert "risk_analysis" in res and res["risk_analysis"], "Risk analysis missing"
    assert "scores" in res and "overall" in res["scores"], "Scores missing"
    
    print("Scores:", res["scores"])
    print("PASSED: Full multi-agent validation graph executed successfully.")


if __name__ == "__main__":
    test_turn_by_turn_profile_progression()
    test_competitor_direct_answer()
    test_no_raw_scrape_dump()
    test_no_fake_examples_or_leaked_headers()
    test_full_validation_workflow()
    print("\nALL VERIFICATION TESTS PASSED SUCCESSFULLY!")
