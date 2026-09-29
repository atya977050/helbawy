from dataclasses import dataclass


@dataclass
class SearchResult:
    query: str
    results: list


class SearchService:
    """خدمة البحث الاختيارية للمشروع الناتج."""

    def search(self, query, items=None):
        query = str(query or "").strip()

        if not query:
            raise ValueError("عبارة البحث مطلوبة.")

        items = items or []
        query_lower = query.casefold()

        results = [
            item
            for item in items
            if query_lower in str(item).casefold()
        ]

        return SearchResult(
            query=query,
            results=results,
        )


def search(query, items=None):
    return SearchService().search(query, items)
