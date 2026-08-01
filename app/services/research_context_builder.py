def build_research_context(results):

    if not results:
        return ""

    sections = [
        "WEB SEARCH RESULTS\n"
    ]

    for i, item in enumerate(results, start=1):

        sections.append(
            f"""
Source {i}

Title:
{item.get("title","")}

Summary:
{item.get("content","")}

URL:
{item.get("url","")}
"""
        )

    return "\n".join(sections)