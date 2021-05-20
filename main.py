from stellar_helpers import validate_pub_key
import discord
import sqlite3
from sqlite3 import Error
import psycopg2
import os
from helper import *
from discord_helpers import leaderboard, hasRole, notify_submitter
from discord_slash import SlashCommand
from discord_slash.utils.manage_commands import create_option
import json

DATABASE_NAME = 'votes.db'
REACTION_TO_COMPARE = ['🐻'] if not 'DISCORD_ALLOWED_REACTION' in os.environ else json.loads(os.environ['DISCORD_ALLOWED_REACTION'])
LEADERBOARD_LIMIT = 10
BOT_TOKEN = os.environ['DISCORD_BOT_TOKEN']
REQUIRED_ROLE_ID = os.environ['ROLE_ID']
NOTIFY_USER = os.environ['NOTIFY_USER']

IGNORED_CHANNELS = [763798356484161569, 772838189920026635,  839229026194423898] if not 'DISCORD_IGNORED_CHANNELS' in os.environ else json.load(os.environ['DISCORD_IGNORED_CHANNELS'])
SQLITE3_ENABLED = True if not 'SQLITE3_ENABLED' in os.environ else os.envior['SQLITE3_ENABLED']
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
slash = SlashCommand(client, sync_commands=True)
conn = create_connection(DATABASE_NAME)

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

    if message.content.startswith('$$distribute') and int(message.author.id) == int(NOTIFY_USER):
        print("We were asked to manually run the distribution script")
        await notify_submitter(client, conn, NOTIFY_USER)
    
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

@slash.slash(name="link", 
             description="Link your public key",
             options=[
                 create_option(
                     name="public_key",
                     description="public-net public key",
                     option_type=3,
                     required=True)  
])
async def _link_reward(ctx, public_key: str):
    if not validate_pub_key(public_key):
        await ctx.send("Invalid public key supplied!")
    else:
        if linkUserPubKey(conn, ctx.author_id, public_key):
            await ctx.send(f"Linked `{public_key}` to your discord account!")
        else:
            await ctx.send("Unknown error linking your public key! Please ask somewhere...")
if __name__ == '__main__':
    setup_db(conn)
    client.run(BOT_TOKEN)
