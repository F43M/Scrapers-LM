import requests
import json
import logging
from pydantic import BaseModel
from typing import List

logging.basicConfig(level=logging.INFO)

class GitHubData(BaseModel):
    id: str
    content: str
    metadata: dict

class GitHubScraper:
    def __init__(self, token: str):
        self.base_url = "https://api.github.com"
        self.headers = {"Authorization": f"Bearer {token}"}
        self.output_file = "github_issues.json"

    def fetch_issues(self, repo: str, pages: int = 5) -> List[GitHubData]:
        data = []
        for page in range(1, pages + 1):
            try:
                params = {"state": "all", "page": page, "per_page": 100}
                response = requests.get(f"{self.base_url}/repos/{repo}/issues", headers=self.headers, params=params)
                response.raise_for_status()
                items = response.json()
                for item in items:
                    data.append(GitHubData(
                        id=str(item["id"]),
                        content=item["title"] + "\n" + item.get("body", ""),
                        metadata={
                            "url": item["html_url"],
                            "timestamp": item["created_at"],
                            "tags": item.get("labels", []),
                            "language": "unknown",
                            "type": "issue"
                        }
                    ))
            except Exception as e:
                logging.error(f"Erro ao coletar issues de {repo}, página {page}: {e}")
        return data

    def save_to_json(self, data: List[GitHubData]):
        with open(self.output_file, "w", encoding="utf-8") as f:
            json.dump([d.dict() for d in data], f, indent=2, ensure_ascii=False)
        logging.info(f"Dados salvos em {self.output_file}")

# Exemplo de uso
scraper = GitHubScraper(token="SEU_TOKEN")
data = scraper.fetch_issues(repo="kubernetes/kubernetes", pages=5)
scraper.save_to_json(data)