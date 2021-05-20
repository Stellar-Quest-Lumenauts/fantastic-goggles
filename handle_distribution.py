import discord
import os
from helper import *
from main import *
from discord_helpers import notify_submitter

intents = discord.Intents(dm_messages=True)
client = discord.Client(intents=intents)
conn = create_connection(DATABASE_NAME)
NOTIFY_USER  = os.environ['NOTIFY_USER']

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')
    await notify_submitter(client, conn, NOTIFY_USER)
    await client.close()

def start():
    setup_db(conn)
    client.run(BOT_TOKEN)

if __name__ == '__main__':
    start()