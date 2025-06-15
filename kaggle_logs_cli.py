import argparse
import json
import logging
import os
import zipfile
from typing import List, Dict

import kaggle

logging.basicConfig(level=logging.INFO)

MAX_LOG_SIZE = 10000  # bytes

class KaggleLogScraper:
    def __init__(self, max_bytes: int = MAX_LOG_SIZE, output_file: str = "kaggle_logs_cli.json"):
        self.max_bytes = max_bytes
        self.output_file = output_file
        kaggle.api.authenticate()

    def _download_and_read_file(self, dataset_ref: str, file_name: str, temp_dir: str) -> str:
        """Download a single file from Kaggle and return its content."""
        kaggle.api.dataset_download_file(dataset_ref, file_name, path=temp_dir, force=True, quiet=True)
        zipped_path = os.path.join(temp_dir, file_name)
        if not os.path.exists(zipped_path):
            zipped_path = zipped_path + ".zip"
        if zipped_path.endswith('.zip'):
            with zipfile.ZipFile(zipped_path) as z:
                inner_name = z.namelist()[0]
                with z.open(inner_name) as f:
                    return f.read(self.max_bytes).decode("utf-8", errors="ignore")
        with open(zipped_path, "rb") as f:
            return f.read(self.max_bytes).decode("utf-8", errors="ignore")

    def fetch_logs(self, search_term: str, limit: int) -> List[Dict]:
        datasets = kaggle.api.dataset_list(search=search_term)
        data = []
        temp_dir = "temp_kaggle_logs"
        os.makedirs(temp_dir, exist_ok=True)
        for dataset in datasets[:limit]:
            try:
                files = kaggle.api.dataset_list_files(dataset.ref)
                for f in files.get("files", []):
                    name = f.get("name")
                    if not name:
                        continue
                    if name.lower().endswith(".log") or name.lower().endswith(".txt"):
                        content = self._download_and_read_file(dataset.ref, name, temp_dir)
                        data.append({
                            "id": f"{dataset.ref}/{name}",
                            "content": content,
                            "metadata": {
                                "url": f"https://www.kaggle.com/datasets/{dataset.ref}",
                                "timestamp": f.get("dateCreated", ""),
                                "tags": ["kaggle", dataset.ref],
                                "language": "log",
                                "type": "log"
                            }
                        })
            except Exception as e:
                logging.error(f"Erro ao processar {dataset.ref}: {e}")
        try:
            for item in os.listdir(temp_dir):
                os.remove(os.path.join(temp_dir, item))
            os.rmdir(temp_dir)
        except Exception:
            pass
        return data

    def save_to_json(self, data: List[Dict]):
        with open(self.output_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logging.info(f"Dados salvos em {self.output_file}")

def main():
    parser = argparse.ArgumentParser(description="Baixa logs de datasets da Kaggle")
    parser.add_argument("term", help="Termo de busca")
    parser.add_argument("--limit", type=int, default=5, help="Número máximo de datasets")
    args = parser.parse_args()

    scraper = KaggleLogScraper()
    logs = scraper.fetch_logs(args.term, args.limit)
    scraper.save_to_json(logs)

if __name__ == "__main__":
    main()
