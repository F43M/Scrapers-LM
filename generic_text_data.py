from datasets import load_dataset
import json
import logging
import time

logging.basicConfig(level=logging.INFO)

class GenericTextScraper:
    def __init__(self, output_file: str = "generic_text_data.json"):
        self.output_file = output_file

    def fetch_data(self, dataset_name: str, split: str = "train", max_samples: int = 1000):
        try:
            dataset = load_dataset(dataset_name, split=split, streaming=True)
            for i, item in enumerate(dataset):
                if i >= max_samples:
                    break
                yield {
                    "id": str(i),
                    "content": item.get("text", ""),
                    "metadata": {
                        "url": f"https://huggingface.co/datasets/{dataset_name}",
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "tags": ["generic", dataset_name],
                        "language": "english",
                        "type": "text"
                    }
                }
        except Exception as e:
            logging.error(f"Erro ao coletar {dataset_name}: {e}")

    def save_to_json(self, data_iter):
        with open(self.output_file, "w", encoding="utf-8") as f:
            f.write("[\n")
            first = True
            for item in data_iter:
                if not first:
                    f.write(",\n")
                json.dump(item, f, ensure_ascii=False)
                first = False
            f.write("\n]")
        logging.info(f"Dados salvos em {self.output_file}")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Baixar dados de um dataset do HuggingFace")
    parser.add_argument("dataset", help="Nome do dataset no HuggingFace")
    parser.add_argument("--split", default="train", help="Split do dataset (train, validation, etc.)")
    parser.add_argument("--max_samples", type=int, default=1000, help="Número máximo de amostras")
    parser.add_argument("--output", default="generic_text_data.json", help="Arquivo de saída")
    args = parser.parse_args()

    scraper = GenericTextScraper(output_file=args.output)
    data_iter = scraper.fetch_data(dataset_name=args.dataset, split=args.split, max_samples=args.max_samples)
    scraper.save_to_json(data_iter)
