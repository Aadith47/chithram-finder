import os
import requests
from models import Image

PEXELS_URL = "https://api.pexels.com/v1/search"


def search_images(query, per_page=5):
    api_key = os.getenv("PEXELS_API_KEY")
    if not api_key:
        print("PEXELS_API_KEY is missing from .env")
        return []

    headers = {
        "Authorization": api_key
    }
    params = {
        "query": query,
        "per_page": per_page
    }

    response = requests.get(PEXELS_URL, headers=headers, params=params)

    if response.status_code != 200:
        print(f"Pexels request failed for '{query}': {response.status_code}")
        return []

    data = response.json()
    photos = data.get("photos", [])

    images = []
    for photo in photos:
        image = Image(
            id=str(photo["id"]),
            photographer=photo["photographer"],
            width=photo["width"],
            height=photo["height"],
            image_url=photo["src"]["original"],
            alt=photo.get("alt", "") or "",
            source="pexels"
        )
        images.append(image)

    return images