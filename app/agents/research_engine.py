from app.tools.web_search_tool import (
    web_search_tool,
)

from app.tools.browser_tool import (
    browser_tool,
)

from app.services.research_summarizer import (
    summarize_research,
)

def search_web(
    question: str,
):

    return web_search_tool(
        question,
    )

def extract_urls(
    search_results,
):

    urls = []

    for result in search_results:

        url = result.get(
            "url",
        )

        if url:

            urls.append(url)

    return urls

def read_pages(
    urls,
):

    pages = []

    for url in urls:

        content = browser_tool(
            url,
        )

        pages.append(
            {
                "url": url,
                "content": content,
            }
        )

    return pages

def build_research_context(
    question: str,
):

    search_results = search_web(
        question,
    )

    urls = extract_urls(
        search_results,
    )

    pages = read_pages(
        urls,
    )

    summary = summarize_research(
        pages,
    )

    return {
        "summary": summary,
        "search_results": search_results,
        "pages": pages,
    }