"""
Test module helpers.stellar
"""
import json
from datetime import datetime
from unittest import TestCase
import requests_mock
from stellar_sdk import TransactionEnvelope, CreateClaimableBalance

from helpers.stellar import (
    fetch_account_balance,
    generate_reward_tx,
    fetch_last_tx,
    validate_pub_key,
)
from settings.default import REWARD_PUBLIC_KEY, STELLAR_PASSPHRASE


class StellarTest(TestCase):
    def setUp(self) -> None:
        with open("test/fixtures/single_account.json", "r") as fixture_file:
            self.SINGLE_ACCOUNT = json.load(fixture_file)
        with open("test/fixtures/transactions.json", "r") as fixture_file:
            self.TRANSACTIONS = json.load(fixture_file)

    @requests_mock.Mocker()
    def test_fetch_account_balance(self, m: requests_mock.Mocker):
        m.get(
            "https://horizon.stellar.org/accounts/GTESTACCOUNT",
            json=self.SINGLE_ACCOUNT,
        )
        balance = fetch_account_balance("GTESTACCOUNT")
        self.assertEqual(balance, 100)

    @requests_mock.Mocker()
    def test_generate_reward_tx(self, m: requests_mock.Mocker):
        m.get(
            f"https://horizon.stellar.org/accounts/{REWARD_PUBLIC_KEY}",
            json=self.SINGLE_ACCOUNT,
        )
        xdr = generate_reward_tx(
            [
                ("GDR4LHPFDDNX27ZOI5QSLNDZV5GWJ5JGBRID5D3ZM7FFCFHSXI5PVL2I", 200.345),
                ("GCVP5WD3ZJ3NHVIW24Y2OZJGEZHIR5F6QFWUCMDQUJBFWONAAIC5NI6D", 123.5),
            ]
        )
        txe = TransactionEnvelope.from_xdr(xdr, STELLAR_PASSPHRASE)
        self.assertEqual(txe.transaction.memo.memo_text, b"Lumenaut reward!")
        self.assertEqual(len(txe.transaction.operations), 2)
        self.assertEqual(type(txe.transaction.operations[0]), CreateClaimableBalance)

    @requests_mock.Mocker()
    def test_fetch_last_tx(self, m: requests_mock.Mocker):
        m.get(
            f"https://horizon.stellar.org/accounts/{REWARD_PUBLIC_KEY}/transactions",
            json=self.TRANSACTIONS,
        )
        last_tx = fetch_last_tx()
        self.assertEqual(last_tx, datetime(2022, 11, 1))

    def test_validate_pub_key(self):
        self.assertTrue(validate_pub_key("GDQF4DKCL5APB4EDWJY5CJHMB2GLAAYJPO4QDOVEQO624LJ5BIVQS6C7"))
        self.assertFalse(validate_pub_key("GOBBLEYGOOK"))
