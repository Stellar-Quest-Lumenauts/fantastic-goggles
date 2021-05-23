from helper import *
from main import *
from discord_helpers import hasRole

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')
    leaderboard = fetchLeaderboard(conn)
    to_be_removed = []
    guild = client.get_guild(763798356484161566)
    
    for row in leaderboard:
        if row[0] in to_be_removed:
            continue
        try:
            member = guild.get_member(row[0])
            if hasRole(member.roles, REQUIRED_ROLE_ID):
                continue
        except:
            print(f"Found invalid user {row[0]}!")

        to_be_removed.append(member)
    
    SQL = "WHERE false"

    for m in to_be_removed:
        print(m)
        SQL +=f" OR user_id={m.id}"
    
    print(SQL)

    await client.close()

def start():
    setup_db(conn)
    client.run(BOT_TOKEN)

if __name__ == '__main__':
    start()