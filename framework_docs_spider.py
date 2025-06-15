import argparse
import json
import logging
from typing import Dict, List
from urllib.parse import urlparse

import scrapy
from scrapy.crawler import CrawlerProcess
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)

class FrameworkDocsData(BaseModel):
    id: str
    content: str
    metadata: dict


FRAMEWORK_URLS: Dict[str, str] = {
    "kubernetes": "https://kubernetes.io/docs/",
    "terraform": "https://developer.hashicorp.com/terraform/docs",
    "huggingface": "https://huggingface.co/docs",
}

class FrameworkDocsSpider(scrapy.Spider):
    name = "framework_docs_spider"

    def __init__(self, start_urls=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start_urls = start_urls or []
        self.collected_data: Dict[str, List[FrameworkDocsData]] = {}

    def extract_framework_name(self, url: str) -> str:
        for name, base in FRAMEWORK_URLS.items():
            if url.startswith(base):
                return name
        parsed = urlparse(url)
        return parsed.netloc.split(".")[0]

    def parse(self, response):
        framework = self.extract_framework_name(response.url)
        data = self.collected_data.setdefault(framework, [])
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
                        "tags": ["framework_docs", framework],
                        "language": "markdown",
                        "type": self.classify_document(content, response.url)
                    }
                ))
        for href in response.css("a::attr(href)").getall():
            if href.startswith("/"):
                yield response.follow(href, callback=self.parse)

    def classify_document(self, content: str, url: str) -> str:
        text = f"{url.lower()} {content.lower()}"

        deployment_keywords = [
            "setup",
            "install",
            "installation",
            "config",
            "getting started",
            "quickstart",
        ]
        api_keywords = [
            "api",
            "endpoint",
            "reference",
            "request",
            "response",
        ]
        monitoring_keywords = [
            "monitor",
            "monitoring",
            "metrics",
            "observability",
            "logging",
        ]

        if any(k in text for k in deployment_keywords):
            return "deployment_guide"
        if any(k in text for k in api_keywords):
            return "api_documentation"
        if any(k in text for k in monitoring_keywords):
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

    def closed(self, reason):
        for framework, docs in self.collected_data.items():
            filename = f"framework_docs_{framework}.json"
            self.save_to_json(docs, filename)

def load_urls(args) -> List[str]:
    urls: List[str] = []

    if args.urls:
        urls.extend(args.urls)

    if args.frameworks:
        for name in args.frameworks:
            url = FRAMEWORK_URLS.get(name.lower())
            if url:
                urls.append(url)
            else:
                logging.warning(f"Framework desconhecido: {name}")

    if args.file:
        try:
            with open(args.file, "r", encoding="utf-8") as f:
                for line in f:
                    entry = line.strip()
                    if not entry:
                        continue
                    if entry.startswith("http"):
                        urls.append(entry)
                    else:
                        url = FRAMEWORK_URLS.get(entry.lower())
                        if url:
                            urls.append(url)
                        else:
                            logging.warning(f"Framework desconhecido: {entry}")
        except Exception as e:
            logging.error(f"Erro ao ler arquivo {args.file}: {e}")

    if not urls:
        urls = list(FRAMEWORK_URLS.values())

    return urls


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scrape framework documentation")
    parser.add_argument("--urls", nargs="*", help="Lista de URLs a serem raspadas")
    parser.add_argument("--frameworks", nargs="*", help="Nomes dos frameworks predefinidos")
    parser.add_argument("--file", help="Arquivo com URLs ou nomes de frameworks")
    args = parser.parse_args()

    start_urls = load_urls(args)

    process = CrawlerProcess(settings={
        "FEEDS": {},
        "USER_AGENT": "Mozilla/5.0",
        "DOWNLOAD_DELAY": 2,
    })
    process.crawl(FrameworkDocsSpider, start_urls=start_urls)
    process.start()
