import requests
import json
import logging
from pydantic import BaseModel
from typing import List

logging.basicConfig(level=logging.INFO)

class CVEData(BaseModel):
    id: str
    content: str
    metadata: dict

class NVDApiScraper:
    def __init__(self, api_key: str):
        self.base_url = "https://services.nvd.nist.gov/rest/json/cves/2.0"
        self.api_key = api_key
        self.output_file = "cve_data.json"

    def fetch_cves(self, start_index: int = 0, results_per_page: int = 1000) -> List[CVEData]:
        data = []
        try:
            params = {
                "startIndex": start_index,
                "resultsPerPage": results_per_page,
                "apiKey": self.api_key
            }
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            items = response.json().get("vulnerabilities", [])
            for item in items:
                cve = item["cve"]
                data.append(CVEData(
                    id=cve["id"],
                    content=cve["descriptions"][0]["value"],
                    metadata={
                        "url": f"https://nvd.nist.gov/vuln/detail/{cve['id']}",
                        "timestamp": cve["published"],
                        "tags": cve.get("metrics", {}).get("cvssMetricV31", [{}])[0].get("cvssData", {}).get("attackVector", []),
                        "language": "unknown",
                        "type": "cve"
                    }
                ))
        except Exception as e:
            logging.error(f"Erro ao coletar CVEs: {e}")
        return data

    def save_to_json(self, data: List[CVEData]):
        with open(self.output_file, "w", encoding="utf-8") as f:
            json.dump([d.dict() for d in data], f, indent=2, ensure_ascii=False)
        logging.info(f"Dados salvos em {self.output_file}")

# Exemplo de uso
scraper = NVDApiScraper(api_key="SUA_API_KEY")
data = scraper.fetch_cves()
scraper.save_to_json(data)