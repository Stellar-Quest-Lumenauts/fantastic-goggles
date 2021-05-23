import os
import time
from datetime import datetime
from stellar_sdk import TransactionBuilder, Server, Network, Keypair, asset
from stellar_sdk.operation.create_claimable_balance import Claimant

STELLAR_USE_TESTNET = "USE_STELLAR_TEST_NET" in os.environ
STELLAR_ENDPOINT = "https://horizon-testnet.stellar.org" if STELLAR_USE_TESTNET else "https://horizon.stellar.org"
STELLAR_PASSPHRASE = Network.TESTNET_NETWORK_PASSPHRASE if STELLAR_USE_TESTNET else Network.PUBLIC_NETWORK_PASSPHRASE

BASE_FEE = 10000 if "STELLAR_BASE_FEE" not in os.environ else os.environ["STELLAR_BASE_FEE"]

if STELLAR_USE_TESTNET:
    print("Using stellar testnet")

PUBLIC_KEY = os.environ["REWARD_PUBLIC_KEY"]

server = Server(horizon_url=STELLAR_ENDPOINT)


def fetch_account_balance(pubKey: str = PUBLIC_KEY) -> float:
    """
    Returns the balance of the given account available to be send
    """
    try:
        acc = server.accounts().account_id(PUBLIC_KEY).call()
    except Exception:
        print(f"Specified account ({pubKey}) does not exists")
        return 0
    balance = 0

    for b in acc["balances"]:
        if b["asset_type"] == "native":
            balance = float(b["balance"])
            break

    balance -= 0.5 * (2 + acc["subentry_count"])  # base reserve
    return balance


def generate_reward_tx(rewardee, base_fee=None):
    """
    Generates transaction XDR full of claimable balance operations
    takes tewardee (array of tuples (pub_key, amount)) where pub_key is str and amount is float
    returns XDR as string | None if unable to load account
    """
    try:
        source_acc = server.load_account(PUBLIC_KEY)  # fetch sequence or will it be used with a fee bump?
    except Exception:
        print(f"Failed to load public reward account {PUBLIC_KEY}!")
        return None

    fee = BASE_FEE

    try:
        fee = server.fetch_base_fee() if base_fee is None else base_fee
    except Exception:
        print(f"Error fetching base fees from networking! Defaulting to {BASE_FEE}")
    tx = TransactionBuilder(
        source_account=source_acc,
        network_passphrase=STELLAR_PASSPHRASE,
        base_fee=fee,
    ).add_text_memo("Lumenaut reward!")

    for rewarded in rewardee:
        reward = round(rewarded[1], 7)
        if reward <= 0:
            continue

        tx.append_create_claimable_balance_op(
            asset=asset.Asset.native(),
            amount=str(reward),
            claimants=[Claimant(rewarded[0]), Claimant(PUBLIC_KEY)],
        )

    now = int(time.time())
    xdr = tx.add_time_bounds(now, 0).build().to_xdr()  # make valid one day from now

    return xdr


def fetch_last_tx(pubKey: str = PUBLIC_KEY, memo: str = "Lumenaut reward!"):
    """
    Finds the last transaction a account submitted and fetches the creation time
    memo can be specified to search for a specific memo
    If timeBounds.minTime is not set use created_at
    Returns datetime or None if account not found
    """
    try:
        txs = (
            server.transactions()
            .for_account(pubKey)
            .include_failed(False)
            .limit(200)
            .order("desc")
            .call()["_embedded"]["records"]
        )

        for records in txs:
            if records["source_account"] != pubKey:
                continue

            if memo is not None and (records["memo_type"] != "text" or records["memo"] != memo):
                continue

            created = records["created_at"]
            timeBound = records["valid_after"]
            if timeBound == "1970-01-01T00:00:00Z":  # not set
                return datetime.strptime(created, "%Y-%m-%dT%H:%M:%SZ")
            return datetime.strptime(timeBound, "%Y-%m-%dT%H:%M:%SZ")
        return None
    except Exception:
        return None


def validate_pub_key(pub_key: str):
    """
    Valids a public key
    Returns true if valid key
    """
    try:
        Keypair.from_public_key(pub_key)
        return True
    except Exception:
        return False
