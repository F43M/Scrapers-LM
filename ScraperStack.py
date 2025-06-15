import argparse
import json
import logging
import time
from datetime import datetime
from typing import List, Optional

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
    def __init__(self, api_key: str, output_file: str = "QA_stack_data.json"):
        self.base_url = "https://api.stackexchange.com/2.3"
        self.api_key = api_key
        self.output_file = output_file

    def fetch_questions(
        self,
        tags: List[str],
        pages: int = 5,
        min_date: Optional[str] = None,
    ) -> List[StackOverflowData]:
        data = []
        fromdate = None
        if min_date:
            try:
                dt = datetime.strptime(min_date, "%Y-%m-%d")
                fromdate = int(dt.timestamp())
            except ValueError:
                logging.error(f"Data mínima inválida: {min_date}")
        for tag in tags:
            for page in range(1, pages + 1):
                try:
                    params = {
                        "page": page,
                        "pagesize": 100,
                        "order": "desc",
                        "sort": "votes",
                        "tagged": tag,
                        "site": "stackoverflow",
                        "key": self.api_key,
                    }
                    if fromdate:
                        params["fromdate"] = fromdate
                    response = requests.get(f"{self.base_url}/questions", params=params)
                    response.raise_for_status()
                    items = response.json().get("items", [])
                    for item in items:
                        data.append(StackOverflowData(
                            id=str(item["question_id"]),
                            content=item["title"] + "\n" + item.get("body", ""),
                            metadata={
                                "url": item["link"],
                                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                                "tags": item["tags"],
                                "language": item.get("language", "unknown"),
                                "type": "question"
                            }
                        ))
                    remaining = response.headers.get("rate_limit_remaining")
                    if remaining is not None and remaining.isdigit() and int(remaining) == 0:
                        wait_time = int(response.headers.get("rate_limit_reset", "1"))
                        logging.info(f"Rate limit alcançado. Aguardando {wait_time}s...")
                        time.sleep(wait_time)
                    else:
                        time.sleep(1)
                except Exception as e:
                    logging.error(f"Erro ao coletar dados para tag {tag}, página {page}: {e}")
        return data

    def save_to_json(self, data: List[StackOverflowData]):
        with open(self.output_file, "w", encoding="utf-8") as f:
            json.dump([d.dict() for d in data], f, indent=2, ensure_ascii=False)
        logging.info(f"Dados salvos em {self.output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scraper de perguntas do StackOverflow")
    parser.add_argument("--api-key", required=True, help="Chave da API do StackExchange")
    parser.add_argument("--tags", required=True, nargs="+", help="Lista de tags")
    parser.add_argument("--pages", type=int, default=5, help="Número de páginas a coletar")
    parser.add_argument("--min-date", help="Data mínima no formato YYYY-MM-DD")
    parser.add_argument("--output", default="QA_stack_data.json", help="Arquivo de saída")
    args = parser.parse_args()

    scraper = StackOverflowScraper(api_key=args.api_key, output_file=args.output)
    data = scraper.fetch_questions(tags=args.tags, pages=args.pages, min_date=args.min_date)
    scraper.save_to_json(data)
