# Insurance Claims DApp

A decentralised insurance claims application built on Ethereum. A policyholder
pays a premium and submits a claim with a Keccak-256 hash of the supporting
evidence; the insurer approves or rejects it; an approved claim is paid
automatically by the smart contract.

**Student:** Maycon Almeida (2024354)
**Module:** Blockchain / Distributed Ledger Technologies — CCT College Dublin
**Lecturer:** Dr. Muhammad Iqbal

Design rationale, UML diagrams and references are in [docs/design.md](docs/design.md).

---

## Project structure

```
contracts/InsuranceClaims.sol   the smart contract
scripts/interact.py             Web3 script, runs the full claim lifecycle
scripts/run_demo.sh             checks Ganache, installs deps, runs the demo
abi/InsuranceClaims.json        ABI exported from the Remix compiler
docs/design.md                  design document (problem, solution, cryptography)
docs/diagrams/                  editable Mermaid sources for the UML diagrams
docs/screenshots/               UML exports and Remix/Ganache evidence
```

## Requirements

- [Ganache GUI](https://github.com/trufflesuite/ganache-ui/releases)
- Python 3.9 or newer
- A browser, for [remix.ethereum.org](https://remix.ethereum.org)

Install the Python dependency:

```bash
pip install -r requirements.txt
```

---

## 1. Start Ganache

Open Ganache and click **Quickstart**. It starts a local chain on
`http://127.0.0.1:7545` with 10 unlocked accounts.

- **Account 0** is used as the **insurer** (it deploys the contract and owns it).
- **Account 1** is used as the **policyholder**.

## 2. Deploy the contract in Remix

1. Open [remix.ethereum.org](https://remix.ethereum.org).
2. Create `contracts/InsuranceClaims.sol` and paste in the contract source.
3. **Solidity Compiler** tab:
   - Open **Advanced Configurations** and set **EVM Version** to **`paris`**.
   - Compile with 0.8.20 or newer.

   > This step is not optional. Ganache 7.7.3 runs the *merge* (Paris) hardfork,
   > but Solidity 0.8.20+ targets *shanghai* by default and emits the `PUSH0`
   > opcode, which Ganache cannot execute. Deploying a shanghai build fails with
   > an invalid opcode: the transaction burns the whole gas limit
   > (`gasUsed == gasLimit`), the receipt comes back with `status: 0x0`, and no
   > code is written to the address.

4. **Deploy & Run Transactions** tab:
   - **Environment** → *Custom - External Http Provider* → enter
     `http://127.0.0.1:7545`.
   - Confirm the Ganache accounts now appear in the **Account** dropdown.
   - Select **account 0**.
   - Set **Value** to `10` and the unit to **Ether**. The constructor is
     `payable`, and this funds the reserve that claims are paid from. Deploying
     with a value of 0 will make `payClaim` revert with `"Insufficient funds"`.
   - Click **Deploy**.
5. Copy the deployed contract address.

## 3. Run the demo

```bash
./scripts/run_demo.sh 0xYourContractAddress
```

The script checks that Ganache is responding, installs the dependencies and
then runs the full lifecycle:

`createPolicy` → `payPremium` → `submitClaim` → `approveClaim` → `payClaim`

It prints the transaction hashes, the decoded events and the policyholder and
contract balances before and after, so you can see the settlement actually move
funds.

You can also run the Python script on its own:

```bash
CONTRACT_ADDRESS=0xYourContractAddress python scripts/interact.py
```

> The contract address changes every time you redeploy, and every time Ganache
> is restarted. Pass the current one rather than relying on the default baked
> into `interact.py`.

---

## Contract overview

| Function | Caller | Effect |
|---|---|---|
| `createPolicy(holder, premium, coverage)` | insurer | registers a policy, inactive until the premium is paid |
| `payPremium()` | policyholder | requires `msg.value == premium`, activates the policy |
| `submitClaim(amount, evidenceHash)` | policyholder | requires an active policy and `amount <= coverage` |
| `approveClaim(id)` / `rejectClaim(id)` | insurer | only valid from `Submitted` |
| `payClaim(id)` | insurer | requires `Approved`, transfers the amount to the claimant |

Claim states: `Submitted → Approved → Paid`, or `Submitted → Rejected`.

### Access control

The contract has no login. Every transaction is signed with the sender's
private key (ECDSA over secp256k1), and the EVM exposes the recovered address
as `msg.sender`, which cannot be forged. That is what `onlyInsurer` and
`require(p.holder == msg.sender)` rely on.

### Evidence handling

Supporting documents stay **off-chain**. Only their Keccak-256 digest is stored
on-chain, which proves the document has not been altered while keeping personal
data off the ledger. See [docs/design.md](docs/design.md) §5 for the full
argument, including the GDPR implications.

---

## Expected failures

These reverts are part of the demonstration — they show the access control and
the guards working:

| Action | Expected revert |
|---|---|
| Account 1 calls `approveClaim` | `Not insurer` |
| `submitClaim` with `amount > coverage` | `Amount exceeds coverage` |
| `payPremium` with the wrong value | `Incorrect premium` |
| `submitClaim` before `payPremium` | `Policy not active` |
| `payClaim` on a claim that is not approved | `Not approved` |

## Evidence

Screenshots of the compilation, deployment, transactions, reverts and the
Ganache **Transactions**, **Blocks** and **Events** tabs are in
[docs/screenshots/](docs/screenshots/), together with the exported UML diagrams.

## A note on `transfer`

`payClaim` uses `payable(...).transfer(...)` and writes the `Paid` status
*before* transferring, which follows checks-effects-interactions and prevents
re-entrancy. Solidity 0.8.34 reports `transfer` as deprecated in favour of
`call{value: ...}`; the contract still compiles and behaves correctly. The
trade-off between the two is discussed in `docs/design.md`.
