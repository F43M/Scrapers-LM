import scrapy
from scrapy.crawler import CrawlerProcess
import argparse
import json
import logging
from pydantic import BaseModel
from typing import List, Dict
from urllib.parse import urlparse, urljoin

logging.basicConfig(level=logging.INFO)

# Projetos suportados e respectivas URLs base
PROJECT_URLS: Dict[str, str] = {
    "kubernetes": "https://kubernetes.io/docs/",
    "terraform": "https://developer.hashicorp.com/terraform/docs",
    "huggingface": "https://huggingface.co/docs",
}

# Limite de profundidade dos links seguidos
DEPTH_LIMIT = 2

class FrameworkDocsData(BaseModel):
    id: str
    content: str
    metadata: dict

class FrameworkDocsSpider(scrapy.Spider):
    name = "framework_docs_spider"

    def __init__(self, base_url: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start_urls = [base_url]
        self.allowed_domains = [urlparse(base_url).netloc]
        self.base_url = base_url.rstrip("/")

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
        self.save_to_json(data, f"framework_docs_{urlparse(self.base_url).netloc}.json")

        for href in response.css("a::attr(href)").getall():
            abs_url = urljoin(response.url, href)
            if abs_url.startswith(self.base_url):
                yield response.follow(abs_url, callback=self.parse)

    def classify_document(self, content: str, url: str) -> str:
        """Classifica o tipo de documento conforme palavras-chave."""
        url = url.lower()
        content = content.lower()
        if "setup" in url or "installation" in content:
            return "deployment_guide"
        if "api" in url or "endpoint" in content:
            return "api_documentation"
        if "monitor" in url or "metric" in content:
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

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Spider para documentações de frameworks")
    parser.add_argument("--project", choices=list(PROJECT_URLS.keys()), help="Projeto conhecido a ser coletado")
    parser.add_argument("--base-url", help="URL base personalizada")
    parser.add_argument("--delay", type=int, default=2, help="Delay entre requisições")
    parser.add_argument("--user-agent", default="Mozilla/5.0", help="User-Agent para o crawler")
    args = parser.parse_args()

    base_url = args.base_url or PROJECT_URLS.get(args.project)
    if not base_url:
        parser.error("Informe --project ou --base-url")

    process = CrawlerProcess(settings={
        "FEEDS": {},
        "USER_AGENT": args.user_agent,
        "DOWNLOAD_DELAY": args.delay,
        "DEPTH_LIMIT": DEPTH_LIMIT,
    })
    process.crawl(FrameworkDocsSpider, base_url=base_url)
    process.start()
