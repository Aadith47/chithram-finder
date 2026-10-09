import html

PLATFORM_NAMES = {"pexels": "Pexels", "unsplash": "Unsplash", "pixabay": "Pixabay"}


def link(url, text):
    # Only https links become clickable. The URLs come from outside APIs,
    # so anything else (like "javascript:...") is shown as plain text.
    if url.startswith("https://"):
        safe_url = html.escape(url, quote=True)
        return f'<a href="{safe_url}" target="_blank" rel="noopener noreferrer">{text}</a>'
    return text


def credit_html(image):
    """'Photo by <photographer> on <platform>', each part linked to its page."""
    platform = html.escape(PLATFORM_NAMES.get(image.source, image.source))
    photographer = html.escape(image.photographer)
    return f"Photo by {link(image.photographer_url, photographer)} on {link(image.page_url, platform)}"