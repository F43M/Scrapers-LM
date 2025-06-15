import requests
import json
import logging
import os
import argparse
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

    def fetch_issues(self, repo: str, max_pages: int = 5) -> List[GitHubData]:
        data = []
        url = f"{self.base_url}/repos/{repo}/issues"
        params = {"state": "all", "per_page": 100}
        page = 0

        while url and page < max_pages:
            try:
                response = requests.get(url, headers=self.headers, params=params)
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
                logging.error(f"Erro ao coletar issues de {repo}, página {page + 1}: {e}")
                break

            link_header = response.headers.get("Link", "")
            next_url = None
            if link_header:
                for part in link_header.split(','):
                    if 'rel="next"' in part:
                        next_url = part[part.find('<') + 1:part.find('>')]
                        break

            url = next_url
            params = None  # next_url já possui os parâmetros
            page += 1

        return data

    def save_to_json(self, data: List[GitHubData]):
        with open(self.output_file, "w", encoding="utf-8") as f:
            json.dump([d.dict() for d in data], f, indent=2, ensure_ascii=False)
        logging.info(f"Dados salvos em {self.output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Coleta issues de um repositório GitHub")
    parser.add_argument("--repo", required=True, help="Repositório no formato owner/repo")
    parser.add_argument("--token", default=os.getenv("GITHUB_TOKEN"), help="Token de acesso do GitHub")
    parser.add_argument("--max-pages", type=int, default=5, help="Número máximo de páginas a coletar")
    args = parser.parse_args()

    if not args.token:
        parser.error("Token não informado e GITHUB_TOKEN ausente")

    scraper = GitHubScraper(token=args.token)
    data = scraper.fetch_issues(repo=args.repo, max_pages=args.max_pages)
    scraper.save_to_json(data)
