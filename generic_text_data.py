from datasets import load_dataset
import json
import logging

logging.basicConfig(level=logging.INFO)

class GenericTextScraper:
    def __init__(self):
        self.output_file = "generic_text_data.json"

    def fetch_data(self, dataset_name: str, split: str = "train"):
        data = []
        try:
            dataset = load_dataset(dataset_name, split=split, streaming=True)
            for i, item in enumerate(dataset.take(1000)):  # Limitar para teste
                data.append({
                    "id": str(i),
                    "content": item.get("text", ""),
                    "metadata": {
                        "url": f"https://huggingface.co/datasets/{dataset_name}",
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "tags": ["generic", dataset_name],
                        "language": "english",
                        "type": "text"
                    }
                })
        except Exception as e:
            logging.error(f"Erro ao coletar {dataset_name}: {e}")
        return data

    def save_to_json(self, data):
        with open(self.output_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logging.info(f"Dados salvos em {self.output_file}")

# Exemplo de uso
scraper = GenericTextScraper()
data = scraper.fetch_data(dataset_name="openwebtext")
scraper.save_to_json(data)