from stellar_helpers import fetch_last_tx
import discord
from discord.embeds import Embed
from helper import *
from main import *

intents = discord.Intents(dm_messages=True)
client = discord.Client(intents=intents)
conn = create_connection(DATABASE_NAME)

async def fetch_users_missing_pub():
    """
    Fetches all users still missing an public key for reward distribution
    returns array of tuples (user_id, potential_votes) 
    """

    leaderboard_rows = fetchLeaderboard(conn, fetch_last_tx(), datetime.now())
    user_rows = fetchUserPubKeys(conn)
    missingUsers = []

    for row in leaderboard_rows:

        if not [user for user in user_rows if user[0] == row[0]] and row[0] != client.user.id:
            print(f"{row[0]} has no pub key connected to their account! They are missing out on {row[1]} upvotes.")
            missingUsers.append(row)
    
    return missingUsers

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')
    for missing in await fetch_users_missing_pub():
        user = await client.fetch_user(missing[0])
        if user.id == client.user.id:
            continue

        await user.send(embed=Embed(title="REMINDER:", description=f"\
You have yet to connect an Stellar Public key to your discord account!\n\
You would miss out on {missing[1]} vote(s) for the next reward distribution!\n\
Use `/link <public_key>` now to connect your public-net stellar account!\
", colour=0xFF0000))
    await client.close()

def start():
    setup_db(conn)
    client.run(BOT_TOKEN)

if __name__ == '__main__':
    start()