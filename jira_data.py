import argparse
import json
import logging
from typing import List

import requests
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)

class JiraData(BaseModel):
    id: str
    content: str
    metadata: dict

class JiraScraper:
    def __init__(self, email: str, api_token: str, base_url: str, output_file: str = "jira_data.json"):
        self.base_url = base_url.rstrip("/") + "/rest/api/3"
        self.auth = (email, api_token)
        self.output_file = output_file

    def fetch_issues(self, project_key: str, max_results: int = 100) -> List[JiraData]:
        data = []
        start_at = 0
        while True:
            params = {
                "jql": f"project={project_key}",
                "maxResults": max_results,
                "startAt": start_at,
            }
            try:
                response = requests.get(
                    f"{self.base_url}/search",
                    auth=self.auth,
                    params=params,
                )
                if response.status_code >= 400:
                    logging.error(
                        "Erro HTTP %s ao coletar issues: %s",
                        response.status_code,
                        response.text,
                    )
                    break
                issues = response.json().get("issues", [])
                if not issues:
                    break
                for issue in issues:
                    data.append(
                        JiraData(
                            id=issue["key"],
                            content=issue["fields"]["summary"]
                            + "\n"
                            + (issue["fields"].get("description") or ""),
                            metadata={
                                "url": f"{self.base_url.replace('/rest/api/3', '')}/browse/{issue['key']}",
                                "timestamp": issue["fields"]["created"],
                                "tags": [project_key],
                                "language": "english",
                                "type": "issue",
                            },
                        )
                    )
                start_at += max_results
            except Exception as e:
                logging.error(f"Erro ao coletar issues de {project_key}: {e}")
                break
        return data

    def save_to_json(self, data: List[JiraData]):
        output = {
            "source": "jira",
            "category": "issues",
            "document_type": "issue",
            "data": [d.dict() for d in data],
        }
        with open(self.output_file, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        logging.info(f"Dados salvos em {self.output_file}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Coletar issues do Jira")
    parser.add_argument("--email", required=True, help="Email de acesso")
    parser.add_argument("--api_token", required=True, help="Token da API")
    parser.add_argument("--base_url", required=True, help="URL base do Jira")
    parser.add_argument("--project_key", required=True, help="Chave do projeto")
    parser.add_argument("--max_results", type=int, default=100, help="Quantidade de resultados por requisi\u00e7\u00e3o")
    parser.add_argument("--output", default="jira_data.json", help="Arquivo de sa\u00edda")
    args = parser.parse_args()

    scraper = JiraScraper(
        email=args.email,
        api_token=args.api_token,
        base_url=args.base_url,
        output_file=args.output,
    )
    issues = scraper.fetch_issues(project_key=args.project_key, max_results=args.max_results)
    scraper.save_to_json(issues)
