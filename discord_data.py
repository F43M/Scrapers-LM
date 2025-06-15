import argparse
import asyncio
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
        self.client = discord.Client(
            intents=discord.Intents(messages=True, message_content=True)
        )
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

    async def run(self, server_id: int, channel_id: int, limit: int = 100):
        @self.client.event
        async def on_ready():
            try:
                await self.fetch_messages(server_id, channel_id, limit)
            finally:
                await self.client.close()

        try:
            await self.client.start(self.token)
        except Exception as e:
            logging.error(f"Erro de conexão: {e}")
        finally:
            await self.client.close()
            self.save_to_json()


async def main() -> None:
    parser = argparse.ArgumentParser(description="Coleta mensagens do Discord")
    parser.add_argument("--token", required=True, help="Token do bot")
    parser.add_argument("--server", type=int, required=True, help="ID do servidor")
    parser.add_argument("--channel", type=int, required=True, help="ID do canal")
    parser.add_argument("--limit", type=int, default=100, help="Limite de mensagens")
    args = parser.parse_args()

    scraper = DiscordScraper(token=args.token)
    await scraper.run(server_id=args.server, channel_id=args.channel, limit=args.limit)


if __name__ == "__main__":
    asyncio.run(main())
