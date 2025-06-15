import kaggle
import json
import logging
import os
import shutil
import time
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
        self.temp_dir = "temp_logs"

    def prepare_temp_logs(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
        os.makedirs(self.temp_dir, exist_ok=True)

    def fetch_and_process_logs(self, dataset_ref: str) -> List[KaggleLogData]:
        data = []
        try:
            self.prepare_temp_logs()
            kaggle.api.dataset_download_files(dataset_ref, path=self.temp_dir, unzip=True)
            # Exemplo: processar arquivos .log ou .txt
            for file in os.listdir(self.temp_dir):
                if file.endswith(".log"):
                    with open(f"{self.temp_dir}/{file}", "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
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
            logging.error(f"Erro ao processar {dataset_ref}: {e}")
        return data

    def save_to_json(self, data: List[KaggleLogData]):
        with open(self.output_file, "w", encoding="utf-8") as f:
            json.dump([d.dict() for d in data], f, indent=2, ensure_ascii=False)
        logging.info(f"Dados salvos em {self.output_file}")

# Exemplo de uso
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Process Kaggle logs")
    parser.add_argument("dataset_ref", help="Kaggle dataset reference")
    args = parser.parse_args()

    scraper = KaggleLogScraper()
    data = scraper.fetch_and_process_logs(dataset_ref=args.dataset_ref)
    scraper.save_to_json(data)
