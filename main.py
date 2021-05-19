import discord
import sqlite3
import psycopg2
from sqlite3 import Error
import os
from helper import *
from discord_helpers import leaderboard, hasRole

DATABASE_NAME = 'votes.db'
REACTION_TO_COMPARE = '🐻'
LEADERBOARD_LIMIT = 10
BOT_TOKEN = os.environ['DISCORD_BOT_TOKEN']
REQUIRED_ROLE_ID = os.environ['ROLE_ID']
SQLITE3_ENABLED = True if os.environ['SQLITE3_ENABLED'] == True else False

def create_connection(db_file):
    """ create a database connection to a SQLite database """
    conn = None
    try:
        if SQLITE3_ENABLED:
            conn = sqlite3.connect(db_file)
        else:
            conn = psycopg2.connect(
                host = os.environ['POSTGRE_HOST'],
                database = os.environ['POSTGRE_DB'],
                port = os.environ['POSTGRE_PORT'],
                user = os.environ['POSTGRE_USER'],
                password = os.environ['POSTGRE_PASSWORD']
            )
        return conn
    except Exception as e:
        print(e)

intents = discord.Intents(messages=True, guilds=True, members=True, reactions=True)
client = discord.Client(intents=intents)
conn = create_connection(DATABASE_NAME)

def setup_db():
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS votes_history (id INTEGER AUTO_INCREMENT PRIMARY KEY, user_id INTEGER, message_id INTEGER, backer INTEGER, vote_time DATETIME DEFAULT CURRENT_TIMESTAMP)''')

def processVote(message_id, author, backer):
    if updateHistory(conn, author, message_id, backer):
        print(f"{author} got an upvote!")

@client.event
async def on_ready():
    await client.change_presence(status=discord.Status.offline) # Let's hide the bot
    print(f'We have logged in as {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.channel.id in [763798356484161569, 772838189920026635,  839229026194423898]: # General, Lumenauts, Report-spam
        return

    if message.content.startswith('$hello'):
        await message.channel.send('Hello!')

    if message.content.startswith('$$leaderboard'):
        await leaderboard(conn, client, message, LEADERBOARD_LIMIT)
    
    if message.mentions != []:
        for member in message.mentions:
            if member.id == message.author.id and hasRole(member.roles, REQUIRED_ROLE_ID):
                continue
            processVote(message.id, member.id, message.author.id)

@client.event
async def on_reaction_add(reaction, user):
    channel = reaction.message.channel
    if reaction.emoji == REACTION_TO_COMPARE and user.id != reaction.message.author.id and hasRole(reaction.message.author.roles, REQUIRED_ROLE_ID):
       processVote(reaction.message.id, reaction.message.author.id, user.id)

if __name__ == '__main__':
    setup_db()
    client.run(BOT_TOKEN)
