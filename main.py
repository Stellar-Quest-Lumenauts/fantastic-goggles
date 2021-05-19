import discord
import sqlite3
from sqlite3 import Error
import os
from helper import *
from discord_helpers import leaderboard, hasRole

DATABASE_NAME = 'votes.db'
REACTION_TO_COMPARE = '🐻'
LEADERBOARD_LIMIT = 10
BOT_TOKEN = os.environ['DISCORD_BOT_TOKEN']
REQUIRED_ROLE_ID = os.environ['ROLE_ID']

def create_connection(db_file):
    """ create a database connection to a SQLite database """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except Error as e:
        print(e)

intents = discord.Intents(messages=True, guilds=True, members=True, reactions=True)
client = discord.Client(intents=intents)
conn = create_connection(DATABASE_NAME)

def processVote(message_id, author, backer):
    if updateHistory(conn, author, message_id, backer):
        print(f"{author} got an upvote!")

@client.event
async def on_ready():
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
    setup_db(conn)
    client.run(BOT_TOKEN)
