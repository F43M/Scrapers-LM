from slack_sdk import WebClient
import json
import logging
from pydantic import BaseModel
from typing import List

logging.basicConfig(level=logging.INFO)

class SlackData(BaseModel):
    id: str
    content: str
    metadata: dict

class SlackScraper:
    def __init__(self, token: str):
        self.client = WebClient(token=token)
        self.output_file = "slack_data.json"

    def fetch_messages(self, channel_id: str, limit: int = 100) -> List[SlackData]:
        data = []
        cursor = None
        try:
            while True:
                response = self.client.conversations_history(
                    channel=channel_id,
                    limit=limit,
                    cursor=cursor,
                )
                for message in response.get("messages", []):
                    data.append(
                        SlackData(
                            id=message.get("ts", ""),
                            content=message.get("text", ""),
                            metadata={
                                "url": f"https://slack.com/archives/{channel_id}",
                                "timestamp": message.get("ts", ""),
                                "tags": [channel_id],
                                "language": "english",
                                "type": "message",
                            },
                        )
                    )
                cursor = response.get("response_metadata", {}).get("next_cursor")
                if not cursor:
                    break
        except Exception as e:
            logging.error(f"Erro ao coletar mensagens de {channel_id}: {e}")
        return data

    def save_to_json(self, data: List[SlackData]):
        with open(self.output_file, "w", encoding="utf-8") as f:
            json.dump([d.dict() for d in data], f, indent=2, ensure_ascii=False)
        logging.info(f"Dados salvos em {self.output_file}")

if __name__ == "__main__":
    import argparse
    import os

    parser = argparse.ArgumentParser(description="Slack message scraper")
    parser.add_argument("channel_id", help="Slack channel ID")
    parser.add_argument(
        "--token",
        help="Slack token (or set SLACK_TOKEN env var)",
        default=os.getenv("SLACK_TOKEN"),
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=100,
        help="Messages per request (max 100)",
    )
    args = parser.parse_args()

    if not args.token:
        parser.error("Slack token must be provided via --token or SLACK_TOKEN env var")

    scraper = SlackScraper(token=args.token)
    messages = scraper.fetch_messages(channel_id=args.channel_id, limit=args.limit)
    scraper.save_to_json(messages)
