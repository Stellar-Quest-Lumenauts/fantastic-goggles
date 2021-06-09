"""
Test module helpers.generic
"""
from unittest import TestCase
import requests_mock
from stellar_sdk import TransactionBuilder, Account

from helpers.generic import post_to_refractor
from settings.default import REWARD_PUBLIC_KEY, STELLAR_PASSPHRASE


class GenericTest(TestCase):
    def setUp(self) -> None:
        self.account = Account(REWARD_PUBLIC_KEY, 0)
        self.tx = (
            TransactionBuilder(
                self.account,
                STELLAR_PASSPHRASE,
            )
            .add_text_memo("This is a test")
            .append_manage_data_op("foo", "bar")
            .build()
        )

    @requests_mock.Mocker()
    def test_post_to_refractor(self, m: requests_mock.Mocker):
        m.post("https://api.refractor.stellar.expert/tx")
        refractor_url = post_to_refractor(self.tx.to_xdr())
        self.assertIn(self.tx.hash_hex(), refractor_url)

    @requests_mock.Mocker()
    def test_refractor_error(self, m: requests_mock.Mocker):
        m.post("https://api.refractor.stellar.expert/tx", status_code=500)
        self.assertRaises(Exception, post_to_refractor, self.tx.to_xdr())
