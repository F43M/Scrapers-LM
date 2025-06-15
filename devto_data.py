import requests
import json
import logging
from pydantic import BaseModel
from typing import List

logging.basicConfig(level=logging.INFO)

class DevToData(BaseModel):
    id: str
    content: str
    metadata: dict

class DevToScraper:
    def __init__(self):
        self.base_url = "https://dev.to/api/articles"
        self.output_file = "devto_data.json"

    def fetch_articles(self, tags: List[str] = ["documentation", "technicalwriting"], per_page: int = 100) -> List[DevToData]:
        data = []
        for tag in tags:
            try:
                params = {"tag": tag, "per_page": per_page}
                response = requests.get(self.base_url, params=params)
                response.raise_for_status()
                articles = response.json()
                for article in articles:
                    data.append(DevToData(
                        id=str(article["id"]),
                        content=article["title"] + "\n" + article.get("description", ""),
                        metadata={
                            "url": article["url"],
                            "timestamp": article["published_at"],
                            "tags": article["tag_list"],
                            "language": "english",
                            "type": "article"
                        }
                    ))
            except Exception as e:
                logging.error(f"Erro ao coletar artigos para tag {tag}: {e}")
        return data

    def save_to_json(self, data: List[DevToData]):
        output = {
            "source": "devto",
            "category": "documentacao_tecnica",
            "document_type": "article",
            "data": [d.dict() for d in data]
        }
        with open(self.output_file, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        logging.info(f"Dados salvos em {self.output_file}")

# Exemplo de uso
scraper = DevToScraper()
data = scraper.fetch_articles(tags=["documentation", "technicalwriting"])
scraper.save_to_json(data)