from unittest import TestCase

from helpers.database import (
    create_connection,
    setup_db,
    linkUserPubKey,
    getUserPubKey,
    updateHistory,
    getUser,
    removeHistory,
    fetchLeaderboard,
    queryHistory,
)


class DatabaseTest(TestCase):
    def setUp(self):
        self.conn = create_connection(":memory:")
        setup_db(self.conn)

    def tearDown(self):
        self.conn.close()

    def test_link_pubkey(self):
        linkUserPubKey(
            self.conn,
            "1234",
            "GDXXLZO42GOGK3WFJQ2LZVB464ACT6EXLU6HMXLQRJM735SB5X74M5RR",
        )
        pubkey = getUserPubKey(self.conn, "1234")
        self.assertEqual(
            pubkey,
            "GDXXLZO42GOGK3WFJQ2LZVB464ACT6EXLU6HMXLQRJM735SB5X74M5RR",
        )

    def test_history(self):
        res = updateHistory(self.conn, "1234", "4567", "7890", "0", "0")
        self.assertTrue(res)

        user = getUser(self.conn, "1234")
        self.assertEqual(user[0], 1234)
        self.assertEqual(user[1], 1)

        res = removeHistory(self.conn, "4567")
        self.assertTrue(res)

        user = getUser(self.conn, "1234")
        self.assertEqual(user, (None, 0))

    def test_leaderboard(self):
        updateHistory(self.conn, "1234", "4567", "7890", "0", "0")
        updateHistory(self.conn, "1234", "3456", "7890", "0", "0")
        updateHistory(self.conn, "2233", "4568", "7890", "0", "0")
        res = fetchLeaderboard(self.conn)
        self.assertEqual(len(res), 2)

    def test_query_history(self):
        updateHistory(self.conn, "1234", "4567", "7890", "0", "0")
        res = queryHistory(self.conn, "4567")
        self.assertEqual(res[0], 1234)

    """
    def test_unique(self):
        self.assertTrue(updateHistory(self.conn, "1234", "4567", "7890"))
        self.assertFalse(updateHistory(self.conn, "1234", "4567", "7890"))
        self.assertTrue(updateHistory(self.conn, "1234", "1111", "7890"))
        self.assertTrue(updateHistory(self.conn, "1234", "4567", "7891"))
    """
