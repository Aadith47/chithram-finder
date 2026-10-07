import os
from models import Image, PlatformError
from platforms.http_client import get_json

PEXELS_URL = "https://api.pexels.com/v1/search"


def search_images(query, per_page=5):
    api_key = os.getenv("PEXELS_API_KEY")
    if not api_key:
        raise PlatformError("Pexels: PEXELS_API_KEY is missing from .env")

    headers = {
        "Authorization": api_key
    }
    params = {
        "query": query,
        "per_page": per_page
    }

    data = get_json("Pexels", PEXELS_URL, headers=headers, params=params)
    photos = data.get("photos", [])

    images = []
    for photo in photos:
        image = Image(
            id=str(photo["id"]),
            photographer=photo["photographer"],
            width=photo["width"],
            height=photo["height"],
            image_url=photo["src"]["large"],
            alt=photo.get("alt", "") or "",
            source="pexels"
        )
        images.append(image)

    return images