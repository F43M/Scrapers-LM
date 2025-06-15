import os
import json
import time
import logging
from typing import List

import requests
from pydantic import BaseModel
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

logging.basicConfig(level=logging.INFO)


class ConfluenceData(BaseModel):
    id: str
    content: str
    metadata: dict


class ConfluenceScraper:
    def __init__(self, base_url: str, username: str, token: str, use_api: bool = True):
        self.base_url = base_url.rstrip('/')
        self.auth = (username, token)
        self.use_api = use_api
        self.output_file = "confluence_data.json"

    def _fetch_via_api(self, page_id: str) -> ConfluenceData:
        url = f"{self.base_url}/rest/api/content/{page_id}?expand=body.storage,version"
        response = requests.get(url, auth=self.auth, timeout=10)
        response.raise_for_status()
        item = response.json()
        content = item.get("body", {}).get("storage", {}).get("value", "")
        timestamp = item.get("version", {}).get("when", time.strftime("%Y-%m-%d %H:%M:%S"))
        return ConfluenceData(
            id=str(item.get("id", page_id)),
            content=content[:10000],
            metadata={
                "url": f"{self.base_url}/pages/viewpage.action?pageId={page_id}",
                "timestamp": timestamp,
                "tags": ["confluence"],
                "language": "english",
                "type": "documentation",
            },
        )

    def _fetch_via_selenium(self, page_id: str) -> ConfluenceData:
        url = f"{self.base_url}/pages/viewpage.action?pageId={page_id}"
        options = Options()
        options.headless = True
        driver = webdriver.Chrome(options=options)
        try:
            driver.get(url)
            body = driver.find_element(By.TAG_NAME, "body").text
            return ConfluenceData(
                id=page_id,
                content=body[:10000],
                metadata={
                    "url": url,
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "tags": ["confluence"],
                    "language": "english",
                    "type": "documentation",
                },
            )
        finally:
            driver.quit()

    def fetch_pages(self, page_ids: List[str]) -> List[ConfluenceData]:
        data = []
        for pid in page_ids:
            if self.use_api:
                try:
                    data.append(self._fetch_via_api(pid))
                    continue
                except Exception as e:
                    logging.error(f"API error for {pid}: {e}. Falling back to Selenium.")
            try:
                data.append(self._fetch_via_selenium(pid))
            except Exception as e:
                logging.error(f"Selenium error for {pid}: {e}")
        return data

    def save_to_json(self, data: List[ConfluenceData]):
        output = {"data": [d.dict() for d in data]}
        with open(self.output_file, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        logging.info(f"Dados salvos em {self.output_file}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Scrape Confluence pages")
    parser.add_argument("page_ids", nargs="+", help="IDs das páginas a baixar")
    parser.add_argument("--base-url", default=os.getenv("CONFLUENCE_URL", ""), help="URL base do Confluence")
    parser.add_argument("--username", default=os.getenv("CONFLUENCE_USER", ""), help="Usuário para autenticação")
    parser.add_argument("--token", default=os.getenv("CONFLUENCE_TOKEN", ""), help="Token ou senha para autenticação")
    parser.add_argument("--no-api", action="store_true", help="Não utilizar a API REST")
    args = parser.parse_args()

    scraper = ConfluenceScraper(
        base_url=args.base_url,
        username=args.username,
        token=args.token,
        use_api=not args.no_api,
    )
    pages = scraper.fetch_pages(args.page_ids)
    scraper.save_to_json(pages)

