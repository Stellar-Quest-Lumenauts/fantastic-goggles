from datetime import datetime

def setup_db(conn):
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS votes_history (id INTEGER AUTO_INCREMENT PRIMARY KEY, user_id INTEGER, message_id INTEGER, backer INTEGER, vote_time DATETIME DEFAULT CURRENT_TIMESTAMP)''')
def getUser(conn, author):
    """
    Query the User
    """
    c = conn.cursor()
    c.execute("SELECT user_id, COUNT(*) as votes from votes_history WHERE user_id=?", (int(author), ))
    row = c.fetchone()
    return row

def updateHistory(conn, author, message_id, backer):
    """
    Updates the history
    Returns success
    """
    c = conn.cursor()
    c.execute("INSERT INTO votes_history (user_id, message_id, backer) VALUES (?,?,?)", (int(author), int(message_id), int(backer), ))
    conn.commit()
    return c.rowcount > 0

def removeHistory(conn, message_id, author = None, backer = None):
    """
    Updates the history to remove vote
    Returns success
    """
    c = conn.cursor()
    if backer != None and author != None:
        c.execute("DELETE FROM votes_history WHERE user_id=? AND message_id=? AND backer=?", (int(author), int(message_id), int(backer), ))
    else:
        c.execute("DELETE FROM votes_history WHERE message_id=?", (int(message_id), ))
    conn.commit()
    return c.rowcount > 0

def fetchLeaderboard(conn, dateFrom = None, dateTo = None):
    """
    Returns the current leaderboard
    """
    if dateFrom == None:
        dateFrom = datetime.utcfromtimestamp(0)
    if dateTo == None:
        dateTo = datetime.now()


    c = conn.cursor()
    c.execute("SELECT user_id, COUNT() as votes FROM votes_history WHERE vote_time >= ? AND vote_time <= ? ORDER by votes DESC", (dateFrom, dateTo))
    return c.fetchall()

def queryHistory(conn, message_id):
    """
    Query for a Specific Message
    """
    c = conn.cursor()
    c.execute("SELECT user_id from votes_history WHERE message_id=?", (int(message_id), ))
    row = c.fetchone()
    return row
