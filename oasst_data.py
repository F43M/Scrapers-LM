from datasets import load_dataset
import json
import logging

logging.basicConfig(level=logging.INFO)

class OASSTScraper:
    def __init__(self):
        self.output_file = "oasst_data.json"

    def fetch_data(self):
        data = []
        try:
            dataset = load_dataset("OpenAssistant/oasst1", split="train")
            for item in dataset:
                data.append({
                    "id": item["message_id"],
                    "content": item["text"],
                    "metadata": {
                        "url": "https://huggingface.co/datasets/OpenAssistant/oasst1",
                        "timestamp": item.get("created_date", ""),
                        "tags": ["feedback", "human"],
                        "language": item.get("lang", "english"),
                        "type": "conversation"
                    }
                })
        except Exception as e:
            logging.error(f"Erro ao coletar OASST: {e}")
        return data

    def save_to_json(self, data):
        with open(self.output_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logging.info(f"Dados salvos em {self.output_file}")

# Exemplo de uso
scraper = OASSTScraper()
data = scraper.fetch_data()
scraper.save_to_json(data)