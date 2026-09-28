from dataclasses import dataclass

@dataclass
class Image:
    id: str
    photographer: str
    width: int
    height: int
    image_url: str
    alt: str
    source: str = "unknown"