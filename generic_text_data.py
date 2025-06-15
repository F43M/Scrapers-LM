from datasets import load_dataset
import json
import logging
import time
import argparse
from typing import Optional

logging.basicConfig(level=logging.INFO)

class GenericTextScraper:
    def __init__(self, output_file: str = "generic_text_data.json"):
        self.output_file = output_file

    def fetch_data(self, dataset_name: str, split: str = "train", max_samples: Optional[int] = None):
        """Baixa amostras de um dataset do HuggingFace de forma incremental."""
        count = 0
        try:
            dataset = load_dataset(dataset_name, split=split, streaming=True)
            with open(self.output_file, "w", encoding="utf-8") as f:
                for item in dataset:
                    record = {
                        "id": str(count),
                        "content": item.get("text", ""),
                        "metadata": {
                            "url": f"https://huggingface.co/datasets/{dataset_name}",
                            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                            "tags": ["generic", dataset_name],
                            "language": "english",
                            "type": "text",
                        },
                    }
                    f.write(json.dumps(record, ensure_ascii=False) + "\n")
                    count += 1
                    if max_samples is not None and count >= max_samples:
                        break
        except Exception as e:
            logging.error(f"Erro ao coletar {dataset_name}: {e}")
        logging.info(f"Dados salvos em {self.output_file}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Coleta textos genéricos de datasets do HuggingFace")
    parser.add_argument("dataset_name", help="Nome do dataset no HuggingFace")
    parser.add_argument("--split", default="train", help="Split a ser utilizado")
    parser.add_argument("--max_samples", type=int, default=None, help="Número máximo de amostras")
    parser.add_argument("--output_file", default="generic_text_data.json", help="Arquivo de saída")
    args = parser.parse_args()

    scraper = GenericTextScraper(output_file=args.output_file)
    scraper.fetch_data(dataset_name=args.dataset_name, split=args.split, max_samples=args.max_samples)
