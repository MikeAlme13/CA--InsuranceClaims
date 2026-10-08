"""
Insurance Claims DApp - Web3 interaction script.

Runs the full claim lifecycle against a contract already deployed on Ganache:
    createPolicy -> payPremium -> submitClaim -> approveClaim -> payClaim

Usage:
    python scripts/interact.py
    CONTRACT_ADDRESS=0x... python scripts/interact.py

The contract address changes every time you redeploy from Remix, so pass it
through the CONTRACT_ADDRESS environment variable (run_demo.sh does this for
you) or edit DEFAULT_CONTRACT_ADDRESS below.
"""

import json
import os
import sys
from pathlib import Path

from web3 import Web3

# Paths are resolved from the repository root, so the script works no matter
# which directory you run it from.
ROOT = Path(__file__).resolve().parent.parent
ABI_PATH = ROOT / "abi" / "InsuranceClaims.json"

GANACHE_URL = "http://127.0.0.1:7545"
DEFAULT_CONTRACT_ADDRESS = "0x0687ab54002cd89be3c30da43252d4752f70e9fd"

# Amounts are kept at ether scale on purpose. With wei-sized values the payout
# is dwarfed by gas costs and the policyholder's balance in Ganache goes *down*
# after settlement, which is the opposite of what the demo needs to show.
PREMIUM = Web3.to_wei(1, "ether")
COVERAGE = Web3.to_wei(5, "ether")
CLAIM_AMOUNT = Web3.to_wei(2, "ether")


def eth(wei_value, signed=False):
    """Format a wei amount as ether. from_wei rejects negatives, so the sign is
    handled here: balance deltas are routinely negative."""
    if wei_value < 0:
        prefix = "-"
    elif signed:
        prefix = "+"
    else:
        prefix = ""
    return "{}{} ETH".format(prefix, Web3.from_wei(abs(wei_value), "ether"))


def tx_hex(value):
    """Return a 0x-prefixed hash string across hexbytes versions."""
    if hasattr(value, "to_0x_hex"):
        return value.to_0x_hex()
    text = value.hex()
    return text if text.startswith("0x") else "0x" + text


def show_events(contract, event_name, receipt):
    """Print every log of one event type found in a receipt, and return them."""
    try:
        logs = getattr(contract.events, event_name)().process_receipt(receipt)
    except Exception as exc:  # pragma: no cover - depends on web3 version
        print("    (could not decode {}: {})".format(event_name, exc))
        return []
    for log in logs:
        args = dict(log["args"])
        print("    event {}: {}".format(event_name, args))
    return logs


# ---------------------------------------------------------------------------
# 1. Connect to Ganache
# ---------------------------------------------------------------------------
w3 = Web3(Web3.HTTPProvider(GANACHE_URL))

if not w3.is_connected():
    print("ERROR: cannot reach Ganache at {}".format(GANACHE_URL))
    print("Open Ganache and click Quickstart, then run this script again.")
    sys.exit(1)

print("Connected to Ganache at {}".format(GANACHE_URL))

# ---------------------------------------------------------------------------
# 2. Accounts
# ---------------------------------------------------------------------------
insurer = w3.eth.accounts[0]       # account 0 - the insurer, deployed the contract
policyholder = w3.eth.accounts[1]  # account 1 - the policyholder

print("Insurer     (account 0): {}".format(insurer))
print("Policyholder(account 1): {}".format(policyholder))

# ---------------------------------------------------------------------------
# 3. Load the ABI
# ---------------------------------------------------------------------------
with open(ABI_PATH) as f:
    abi = json.load(f)

# ---------------------------------------------------------------------------
# 4. Attach to the deployed contract
# ---------------------------------------------------------------------------
raw_address = os.environ.get("CONTRACT_ADDRESS", DEFAULT_CONTRACT_ADDRESS)
contract_address = w3.to_checksum_address(raw_address)

if w3.eth.get_code(contract_address) in (b"", b"0x"):
    print("\nERROR: no contract found at {}".format(contract_address))
    print("Deploy InsuranceClaims.sol in Remix first, copy the address, then run:")
    print("    CONTRACT_ADDRESS=0xYourAddress python scripts/interact.py")
    sys.exit(1)

contract = w3.eth.contract(address=contract_address, abi=abi)
print("Contract: {}".format(contract_address))

