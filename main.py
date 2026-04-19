import argparse
import sys
import os

try:
    import RedditScrapper
    import voiceSyn
    import videoGenerator
except ImportError as e:
    print(f"[-] Error importing modules: {e}")
    print("Ensure RedditScrapper.py, voiceSyn.py, and videoGenerator.py are in the same directory.")
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="YouTube Shorts Automation CLI",
        epilog="Example: python main.py auto -s 'tifu' -p 'kokoro' -bg 'https://youtube.com/...'"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # ---------------------------------------------------------
    # 1. Scrape Command
    # ---------------------------------------------------------
    scrape_parser = subparsers.add_parser("scrape", help="Scrape stories from a Subreddit")
    scrape_parser.add_argument("-s", "--subreddit", type=str, required=True, help="Name of the subreddit")
    scrape_parser.add_argument("-l", "--limit", type=int, default=10, help="Number of posts to fetch")
    scrape_parser.add_argument("-o", "--output", type=str, default="story.txt", help="Output text file")

    # ---------------------------------------------------------
    # 2. Voice Command
    # ---------------------------------------------------------
    voice_parser = subparsers.add_parser("voice", help="Generate voiceover and subtitles")
    voice_parser.add_argument("-i", "--input", type=str, required=True, help="Input text file")
    voice_parser.add_argument("-p", "--provider", type=str, choices=voiceSyn.options_list, default="kokoro",
                              help="TTS Provider")

    # ---------------------------------------------------------
    # 3. Video Command
    # ---------------------------------------------------------
    video_parser = subparsers.add_parser("video",
                                         help="Download BG and render final video from existing files in Clips/")
    video_parser.add_argument("-bg", "--bg_url", type=str, help="YouTube URL for background gameplay")

    # ---------------------------------------------------------
    # 4. Auto Command (Full Pipeline)
    # ---------------------------------------------------------
    auto_parser = subparsers.add_parser("auto", help="Run the full pipeline (Scrape -> Voice -> Video)")
    auto_parser.add_argument("-s", "--subreddit", type=str, required=True, help="Name of the subreddit")
    auto_parser.add_argument("-l", "--limit", type=int, default=10, help="Number of posts to fetch")
    auto_parser.add_argument("-p", "--provider", type=str, choices=voiceSyn.options_list, default="kokoro",
                             help="TTS Provider")
    auto_parser.add_argument("-bg", "--bg_url", type=str, help="YouTube URL for background gameplay")

    args = parser.parse_args()

    if args.command == "scrape":
        print(f"[*] Fetching top posts from r/{args.subreddit}...")
        posts = RedditScrapper.get_posts(args.subreddit, limit=args.limit)
        selected_post = RedditScrapper.choose_post(posts)

        if selected_post:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(selected_post["body"])
            print(f"[+] Story saved to Clips/{args.output}")
        else:
            print("[-] No post selected.")

    elif args.command == "voice":
        print(f"[*] Reading text from {args.input}")
        try:
            with open(args.input, "r", encoding="utf-8") as f:
                text = f.read()
        except FileNotFoundError:
            print(f"[-] Error: Could not find {args.input} in the Clips directory.")
            sys.exit(1)

        print(f"[*] Generating voiceover and subtitles using {args.provider}...")
        voiceSyn.main(text, args.provider)
        print("[+] Audio and subtitles generated successfully in Clips/")

    elif args.command == "video":
        print(f"[*] Preparing background video...")
        videoGenerator.youtube_vids(args.bg_url)

        print(f"[*] Rendering final video...")
        try:
            videoGenerator.videos_clips()
            print("[+] Rendering complete! Check 'Clips/output.mp4'")
        except Exception as e:
            print(f"[-] Video generation failed: {e}")

    elif args.command == "auto":
        print("[*] Starting automation pipeline...")

        # STEP 1: SCRAPE
        print(f"\n--- STEP 1: Scrape r/{args.subreddit} ---")
        posts = RedditScrapper.get_posts(args.subreddit, limit=args.limit)
        selected_post = RedditScrapper.choose_post(posts)
        if not selected_post:
            print("[-] Automation aborted. No post was selected.")
            sys.exit(1)

        # STEP 2: VOICE
        print(f"\n--- STEP 2: Generate Voiceover ({args.provider}) ---")
        voiceSyn.main(selected_post["body"], args.provider)

        # STEP 3: BACKGROUND
        print("\n--- STEP 3: Download Background Video ---")
        videoGenerator.youtube_vids(args.bg_url)

        # STEP 4: RENDER
        print("\n--- STEP 4: Render Final Video ---")
        try:
            videoGenerator.videos_clips()
            print(f"\n[+] Pipeline complete! Final video saved to Clips/output.mp4")
        except Exception as e:
            print(f"\n[-] Video generation failed: {e}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()