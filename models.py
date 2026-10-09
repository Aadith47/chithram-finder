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
    page_url: str = ""          # the photo's own page on the platform
    photographer_url: str = ""  # the photographer's profile on the platform


class PlatformError(Exception):
    """Raised when an image platform can't be searched
    (missing key, bad status code, network problem, bad response)."""