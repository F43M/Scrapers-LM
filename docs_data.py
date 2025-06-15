import scrapy
from scrapy.crawler import CrawlerProcess
import json
import logging

logging.basicConfig(level=logging.INFO)

class DocsSpider(scrapy.Spider):
    name = "docs_spider"
    start_urls = ["https://docs.python.org/3/"]

    def parse(self, response):
        data = {
            "source": "readthedocs",
            "category": "documentation",
            "data": []
        }
        for section in response.css("div.section"):
            content = section.css("::text").getall()
            content = " ".join(content).strip()
            if content:
                data["data"].append({
                    "id": response.url + "#" + section.css("::attr(id)").get(""),
                    "content": content,
                    "metadata": {
                        "url": response.url,
                        "timestamp": response.headers.get("Date", "").decode(),
                        "tags": ["documentation", "python"],
                        "language": "python",
                        "type": "documentation"
                    }
                })
        with open("docs_data.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logging.info(f"Dados salvos em docs_data.json")

        # Seguir links para outras páginas
        for href in response.css("a::attr(href)").getall():
            yield response.follow(href, callback=self.parse)

# Executar o crawler
process = CrawlerProcess(settings={
    "FEEDS": {},
    "USER_AGENT": "Mozilla/5.0",
    "DOWNLOAD_DELAY": 2,
})
process.crawl(DocsSpider)
process.start()