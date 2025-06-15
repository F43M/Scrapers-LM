import argparse
import json
import logging
import os
import time
from typing import List

import requests
from pydantic import BaseModel

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Modelo Pydantic para validação
class StackOverflowData(BaseModel):
    id: str
    content: str
    metadata: dict

class StackOverflowScraper:
    def __init__(self, api_key: str):
        self.base_url = "https://api.stackexchange.com/2.3"
        self.api_key = api_key
        self.output_file = "QA_stack_data.json"

    def fetch_questions(self, tags: List[str], pages: int = 5) -> List[StackOverflowData]:
        data: List[StackOverflowData] = []
        for tag in tags:
            page = 1
            backoff = 1
            while True:
                try:
                    params = {
                        "page": page,
                        "pagesize": 100,
                        "order": "desc",
                        "sort": "votes",
                        "tagged": tag,
                        "site": "stackoverflow",
                        "filter": "withbody",
                    }
                    if self.api_key:
                        params["key"] = self.api_key
                    response = requests.get(f"{self.base_url}/questions", params=params)
                    if response.status_code == 429:
                        logging.warning("Rate limit excedido. Aguardando %s segundos", backoff)
                        time.sleep(backoff)
                        backoff = min(backoff * 2, 60)
                        continue
                    response.raise_for_status()
                    backoff = 1
                    items = response.json().get("items", [])
                    for item in items:
                        data.append(
                            StackOverflowData(
                                id=str(item.get("question_id")),
                                content=item.get("title", "") + "\n" + item.get("body", ""),
                                metadata={
                                    "url": item.get("link"),
                                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                                    "tags": item.get("tags", []),
                                    "language": item.get("language", "unknown"),
                                    "type": "question",
                                },
                            )
                        )
                    if not response.json().get("has_more") or not items:
                        break
                    page += 1
                    if page > pages:
                        break
                    time.sleep(1)
                except Exception as e:
                    logging.error(
                        f"Erro ao coletar dados para tag {tag}, página {page}: {e}"
                    )
                    break
        return data

    def save_to_json(self, data: List[StackOverflowData]):
        with open(self.output_file, "w", encoding="utf-8") as f:
            json.dump([d.dict() for d in data], f, indent=2, ensure_ascii=False)
        logging.info(f"Dados salvos em {self.output_file}")

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Baixa questões do StackOverflow")
    parser.add_argument("--api-key", help="Chave da API do StackExchange")
    parser.add_argument("--tags", required=True, help="Lista de tags separadas por vírgula")
    parser.add_argument("--pages", type=int, default=5, help="Número máximo de páginas por tag")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    api_key = args.api_key or os.getenv("STACK_API_KEY")
    tags = [t.strip() for t in args.tags.split(",") if t.strip()]
    scraper = StackOverflowScraper(api_key=api_key)
    data = scraper.fetch_questions(tags=tags, pages=args.pages)
    scraper.save_to_json(data)
