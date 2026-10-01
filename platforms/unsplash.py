import os
from models import Image, PlatformError
from platforms.http_client import get_json

UNSPLASH_URL = "https://api.unsplash.com/search/photos"


def search_images(query, per_page=5):
    access_key = os.getenv("UNSPLASH_ACCESS_KEY")
    if not access_key:
        raise PlatformError("Unsplash: UNSPLASH_ACCESS_KEY is missing from .env")

    headers = {
        "Authorization": f"Client-ID {access_key}"
    }
    params = {
        "query": query,
        "per_page": per_page
    }

    data = get_json("Unsplash", UNSPLASH_URL, headers=headers, params=params)
    photos = data.get("results", [])

    images = []
    for photo in photos:
        alt_text = photo.get("alt_description") or photo.get("description") or ""

        image = Image(
            id=photo["id"],
            photographer=photo["user"]["name"],
            width=photo["width"],
            height=photo["height"],
            image_url=photo["urls"]["regular"],
            alt=alt_text,
            source="unsplash"
        )
        images.append(image)

    return images