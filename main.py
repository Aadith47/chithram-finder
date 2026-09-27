from dotenv import load_dotenv
from graph import create_graph, initial_state

load_dotenv()


def main():
    context = input("Describe the image you need: ")

    graph = create_graph()
    result = graph.invoke(initial_state(context))

    if result["structured_info"]:
        info = result["structured_info"]
        print("\nUnderstood description as:")
        print("  main subject:", info.get("main_subject", ""))
        print("  environment:", info.get("environment", ""))
        print("  device:", info.get("device", ""))
        print("  screen content:", info.get("screen_content", ""))
        print("  style:", info.get("style", ""))

    print("\nGenerated search queries:")
    for query in result["queries"]:
        print("-", query)

    print(f"\nFound {len(result['images'])} images.\n")

    for image in result["images"]:
        print("ID:", image.id)
        print("Photographer:", image.photographer)
        print("Alt:", image.alt)
        print("URL:", image.image_url)
        print("-" * 50)


if __name__ == "__main__":
    main()