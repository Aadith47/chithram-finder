from models import PlatformError


def search_from_queries(queries, search_fn, per_query=5):
    all_images = []
    errors = []
    seen_keys = set()

    for query in queries:
        try:
            results = search_fn(query, per_page=per_query)
        except PlatformError as error:
            message = str(error)
            if message not in errors:
                errors.append(message)
            continue

        for image in results:
            key = (image.source, str(image.id))
            if key not in seen_keys:
                seen_keys.add(key)
                all_images.append(image)

    return all_images, errors