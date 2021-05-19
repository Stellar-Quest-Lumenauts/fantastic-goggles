import os

SQLITE3_ENABLED = True if os.environ['SQLITE3_ENABLED'] == True else False

def prepareQuery(query):
    if SQLITE3_ENABLED == False:
        return query.replace('?', '%s')

def getUser(conn, author):
    """
    Query the User
    """
    c = conn.cursor()
    c.execute(prepareQuery("SELECT user_id, COUNT(*) as votes from votes_history WHERE user_id=?"), (int(author), ))
    row = c.fetchone()
    return row

def updateHistory(conn, author, message_id, backer):
    """
    Updates the history
    Returns success
    """
    c = conn.cursor()
    c.execute(prepareQuery("INSERT INTO votes_history (user_id, message_id, backer) VALUES (?,?,?)"), (int(author), int(message_id), int(backer), ))
    conn.commit()
    return c.rowcount > 0

def removeHistory(conn, message_id, author = None, backer = None):
    """
    Updates the history to remove vote
    Returns success
    """
    c = conn.cursor()
    if backer != None and author != None:
        c.execute(prepareQuery("DELETE FROM votes_history WHERE user_id=? AND message_id=? AND backer=?"), (int(author), int(message_id), int(backer), ))
    else:
        c.execute(prepareQuery("DELETE FROM votes_history WHERE message_id=?"), (int(message_id), ))
    conn.commit()
    return c.rowcount > 0

def fetchLeaderboard(conn):
    """
    Returns the current leaderboard
    """
    c = conn.cursor()
    c.execute(prepareQuery("SELECT user_id, COUNT() as votes FROM votes_history ORDER by votes DESC"))
    return c.fetchall()

def queryHistory(conn, message_id):
    """
    Query for a Specific Message
    """
    c = conn.cursor()
    c.execute(prepareQuery("SELECT user_id from votes_history WHERE message_id=?", (int(message_id), )))
    row = c.fetchone()
    return row
