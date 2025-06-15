import kaggle
import pandas as pd
import json
import logging
from pydantic import BaseModel
from typing import List

logging.basicConfig(level=logging.INFO)

class KaggleLogData(BaseModel):
    id: str
    content: str
    metadata: dict

class KaggleLogScraper:
    def __init__(self):
        self.output_file = "kaggle_logs_processed.json"
        kaggle.api.authenticate()

    def fetch_and_process_logs(self, dataset_ref: str) -> List[KaggleLogData]:
        data = []
        try:
            kaggle.api.dataset_download_files(dataset_ref, path="temp_logs", unzip=True)
            # Exemplo: processar arquivos .log ou .txt
            import os
            for file in os.listdir("temp_logs"):
                if file.endswith(".log"):
                    with open(f"temp_logs/{file}", "r", encoding="utf-8", errors="ignore") as f:
                        content = file.read()
                        data.append(KaggleLogData(
                            id=file,
                            content=content[:10000],  # Limitar tamanho
                            metadata={
                                "url": f"https://www.kaggle.com/datasets/{dataset_ref}",
                                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                                "tags": ["log", dataset_ref],
                                "language": "log",
                                "type": "log"
                            }
                        ))
        except Exception as e:
            logging.error(f"Erro ao processar {dataset_ref}: {e}"")
        return data

    def save_to_json(self, data: List[KaggleLogData]):
        with open(self.output_file, "w", encoding="utf-8") as f:
            json.dump([d.dict() for d in data], f, indent=2, ensure_ascii=False)
        logging.info(f"Dados salvos em {self.output_file}")

# Exemplo de uso
scraper = KaggleLogScraper()
data = scraper.fetch_and_process_logs(dataset_ref="dataset/logs")
scraper.save_to_json(data)