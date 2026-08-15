def rerank_results(
    query: str,
    results: list,
):

    query_words = set(query.lower().split())

    for result in results:

        text = result["text"].lower()

        score = 0

        for word in query_words:

            if word in text:
                score += 1

        result["rerank_score"] = score

    results.sort(
        key=lambda x: x["rerank_score"],
        reverse=True,
    )

    return results[:5]