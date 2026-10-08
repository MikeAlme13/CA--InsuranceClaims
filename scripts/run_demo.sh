#!/bin/bash
#
# Insurance Claims DApp - demo runner.
#
# Checks that Ganache is up, installs the Python dependencies and runs the
# full claim lifecycle against the deployed contract.
#
# Usage:
#   ./scripts/run_demo.sh
#   ./scripts/run_demo.sh 0xYourContractAddress
#
set -e

GANACHE_URL="http://127.0.0.1:7545"

# Always run from the repository root, whichever directory this was called from.
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "==> 1/3  Checking Ganache at $GANACHE_URL"

# A plain GET returns an error page, so send a real JSON-RPC call instead:
# only a working node answers eth_blockNumber.
if ! curl -s -X POST "$GANACHE_URL" \
        -H "Content-Type: application/json" \
        --data '{"jsonrpc":"2.0","id":1,"method":"eth_blockNumber","params":[]}' \
        | grep -q '"result"'; then
    echo "ERROR: Ganache is not responding at $GANACHE_URL"
    echo "Open Ganache, click Quickstart, then run this script again."
    exit 1
fi
echo "    Ganache is running."

echo "==> 2/3  Installing Python dependencies"
pip install -r requirements.txt --quiet

echo "==> 3/3  Running the claim lifecycle"

# An address passed as the first argument wins; otherwise interact.py falls
# back to CONTRACT_ADDRESS, then to its own default.
if [ -n "$1" ]; then
    CONTRACT_ADDRESS="$1" python scripts/interact.py
else
    python scripts/interact.py
fi

echo
echo "Demo finished."
