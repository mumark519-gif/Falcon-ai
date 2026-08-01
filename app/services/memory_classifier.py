def classify_memory(
    memory: dict,
):

    categories = {
        "personal": {},
        "business": {},
        "preferences": {},
        "projects": {},
        "other": {},
    }

    for key, value in memory.items():

        key_lower = key.lower()

        if any(
            word in key_lower
            for word in [
                "name",
                "age",
                "birthday",
                "location",
            ]
        ):

            categories["personal"][key] = value

        elif any(
            word in key_lower
            for word in [
                "company",
                "business",
                "customer",
                "industry",
            ]
        ):

            categories["business"][key] = value

        elif any(
            word in key_lower
            for word in [
                "favorite",
                "prefer",
                "like",
                "dislike",
            ]
        ):

            categories["preferences"][key] = value

        elif any(
            word in key_lower
            for word in [
                "project",
                "goal",
                "mission",
            ]
        ):

            categories["projects"][key] = value

        else:

            categories["other"][key] = value

    return categories