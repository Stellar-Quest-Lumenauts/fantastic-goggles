def getUser(conn, author):
    """
    Query the User
    """
    c = conn.cursor()
    c.execute("SELECT user_id, votes from votes WHERE user_id=?", (int(author), ))
    row = c.fetchone()
    return row

def createUser(conn, author):
    """
    Creates the User
    """
    c = conn.cursor()
    c.execute("INSERT INTO votes (user_id, votes) VALUES (?,1)", (int(author), ))
    conn.commit()

def updateVote(conn, author, vote):
    """
    Updates the Vote counter
    """
    c = conn.cursor()
    c.execute("UPDATE votes SET votes=? WHERE user_id=?", (int(vote), int(author), ))
    conn.commit()

def updateHistory(conn, author, message_id, backer):
    """
    Updates the history
    """
    c = conn.cursor()
    c.execute("INSERT INTO votes_history (user_id, message_id, backer) VALUES (?,?,?)", (int(author), int(message_id), int(backer), ))
    conn.commit()

def queryHistory(conn, message_id):
    """
    Query for a Specific Message
    """
    c = conn.cursor()
    c.execute("SELECT user_id from votes_history WHERE message_id=?", (int(message_id), ))
    row = c.fetchone()
    return row
