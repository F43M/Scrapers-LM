import requests
import json
import logging
from pydantic import BaseModel
from typing import List

logging.basicConfig(level=logging.INFO)

class GitHubCommentData(BaseModel):
    id: str
    content: str
    metadata: dict

class GitHubCommentScraper:
    def __init__(self, token: str):
        self.base_url = "https://api.github.com"
        self.headers = {"Authorization": f"Bearer {token}"}
        self.output_file = "github_comments_data.json"

    def fetch_comments(self, repo: str, pages: int = 5) -> List[GitHubCommentData]:
        data = []
        for page in range(1, pages + 1):
            try:
                # Coletar comentários de issues
                params = {"page": page, "per_page": 100}
                response = requests.get(
                    f"{self.base_url}/repos/{repo}/issues/comments",
                    headers=self.headers,
                    params=params
                )
                response.raise_for_status()
                items = response.json()
                for item in items:
                    data.append(GitHubCommentData(
                        id=str(item["id"]),
                        content=item["body"],
                        metadata={
                            "url": item["html_url"],
                            "timestamp": item["created_at"],
                            "tags": ["comment", repo],
                            "language": "english",
                            "type": "comment"
                        }
                    ))
            except Exception as e:
                logging.error(f"Erro ao coletar comentários de {repo}, página {page}: {e}")
        return data

    def save_to_json(self, data: List[GitHubCommentData]):
        with open(self.output_file, "w", encoding="utf-8") as f:
            json.dump([d.dict() for d in data], f, indent=2, ensure_ascii=False)
        logging.info(f"Dados salvos em {self.output_file}")

# Exemplo de uso
scraper = GitHubCommentScraper(token="SEU_TOKEN")
data = scraper.fetch_comments(repo="kubernetes/kubernetes", pages=5)
scraper.save_to_json(data)