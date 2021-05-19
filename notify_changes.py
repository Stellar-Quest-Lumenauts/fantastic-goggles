import discord
import sqlite3
from sqlite3 import Error
import os
from helper import *
from main import *
import math
from stellar_helpers import *

intents = discord.Intents(dm_messages=True)
client = discord.Client(intents=intents)
conn = create_connection(DATABASE_NAME)
NOTIFY_USER  = os.environ['NOTIFY_USER']

async def get_pricepot():
    return fetch_account_balance()

async def generate_report():
    week = getWeek(-1) # run on somewhen on monday therefor fetch last week
    leaderboard_rows = fetchLeaderboard(conn, week[0], week[1])
    user_rows = fetchUserPubKeys(conn)
    sumVotes = 0

    payoutUser = []

    for row in leaderboard_rows:
        pubKey = None

        for user in user_rows:
            if user[0] == row[0]:
                pubKey = user[1]

        if pubKey != None:
            # user has public key
            sumVotes += row[1]
            payoutUser.append((row[0], row[1], pubKey))
        else:
            print(f"{row[0]} has no pub key connected to their account! They are missing out on {row[1]} upvotes :(")
    
    pricepot = await get_pricepot()

    payouts = []

    for user in payoutUser:
        payout = user[1] / sumVotes * pricepot
        payouts.append((user[2], payout))
        
    tx_xdr = generate_reward_tx(payouts)


    return f"```{tx_xdr}```" #todo size limit?

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')
    notify_user = await client.fetch_user(NOTIFY_USER)
    await notify_user.send(content = await generate_report())
    await client.close()

if __name__ == '__main__':
    setup_db(conn)
    client.run(BOT_TOKEN)
