import discord
from helper import fetchLeaderboard, getWeek

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
