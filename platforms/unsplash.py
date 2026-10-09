import os
from models import Image, PlatformError
from platforms.http_client import get_json

UNSPLASH_URL = "https://api.unsplash.com/search/photos"

# Unsplash asks for links back to them to carry these two tracking parameters.
UTM = "utm_source=pixora&utm_medium=referral"


def with_utm(url):
    if not url:
        return ""
    separator = "&" if "?" in url else "?"
    return url + separator + UTM


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
            source="unsplash",
            page_url=with_utm(photo.get("links", {}).get("html", "")),
            photographer_url=with_utm(photo["user"].get("links", {}).get("html", ""))
        )
        images.append(image)

    return images