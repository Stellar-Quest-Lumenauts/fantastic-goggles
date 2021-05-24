import discord

from helpers.discord import notify_submitter
from helpers.database import setup_db, create_connection
from settings.default import DISCORD_BOT_TOKEN, DATABASE_NAME, NOTIFY_USER

intents = discord.Intents(dm_messages=True)
client = discord.Client(intents=intents)
conn = create_connection(DATABASE_NAME)


@client.event
async def on_ready():
    print(f"We have logged in as {client.user}")
    await notify_submitter(client, conn, NOTIFY_USER)
    await client.close()


def start():
    setup_db(conn)
    client.run(DISCORD_BOT_TOKEN)


if __name__ == "__main__":
    start()
