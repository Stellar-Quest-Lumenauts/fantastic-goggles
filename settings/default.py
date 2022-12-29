import environs
from stellar_sdk import Network

env = environs.Env()

env.read_env()

SQLITE3_ENABLED = env.bool("SQLITE3_ENABLED", True)
DATABASE_NAME = env.str("DATABASE_NAME", "votes.db")

SENTRY_ENABLED = env.bool("SENTRY_ENABLED", False)
SENTRY_URL = env.str("SENTRY_URL", "")

STELLAR_USE_TESTNET = env.bool("STELLAR_USE_TESTNET", False)
STELLAR_ENDPOINT = "https://horizon-testnet.stellar.org" if STELLAR_USE_TESTNET else "https://horizon.stellar.org"
STELLAR_PASSPHRASE = Network.TESTNET_NETWORK_PASSPHRASE if STELLAR_USE_TESTNET else Network.PUBLIC_NETWORK_PASSPHRASE
BASE_FEE = env.int("BASE_FEE", 10000)
REWARD_PUBLIC_KEY = env.str("REWARD_PUBLIC_KEY")

USE_REFRACTOR = env.bool("USE_REFRACTOR", False)

DISCORD_ALLOWED_REACTION = env.json("DISCORD_ALLOWED_REACTION", "[]")
LEADERBOARD_LIMIT = env.int("LEADERBOARD_LIMIT", 10)
DISCORD_BOT_TOKEN = env.str("DISCORD_BOT_TOKEN")
REQUIRED_ROLE_ID = env.int("REQUIRED_ROLE_ID")
NOTIFY_USER = env.int("NOTIFY_USER")
DISCORD_WHITELIST_CHANNELS = env.json("DISCORD_WHITELIST_CHANNELS", "[]")
DISCORD_SERVER_ID = env.int("DISCORD_SERVER_ID", 0)

# Event Types
MESSAGE_REPLY = env.int("MESSAGE_REPLY_TYPE_CODE", 0)
REACTION = env.int("MESSAGE_REACTION_TYPE_CODE", 1)
POSTED_MESSAGE = env.int("MESSAGE_POSTED_TYPE_CODE", 2)

MESSAGE_REPLY_POINTS = env.int("MESSAGE_REPLY_TYPE_CODE", 2)
REACTION_POINTS = env.int("MESSAGE_REACTION_TYPE_CODE", 1)
POSTED_MESSAGE_POINTS = env.int("MESSAGE_POSTED_TYPE_CODE", 1)

# Event Points
# TODO: FIGURE OUT HOW TO USE ENVIORNMENT VARIABLES FOR THIS
TYPE_TO_VAR = {0: MESSAGE_REPLY, 1: REACTION, 2: POSTED_MESSAGE, None: None}
EVENT_POINTS = {MESSAGE_REPLY: MESSAGE_REPLY_POINTS, REACTION: REACTION_POINTS, POSTED_MESSAGE: POSTED_MESSAGE_POINTS, None: 1}

# LOWER BOUND, UPPER BOUND, POINTS
# TODO: FIGURE OUT HOW TO USE ENVIORNMENT VARIABLES FOR THIS.
MESSAGE_UPVOTE_DISTRIBUTION = [
	(25, 75, 1),
	(76, 150, 2),
	(151, 6000, 3) # 6000 is the maximum chars for an upvote - Set By Discord
]

