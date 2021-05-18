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

def setup_db():
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS votes_history (id INTEGER AUTO_INCREMENT PRIMARY KEY, user_id INTEGER, message_id INTEGER, backer INTEGER, vote_time DATETIME DEFAULT CURRENT_TIMESTAMP)''')

def processVote(message_id, author, backer):
    if updateHistory(conn, author, message_id, backer):
        print(f"{author} got an upvote!")

def processDownvote(message_id, author = None, backer = None):
    if removeHistory(conn, message_id, author, backer):
        if backer != None and author != None:
            print(f"{author} got an downvote!")
        else:
            print(f"{message_id} was deleted resulting in a downvote to the referenced!" )


@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('$hello'):
        await message.channel.send('Hello!')

    if message.content.startswith('$$leaderboard'):
        await leaderboard(conn, client, message, LEADERBOARD_LIMIT)

    if message.reference is not None:
        try:
            channel = client.get_channel(message.reference.channel_id)
            orig_msg = await channel.fetch_message(message.reference.message_id)
            if orig_msg.author.id != message.author.id and hasRole(orig_msg.author.roles, REQUIRED_ROLE_ID):
                processVote(message.id, orig_msg.author.id, message.author.id)
        except discord.NotFound:
            pass
    
    if message.mentions != []:
        for member in message.mentions:
            if member.id == message.author.id:
                continue
            processVote(message.id, member.id, message.author.id)

@client.event
async def on_reaction_add(reaction, user):
    channel = reaction.message.channel
    if reaction.emoji == REACTION_TO_COMPARE and user.id != reaction.message.author.id and hasRole(reaction.message.author.roles, REQUIRED_ROLE_ID):
       processVote(reaction.message.id, reaction.message.author.id, user.id)

@client.event
async def on_reaction_remove(reaction, user):
    channel = reaction.message.channel
    if reaction.emoji == REACTION_TO_COMPARE and user.id != reaction.message.author.id and hasRole(reaction.message.author.roles, REQUIRED_ROLE_ID):
        processDownvote(reaction.message.id, reaction.message.author.id, user.id)

@client.event
async def on_message_delete(message):
    if message.mentions != []:
        processDownvote(message.id)


if __name__ == '__main__':
    setup_db()
    client.run(BOT_TOKEN)

