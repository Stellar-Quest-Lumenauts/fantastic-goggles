import discord
import sqlite3
from sqlite3 import Error
import os
from helper import *
from main import *

intents = discord.Intents(dm_messages=True)
client = discord.Client(intents=intents)
conn = create_connection(DATABASE_NAME)
NOTIFY_USER  = os.environ['NOTIFY_USER']

def generate_report():
    return "unimplemented" #todo

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')
    notify_user = await client.fetch_user(NOTIFY_USER)
    await notify_user.send(content = generate_report())
    await client.close()

if __name__ == '__main__':
    setup_db()
    client.run(BOT_TOKEN)
