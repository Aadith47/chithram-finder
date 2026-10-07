from concurrent.futures import ThreadPoolExecutor
from models import PlatformError


def _search_one(search_fn, query, per_query):
    try:
        return search_fn(query, per_page=per_query), None
    except PlatformError as error:
        return [], str(error)


def search_from_queries(queries, search_fn, per_query=5):
    if not queries:
        return [], []

    # The queries don't depend on each other, so search them at the same time.
    # pool.map keeps the results in the same order as the queries.
    with ThreadPoolExecutor(max_workers=len(queries)) as pool:
        outcomes = list(pool.map(lambda query: _search_one(search_fn, query, per_query), queries))

    all_images = []
    errors = []
    seen_keys = set()

    for results, error in outcomes:
        if error and error not in errors:
            errors.append(error)

        for image in results:
            key = (image.source, str(image.id))
            if key not in seen_keys:
                seen_keys.add(key)
                all_images.append(image)

    return all_images, errors