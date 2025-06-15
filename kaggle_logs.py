import kaggle
import json
import logging

logging.basicConfig(level=logging.INFO)

class KaggleScraper:
    def __init__(self):
        self.output_file = "kaggle_logs.json"
        kaggle.api.authenticate()

    def fetch_datasets(self, search_term: str = "logs") -> list:
        datasets = kaggle.api.dataset_list(search=search_term)
        data = []
        for dataset in datasets[:5]:  # Limitar para testes
            try:
                files = kaggle.api.dataset_view(dataset.ref)
                for file in files["files"]:
                    if file["name"].endswith(".log") or "log" in file["name"].lower():
                        data.append({
                            "id": file["name"],
                            "content": "Conteúdo do log (baixe o arquivo para processar)",
                            "metadata": {
                                "url": dataset.url,
                                "timestamp": file["creationDate"],
                                "tags": ["logs", dataset.ref],
                                "language": "log",
                                "type": "log"
                            }
                        })
            except Exception as e:
                logging.error(f"Erro ao coletar dataset {dataset.ref}: {e}")
        return data

    def save_to_json(self, data: list):
        with open(self.output_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logging.info(f"Dados salvos em {self.output_file}")

# Exemplo de uso
scraper = KaggleScraper()
data = scraper.fetch_datasets()
scraper.save_to_json(data)