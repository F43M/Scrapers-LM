import os
import requests
import json
import logging
from pydantic import BaseModel
from typing import List
import time
import argparse

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

    def fetch_cves(
        self,
        start_index: int = 0,
        results_per_page: int = 1000,
        max_results: int = 1000,
    ) -> List[CVEData]:
        data: List[CVEData] = []
        current_index = start_index
        while len(data) < max_results:
            remaining = max_results - len(data)
            per_page = min(results_per_page, remaining)
            try:
                params = {
                    "startIndex": current_index,
                    "resultsPerPage": per_page,
                    "apiKey": self.api_key,
                }
                response = requests.get(self.base_url, params=params)
                response.raise_for_status()

                items = response.json().get("vulnerabilities", [])
                for item in items:
                    cve = item["cve"]
                    data.append(
                        CVEData(
                            id=cve["id"],
                            content=cve["descriptions"][0]["value"],
                            metadata={
                                "url": f"https://nvd.nist.gov/vuln/detail/{cve['id']}",
                                "timestamp": cve["published"],
                                "tags": cve.get("metrics", {})
                                .get("cvssMetricV31", [{}])[0]
                                .get("cvssData", {})
                                .get("attackVector", []),
                                "language": "unknown",
                                "type": "cve",
                            },
                        )
                    )

                remaining_header = response.headers.get("X-Rate-Limit-Remaining")
                if remaining_header is not None:
                    try:
                        remaining_limit = int(remaining_header)
                        if remaining_limit <= 1:
                            logging.info("Aguardando devido ao limite de taxa...")
                            time.sleep(30)
                    except ValueError:
                        pass

                if not items or len(items) < per_page:
                    break

                current_index += per_page
            except Exception as e:
                logging.error(f"Erro ao coletar CVEs: {e}")
                break

        return data

    def save_to_json(self, data: List[CVEData]):
        with open(self.output_file, "w", encoding="utf-8") as f:
            json.dump([d.dict() for d in data], f, indent=2, ensure_ascii=False)
        logging.info(f"Dados salvos em {self.output_file}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Coleta CVEs do NVD")
    parser.add_argument(
        "--api-key",
        default=os.getenv("NVD_API_KEY"),
        help="Chave de API do NVD ou variavel de ambiente NVD_API_KEY",
    )
    parser.add_argument("--start-index", type=int, default=0)
    parser.add_argument("--results-per-page", type=int, default=1000)
    parser.add_argument(
        "--max-results",
        type=int,
        default=1000,
        help="Numero total de CVEs a serem baixados",
    )
    parser.add_argument(
        "--output",
        default="cve_data.json",
        help="Arquivo de saida",
    )

    args = parser.parse_args()

    if not args.api_key:
        parser.error("API key nao informada e variavel NVD_API_KEY nao definida")

    scraper = NVDApiScraper(api_key=args.api_key)
    scraper.output_file = args.output
    data = scraper.fetch_cves(
        start_index=args.start_index,
        results_per_page=args.results_per_page,
        max_results=args.max_results,
    )
    scraper.save_to_json(data)


if __name__ == "__main__":
    main()
