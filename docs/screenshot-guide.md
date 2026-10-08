# Screenshot capture guide

Every screenshot the assignment asks for, in the order that needs the fewest
restarts. Save them all into `docs/screenshots/` using the file names below.

Use **Win + Shift + S** to capture a region, then paste into Paint and save as
PNG. Keep the browser maximised — a cramped window makes the text unreadable
once the poster is printed at A1.

Values used throughout, matching `scripts/interact.py` so Remix and the Python
demo tell the same story:

| Field | Value |
|---|---|
| premium | `10` wei |
| coverage | `100` wei |
| claim amount | `50` wei |
| deploy value | `10` Ether |

---

## Setup (do this once)

1. Open **Ganache** → **Quickstart**. Leave it running.
2. Open **remix.ethereum.org**.
3. Create `contracts/InsuranceClaims.sol` and paste in the contract.
4. **Solidity Compiler** tab → set the compiler to **0.8.20** or newer →
   **Compile InsuranceClaims.sol**.

> **`01-compile.png`** — the Solidity Compiler panel with the green tick on the
> Compile icon and `InsuranceClaims` showing in the CONTRACT dropdown.

5. **Deploy & Run Transactions** tab → **Environment** →
   **Custom - External Http Provider** → `http://127.0.0.1:7545` → **OK**.

> **`02-remix-ganache-connected.png`** — the Account dropdown opened, showing
> the Ganache addresses. This is the proof that Remix is talking to Ganache and
> not to the Remix VM. Make sure the Environment field is visible in the shot.

---

## Deployment

6. **Account** → select **account 0** (this becomes the insurer).
7. **Value** → `10`, and change the unit dropdown from *wei* to **Ether**.
8. Click **Deploy**.

> **`03-deploy.png`** — the deployed contract under *Deployed Contracts*, with
> the terminal at the bottom showing the successful deployment transaction.

9. Copy the contract address (the copy icon next to the deployed contract).
   You need it for `run_demo.sh`.

> **`04-ganache-contract-balance.png`** — the Ganache **Accounts** tab. Account 0
> has dropped from 100 to roughly 90 ETH, because 10 ETH went into the contract
> reserve.

---

## Happy path

10. Still on **account 0**, expand the deployed contract and call
    `createPolicy` with:
    - `holder` = the **account 1** address (copy it from Ganache)
    - `premium` = `10`
    - `coverage` = `100`

11. Switch **Account** to **account 1**.
12. Set **Value** to `10` **wei**, then call `payPremium`.

> **`05-paypremium.png`** — the green tick in the Remix terminal for the
> `payPremium` transaction.

13. Produce the evidence hash. In the Remix terminal, run:

    ```
    web3.utils.keccak256("claim_evidence_document.pdf")
    ```

    Copy the resulting `0x...` value.

14. Call `submitClaim` with:
    - `amount` = `50`
    - `evidenceHash` = the hash you just copied

> **`06-submitclaim.png`** — the transaction succeeded, with the decoded
> `ClaimSubmitted` event expanded in the terminal so the claim id, claimant and
> amount are readable.

15. Switch back to **account 0**.
16. Call `approveClaim` with `id` = `0`.
17. Call `payClaim` with `id` = `0`.

> **`07-payclaim.png`** — the `payClaim` transaction with the `ClaimPaid` event
> expanded.

> **`08-ganache-balance-after.png`** — the Ganache **Accounts** tab showing
> account 1's balance higher than before. This is the single most important
> screenshot: it is the proof that the settlement actually moved funds.

---

## Failure tests

These prove the access control and the guards work. Each one should revert.

18. Switch to **account 1** and call `approveClaim(0)`.

> **`09-revert-not-insurer.png`** — the red error in the terminal containing
> `Not insurer`.

19. Switch to **account 0**, call `createPolicy` again for account 1 with the
    same values. Switch to **account 1**, call `payPremium` with `10` wei, then
    call `submitClaim` with `amount` = `500` (above the coverage of 100).

> **`10-revert-exceeds-coverage.png`** — the error containing
> `Amount exceeds coverage`.

20. Still on **account 1**, call `payPremium` with a **Value** of `7` wei.

> **`11-revert-incorrect-premium.png`** — the error containing
> `Incorrect premium`.

---

## Ganache tabs

21. In Ganache, open each tab in turn and capture it.

> **`12-ganache-transactions.png`** — the **Transactions** tab, with the list of
> contract calls.

> **`13-ganache-blocks.png`** — the **Blocks** tab.

> **`14-ganache-events.png`** — the **Events** tab, showing the emitted
> `PolicyCreated` / `ClaimSubmitted` / `ClaimDecided` / `ClaimPaid` events.

---

## Python demo

22. Back in the terminal, with the contract address you copied in step 9:

    ```bash
    ./scripts/run_demo.sh 0xYourContractAddress
    ```

> **`15-run-demo.png`** — the full terminal output: the Ganache check, the
> transaction hashes, the decoded events and the before/after balances.

Note that the script runs its own `createPolicy`, so it will create a **second**
claim on the same contract. That is expected — the script reads the new claim id
from the `ClaimSubmitted` event rather than assuming it is 0.

---

## Checklist

- [ ] `01-compile.png`
- [ ] `02-remix-ganache-connected.png`
- [ ] `03-deploy.png`
- [ ] `04-ganache-contract-balance.png`
- [ ] `05-paypremium.png`
- [ ] `06-submitclaim.png`
- [ ] `07-payclaim.png`
- [ ] `08-ganache-balance-after.png`
- [ ] `09-revert-not-insurer.png`
- [ ] `10-revert-exceeds-coverage.png`
- [ ] `11-revert-incorrect-premium.png`
- [ ] `12-ganache-transactions.png`
- [ ] `13-ganache-blocks.png`
- [ ] `14-ganache-events.png`
- [ ] `15-run-demo.png`

Once these exist, the poster's **Findings** section and the live demo section of
the video are both covered.
