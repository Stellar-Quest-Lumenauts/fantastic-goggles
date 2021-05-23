import os

from main import conn, client, BOT_TOKEN
from helpers.discord import notify_submitter
from helpers.database import setup_db

NOTIFY_USER = os.environ["NOTIFY_USER"]


@client.event
async def on_ready():
    print(f"We have logged in as {client.user}")
    await notify_submitter(client, conn, NOTIFY_USER)
    await client.close()


def start():
    setup_db(conn)
    client.run(BOT_TOKEN)


if __name__ == "__main__":
    start()
