from datetime import datetime, timedelta

def setup_db(conn):
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS votes_history (id INTEGER AUTO_INCREMENT PRIMARY KEY, user_id INTEGER, message_id INTEGER, backer INTEGER, vote_time DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS users(user_id INTEGER PRIMARY KEY, stellar_account VARCHAR(55) NOT NULL ON CONFLICT REPLACE)''')

def linkUserPubKey(conn, user, key):
    """
    Insersts the connection discord_id <-> public key into the DB
    return success as bool
    """
    c = conn.cursor()
    c.execute("INSERT INTO users(user_id, stellar_account) VALUES (?, ?)", (int(user), str(key)))
    conn.commit()
    return c.rowcount > 0

def getUserPubKey(conn, user):
    """
    Queries the users public stellar key
    Returns string or None
    """
    c = conn.cursor()
    c.execute("SELECT stellar_account FROM users WHERE user_id=?", (int(user)))
    row = c.fetchone()

    if row == None:
        return None
    return row[0]

def fetchUserPubKeys(conn):
    """
    Returns array containing (discord_id, stellar_public_key) tuples
    """
    c = conn.cursor()
    c.execute("SELECT user_id, stellar_account FROM users")
    return c.fetchall()

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
    c.execute("SELECT user_id, COUNT() as votes FROM votes_history WHERE vote_time >= ? AND vote_time <= ? GROUP BY user_id ORDER by votes DESC", (dateFrom, dateTo))
    return c.fetchall()

def queryHistory(conn, message_id):
    """
    Query for a Specific Message
    """
    c = conn.cursor()
    c.execute("SELECT user_id from votes_history WHERE message_id=?", (int(message_id), ))
    row = c.fetchone()
    return row