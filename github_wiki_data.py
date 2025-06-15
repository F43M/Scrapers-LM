import requests
import json
import logging
from pydantic import BaseModel
from typing import List

logging.basicConfig(level=logging.INFO)

class GitHubWikiData(BaseModel):
    id: str
    content: str
    metadata: dict

class GitHubWikiScraper:
    def __init__(self, token: str):
        self.base_url = "https://api.github.com"
        self.headers = {"Authorization": f"Bearer {token}"}
        self.output_file = "github_wiki_data.json"

    def fetch_wiki(self, repo: str) -> List[GitHubWikiData]:
        data = []
        try:
            # Buscar arquivos do repositório (ex.: docs/, README.md, CONTRIBUTING.md)
            response = requests.get(
                f"{self.base_url}/repos/{repo}/contents/docs",
                headers=self.headers
            )
            response.raise_for_status()
            files = response.json()
            for file in files:
                if file["name"].endswith((".md", ".rst")):
                    file_content = requests.get(file["download_url"]).text
                    data.append(GitHubWikiData(
                        id=file["sha"],
                        content=file_content,
                        metadata={
                            "url": file["html_url"],
                            "timestamp": file["last_modified"],
                            "tags": [repo, file["name"]],
                            "language": "markdown" if file["name"].endswith(".md") else "rst",
                            "type": self.classify_document(file["name"], file_content)
                        }
                    ))
        except Exception as e:
            logging.error(f"Erro ao coletar wiki de {repo}: {e}")
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
        output = {
            "source": "github_wiki",
            "category": "documentacao_tecnica",
            "document_type": "mixed",
            "data": [d.dict() for d in data]
        }
        with open(self.output_file, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        logging.info(f"Dados salvos em {self.output_file}")

# Exemplo de uso
scraper = GitHubWikiScraper(token="SEU_TOKEN")
data = scraper.fetch_wiki(repo="kubernetes/website")
scraper.save_to_json(data)