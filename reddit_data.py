import argparse
import json
import logging
import os
import time
from typing import List

import praw
from pydantic import BaseModel
from prawcore.exceptions import RateLimitExceeded

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class RedditData(BaseModel):
    id: str
    content: str
    metadata: dict


class RedditScraper:
    def __init__(self, client_id: str, client_secret: str, user_agent: str, wait_time: float = 1.0):
        self.reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent,
        )
        self.wait_time = wait_time

    def fetch_posts(self, subreddits: List[str], post_limit: int = 10, comment_limit: int = 10) -> List[RedditData]:
        data: List[RedditData] = []
        for subreddit_name in subreddits:
            try:
                subreddit = self.reddit.subreddit(subreddit_name)
                for submission in subreddit.hot(limit=post_limit):
                    content = submission.title + "\n" + (submission.selftext or "")
                    data.append(
                        RedditData(
                            id=submission.id,
                            content=content,
                            metadata={
                                "url": submission.url,
                                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                                "tags": [subreddit_name],
                                "language": "english",
                                "type": "post",
                            },
                        )
                    )
                    submission.comments.replace_more(limit=0)
                    for comment in submission.comments.list()[:comment_limit]:
                        data.append(
                            RedditData(
                                id=comment.id,
                                content=comment.body,
                                metadata={
                                    "url": submission.url + "#comment",
                                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                                    "tags": [subreddit_name],
                                    "language": "english",
                                    "type": "comment",
                                },
                            )
                        )
                    time.sleep(self.wait_time)
            except RateLimitExceeded as e:
                wait_for = int(e.sleep_time) + 1
                logging.warning(f"Rate limit atingido, aguardando {wait_for}s...")
                time.sleep(wait_for)
            except Exception as e:
                logging.error(f"Erro ao coletar dados de r/{subreddit_name}: {e}")
        return data

    def save_to_json(self, data: List[RedditData], filename: str):
        output = {
            "source": "reddit",
            "category": "forum",
            "document_type": "post_comment",
            "data": [d.dict() for d in data],
        }
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        logging.info(f"Dados salvos em {filename}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scraper simples do Reddit")
    parser.add_argument("--client-id", default=os.getenv("REDDIT_CLIENT_ID"), help="Client ID do Reddit")
    parser.add_argument("--client-secret", default=os.getenv("REDDIT_CLIENT_SECRET"), help="Client Secret do Reddit")
    parser.add_argument("--user-agent", default=os.getenv("REDDIT_USER_AGENT", "reddit-scraper"), help="User Agent a ser usado")
    parser.add_argument("--subreddits", default="devops,programming", help="Lista de subreddits separada por vírgula")
    parser.add_argument("--posts", type=int, default=50, help="Quantidade de posts por subreddit")
    parser.add_argument("--comments", type=int, default=10, help="Quantidade de comentários por post")
    parser.add_argument("--wait", type=float, default=1.0, help="Tempo de espera entre chamadas")
    parser.add_argument("--output", default="reddit_data.json", help="Arquivo de saída")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    scraper = RedditScraper(
        client_id=args.client_id,
        client_secret=args.client_secret,
        user_agent=args.user_agent,
        wait_time=args.wait,
    )
    subreddit_list = [s.strip() for s in args.subreddits.split(",") if s.strip()]
    posts = scraper.fetch_posts(subreddit_list, post_limit=args.posts, comment_limit=args.comments)
    scraper.save_to_json(posts, args.output)
