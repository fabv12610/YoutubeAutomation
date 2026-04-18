import requests

def get_posts(subreddit, limit=100):
    try:
        subreddit = subreddit.strip().replace("r/", "").replace("/", "")

        url = f"https://www.reddit.com/r/{subreddit}/hot.json?limit={limit}"

        headers = {
            "User-Agent": "python:reddit.scraper:v1.0 (by /u/yourname)"
        }

        response = requests.get(url, headers=headers)

        if response.status_code == 404:
            print("Subreddit not found (404). Check the name.")
            return []

        if response.status_code != 200:
            print(f"Error: {response.status_code}")
            print(response.text[:200])
            return []

        data = response.json()

        posts = []
        for post in data["data"]["children"]:
            post_data = post["data"]

            if post_data.get("selftext", "") == "":
                continue

            posts.append({
                "title": post_data.get("title", ""),
                "body": post_data.get("selftext", "")
            })

        return posts
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return []


def choose_post(posts):
    if not posts:
        print("No posts available.")
        return

    # Show numbered list
    print("\nSelect a post:\n")
    for i, post in enumerate(posts, start=1):
        print(f"{i}. {post['title']}")

    # Get user choice
    while True:
        try:
            choice = int(input("\nEnter number: "))
            if 1 <= choice <= len(posts):
                selected = posts[choice - 1]
                print("\n--- POST ---")
                print("Title:", selected["title"])
                print("\nBody:\n", selected["body"])
                return
            else:
                print("Invalid number.")
        except ValueError:
            print("Enter a valid number.")

