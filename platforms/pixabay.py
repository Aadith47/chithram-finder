import os
from models import Image, PlatformError
from platforms.http_client import get_json

PIXABAY_URL = "https://pixabay.com/api/"


def search_images(query, per_page=5):
    api_key = os.getenv("PIXABAY_API_KEY")
    if not api_key:
        raise PlatformError("Pixabay: PIXABAY_API_KEY is missing from .env")

    params = {
        "key": api_key,
        "q": query,
        "image_type": "photo",
        "per_page": per_page
    }

    data = get_json("Pixabay", PIXABAY_URL, params=params)
    hits = data.get("hits", [])

    images = []
    for hit in hits:
        image = Image(
            id=str(hit["id"]),
            photographer=hit["user"],
            width=hit["imageWidth"],
            height=hit["imageHeight"],
            image_url=hit["largeImageURL"],
            alt=hit.get("tags", ""),
            source="pixabay"
        )
        images.append(image)

    return images