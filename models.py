from dataclasses import dataclass


@dataclass
class Image:
    id: str
    photographer: str
    width: int
    height: int
    image_url: str
    alt: str
    source: str = "pexels"


class PlatformError(Exception):
    """Raised when an image platform can't be searched
    (missing key, bad status code, network problem, bad response)."""