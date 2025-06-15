import slack_sdk
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
        self.client = slack_sdk.WebClient(token=token)
        self.output_file = "slack_data.json"

    def fetch_messages(self, channel_id: str, limit: int = 100) -> List[SlackData]:
        data = []
        try:
            response = self.client.conversations_history(
                channel=channel_id,
                limit=limit
            )
            for message in response["messages"]:
                data.append(SlackData(
                    id=message["ts"],
                    content=message["text"],
                    metadata={
                        "url": f"https://slack.com/archives/{channel_id}",
                        "timestamp": message["ts"],
                        "tags": [channel_id],
                        "language": "english",
                        "type": "message"
                    }
                ))
        except Exception as e:
            logging.error(f"Erro ao coletar mensagens de {channel_id}: {e}")
        return data

    def save_to_json(self, data: List[SlackData]):
        with open(self.output_file, "w", encoding="utf-8") as f:
            json.dump([d.dict() for d in data], f, indent=2, ensure_ascii=False)
        logging.info(f"Dados salvos em {self.output_file}")

# Exemplo de uso
scraper = SlackScraper(token="SEU_TOKEN")
data = scraper.fetch_messages(channel_id="CANAL_ID", limit=50)
scraper.save_to_json(data)