import logging
import operator
import time
from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, END

from llm import get_queries
from search import search_from_queries
from platforms.pexels import search_images as pexels_search
from platforms.unsplash import search_images as unsplash_search
from platforms.pixabay import search_images as pixabay_search
from ranker import rank_images
from jev import rank_with_jev


logger = logging.getLogger(__name__)


class ImageFinderState(TypedDict):
    context: str
    queries: list[str]
    structured_info: dict
    pexels_images: list
    unsplash_images: list
    pixabay_images: list
    images: list
    ranking_method: str
    # The three search nodes run at the same time and can all add errors.
    # operator.add tells LangGraph to join those lists instead of complaining.
    errors: Annotated[list[str], operator.add]


def initial_state(context: str) -> ImageFinderState:
    """The starting state for a search - kept in one place so main.py
    and app.py don't each maintain their own copy of this dict."""
    return {
        "context": context,
        "queries": [],
        "structured_info": None,
        "pexels_images": [],
        "unsplash_images": [],
        "pixabay_images": [],
        "images": [],
        "ranking_method": "",
        "errors": []
    }


# Every node returns only the keys it changes. Nodes that run in parallel
# must not return the whole state, or they would all write the same keys.

def generate_queries(state: ImageFinderState):
    structured_info, queries = get_queries(state["context"])
    update = {"structured_info": structured_info, "queries": queries}

    if not queries:
        update["errors"] = ["Could not generate search queries - every language model failed"]

    return update


def search_pexels(state: ImageFinderState):
    images, errors = search_from_queries(state["queries"], pexels_search, per_query=5)
    return {"pexels_images": images, "errors": errors}


def search_unsplash(state: ImageFinderState):
    images, errors = search_from_queries(state["queries"], unsplash_search, per_query=5)
    return {"unsplash_images": images, "errors": errors}


def search_pixabay(state: ImageFinderState):
    images, errors = search_from_queries(state["queries"], pixabay_search, per_query=5)
    return {"pixabay_images": images, "errors": errors}


def combine_images(state: ImageFinderState):
    combined = []
    seen_keys = set()

    all_images = state["pexels_images"] + state["unsplash_images"] + state["pixabay_images"]

    for image in all_images:
        key = (image.source, image.id)
        if key not in seen_keys:
            seen_keys.add(key)
            combined.append(image)

    return {"images": combined}


def rank_node(state: ImageFinderState):
    try:
        ranked = rank_with_jev(state["context"], state["images"])
        print("(ranked using Jev)")
        return {"images": ranked, "ranking_method": "jev"}

    except Exception as error:
        logger.warning("Jev ranking failed: %s: %s", type(error).__name__, error)
        ranked = rank_images(state["context"], state["images"])
        return {"images": ranked, "ranking_method": "keyword"}


def timed(name, node):
    """Wrap a node so the log shows how long it took."""
    def run(state):
        start = time.time()
        update = node(state)
        print(f"[timing] {name}: {time.time() - start:.1f}s", flush=True)
        return update
    return run


def create_graph():
    graph = StateGraph(ImageFinderState)

    graph.add_node("generate_queries", timed("generate_queries", generate_queries))
    graph.add_node("search_pexels", timed("search_pexels", search_pexels))
    graph.add_node("search_unsplash", timed("search_unsplash", search_unsplash))
    graph.add_node("search_pixabay", timed("search_pixabay", search_pixabay))
    graph.add_node("combine_images", timed("combine_images", combine_images))
    graph.add_node("rank_images", timed("rank_images", rank_node))

    graph.set_entry_point("generate_queries")

    # fan out: all three platforms start together
    graph.add_edge("generate_queries", "search_pexels")
    graph.add_edge("generate_queries", "search_unsplash")
    graph.add_edge("generate_queries", "search_pixabay")

    # fan in: combine waits until all three have finished
    graph.add_edge(["search_pexels", "search_unsplash", "search_pixabay"], "combine_images")

    graph.add_edge("combine_images", "rank_images")
    graph.add_edge("rank_images", END)

    return graph.compile()