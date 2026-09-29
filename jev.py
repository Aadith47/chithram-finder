import os
import requests

JEV_URL = "https://openrouter.ai/api/alpha/decisions"


def rank_with_jev(context, images):
    if not images:
        return images

    api_key = os.getenv("OPENRyOUTER_API_KEY")
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY is missing from .env")

    criteria = {}
    for i, image in enumerate(images):
        criteria[str(i)] = image.alt if image.alt else "no description"

    payload = {
        "model": "typesafe/jev-1.13",
        "state": context,
        "questions": {
            "best_match": {
                "type": "choice",
                "instructions": "Which image best matches this description?",
                "criteria": criteria
            }
        }
    }
    headers = {"Authorization": f"Bearer {api_key}"}

    response = requests.post(JEV_URL, json=payload, headers=headers)

    if response.status_code != 200:
        raise RuntimeError(f"Jev request failed: {response.status_code} {response.text}")

    data = response.json()
    probabilities = data["answers"]["best_match"]["probabilities"]

    scored = []
    for i, image in enumerate(images):
        score = probabilities.get(str(i), 0)
        scored.append((score, image))

    scored.sort(key=lambda pair: pair[0], reverse=True)

    ranked_images = []
    for score, image in scored:
        ranked_images.append(image)

    return ranked_images