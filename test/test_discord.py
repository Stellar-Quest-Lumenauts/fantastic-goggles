"""
Test module helpers.discord
"""
from unittest import TestCase, mock

from helpers.database import create_connection, setup_db, updateHistory, linkUserPubKey
from helpers.discord import generate_payouts


class DiscordTest(TestCase):
    def setUp(self):
        self.conn = create_connection(":memory:")
        setup_db(self.conn)

    def tearDown(self):
        self.conn.close()

    @mock.patch("helpers.discord.fetch_last_tx")
    @mock.patch("helpers.discord.fetch_account_balance")
    def test_generate_payouts(self, mock_fetch_balance: mock.MagicMock, mock_fetch_last_tx: mock.MagicMock):
        mock_fetch_last_tx.return_value = None
        mock_fetch_balance.return_value = 100
        # Generate some votes
        # - 2 for leader
        # - 1 for 4 more users
        updateHistory(self.conn, "1234", "35634535", "8888", "5656734", "0", "0")
        updateHistory(self.conn, "1234", "65765765", "8888", "7675654", "0", "0")
        updateHistory(self.conn, "3456", "24435646", "8888", "2376558", "0", "0")
        updateHistory(self.conn, "4567", "56677456", "8888", "6754326", "0", "0")
        updateHistory(self.conn, "5678", "76867574", "8888", "9763453", "0", "0")
        updateHistory(self.conn, "9999", "76867574", "8888", "9763453", "0", "0")  # will not be linked
        # Link accounts - 4 users linked, one user with 1 vote missing a link
        linkUserPubKey(self.conn, "1234", "GBFCLLXBHWJMRY6SX7VVPXDGOWRGP7TWXCCNAEFOOCTCQAE3TDSH6GWC")
        linkUserPubKey(self.conn, "3456", "GCUSNN2ME2IPEGVXAT4YRH3HNZXMWEGCPUNMSMSIUR6TIBGTDE36CBWX")
        linkUserPubKey(self.conn, "4567", "GBTE7ZQM3K6JSITR4H7F2OAMDN2GJKF2VB7Z4F4CIOYPI4QGWLI6RV4V")
        linkUserPubKey(self.conn, "5678", "GAXWVPAJGB7O7FG7C42EUJKFYFQXCWHSQNCXCIU3S3HPWDYAGG4R57AK")
        # Generate report
        res = generate_payouts(self.conn)
        # Validate
        self.assertEqual(len(res), 4)
        # Values verified in Excel
        self.assertEqual(res[0], ("GBFCLLXBHWJMRY6SX7VVPXDGOWRGP7TWXCCNAEFOOCTCQAE3TDSH6GWC", 38.384))
        self.assertEqual(res[1], ("GCUSNN2ME2IPEGVXAT4YRH3HNZXMWEGCPUNMSMSIUR6TIBGTDE36CBWX", 19.192))
