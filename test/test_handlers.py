from unittest import TestCase, mock
import asyncio

from helpers.database import create_connection, setup_db, updateHistory, linkUserPubKey
from handlers.account_missing_warning import fetch_users_missing_pub


class WarningTest(TestCase):
    def setUp(self):
        self.conn = create_connection(":memory:")
        setup_db(self.conn)
        updateHistory(self.conn, "1234", "4567", "7890", "0", "0")
        updateHistory(self.conn, "2345", "5678", "7890", "0", "0")
        linkUserPubKey(
            self.conn,
            "1234",
            "GDXXLZO42GOGK3WFJQ2LZVB464ACT6EXLU6HMXLQRJM735SB5X74M5RR",
        )

    def tearDown(self):
        self.conn.close()

    @mock.patch("handlers.account_missing_warning.fetch_last_tx")
    @mock.patch("handlers.account_missing_warning.client")
    def test_fetch_users_missing_pub(self, client: mock.MagicMock, tx: mock.MagicMock):
        tx.return_value = None
        client.user.id = None
        loop = asyncio.get_event_loop()
        res = loop.run_until_complete(fetch_users_missing_pub(self.conn))
        self.assertEqual(len(res), 1)
