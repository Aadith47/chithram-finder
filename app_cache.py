import streamlit as st
from graph import create_graph, initial_state

# Pixabay asks API users to cache results for 24 hours.
CACHE_SECONDS = 24 * 60 * 60

_runs = {"count": 0}


class IncompleteSearch(Exception):
    """Raised when a search had errors or found nothing.
    Streamlit never caches an exception, so a failed search is not kept for 24 hours."""

    def __init__(self, result):
        self.result = result


@st.cache_resource
def get_graph():
    return create_graph()


@st.cache_data(ttl=CACHE_SECONDS, max_entries=100, show_spinner=False)
def _cached_search(description):
    _runs["count"] += 1
    result = get_graph().invoke(initial_state(description))

    if result["errors"] or not result["images"]:
        raise IncompleteSearch(result)

    return result


def run_search(context):
    """Returns (result, from_cache). The same description, in any capitals
    or spacing, is answered from the cache for 24 hours."""
    description = " ".join(context.lower().split())
    runs_before = _runs["count"]

    try:
        result = _cached_search(description)
    except IncompleteSearch as incomplete:
        result = incomplete.result

    return result, _runs["count"] == runs_before