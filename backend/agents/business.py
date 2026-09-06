def business_agent(state):

    idea = state.get("user_query", "").lower()
    context = state.get("idea_context", {})
    retrieved_context = state.get("retrieved_context", "")
    context_text = " ".join(str(v) for v in context.values()).lower()
    combined = f"{idea} {context_text} {retrieved_context.lower()}"

    score = 0
    signals = []

    checks = [
        ("ai", 2, "AI-driven differentiation"),
        ("platform", 2, "platform / network-effect model"),
        ("subscription", 2, "recurring subscription revenue"),
        ("health", 2, "high-value healthcare vertical"),
        ("education", 2, "resilient education vertical"),
        ("fintech", 2, "regulated but high-margin fintech vertical"),
        ("marketplace", 1, "two-sided marketplace dynamics"),
        ("b2b", 1, "B2B model (typically higher willingness to pay)"),
    ]

    for keyword, weight, label in checks:
        if keyword in combined:
            score += weight
            signals.append(label)

    score = min(score, 10)

    if score >= 7:
        verdict = "Excellent Business Potential"
    elif score >= 5:
        verdict = "Good Business Potential"
    elif score >= 3:
        verdict = "Average Business Potential"
    else:
        verdict = "Needs Improvement"

    signal_lines = "\n".join(f"• {s}" for s in signals) or "• No strong monetization signals detected yet"

    analysis = f"""Business Score: {score}/10
Verdict: {verdict}

Signals detected:
{signal_lines}

Still worth validating:
• Revenue model
• Target customers
• Pricing
• Scalability
• Market demand"""

    scores = {**state.get("scores", {}), "business": score * 10}

    return {
        "business_analysis": analysis,
        "scores": scores,
    }
