import praw
import json
import time
import logging
from pydantic import BaseModel
from typing import List

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class RedditData(BaseModel):
    id: str
    content: str
    metadata: dict

class RedditScraper:
    def __init__(self, client_id: str, client_secret: str, user_agent: str):
        self.reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent
        )
        self.output_file = "reddit_data.json"

    def fetch_posts(self, subreddits: List[str], limit: int = 100) -> List[RedditData]:
        data = []
        for subreddit_name in subreddits:
            try:
                subreddit = self.reddit.subreddit(subreddit_name)
                for submission in subreddit.hot(limit=limit):
                    content = submission.title + "\n" + (submission.selftext or "")
                    data.append(RedditData(
                        id=submission.id,
                        content=content,
                        metadata={
                            "url": submission.url,
                            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                            "tags": [subreddit_name],
                            "language": "english",
                            "type": "post"
                        }
                    ))
                    # Coletar comentários
                    submission.comments.replace_more(limit=0)
                    for comment in submission.comments.list()[:10]:  # Limitar para evitar excesso
                        data.append(RedditData(
                            id=comment.id,
                            content=comment.body,
                            metadata={
                                "url": submission.url + "#comment",
                                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                                "tags": [subreddit_name],
                                "language": "english",
                                "type": "comment"
                            }
                        ))
                time.sleep(1)  # Respeitar rate limit
            except Exception as e:
                logging.error(f"Erro ao coletar dados de r/{subreddit_name}: {e}")
        return data

    def save_to_json(self, data: List[RedditData]):
        with open(self.output_file, "w", encoding="utf-8") as f:
            json.dump([d.dict() for d in data], f, indent=2, ensure_ascii=False)
        logging.info(f"Dados salvos em {self.output_file}")

# Exemplo de uso
scraper = RedditScraper(
    client_id="SEU_CLIENT_ID",
    client_secret="SEU_CLIENT_SECRET",
    user_agent="DevAI-R1-Scraper/1.0"
)
data = scraper.fetch_posts(subreddits=["devops", "programming"], limit=50)
scraper.save_to_json(data)