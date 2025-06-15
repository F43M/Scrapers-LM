import requests
import json
import time
import logging
from pydantic import BaseModel, Field
from typing import List

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
        data = []
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
                        "key": self.api_key
                    }
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
                    time.sleep(1)  # Respeitar rate limit
                except Exception as e:
                    logging.error(f"Erro ao coletar dados para tag {tag}, página {page}: {e}")
        return data

    def save_to_json(self, data: List[StackOverflowData]):
        with open(self.output_file, "w", encoding="utf-8") as f:
            json.dump([d.dict() for d in data], f, indent=2, ensure_ascii=False)
        logging.info(f"Dados salvos em {self.output_file}")

# Exemplo de uso
scraper = StackOverflowScraper(api_key= "sua_api_key_aqui")
data = scraper.fetch_questions(tags=["python", "devops", "cloud"], pages=5)
scraper.save_to_json(data)