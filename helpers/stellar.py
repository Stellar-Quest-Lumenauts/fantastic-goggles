import time
from datetime import datetime
from typing import Union
from stellar_sdk import TransactionBuilder, Server, Keypair, Asset
from stellar_sdk.operation.create_claimable_balance import Claimant

from settings.default import (
    STELLAR_USE_TESTNET,
    STELLAR_ENDPOINT,
    STELLAR_PASSPHRASE,
    BASE_FEE,
    REWARD_PUBLIC_KEY,
)

if STELLAR_USE_TESTNET:
    print("Using stellar testnet")

server = Server(horizon_url=STELLAR_ENDPOINT)


def fetch_account_balance(pubKey: str = REWARD_PUBLIC_KEY) -> float:
    """
    Returns the balance of the given account available to be send
    """
    try:
        acc = server.accounts().account_id(pubKey).call()
    except Exception as e:
        print(f"Specified account ({pubKey}) does not exists:", e)
        return 0
    balance = 0

    for b in acc["balances"]:
        if b["asset_type"] == "native":
            balance = float(b["balance"])
            break

    balance -= 0.5 * (2 + acc["subentry_count"] + acc["num_sponsoring"])  # base reserve
    return balance


def generate_reward_tx(rewardees: list[tuple[str, float]], base_fee: int = BASE_FEE) -> str:
    """
    Generates transaction XDR full of claimable balance operations
    takes tewardee (array of tuples (pub_key, amount)) where pub_key is str and amount is float
    returns XDR as string | None if unable to load account
    """
    try:
        # fetch sequence or will it be used with a fee bump?
        source_acc = server.load_account(REWARD_PUBLIC_KEY)
    except Exception as e:
        print(f"Failed to load public reward account {REWARD_PUBLIC_KEY}!", e)
        return None

    tx = TransactionBuilder(
        source_account=source_acc,
        network_passphrase=STELLAR_PASSPHRASE,
        base_fee=base_fee,
    ).add_text_memo("Lumenaut reward!")

    for account, reward in rewardees:
        reward = round(reward, 7)
        if reward <= 0:
            continue

        tx.append_create_claimable_balance_op(
            asset=Asset.native(),
            amount=str(reward),
            claimants=[Claimant(account), Claimant(REWARD_PUBLIC_KEY)],
        )

    now = int(time.time())
    xdr = tx.add_time_bounds(now, 0).build().to_xdr()  # make valid one day from now

    return xdr


def fetch_last_tx(pubKey: str = REWARD_PUBLIC_KEY, memo: str = "Lumenaut reward!") -> Union[datetime, None]:
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

            if memo is not None:
                if records.get("memo") != memo:
                    continue

            created = records["created_at"]
            timeBound = records["valid_after"]
            if timeBound == "1970-01-01T00:00:00Z":  # not set
                return datetime.strptime(created, "%Y-%m-%dT%H:%M:%SZ")
            return datetime.strptime(timeBound, "%Y-%m-%dT%H:%M:%SZ")
        return None
    except Exception:
        return None


def validate_pub_key(pub_key: str) -> bool:
    """
    Valids a public key
    Returns true if valid key
    """
    try:
        Keypair.from_public_key(pub_key)
        return True
    except Exception:
        return False
