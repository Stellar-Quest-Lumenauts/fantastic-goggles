import seaborn as sns
import matplotlib.pyplot as plt
import discord
import io


def generate_graph(usernames, upvotes):
    """
    Generate a Bar chart with each username and the current number of upvotes
    """
    if usernames == [] and upvotes == []:
        usernames = ["KanayeNet"]  # I didn't get bribed for this.
        upvotes = [420]

    sns.set_theme(style="dark")
    ax = sns.barplot(x=usernames, y=upvotes)
    ax.set(xlabel="Username", ylabel="Upvotes", title="Upvote Distribution")

    data_stream = io.BytesIO()
    plt.savefig(data_stream, format="png", bbox_inches="tight", dpi=80)
    data_stream.seek(0)

    plt.close()
    return discord.File(data_stream, filename="graph.png")
