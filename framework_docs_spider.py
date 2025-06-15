import scrapy
from scrapy.crawler import CrawlerProcess
import json
import logging
from pydantic import BaseModel
from typing import List

logging.basicConfig(level=logging.INFO)

class FrameworkDocsData(BaseModel):
    id: str
    content: str
    metadata: dict

class FrameworkDocsSpider(scrapy.Spider):
    name = "framework_docs_spider"
    start_urls = [
        "https://kubernetes.io/docs/",
        "https://developer.hashicorp.com/terraform/docs",
        "https://huggingface.co/docs"
    ]

    def parse(self, response):
        data = []
        for section in response.css("div.section, article"):
            content = section.css("::text").getall()
            content = " ".join([text.strip() for text in content if text.strip()])
            if content:
                data.append(FrameworkDocsData(
                    id=f"{response.url}_{section.css('::attr(id)').get('')}",
                    content=content,
                    metadata={
                        "url": response.url,
                        "timestamp": response.headers.get("Date", b"").decode(),
                        "tags": ["framework_docs", response.url.split("/")[2]],
                        "language": "markdown",
                        "type": self.classify_document(content, response.url)
                    }
                ))
        self.save_to_json(data, f"framework_docs_{response.url.split('/')[2]}.json")
        for href in response.css("a::attr(href)").getall():
            if href.startswith("/"):
                yield response.follow(href, callback=self.parse)

    def classify_document(self, content: str, url: str) -> str:
        if "setup" in url.lower() or "installation" in content.lower():
            return "deployment_guide"
        elif "api" in url.lower() or "endpoint" in content.lower():
            return "api_documentation"
        elif "monitoring" in url.lower() or "metrics" in content.lower():
            return "monitoring_guide"
        return "documentation"

    def save_to_json(self, data: List[FrameworkDocsData], filename: str):
        output = {
            "source": "framework_docs",
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
process.crawl(FrameworkDocsSpider)
process.start()