import interactions
from interactions import Client, Intents, OptionType, SlashContext, Status, ChannelType, slash_command, slash_option, listen
from interactions.api.events import Ready, MessageCreate, MessageReactionAdd
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
    sentry_sdk.init(SENTRY_URL, traces_sample_rate=1.0, request_bodies='always')

if not isinstance(DISCORD_ALLOWED_REACTION, list) or (
    len(DISCORD_ALLOWED_REACTION) != 0 and not isinstance(DISCORD_ALLOWED_REACTION[0], str)
):
    # REACTION_TO_COMPARE must be str to arr of str; empty array => wildcard
    print("DISCORD_ALLOWED_REACTION env variable has to be array of strs!")
    exit()
if not isinstance(DISCORD_WHITELIST_CHANNELS, list) or (
    len(DISCORD_WHITELIST_CHANNELS) != 0 and not isinstance(DISCORD_WHITELIST_CHANNELS[0], int)
):
    # IGNORE_CHANNELS must be array of ints
    print("DISCORD_WHITELIST_CHANNELS env variable has to be array of ints!")
    exit()


client = Client(
    token=DISCORD_BOT_TOKEN,
    intents=Intents.GUILD_MESSAGES
    | Intents.DIRECT_MESSAGES
    | Intents.GUILD_MESSAGE_REACTIONS
    | Intents.MESSAGE_CONTENT
    | Intents.GUILDS
)

conn = create_connection(DATABASE_NAME)

def processVote(message_id, channel_id, author, backer, vote_type, characther_count):
    if updateHistory(conn, author, message_id, channel_id, backer, vote_type, characther_count):
        print(f"{author} got an upvote!")

@listen(Ready)
async def on_ready():
    await client.change_presence(Status.ONLINE)
    print(f"We have logged in as {client.user.display_name}")


@listen(MessageCreate)
async def on_message_create(event: MessageCreate):
    message = event.message
    channel = message.channel
    channel_id = channel.id

    # Each Discord Thread is it's own Channel, So get the Parent Channel's ID and check that instead.
    if channel.type == ChannelType.GUILD_PUBLIC_THREAD:
        channel_id = channel.parent_id

    if message.author == client.user.id:
        return  

    if channel_id not in DISCORD_WHITELIST_CHANNELS and len(DISCORD_WHITELIST_CHANNELS) != 0:
        return

    # We are just looking for an individual user ping
    if message.mention_users != []:
        async for member in message.mention_users:
            if member.id == message.author.id or not hasRole(member.roles, REQUIRED_ROLE_ID):
                continue
            processVote(message.id, channel_id, member.id, message.author.id, MESSAGE_REPLY, 0)

    # Check if the Author is a Lumenaut and Count his Content in a Message
    member = await client.fetch_member(message.author.id, message.guild.id)
    if hasRole(member.roles, REQUIRED_ROLE_ID):
        processVote(message.id, channel_id, message.author.id, None, POSTED_MESSAGE, len(message.content))


@listen(MessageReactionAdd)
async def on_message_reaction_add(event):
    message = event.message
    channel = message.channel
    channel_id = channel.id

    reaction = event.reaction

    # Each Discord Thread is it's own Channel, So get the Parent Channel's ID and check that instead.
    if channel.type == ChannelType.GUILD_PUBLIC_THREAD:
        channel_id = channel.parent_id

    user_id = event.author
    message_id = message.id

    member = await client.fetch_member(message.author.id, message.guild.id)

    if channel_id not in DISCORD_WHITELIST_CHANNELS and len(DISCORD_WHITELIST_CHANNELS) != 0:
        return

    if (
        (reaction.emoji.name in DISCORD_ALLOWED_REACTION or len(DISCORD_ALLOWED_REACTION) == 0)
        and user_id != message.author.id
        and hasRole(member.roles, REQUIRED_ROLE_ID)
        and user_id != client.user.id
    ):
        processVote(message_id, reaction.channel.id, message.author.id, user_id, REACTION, "0")


@slash_command(
    name="link",
    description="Link your public key"
)
@slash_option(
    name="public_key",
    description="public-net public key",
    opt_type=OptionType.STRING,
    required=True,
)
async def _link_reward(ctx: SlashContext, public_key: str):
    if not validate_pub_key(public_key):
        await ctx.send("Invalid public key supplied!", ephemeral=True)
    else:
        if linkUserPubKey(conn, str(ctx.user.id), public_key):
            await ctx.send(f"Linked `{public_key}` to your discord account!", ephemeral=True)
        else:
            await ctx.send("Unknown error linking your public key! Please ask somewhere...", ephemeral=True)


@slash_command(
    name="my_public_key",
    description="Display your public key"
)
async def _my_pub_key(ctx: SlashContext):
    public_key = getUserPubKey(conn, ctx.user.id)

    if public_key is not None:
        await ctx.send(f"Your account is associated with the following public_key {public_key}", ephemeral=True)
    else:
        await ctx.send("Your account has not been found. Use `/link public_key` to add it to the database.", ephemeral=True)


@slash_command(
    name="hello",
    description="You get a Hello reply!",
)
async def _hello(ctx: SlashContext):
    await ctx.send("Hello!", ephemeral=True)


@slash_command(
    name="leaderboard",
    description="Display the Leaderboard",
)
async def _leaderboard(ctx: SlashContext):
    channel = await client.fetch_channel(ctx.channel_id)
    await ctx.send("Generating leaderboard... The Leaderboard should show up here, or maybe not.")
    await leaderboard(conn, client, channel, LEADERBOARD_LIMIT, ctx.guild_id)


@slash_command(
    name="distribute", 
    description="Start prize distribution!"
)
async def _distribute(ctx: SlashContext):
    author = ctx.author if ctx.author is not None else ctx.user
    if author.id == NOTIFY_USER:
        await notify_submitter(client, conn, author)
        await ctx.send("https://tenor.com/view/sacha-baron-cohen-great-success-yay-gif-4185058", ephemeral=True)
    else:
        await ctx.send("https://tenor.com/view/you-shall-not-pass-lotr-do-not-enter-not-allowed-scream-gif-16729885", ephemeral=True)

if __name__ == "__main__":
    setup_db(conn)
    client.start()
