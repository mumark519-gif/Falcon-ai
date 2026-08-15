from collections import defaultdict


CATEGORY_RULES = {
    "personal": [
        "name",
        "age",
        "birthday",
        "birth",
        "location",
        "city",
        "country",
        "family",
    ],

    "preferences": [
        "favorite",
        "prefer",
        "like",
        "dislike",
        "love",
        "hate",
        "style",
    ],

    "projects": [
        "project",
        "goal",
        "mission",
        "startup",
        "company",
        "business",
        "falcon",
        "roohe",
    ],

    "skills": [
        "skill",
        "language",
        "python",
        "fastapi",
        "coding",
        "programming",
    ],

    "work": [
        "job",
        "career",
        "industry",
        "customer",
        "client",
    ],

    "other": [],
}


def classify_memory(memory: dict):

    categories = defaultdict(dict)

    for key, value in memory.items():

        key_lower = key.lower()

        assigned = False

        for category, words in CATEGORY_RULES.items():

            if any(
                word in key_lower
                for word in words
            ):

                categories[category][key] = value

                assigned = True

                break

        if not assigned:

            categories["other"][key] = value

    return dict(categories)