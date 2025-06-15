from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import json
import logging
from pydantic import BaseModel
from typing import List

logging.basicConfig(level=logging.INFO)

class ConfluenceData(BaseModel):
    id: str
    content: str
    metadata: dict

class ConfluenceScraper:
    def __init__(self):
        self.output_file = "confluence_data.json"
        options = Options()
        options.headless = True
        self.driver = webdriver.Chrome(options=options)

    def fetch_pages(self, url: str) -> List[ConfluenceData]:
        data = []
        try:
            self.driver.get(url)
            content = self.driver.find_element_by_tag_name("body").text
            data.append(ConfluenceData(
                id=url.split("/")[-1],
                content=content[:10000],  # Limitar tamanho
                metadata={
                    "url": url,
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "tags": ["confluence"],
                    "language": "english",
                    "type": "documentation"
                }
            ))
        except Exception as e:
            logging.error(f"Erro ao coletar {url}: {e}")
        finally:
            self.driver.quit()
        return data

    def save_to_json(self, data: List[ConfluenceData]):
        output = {
            "source": "confluence",
            "category": "documentacao_tecnica",
            "document_type": "mixed",
            "data": [d.dict() for d in data]
        }
        with open(self.output_file, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        logging.info(f"Dados salvos em {self.output_file}")

# Exemplo de uso
scraper = ConfluenceScraper()
data = scraper.fetch_pages(url="https://confluence.atlassian.com/display/OPEN")
scraper.save_to_json(data)