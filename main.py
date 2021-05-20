import discord
import sqlite3
from sqlite3 import Error
import os
from helper import *
from discord_helpers import leaderboard, hasRole
import json

DATABASE_NAME = 'votes.db'
REACTION_TO_COMPARE = ['🐻'] if not 'DISCORD_ALLOWED_REACTION' in os.environ else json.loads(os.environ['DISCORD_ALLOWED_REACTION'])
LEADERBOARD_LIMIT = 10
BOT_TOKEN = os.environ['DISCORD_BOT_TOKEN']
REQUIRED_ROLE_ID = os.environ['ROLE_ID']
NOTIFY_USER = os.environ['NOTIFY_USER']
IGNORED_CHANNELS = [763798356484161569, 772838189920026635,  839229026194423898] if not 'DISCORD_IGNORED_CHANNELS' in os.environ else json.load(os.environ['DISCORD_IGNORED_CHANNELS'])
# defaults to General, Lumenauts, Report-spam

if not isinstance(REACTION_TO_COMPARE, list) \
   or (
       len(REACTION_TO_COMPARE) != 0 \
       and not isinstance(REACTION_TO_COMPARE[0], str)\
      ):
    # REACTION_TO_COMPARE must be str to arr of str; empty array => wildcard 
    print("DISCORD_ALLOWED_REACTION env variable has to be array of strs!")
    exit
if not isinstance(IGNORED_CHANNELS, list)\
   or (
       len(IGNORED_CHANNELS) != 0\
       and not isinstance(IGNORED_CHANNELS[0], int)\
      ):
    # IGNORE_CHANNELS must be array of ints
    print("DISCORD_IGNORED_CHANNELS env variable has to be array of ints!")
    exit

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

    if message.content.startswith('$hello'):
        await message.channel.send('Hello!')

    if message.content.startswith('$$leaderboard'):
        await leaderboard(conn, client, message, LEADERBOARD_LIMIT)
    
    if message.channel.id in IGNORED_CHANNELS:
        return

    if message.mentions != []:
        for member in message.mentions:
            if member.id == message.author.id and hasRole(member.roles, REQUIRED_ROLE_ID):
                continue
            processVote(message.id, member.id, message.author.id)

@client.event
async def on_reaction_add(reaction, user):
    channel = reaction.message.channel
    
    if channel.id in IGNORED_CHANNELS:
        return

    if (reaction.emoji in REACTION_TO_COMPARE or len(REACTION_TO_COMPARE) == 0)\
        and user.id != reaction.message.author.id\
        and hasRole(reaction.message.author.roles, REQUIRED_ROLE_ID)\
        and user.id != client.user.id:
       processVote(reaction.message.id, reaction.message.author.id, user.id)

if __name__ == '__main__':
    setup_db()
    client.run(BOT_TOKEN)
