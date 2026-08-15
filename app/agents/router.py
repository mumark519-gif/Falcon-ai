from app.agents.business_agent import BUSINESS_PROMPT
from app.agents.investment_agent import INVESTMENT_PROMPT
from app.agents.coding_agent import CODING_PROMPT
from app.agents.research_agent import RESEARCH_PROMPT
from app.agents.classifier import CLASSIFIER_PROMPT
from app.services.ai.ai_gateway import generate


def get_system_prompt(message: str):

    text = message.lower()

    investment_keywords = [
        "stock",
        "stocks",
        "etf",
        "invest",
        "investment",
        "portfolio",
        "dividend",
        "crypto",
        "bitcoin",
        "finance",
        "market",
    ]

    coding_keywords = [
        "python",
        "fastapi",
        "api",
        "bug",
        "error",
        "code",
        "coding",
        "program",
        "javascript",
        "react",
        "sql",
    ]

    business_keywords = [
        "business",
        "startup",
        "marketing",
        "sales",
        "company",
        "revenue",
        "profit",
        "strategy",
    ]

    if any(word in text for word in investment_keywords):
        return INVESTMENT_PROMPT

    if any(word in text for word in coding_keywords):
        return CODING_PROMPT

    if any(word in text for word in business_keywords):
        return BUSINESS_PROMPT

    return RESEARCH_PROMPT


def classify_agent(message: str):
    """Classify a request using Falcon's unified AI provider gateway."""
    prompt = (
        CLASSIFIER_PROMPT
        + "\n\nQuestion:\n"
        + str(message).strip()
    )
    response = generate(prompt)
    return response.strip().upper()

def route_agent(message: str):

    return get_system_prompt(message)