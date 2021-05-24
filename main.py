import discord
from discord_slash import SlashCommand
from discord_slash.utils.manage_commands import create_option
import sentry_sdk

from helpers.stellar import validate_pub_key
from helpers.discord import leaderboard, hasRole, notify_submitter
from helpers.database import updateHistory, linkUserPubKey, setup_db, create_connection
from settings.default import (
    SENTRY_ENABLED,
    SENTRY_URL,
    REACTION_TO_COMPARE,
    DISCORD_WHITELIST_CHANNELS,
    DATABASE_NAME,
    LEADERBOARD_LIMIT,
    NOTIFY_USER,
    REQUIRED_ROLE_ID,
    DISCORD_BOT_TOKEN,
)

if SENTRY_ENABLED:
    sentry_sdk.init(SENTRY_URL, traces_sample_rate=1.0)

if not isinstance(REACTION_TO_COMPARE, list) or (
    len(REACTION_TO_COMPARE) != 0 and not isinstance(REACTION_TO_COMPARE[0], str)
):
    # REACTION_TO_COMPARE must be str to arr of str; empty array => wildcard
    print("DISCORD_ALLOWED_REACTION env variable has to be array of strs!")
    exit
if not isinstance(DISCORD_WHITELIST_CHANNELS, list) or (
    len(DISCORD_WHITELIST_CHANNELS) != 0 and not isinstance(DISCORD_WHITELIST_CHANNELS[0], int)
):
    # IGNORE_CHANNELS must be array of ints
    print("DISCORD_WHITELIST_CHANNELS env variable has to be array of ints!")
    exit


intents = discord.Intents(messages=True, guilds=True, members=True, reactions=True)
client = discord.Client(intents=intents)
slash = SlashCommand(client, sync_commands=True)
conn = create_connection(DATABASE_NAME)


def processVote(message_id, author, backer):
    if updateHistory(conn, author, message_id, backer):
        print(f"{author} got an upvote!")


@client.event
async def on_ready():
    await client.change_presence(status=discord.Status.offline)  # Let's hide the bot
    print(f"We have logged in as {client.user}")


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith("$hello"):
        await message.channel.send("Hello!")

    if message.content.startswith("$$leaderboard"):
        await leaderboard(conn, client, message, LEADERBOARD_LIMIT)

    if message.content.startswith("$$distribute") and int(message.author.id) == int(NOTIFY_USER):
        print("We were asked to manually run the distribution script")
        await notify_submitter(client, conn, NOTIFY_USER)

    if message.channel.id not in DISCORD_WHITELIST_CHANNELS and len(DISCORD_WHITELIST_CHANNELS) != 0:
        return

    if message.mentions != []:
        for member in message.mentions:
            if member.id == message.author.id or not hasRole(member.roles, REQUIRED_ROLE_ID):
                continue
            processVote(message.id, member.id, message.author.id)


@client.event
async def on_reaction_add(reaction, user):
    channel = reaction.message.channel

    if channel.id not in DISCORD_WHITELIST_CHANNELS and len(DISCORD_WHITELIST_CHANNELS) != 0:
        return

    if (
        (reaction.emoji in REACTION_TO_COMPARE or len(REACTION_TO_COMPARE) == 0)
        and user.id != reaction.message.author.id
        and hasRole(reaction.message.author.roles, REQUIRED_ROLE_ID)
        and user.id != client.user.id
    ):
        processVote(reaction.message.id, reaction.message.author.id, user.id)


@slash.slash(
    name="link",
    description="Link your public key",
    options=[
        create_option(
            name="public_key",
            description="public-net public key",
            option_type=3,
            required=True,
        )
    ],
)
async def _link_reward(ctx, public_key: str):
    if not validate_pub_key(public_key):
        await ctx.send("Invalid public key supplied!")
    else:
        if linkUserPubKey(conn, ctx.author_id, public_key):
            await ctx.send(f"Linked `{public_key}` to your discord account!")
        else:
            await ctx.send("Unknown error linking your public key! Please ask somewhere...")
            
@slash.slash(
    name="my_public_key",
    description="Display your public key",
)
async def _my_pub_key(ctx):
    
    public_key = getUserPubKey(conn, ctx.author_id):
    
    if public_key is not None:
        await ctx.send(f"Your account is associated with the following public_key {public_key}")
    else:
        await ctx.send("Your account has not been found. Use `/set public_key` to add it to the database.")



if __name__ == "__main__":
    setup_db(conn)
    client.run(DISCORD_BOT_TOKEN)
