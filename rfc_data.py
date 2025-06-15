import argparse
import json
import logging
import time
from typing import List

import requests
from bs4 import BeautifulSoup
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)

class RFCData(BaseModel):
    id: str
    content: str
    metadata: dict

class RFCScraper:
    def __init__(self, output_file: str = "rfc_data.json"):
        self.base_url = "https://datatracker.ietf.org/doc"
        self.output_file = output_file

    def fetch_rfcs(
        self,
        start: int = 1,
        end: int = 100,
        retries: int = 3,
        delay: float = 1.0,
    ) -> List[RFCData]:
        data = []
        for rfc_id in range(start, end + 1):
            url = f"{self.base_url}/rfc{rfc_id}/"
            for attempt in range(1, retries + 1):
                try:
                    response = requests.get(url, timeout=10)
                    response.raise_for_status()
                    soup = BeautifulSoup(response.text, "html.parser")
                    text = soup.get_text(separator="\n")
                    data.append(
                        RFCData(
                            id=f"rfc{rfc_id}",
                            content=text.strip(),
                            metadata={
                                "url": url,
                                "timestamp": response.headers.get("Date", ""),
                            },
                        )
                    )
                    break
                except Exception as e:
                    logging.warning(
                        f"Erro ao coletar RFC {rfc_id}, tentativa {attempt}: {e}"
                    )
                    if attempt == retries:
                        logging.error(
                            f"Falha ao coletar RFC {rfc_id} apos {retries} tentativas."
                        )
                    time.sleep(delay)
            time.sleep(delay)
        return data

    def save_to_json(self, data: List[RFCData]):
        with open(self.output_file, "w", encoding="utf-8") as f:
            json.dump([d.dict() for d in data], f, indent=2, ensure_ascii=False)
        logging.info(f"Dados salvos em {self.output_file}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Baixa texto de RFCs do IETF")
    parser.add_argument("--start", type=int, default=1, help="Número inicial do RFC")
    parser.add_argument("--end", type=int, default=100, help="Número final do RFC")
    parser.add_argument("--output", type=str, default="rfc_data.json", help="Arquivo de saída")
    args = parser.parse_args()

    scraper = RFCScraper(output_file=args.output)
    data = scraper.fetch_rfcs(start=args.start, end=args.end)
    scraper.save_to_json(data)


if __name__ == "__main__":
    main()
