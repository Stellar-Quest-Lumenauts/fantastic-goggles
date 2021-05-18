import discord
import sqlite3
from sqlite3 import Error
import os
from helper import getUser, createUser, updateVote, updateHistory

DATABASE_NAME = 'votes.db'
REACTION_TO_COMPARE = '🐻'
LEADERBOARD_LIMIT = 10
BOT_TOKEN = os.environ['DISCORD_BOT_TOKEN']

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
    c.execute('''CREATE TABLE IF NOT EXISTS votes (id INTEGER AUTO_INCREMENT PRIMARY KEY, user_id INTEGER, votes INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS votes_history (id INTEGER AUTO_INCREMENT PRIMARY KEY, user_id INTEGER, message_id INTEGER, backer INTEGER)''')

def processVote(author, message_id, backer):
    row = getUser(conn, author)

    if row == None:
        createUser(conn, author)
    else:
        updateVote(conn, author, row[1]+1)

    updateHistory(conn, author, message_id, backer)
    print(f"{author} got an upvote!")

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
        embed=discord.Embed(title="Leaderboard", description="This are currently the Results", color=0x5125aa)

        c = conn.cursor()
        c.execute("SELECT user_id, votes from votes ORDER BY votes DESC")
        rows = c.fetchall()

        counter = 0
        for row in rows: 
            if row == None or counter == LEADERBOARD_LIMIT:
                break

            user = await client.fetch_user(row[0])
            embed.add_field(name=f"``#{counter+1}`` {user.name}", value=f"{row[1]} Upvotes", inline=True)
            counter+=1
            
        embed.set_footer(text="Made with love, code and Python")
        await message.channel.send('And the results are in!', embed=embed)

    print(message.reference)


    if message.reference is not None:
        try:
            channel = client.get_channel(message.reference.channel_id)
            orig_msg = await channel.fetch_message(message.reference.message_id)
            if orig_msg.author.id != message.author.id:
                processVote(orig_msg.author.id, message.id, message.author.id)
        except discord.NotFound:
            pass
    
    
    print(message.mentions)
    if message.mentions != []:
        for member in message.mentions:
            if member.id == message.author.id:
                continue
            processVote(member.id, message.id, message.author.id)


@client.event
async def on_reaction_add(reaction, user):
    channel = reaction.message.channel
    if reaction.emoji == REACTION_TO_COMPARE and user.id != reaction.message.author.id:
       processVote(reaction.message.author.id, reaction.message.id, user.id)

@client.event
async def on_reaction_remove(reaction, user):
    channel = reaction.message.channel
    if reaction.emoji == REACTION_TO_COMPARE and user.id != reaction.message.author.id:
        row = getUser(conn, reaction.message.author.id)
        if row == None:
            return

        updateVote(conn, reaction.message.author.id, row[1]-1)
        c = conn.cursor()
        c.execute("DELETE FROM votes_history WHERE user_id=? AND message_id=? AND backer=?", (int(reaction.message.author.id), int(reaction.message.id), int(user.id), ))
        conn.commit()

        print(f"{reaction.message.author} got a downvote!")

if __name__ == '__main__':
    setup_db()
    client.run(BOT_TOKEN)
