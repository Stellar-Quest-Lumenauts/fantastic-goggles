from interactions import Embed
from .database import fetchUserPubKeys, getUpvoteMap
from .generic import upload_to_hastebin, post_to_refractor
from .stellar import fetch_last_tx, fetch_account_balance, generate_reward_tx
from .graphs import generate_graph
from settings.default import (
    BASE_FEE,
    USE_REFRACTOR,
    MESSAGE_REPLY,
    REACTION,
    POSTED_MESSAGE,
    TYPE_TO_VAR,
)


async def leaderboard(conn, client, channel, limit, guild_id):
    last = fetch_last_tx()
    embed = Embed(
        title="Leaderboard",
        description=f"This are currently the Results\n Last distribution was {last}",
        color=0x5125AA,
    )

    counter = 0
    usernames = []
    upvotes = {MESSAGE_REPLY: [], REACTION: [], POSTED_MESSAGE: []}

    counter = 0
    upvote_per_data_type = getUpvoteMap(conn, last)

    if len(list(upvote_per_data_type.keys())) == 0:
        embed.add_field(name="``#1`` KanayeNet", value="Even without any votes he is leading!")

    upvote_per_data_type = {
        k: v for k, v in sorted(upvote_per_data_type.items(), key=lambda item: item[1]["TOTAL"], reverse=True)
    }
    for row in upvote_per_data_type.keys():
        if counter == limit:
            break

        user = await client.fetch_member(row, guild_id)
        embed.add_field(
            name=f"``#{counter+1}`` {user.display_name}",
            value=f"{upvote_per_data_type[row]['TOTAL']} Upvotes",
            inline=True
        )
        usernames.append(user.display_name)

        print(upvote_per_data_type[row])
        for elem in upvote_per_data_type[row]:
            if elem == "TOTAL":
                break
            upvotes[TYPE_TO_VAR[elem]].append(upvote_per_data_type[row][elem])

        counter += 1
    discord_file = generate_graph(usernames, upvotes)
    embed.set_image(url="attachment://graph.png")
    embed.set_footer(text="Made with love, code and Python")
    await channel.send("And the results are in!", embeds=[embed], files=discord_file)


def hasRole(roles, REQUIRED_ROLE_ID):
    roles = [int(role) for role in roles]
    return REQUIRED_ROLE_ID in roles


def generate_payouts(conn):
    # possible bug if last_tx_date == None =>
    # counting all votes ever <--> this should only happen when account is new
    last_tx_date = fetch_last_tx()

    # Retrieve the number of upvotes for every type we've made.
    upvote_per_data_type = getUpvoteMap(conn, last_tx_date)
    upvote_per_data_type = {
        k: v for k, v in sorted(upvote_per_data_type.items(), key=lambda item: item[1]["TOTAL"], reverse=True)
    }

    user_rows = fetchUserPubKeys(conn)
    sumVotes = 0

    payoutUser = []

    for row in upvote_per_data_type.keys():
        pubKey = None
        upvotes = upvote_per_data_type[row]["TOTAL"]

        for user in user_rows:
            if user[0] == row:
                pubKey = user[1]

        if pubKey is not None:
            # user has public key
            sumVotes += upvotes
            payoutUser.append((row, upvotes, pubKey))
        else:
            print(f"{row} has no pub key connected to their account! They are missing out on {upvotes} upvotes :(")

    tx_cost = (BASE_FEE * len(payoutUser)) / 1000000

    pricepot = fetch_account_balance() - tx_cost

    if len(payoutUser) == 0:
        raise Exception("No eligible users this time!")
    if len(payoutUser) > 100:
        raise Exception(
            "Wow! There are a lot of eligible lumenauts (>100). We should upgrade our code to handle this case..."
        )
    payouts = []

    pricepot -= len(payoutUser)  # base reserve * 2 (2 claimaints for each claimableBalance)

    if pricepot <= 0:
        raise Exception(f"Balance of Pricepot is not high enough to support {len(payoutUser)} eligible lumenauts!")

    for user in payoutUser:
        payout = user[1] / sumVotes * pricepot
        payouts.append((user[2], payout))

    return payouts


def generate_report(payouts: list) -> str:
    tx_xdr = generate_reward_tx(payouts, BASE_FEE)

    if tx_xdr is None:
        raise Exception("Failed to load reward account!")

    return tx_xdr  # todo size limit?


async def notify_submitter(client, conn, user):
    try:
        payouts = generate_payouts(conn)
        report = generate_report(payouts)
        if USE_REFRACTOR:
            content = post_to_refractor(report)
        else:
            content = upload_to_hastebin(report)
    except Exception as e:
        content = f"```{e}```"
    await user.send(content=f"New week, new lumenaut rewards:\n{content}")