# ---------------------------------------------------------------------------
# 5. Balances before
# ---------------------------------------------------------------------------
holder_before = w3.eth.get_balance(policyholder)
contract_before = w3.eth.get_balance(contract_address)

print("\n=== Balances before ===")
print("Policyholder: {}".format(eth(holder_before)))
print("Contract    : {}".format(eth(contract_before)))

# ---------------------------------------------------------------------------
# 6. Create the policy (insurer only)
# ---------------------------------------------------------------------------
print("\n=== createPolicy (from insurer) ===")
tx = contract.functions.createPolicy(policyholder, PREMIUM, COVERAGE).transact(
    {"from": insurer}
)
receipt = w3.eth.wait_for_transaction_receipt(tx)
print("  tx: {}".format(tx_hex(tx)))
show_events(contract, "PolicyCreated", receipt)

# ---------------------------------------------------------------------------
# 7. Pay the premium (activates the policy)
# ---------------------------------------------------------------------------
print("\n=== payPremium (from policyholder, value = {}) ===".format(eth(PREMIUM)))
tx = contract.functions.payPremium().transact(
    {"from": policyholder, "value": PREMIUM}
)
receipt = w3.eth.wait_for_transaction_receipt(tx)
print("  tx: {}".format(tx_hex(tx)))
print("  policy active: {}".format(contract.functions.policies(policyholder).call()[3]))

# ---------------------------------------------------------------------------
# 8. Hash the evidence off-chain (only the digest goes on-chain)
# ---------------------------------------------------------------------------
evidence = "claim_evidence_document.pdf"
evidence_hash = w3.keccak(text=evidence)

print("\n=== Evidence hash (Keccak-256) ===")
print("  document: {}".format(evidence))
print("  keccak256: {}".format(tx_hex(evidence_hash)))

# ---------------------------------------------------------------------------
# 9. Submit the claim
# ---------------------------------------------------------------------------
print("\n=== submitClaim (from policyholder, {}) ===".format(eth(CLAIM_AMOUNT)))
tx = contract.functions.submitClaim(CLAIM_AMOUNT, evidence_hash).transact(
    {"from": policyholder}
)
receipt = w3.eth.wait_for_transaction_receipt(tx)
print("  tx: {}".format(tx_hex(tx)))
submitted = show_events(contract, "ClaimSubmitted", receipt)

# Read the id back from the event rather than assuming 0: the contract may
# already hold claims created earlier from Remix.
if submitted:
    claim_id = submitted[0]["args"]["id"]
else:
    print("ERROR: no ClaimSubmitted event found, cannot continue.")
    sys.exit(1)

print("  claim id: {}".format(claim_id))

# ---------------------------------------------------------------------------
# 10. Approve the claim (insurer only)
# ---------------------------------------------------------------------------
print("\n=== approveClaim({}) (from insurer) ===".format(claim_id))
tx = contract.functions.approveClaim(claim_id).transact({"from": insurer})
receipt = w3.eth.wait_for_transaction_receipt(tx)
print("  tx: {}".format(tx_hex(tx)))
show_events(contract, "ClaimDecided", receipt)

# ---------------------------------------------------------------------------
# 11. Pay the claim (insurer only)
# ---------------------------------------------------------------------------
print("\n=== payClaim({}) (from insurer) ===".format(claim_id))
tx = contract.functions.payClaim(claim_id).transact({"from": insurer})
receipt = w3.eth.wait_for_transaction_receipt(tx)
print("  tx: {}".format(tx_hex(tx)))
show_events(contract, "ClaimPaid", receipt)

# ---------------------------------------------------------------------------
# 12. Balances after
# ---------------------------------------------------------------------------
holder_after = w3.eth.get_balance(policyholder)
contract_after = w3.eth.get_balance(contract_address)

print("\n=== Balances after ===")
print("Policyholder: {}  (change: {})".format(
    eth(holder_after), eth(holder_after - holder_before, signed=True)))
print("Contract    : {}  (change: {})".format(
    eth(contract_after), eth(contract_after - contract_before, signed=True)))

status = contract.functions.claims(claim_id).call()[4]
print("\nFinal claim status: {} (3 = Paid)".format(status))
print("Full lifecycle completed successfully.")
