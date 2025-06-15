import argparse
import json
import logging
import os
from typing import List, Optional

import requests
from pydantic import BaseModel

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

    def fetch_issues(self, repo: str, max_pages: Optional[int] = None) -> List[GitHubData]:
        data: List[GitHubData] = []
        url = f"{self.base_url}/repos/{repo}/issues"
        params = {"state": "all", "per_page": 100}
        page = 0
        while url:
            if max_pages is not None and page >= max_pages:
                break
            try:
                response = requests.get(url, headers=self.headers, params=params)
                response.raise_for_status()
                items = response.json()
                for item in items:
                    data.append(
                        GitHubData(
                            id=str(item.get("id")),
                            content=item.get("title", "") + "\n" + item.get("body", ""),
                            metadata={
                                "url": item.get("html_url", ""),
                                "timestamp": item.get("created_at", ""),
                                "tags": item.get("labels", []),
                                "language": "unknown",
                                "type": "issue",
                            },
                        )
                    )
                page += 1
                next_url = None
                links = requests.utils.parse_header_links(
                    response.headers.get("Link", "")
                )
                for link in links:
                    if link.get("rel") == "next":
                        next_url = link.get("url")
                        break
                url = next_url
                params = None  # next_url already contains query params
            except Exception as e:
                logging.error(f"Erro ao coletar issues de {repo}, página {page}: {e}")
                break
        return data

    def save_to_json(self, data: List[GitHubData]):
        with open(self.output_file, "w", encoding="utf-8") as f:
            json.dump([d.dict() for d in data], f, indent=2, ensure_ascii=False)
        logging.info(f"Dados salvos em {self.output_file}")

def main() -> None:
    parser = argparse.ArgumentParser(description="Scrape GitHub issues")
    parser.add_argument("--repo", default=os.getenv("GITHUB_REPO"), help="owner/repo")
    parser.add_argument("--token", default=os.getenv("GITHUB_TOKEN"), help="GitHub token")
    parser.add_argument("--max-pages", type=int, default=None, help="Stop after N pages (optional)")
    args = parser.parse_args()

    if not args.repo or not args.token:
        parser.error("Repository and token são obrigatórios via argumento ou variável de ambiente")

    scraper = GitHubScraper(token=args.token)
    data = scraper.fetch_issues(repo=args.repo, max_pages=args.max_pages)
    scraper.save_to_json(data)


if __name__ == "__main__":
    main()
