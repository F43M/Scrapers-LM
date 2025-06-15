import argparse
import json
import logging
from urllib.parse import urlparse

class SaveDocsPipeline:
    def open_spider(self, spider):
        self.items = []

    def process_item(self, item, spider):
        self.items.append(dict(item))
        return item

    def close_spider(self, spider):
        output = {
            "source": spider.source,
            "category": "documentation",
            "data": self.items,
        }
        with open("docs_data.json", "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        logging.info("Dados salvos em docs_data.json")

import scrapy
from scrapy.crawler import CrawlerProcess

logging.basicConfig(level=logging.INFO)

class DocsSpider(scrapy.Spider):
    name = "docs_spider"

    def __init__(self, start_url: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start_urls = [start_url]
        self.allowed_domains = [urlparse(start_url).netloc]
        self.source = self.allowed_domains[0]

    def parse(self, response):
        for section in response.css("div.section"):
            content = section.css("::text").getall()
            content = " ".join(content).strip()
            if content:
                yield {
                    "id": response.url + "#" + section.css("::attr(id)").get(""),
                    "content": content,
                    "metadata": {
                        "url": response.url,
                        "timestamp": response.headers.get("Date", b"").decode(),
                        "tags": ["documentation", self.source],
                        "language": "python",
                        "type": "documentation",
                    },
                }

        for href in response.css("a::attr(href)").getall():
            if href.startswith("/") or urlparse(href).netloc == self.allowed_domains[0]:
                yield response.follow(href, callback=self.parse)

# Executar o crawler
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Docs spider")
    parser.add_argument("start_url", help="URL inicial a ser rastreada")
    parser.add_argument("--delay", type=int, default=2, help="Delay entre requisicoes")
    parser.add_argument("--user-agent", dest="user_agent", default="Mozilla/5.0",
                        help="User-Agent para as requisicoes")
    args = parser.parse_args()

    process = CrawlerProcess(settings={
        "USER_AGENT": args.user_agent,
        "DOWNLOAD_DELAY": args.delay,
        "ITEM_PIPELINES": {"__main__.SaveDocsPipeline": 300},
        "LOG_LEVEL": "INFO",
    })

    process.crawl(DocsSpider, start_url=args.start_url)
    process.start()
