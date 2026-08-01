from app.agents.router import route_agent


def test_business_agent():

    prompt = route_agent(
        "How can I increase my company's revenue?"
    )

    assert "business" in prompt.lower()


def test_investment_agent():

    prompt = route_agent(
        "Should I invest in Apple stock?"
    )

    assert "investment" in prompt.lower()


def test_coding_agent():

    prompt = route_agent(
        "Fix this Python FastAPI error."
    )

    assert "coding" in prompt.lower()


def test_research_agent():

    prompt = route_agent(
        "Explain quantum computing."
    )

    assert "research" in prompt.lower()

def test_unknown_agent_falls_back_to_research(monkeypatch):

    from app.agents import router

    monkeypatch.setattr(
        router,
        "classify_agent",
        lambda message: "UNKNOWN"
    )

    prompt = router.route_agent(
        "Something completely unusual"
    )

    assert "research" in prompt.lower()