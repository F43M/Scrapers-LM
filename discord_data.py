import discord
import json
import logging
from pydantic import BaseModel
from typing import List

logging.basicConfig(level=logging.INFO)

class DiscordData(BaseModel):
    id: str
    content: str
    metadata: dict

class DiscordScraper:
    def __init__(self, token: str):
        self.client = discord.Client(intents=discord.Intents.default())
        self.token = token
        self.output_file = "discord_data.json"
        self.data = []

    async def fetch_messages(self, server_id: int, channel_id: int, limit: int = 100):
        try:
            guild = self.client.get_guild(server_id)
            channel = guild.get_channel(channel_id)
            async for message in channel.history(limit=limit):
                self.data.append(DiscordData(
                    id=str(message.id),
                    content=message.content,
                    metadata={
                        "url": f"https://discord.com/channels/{server_id}/{channel_id}/{message.id}",
                        "timestamp": message.created_at.isoformat(),
                        "tags": [channel.name],
                        "language": "english",
                        "type": "message"
                    }
                ))
        except Exception as e:
            logging.error(f"Erro ao coletar mensagens: {e}")

    def save_to_json(self):
        with open(self.output_file, "w", encoding="utf-8") as f:
            json.dump([d.dict() for d in self.data], f, indent=2, ensure_ascii=False)
        logging.info(f"Dados salvos em {self.output_file}")

    def run(self, server_id: int, channel_id: int, limit: int = 100):
        @self.client.event
        async def on_ready():
            await self.fetch_messages(server_id, channel_id, limit)
            await self.client.close()
        self.client.run(self.token)
        self.save_to_json()

# Exemplo de uso
scraper = DiscordScraper(token="SEU_BOT_TOKEN")
scraper.run(server_id=123456789, channel_id=987654321, limit=50)