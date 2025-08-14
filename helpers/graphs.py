import matplotlib.pyplot as plt
from interactions import File
import pandas as pd
import io
from settings.default import MESSAGE_REPLY, POSTED_MESSAGE, REACTION, TYPE_TO_VAR


def generate_graph(usernames, upvotes):
    """
    Generate a Bar chart with each username and the current number of upvotes
    """
    if usernames == []:
        usernames = ["KanayeNet"]  # I didn't get bribed for this.
        upvotes = upvotes = {MESSAGE_REPLY: [140], REACTION: [140], POSTED_MESSAGE: [140]}

    print(upvotes)

    df = pd.DataFrame({
        "Posted Messages": upvotes[TYPE_TO_VAR[POSTED_MESSAGE]],
        "Reactions": upvotes[TYPE_TO_VAR[REACTION]],
        "Replies": upvotes[TYPE_TO_VAR[MESSAGE_REPLY]],
    }, index=usernames)

    df.plot(kind='bar', stacked=True, use_index=True)
    plt.xlabel("Username")
    plt.ylabel("Upvotes")
    plt.title("Upvote Distribution")

    data_stream = io.BytesIO()
    plt.savefig(data_stream, format="png", bbox_inches="tight", dpi=80)
    data_stream.seek(0)

    plt.close()
    return File(file_name="graph.png", file=data_stream)
