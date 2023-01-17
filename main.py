import interactions
from interactions import Client, Intents, Option, OptionType, CommandContext, ClientPresence, StatusType, ChannelType
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
    MESSAGE_REPLY,
    REACTION,
    POSTED_MESSAGE,
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


def processVote(message_id, channel_id, author, backer, vote_type, characther_count):
    if updateHistory(conn, author, message_id, channel_id, backer, vote_type, characther_count):
        print(f"{author} got an upvote!")


@client.event
async def on_ready():
    print(f"We have logged in as {client.me.name}")


@client.event
async def on_message_create(message):
    # Look Up the Channel and Channel Type
    channel = await interactions.get(client, interactions.Channel, object_id=message.channel_id)
    channel_id = message.channel_id

    # Each Discord Thread is it's own Channel, So get the Parent Channel's ID and check that instead.
    if channel.type == ChannelType.PUBLIC_THREAD:
        channel_id = channel.parent_id

    if message.author == client.me.id:
        return

    if channel_id not in DISCORD_WHITELIST_CHANNELS and len(DISCORD_WHITELIST_CHANNELS) != 0:
        return

    if message.mentions != []:
        for member in message.mentions:
            if member["id"] == message.author.id or not hasRole(member["member"]["roles"], REQUIRED_ROLE_ID):
                continue
            processVote(message.id, message.channel_id, member["id"], message.author.id, MESSAGE_REPLY, "0")

    # Check if the Author is a Lumenaut and Count his Content in a Message
    member = await interactions.get(
        client, interactions.Member, parent_id=message.guild_id, object_id=message.author.id
    )
    if hasRole(member.roles, REQUIRED_ROLE_ID):
        processVote(message.id, message.channel_id, message.author.id, None, POSTED_MESSAGE, len(message.content))


@client.event
async def on_message_reaction_add(reaction):
    channel = await interactions.get(client, interactions.Channel, object_id=reaction.channel_id)
    channel_id = reaction.channel_id

    # Each Discord Thread is it's own Channel, So get the Parent Channel's ID and check that instead.
    if channel.type == ChannelType.PUBLIC_THREAD:
        channel_id = channel.parent_id

    user_id = reaction.user_id
    message_id = reaction.message_id

    message = await interactions.get(client, interactions.Message, object_id=message_id, parent_id=reaction.channel_id)
    member = await interactions.get(
        client, interactions.Member, object_id=message.author.id, parent_id=reaction.guild_id
    )

    if channel_id not in DISCORD_WHITELIST_CHANNELS and len(DISCORD_WHITELIST_CHANNELS) != 0:
        return

    if (
        (reaction.emoji.name in DISCORD_ALLOWED_REACTION or len(DISCORD_ALLOWED_REACTION) == 0)
        and user_id != message.author.id
        and hasRole(member.roles, REQUIRED_ROLE_ID)
        and user_id != client.me.id
    ):
        processVote(message_id, reaction.channel_id, message.author.id, user_id, REACTION, "0")


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
        if linkUserPubKey(conn, str(ctx.user.id), public_key):
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
    await ctx.send("Generating leaderboard... The Leaderboard should show up here, or maybe not.")
    await leaderboard(conn, client, channel, LEADERBOARD_LIMIT, ctx.guild_id)


@client.command(name="distribute", description="Start prize distribution!")
async def _distribute(ctx: CommandContext):
    author = ctx.author if ctx.author is not None else ctx.user
    if author.id == NOTIFY_USER:
        await notify_submitter(client, conn, author)
        await ctx.send("https://tenor.com/view/sacha-baron-cohen-great-success-yay-gif-4185058")
    else:
        await ctx.send("https://tenor.com/view/you-shall-not-pass-lotr-do-not-enter-not-allowed-scream-gif-16729885")

if __name__ == "__main__":
    setup_db(conn)
    client.start()
