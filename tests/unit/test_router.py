from app.agents.router import get_system_prompt

print("Investment:")
print(get_system_prompt("Should I buy NVIDIA stock?")[:80])

print("\nBusiness:")
print(get_system_prompt("How can I grow my startup?")[:80])

print("\nCoding:")
print(get_system_prompt("Fix my FastAPI error")[:80])

print("\nResearch:")
print(get_system_prompt("Explain quantum computing")[:80])