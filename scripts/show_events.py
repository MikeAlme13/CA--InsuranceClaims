"""
Insurance Claims DApp - event log reader.

Prints every event the contract has emitted, in block order. This is the
on-chain audit trail described in docs/design.md section 4.1.

Ganache's own EVENTS tab stays empty in Quickstart mode because it has no ABI
for the contract and cannot decode the logs. The events are on the chain either
way; this script decodes them with the ABI in abi/InsuranceClaims.json.

Usage:
    python scripts/show_events.py 0xYourContractAddress
    CONTRACT_ADDRESS=0x... python scripts/show_events.py
"""

import json
import os
import sys
from pathlib import Path

from web3 import Web3

ROOT = Path(__file__).resolve().parent.parent
ABI_PATH = ROOT / "abi" / "InsuranceClaims.json"
GANACHE_URL = "http://127.0.0.1:7545"

EVENTS = ["PolicyCreated", "ClaimSubmitted", "ClaimDecided", "ClaimPaid"]
STATUS = {0: "Submitted", 1: "Approved", 2: "Rejected", 3: "Paid"}


def readable(key, value):
    """Make enum and wei values readable in the printout."""
    if key == "status":
        return "{} ({})".format(value, STATUS.get(value, "?"))
    if key in ("premium", "coverage", "amount") and value >= 10 ** 15:
        return "{} ETH".format(Web3.from_wei(value, "ether"))
    if key in ("premium", "coverage", "amount"):
        return "{} wei".format(value)
    return value


w3 = Web3(Web3.HTTPProvider(GANACHE_URL))
if not w3.is_connected():
    print("ERROR: cannot reach Ganache at {}".format(GANACHE_URL))
    sys.exit(1)

raw = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("CONTRACT_ADDRESS")
if not raw:
    print("Usage: python scripts/show_events.py 0xYourContractAddress")
    sys.exit(1)

address = w3.to_checksum_address(raw)
if w3.eth.get_code(address) in (b"", b"0x"):
    print("ERROR: no contract found at {}".format(address))
    sys.exit(1)

with open(ABI_PATH) as f:
    contract = w3.eth.contract(address=address, abi=json.load(f))

print("Event log for contract {}".format(address))
print("=" * 78)

rows = []
for name in EVENTS:
    for log in getattr(contract.events, name)().get_logs(from_block=0):
        rows.append((log["blockNumber"], name, dict(log["args"])))

if not rows:
    print("No events found. Has the contract been used yet?")
    sys.exit(0)

for block, name, args in sorted(rows, key=lambda r: r[0]):
    pretty = ", ".join(
        "{}={}".format(k, readable(k, v)) for k, v in args.items()
    )
    print("block {:<5} {:<15} {}".format(block, name, pretty))

print("=" * 78)
print("{} events in total.".format(len(rows)))
print("Every claim decision is recorded here permanently and cannot be altered.")
