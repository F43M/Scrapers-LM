import requests
import json
import logging
from pydantic import BaseModel
from typing import List

logging.basicConfig(level=logging.INFO)

class RFCData(BaseModel):
    id: str
    content: str
    metadata: dict

class RFCScraper:
    def __init__(self):
        self.base_url = "https://datatracker.ietf.org/doc"
        self.output_file = "rfc_data.json"

    def fetch_rfcs(self, start: int = 1, end: int = 100) -> List[RFCData]:
        data = []
        for rfc_id in range(start, end + 1):
            try:
                url = f"{self.base_url}/rfc{rfc_id}/"
                response = requests.get(url)
                response.raise_for_status()
                content = response.text  # Extrair texto completo (ajustar com BeautifulSoup se necessário)
                data.append(RFCData(
                    id=f"rfc{rfc_id}",
                    content=content[:10000],  # Limitar tamanho
                    metadata={
                        "url": url,
                        "timestamp": response.headers.get("Date", ""),
                        "tags": ["rfc", "ietf"],
                        "language": "english",
                        "type": "rfc"
                    }
                ))
            except Exception as e:
                logging.error(f"Erro ao coletar RFC {rfc_id}: {e}")
        return data

    def save_to_json(self, data: List[RFCData]):
        output = {
            "source": "ietf_rfc",
            "category": "documentacao_tecnica",
            "document_type": "rfc",
            "data": [d.dict() for d in data]
        }
        with open(self.output_file, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        logging.info(f"Dados salvos em {self.output_file}")

# Exemplo de uso
scraper = RFCScraper()
data = scraper.fetch_rfcs(start=1, end=10)
scraper.save_to_json(data)