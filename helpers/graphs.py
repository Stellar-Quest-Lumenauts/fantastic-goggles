import seaborn as sns
import matplotlib.pyplot as plt
import discord

def generate_graph(usernames, upvotes):
    """
    Generate a Bar chart with each username and the current number of upvotes
    """
    sns.set_theme(style="dark")
    ax = sns.barplot(x=usernames, y=upvotes)
    ax.set(xlabel="Username", ylabel="Upvotes", title="Upvote Distribution")

    data_stream = io.BytesIO()
    plt.savefig(data_stream, format="png", bbox_inches="tight", dpi = 80)
    plt.close()

    return discord.File(data_stream, filename="graph.png")