import interactions
from interactions import Client, Intents, Option, OptionType, CommandContext, ClientPresence, StatusType
import sentry_sdk

from helpers.stellar import validate_pub_key
from helpers.discord import leaderboard, hasRole, notify_submitter
from helpers.database import updateHistory, linkUserPubKey, setup_db, create_connection, getUserPubKey
from settings.default import (
    SENTRY_ENABLED,
    SENTRY_URL,
    DISCORD_ALLOWED_REACTION,
    DISCORD_WHITELIST_CHANNELS,
    DATABASE_NAME,
    LEADERBOARD_LIMIT,
    NOTIFY_USER,
    REQUIRED_ROLE_ID,
    DISCORD_BOT_TOKEN,
)

if SENTRY_ENABLED:
    sentry_sdk.init(SENTRY_URL, traces_sample_rate=1.0)

if not isinstance(DISCORD_ALLOWED_REACTION, list) or (
    len(DISCORD_ALLOWED_REACTION) != 0 and not isinstance(DISCORD_ALLOWED_REACTION[0], str)
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


client = Client(
    token=DISCORD_BOT_TOKEN,
    intents=Intents.GUILD_MESSAGES
    | Intents.DIRECT_MESSAGES
    | Intents.GUILD_MESSAGE_REACTIONS
    | Intents.GUILD_MESSAGE_CONTENT,
    presence=ClientPresence(status=StatusType.OFFLINE),
)
conn = create_connection(DATABASE_NAME)


def processVote(message_id, author, backer):
    if updateHistory(conn, author, message_id, backer):
        print(f"{author} got an upvote!")


@client.event
async def on_ready():
    print(f"We have logged in as {client.me.name}")


@client.event
async def on_message_create(message):
    if message.author == client.me.id:
        return

    if message.content.startswith("$$distribute") and int(message.author.id) == int(NOTIFY_USER):
        print("We were asked to manually run the distribution script")
        await notify_submitter(client, conn, NOTIFY_USER, message.guild_id)

    if message.channel_id not in DISCORD_WHITELIST_CHANNELS and len(DISCORD_WHITELIST_CHANNELS) != 0:
        return

    if message.mentions != []:
        for member in message.mentions:

            if member["id"] == message.author.id or not hasRole(member["member"]["roles"], REQUIRED_ROLE_ID):
                continue
            processVote(message.id, member["id"], message.author.id)


@client.event
async def on_message_reaction_add(reaction):
    channel = reaction.channel_id
    user_id = reaction.user_id
    message_id = reaction.message_id

    message = await interactions.get(client, interactions.Message, object_id=message_id, parent_id=channel)
    member = await interactions.get(client, interactions.Member, object_id=user_id, parent_id=reaction.guild_id)

    if channel not in DISCORD_WHITELIST_CHANNELS and len(DISCORD_WHITELIST_CHANNELS) != 0:
        return

    if (
        (reaction.emoji.name in DISCORD_ALLOWED_REACTION or len(DISCORD_ALLOWED_REACTION) == 0)
        and user_id != message.author.id
        and hasRole(member.roles, REQUIRED_ROLE_ID)
        and user_id != client.me.id
    ):
        processVote(message_id, message.author.id, user_id)


@client.command(
    name="link",
    description="Link your public key",
    options=[
        Option(
            name="public_key",
            description="public-net public key",
            type=OptionType.STRING,
            required=True,
        )
    ],
)
async def _link_reward(ctx: CommandContext, public_key: str):
    if not validate_pub_key(public_key):
        await ctx.send("Invalid public key supplied!")
    else:
        if linkUserPubKey(conn, ctx.user.id, public_key):
            await ctx.send(f"Linked `{public_key}` to your discord account!")
        else:
            await ctx.send("Unknown error linking your public key! Please ask somewhere...")


@client.command(
    name="my_public_key",
    description="Display your public key",
)
async def _my_pub_key(ctx: CommandContext):
    public_key = getUserPubKey(conn, ctx.user.id)

    if public_key is not None:
        await ctx.send(f"Your account is associated with the following public_key {public_key}")
    else:
        await ctx.send("Your account has not been found. Use `/link public_key` to add it to the database.")


@client.command(name="hello", description="You get a Hello reply!")
async def _hello(ctx: CommandContext):
    await ctx.send("Hello!")


@client.command(
    name="leaderboard",
    description="Display the Leaderboard",
)
async def _leaderboard(ctx: CommandContext):
    channel = await interactions.get(client, interactions.Channel, object_id=ctx.channel_id)
    await leaderboard(conn, client, channel, LEADERBOARD_LIMIT, ctx.guild_id)
    await ctx.send("The Leaderboard has been generated.")


@client.command(name="distribute", description="Start prize distribution!")
async def _distribute(ctx: CommandContext):
    if ctx.author.id == NOTIFY_USER:
        await notify_submitter(client, conn, NOTIFY_USER, ctx.guild_id)
        await ctx.send("https://tenor.com/view/sacha-baron-cohen-great-success-yay-gif-4185058")
    else:
        await ctx.send("https://tenor.com/view/you-shall-not-pass-lotr-do-not-enter-not-allowed-scream-gif-16729885")


if __name__ == "__main__":
    setup_db(conn)
    client.start()
