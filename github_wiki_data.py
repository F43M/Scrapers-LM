import argparse
import json
import logging
import os
from typing import List

import requests
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)

class GitHubWikiData(BaseModel):
    id: str
    content: str
    metadata: dict

class GitHubWikiScraper:
    def __init__(self, token: str | None = None):
        self.base_url = "https://api.github.com"
        self.headers = {"Authorization": f"Bearer {token}"} if token else {}
        self.output_file = "github_wiki_data.json"

    def fetch_wiki(self, repo: str) -> List[GitHubWikiData]:
        data: List[GitHubWikiData] = []

        def recurse(path: str = ""):
            url = f"{self.base_url}/repos/{repo}/contents/{path}".rstrip("/")
            try:
                response = requests.get(url, headers=self.headers)
                response.raise_for_status()
                items = response.json()
                if isinstance(items, dict) and items.get("type") == "file":
                    items = [items]
                for item in items:
                    if item["type"] == "dir":
                        recurse(item["path"])
                    elif item["type"] == "file" and item["name"].lower().endswith((".md", ".rst")):
                        file_content = requests.get(item["download_url"]).text
                        data.append(
                            GitHubWikiData(
                                id=item["sha"],
                                content=file_content,
                                metadata={
                                    "url": item["html_url"],
                                    "path": item["path"],
                                    "tags": [repo, item["name"]],
                                    "language": "markdown" if item["name"].lower().endswith(".md") else "rst",
                                    "type": self.classify_document(item["name"], file_content),
                                },
                            )
                        )
            except Exception as e:
                logging.error(f"Erro ao coletar arquivos em {path}: {e}")

        recurse("")
        return data


    def classify_document(self, filename: str, content: str) -> str:
        filename = filename.lower()
        if "readme" in filename:
            return "readme"
        elif "contributing" in filename:
            return "contributing"
        elif "architecture" in filename or "architecture" in content.lower():
            return "architecture_overview"
        elif "api" in filename or "endpoint" in content.lower():
            return "api_documentation"
        return "documentation"

    def save_to_json(self, data: List[GitHubWikiData]):
        output = {"data": [d.dict() for d in data]}
        with open(self.output_file, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        logging.info(f"Dados salvos em {self.output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Coleta arquivos de documentação do GitHub")
    parser.add_argument("--repo", required=True, help="repositório no formato owner/name")
    parser.add_argument("--token", default=os.getenv("GITHUB_TOKEN"), help="token de acesso opcional")
    args = parser.parse_args()

    scraper = GitHubWikiScraper(token=args.token)
    data = scraper.fetch_wiki(repo=args.repo)
    scraper.save_to_json(data)
