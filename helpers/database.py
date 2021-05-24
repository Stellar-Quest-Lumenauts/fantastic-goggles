import os
from datetime import datetime
import sqlite3
from typing import Any, Union
import psycopg2

from settings.default import SQLITE3_ENABLED

Connection = Union[sqlite3.Connection, Any]


def prepareQuery(query):
    """
    Parse for SQLITE3 or Postgress
    """
    if SQLITE3_ENABLED is False:
        return query.replace("?", "%s")
    return query


def create_connection(db_file: str) -> Connection:
    """Create a database connection to a SQLite or Postgres database"""
    try:
        if SQLITE3_ENABLED:
            # print("Using sqlite3!")
            conn = sqlite3.connect(db_file)
        else:
            # print("Using postgres!")
            conn = psycopg2.connect(
                host=os.environ["POSTGRE_HOST"],
                database=os.environ["POSTGRE_DB"],
                port=os.environ["POSTGRE_PORT"],
                user=os.environ["POSTGRE_USER"],
                password=os.environ["POSTGRE_PASSWORD"],
            )
        # print("Database connection established!")
        return conn
    except Exception as e:
        print(e)


def setup_db(conn: Connection) -> None:
    c = conn.cursor()
    if SQLITE3_ENABLED:
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS votes_history (id INTEGER AUTO_INCREMENT PRIMARY KEY, user_id INTEGER,
            message_id INTEGER, backer INTEGER, vote_time DATETIME DEFAULT CURRENT_TIMESTAMP)
            """
        )
        c.execute(
            """CREATE UNIQUE INDEX IF NOT EXISTS one_ring_rules_them_all ON votes_history(message_id, backer)"""
        )
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS users(user_id INTEGER PRIMARY KEY, stellar_account VARCHAR(56) NOT NULL
            ON CONFLICT REPLACE)
            """
        )
    else:
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS votes_history (id SERIAL NOT NULL PRIMARY KEY, user_id BIGINT,
            message_id BIGINT, backer BIGINT, vote_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP)
            """
        )
        c.execute(
            """CREATE UNIQUE INDEX IF NOT EXISTS one_ring_rules_them_all ON votes_history(message_id, backer)"""
        )
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS users(user_id BIGINT NOT NULL PRIMARY KEY,
            stellar_account VARCHAR(56) NOT NULL)
            """
        )


def linkUserPubKey(conn: Connection, user: str, key: str) -> bool:
    """
    Inserts the connection discord_id <-> public key into the DB
    return success as bool
    """
    c = conn.cursor()
    if SQLITE3_ENABLED:
        c.execute(
            "INSERT INTO users(user_id, stellar_account) VALUES (?, ?)",
            (int(user), str(key)),
        )
    else:
        c.execute(
            """
            INSERT INTO users(user_id, stellar_account) VALUES (%s, %s) ON CONFLICT (user_id)
            DO UPDATE SET stellar_account=%s
            """,
            (int(user), str(key), str(key)),
        )
        pass
    conn.commit()
    return c.rowcount > 0


def getUserPubKey(conn: Connection, user: str) -> Union[str, None]:
    """
    Queries the users public stellar key
    Returns string or None
    """
    c = conn.cursor()
    c.execute(
        prepareQuery("SELECT stellar_account FROM users WHERE user_id=?"),
        (int(user),),
    )
    row = c.fetchone()

    if row is None:
        return None
    return row[0]


def fetchUserPubKeys(conn: Connection) -> list:
    """
    Returns array containing (discord_id, stellar_public_key) tuples
    """
    c = conn.cursor()
    c.execute("SELECT user_id, stellar_account FROM users")
    return c.fetchall()


def getUser(conn: Connection, author: str) -> Any:
    """
    Query the User
    """
    c = conn.cursor()
    c.execute(
        prepareQuery("SELECT user_id, COUNT(*) as votes from votes_history WHERE user_id=?"),
        (int(author),),
    )
    row = c.fetchone()
    return row


def updateHistory(conn: Connection, author: str, message_id: str, backer: str) -> bool:
    """
    Updates the history
    Returns success
    """
    c = conn.cursor()
    try:
        c.execute(
            prepareQuery("INSERT INTO votes_history (user_id, message_id, backer) VALUES (?,?,?)"),
            (
                int(author),
                int(message_id),
                int(backer),
            ),
        )
        conn.commit()
    except:
        return False

    return c.rowcount > 0


def removeHistory(conn: Connection, message_id: str, author=None, backer=None) -> bool:
    """
    Updates the history to remove vote
    Returns success
    """
    c = conn.cursor()
    if backer is not None and author is not None:
        c.execute(
            prepareQuery("DELETE FROM votes_history WHERE user_id=? AND message_id=? AND backer=?"),
            (
                int(author),
                int(message_id),
                int(backer),
            ),
        )
    else:
        c.execute(
            prepareQuery("DELETE FROM votes_history WHERE message_id=?"),
            (int(message_id),),
        )
    conn.commit()
    return c.rowcount > 0


def fetchLeaderboard(conn: Connection, dateFrom: datetime = None, dateTo: datetime = None):
    """
    Returns the current leaderboard
    """
    if dateFrom is None:
        dateFrom = datetime.utcfromtimestamp(0)
    if dateTo is None:
        dateTo = datetime.now()

    c = conn.cursor()
    c.execute(
        prepareQuery(
            """
            SELECT user_id, COUNT(user_id) as votes FROM votes_history
            WHERE vote_time >= ? AND vote_time <= ? GROUP BY user_id ORDER by votes DESC, user_id ASC
            """
        ),
        (dateFrom, dateTo),
    )
    return c.fetchall()


def queryHistory(conn: Connection, message_id: str):
    """
    Query for a Specific Message
    """
    c = conn.cursor()
    c.execute(
        prepareQuery("SELECT user_id from votes_history WHERE message_id=?"),
        (int(message_id),),
    )
    row = c.fetchone()
    return row
