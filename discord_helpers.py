import discord
from helper import fetchLeaderboard, fetchUserPubKeys, upload_to_hastebin
from stellar_helpers import *

async def leaderboard(conn, client, message, LEADERBOARD_LIMIT):
    last = fetch_last_tx()
    embed=discord.Embed(title="Leaderboard", description=f"This are currently the Results\n Last distribution was {last}", color=0x5125aa)

    rows = fetchLeaderboard(conn, last, datetime.now())

    if len(rows) == 0:
        embed.add_field(name="``#1`` KanayeNet", value="Even without any votes he is leading!")

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
    last_tx_date = fetch_last_tx()

    if last_tx_date == None:
        return "Failed to load past transactions of reward account! Does it exist?"

    leaderboard_rows = fetchLeaderboard(conn, last_tx_date, datetime.now())
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
        return "No eligible users this time!"
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

async def notify_submitter(client, conn, user):
    notify_user = await client.fetch_user(user)
    content = await generate_report(conn)
    if content.startswith('AA'): # is XDR
        content = upload_to_hastebin(content)
    else:
        content = f"`{content}`"
    await notify_user.send(content = f"New week, new lumenaut rewards:\n{content}")