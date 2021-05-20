import discord
from helper import fetchLeaderboard, fetchUserPubKeys, getWeek
from stellar_helpers import *

async def leaderboard(conn, client, message, LEADERBOARD_LIMIT):
    embed=discord.Embed(title="Leaderboard", description="This are currently the Results", color=0x5125aa)

    dateLimit = getWeek()

    rows = fetchLeaderboard(conn, dateLimit[0], dateLimit[1])

    counter = 0
    for row in rows: 
        if row == None or counter == LEADERBOARD_LIMIT:
            break

        user = await client.fetch_user(row[0])
        embed.add_field(name=f"``#{counter+1}`` {user.name}", value=f"{row[1]} Upvotes", inline=True)
        counter+=1
        
    embed.set_footer(text="Made with love, code and Python")
    await message.channel.send('And the results are in!', embed=embed)

def hasRole(roles, REQUIRED_ROLE_ID):
    if discord.utils.get(roles, id=int(REQUIRED_ROLE_ID)):
        return True
    return False

async def generate_report(conn):
    week = getWeek(-1) # run on somewhen on monday therefor fetch last week
    leaderboard_rows = fetchLeaderboard(conn, week[0], week[1])
    user_rows = fetchUserPubKeys(conn)
    sumVotes = 0

    BASE_FEE = 10000

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

    tx_cost = (BASE_FEE * len(payoutUser)) / 1000000

    pricepot = fetch_account_balance() - tx_cost

    if len(payoutUser) == 0:
        return "No eligible users this week!"
    if len(payoutUser) > 100:
        return "Wow! There are a lot of eligible lumenauts (>100). We should upgrade our code to handle this case..."
    payouts = []

    pricepot -= len(payoutUser) # base reserve * 2 (2 claimaints for each claimableBalance)

    if pricepot <= 0:
        return f"Balance of Pricepot is not high enough to support {len(payoutUser)} eligible lumenauts!"


    for user in payoutUser:
        payout = user[1] / sumVotes * pricepot
        payouts.append((user[2], payout))
        
    tx_xdr = generate_reward_tx(payouts, BASE_FEE)

    if tx_xdr == None: 
        return f"Failed to load reward account!"


    return f"```{tx_xdr}```" #todo size limit?