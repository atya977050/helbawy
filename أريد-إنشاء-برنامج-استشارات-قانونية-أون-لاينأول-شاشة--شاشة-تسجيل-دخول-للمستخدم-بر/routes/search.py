from services.search import SearchService


def search_items(query, items=None):
    return SearchService().search(
        query,
        items,
    )
