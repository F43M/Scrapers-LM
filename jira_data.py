import requests
import json
import logging
from pydantic import BaseModel
from typing import List

logging.basicConfig(level=logging.INFO)

class JiraData(BaseModel):
    id: str
    content: str
    metadata: dict

class JiraScraper:
    def __init__(self, email: str, api_token: str, base_url: str):
        self.base_url = base_url.rstrip("/") + "/rest/api/3"
        self.auth = (email, api_token)
        self.output_file = "jira_data.json"

    def fetch_issues(self, project_key: str, max_results: int = 100) -> List[JiraData]:
        data = []
        try:
            params = {
                "jql": f"project={project_key}",
                "maxResults": max_results
            }
            response = requests.get(
                f"{self.base_url}/search",
                auth=self.auth,
                params=params
            )
            response.raise_for_status()
            issues = response.json()["issues"]
            for issue in issues:
                data.append(JiraData(
                    id=issue["key"],
                    content=issue["fields"]["summary"] + "\n" + (issue["fields"].get("description") or ""),
                    metadata={
                        "url": f"{self.base_url.replace('/rest/api/3', '')}/browse/{issue['key']}",
                        "timestamp": issue["fields"]["created"],
                        "tags": [project_key],
                        "language": "english",
                        "type": "issue"
                    }
                ))
        except Exception as e:
            logging.error(f"Erro ao coletar issues de {project_key}: {e}")
        return data

    def save_to_json(self, data: List[JiraData]):
        with open(self.output_file, "w", encoding="utf-8") as f:
            json.dump([d.dict() for d in data], f, indent=2, ensure_ascii=False)
        logging.info(f"Dados salvos em {self.output_file}")

# Exemplo de uso
scraper = JiraScraper(
    email="seu_email",
    api_token="SEU_API_TOKEN",
    base_url="https://your-jira-instance.atlassian.net"
)
data = scraper.fetch_issues(project_key="PROJ", max_results=50)
scraper.save_to_json(data)