import scrapy
from scrapy.crawler import CrawlerProcess
import json
import logging
from pydantic import BaseModel
from typing import List

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class ReadTheDocsData(BaseModel):
    id: str
    content: str
    metadata: dict

class ReadTheDocsSpider(scrapy.Spider):
    name = "readthedocs_spider"
    start_urls = ["https://readthedocs.org/projects/"]

    def parse(self, response):
        data = []
        # Extrair links de projetos
        for project in response.css("div.project-list-item"):
            project_url = project.css("a::attr(href)").get()
            if project_url:
                yield response.follow(project_url, callback=self.parse_project)
        # Seguir paginação
        next_page = response.css("a.next::attr(href)").get()
        if next_page:
            yield response.follow(next_page, callback=self.parse)

    def parse_project(self, response):
        data = []
        project_name = response.css("h1::text").get(default="").strip()
        for section in response.css("div.section"):
            content = section.css("::text").getall()
            content = " ".join([text.strip() for text in content if text.strip()])
            if content:
                data.append(ReadTheDocsData(
                    id=f"{project_name}_{section.css('::attr(id)').get('')}",
                    content=content,
                    metadata={
                        "url": response.url,
                        "timestamp": response.headers.get("Date", b"").decode(),
                        "tags": ["readthedocs", project_name],
                        "language": "markdown",
                        "type": self.classify_document(content, response.url)
                    }
                ))
        # Salvar dados
        self.save_to_json(data, f"readthedocs_{project_name}.json")
        # Seguir links internos
        for href in response.css("a::attr(href)").getall():
            if href.startswith("/"):
                yield response.follow(href, callback=self.parse_project)

    def classify_document(self, content: str, url: str) -> str:
        """Classificar o tipo de documento com base no conteúdo e URL"""
        if "readme" in url.lower() or "readme" in content.lower():
            return "readme"
        elif "contributing" in url.lower() or "contribute" in content.lower():
            return "contributing"
        elif "api" in url.lower() or "endpoint" in content.lower():
            return "api_documentation"
        return "documentation"

    def save_to_json(self, data: List[ReadTheDocsData], filename: str):
        output = {
            "source": "readthedocs",
            "category": "documentacao_tecnica",
            "document_type": "mixed",
            "data": [d.dict() for d in data]
        }
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        logging.info(f"Dados salvos em {filename}")

# Executar o crawler
process = CrawlerProcess(settings={
    "FEEDS": {},
    "USER_AGENT": "Mozilla/5.0",
    "DOWNLOAD_DELAY": 2,
})
process.crawl(ReadTheDocsSpider)
process.start()