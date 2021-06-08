import postbin
import requests
from stellar_sdk import TransactionEnvelope

from settings.default import STELLAR_PASSPHRASE


def upload_to_hastebin(content: str):
    """
    Upload a given content to hastebin.com
    Returns URL of uploaded content
    """
    return postbin.postSync(content)


def post_to_refractor(xdr: str, use_testnet: bool = False) -> str:
    """
    Posts the transaction to Refractor by Orbitlens
    Returns a URL to the signing interface
    """
    network = "testnet" if use_testnet else "public"
    try:
        resp = requests.post(
            "https://api.refractor.stellar.expert/tx",
            json={
                "network": network,
                "xdr": xdr,
                "submit": True,
            },
        )
        resp.raise_for_status()
        # Parse the xdr to get a transaction hash for the URL
        tx = TransactionEnvelope.from_xdr(xdr, STELLAR_PASSPHRASE)
        return f"https://refractor.stellar.expert/tx/{tx.hash_hex()}"
    except Exception as e:
        raise Exception(f"Failed posting to Refractor: {e}")
