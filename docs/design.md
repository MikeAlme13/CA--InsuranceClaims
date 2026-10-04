# Design Notes — Insurance Claims DApp

**Student:** Maycon Almeida
**Student number:** 2024354
**Module:** Blockchain / Distributed Ledger Technologies — CCT College Dublin
**Lecturer:** Dr. Muhammad Iqbal
**Repository:** https://github.com/MikeAlme13/CA--InsuranceClaims

---

## 1. Introduction to the Problem

Claims handling is still one of the most manual processes in financial services. When a
policyholder suffers a loss, the claim does not travel through a single system: it is passed
between a broker, a loss adjuster, a third-party administrator and, on larger risks, a
reinsurer. Each of these parties keeps its own database, and each re-verifies facts that the
previous party has already verified. The policyholder, who is the only actor with a direct
interest in speed, has no visibility into where the file actually sits. The result is a process
measured in weeks rather than minutes, in which a large share of the cost is not the loss itself
but the administrative overhead of coordinating distrustful intermediaries.

This architecture also creates the conditions for fraud. Because no participant can see the full
picture, the same loss can be presented to two insurers, supporting documents can be altered
after submission, and a claim decision can be disputed with no authoritative record of what was
actually submitted and when. Industry bodies consistently identify claims fraud as a material
component of total claims cost.

Example: Figure X: Total Claims Paid by Irish Insurers (Insurance Ireland, 2022)

According to Insurance Ireland, Irish insurers paid approximately €68 billion in claims during 2022. 
This figure represents the combined value of life, non-life, and health insurance payouts made to policyholders. 
The number highlights the scale of financial flows involved in insurance claims processing and the importance 
of secure, transparent, and efficient claim-handling systems. 
The implementation of blockchain-based smart contracts, such as the InsuranceClaims contract developed in this CA, 
directly addresses these industry needs by automating claim submission, approval, and payment processes.

Source: Insurance Ireland – Market Data Report 2022.

Attempts to solve this by building shared industry
databases have had limited success, because they require competitors to trust a central operator
with commercially sensitive data. The underlying problem is therefore not a lack of software but
the absence of a tamper-evident record.

The system uses a tamper-evident record setup in which no single party can control the data.
It records every transaction, like creating policies, paying premiums, submitting claims, approving them, and making payouts, on a distributed ledger. Since the ledger only allows new entries and is protected by cryptography, any effort to change, delete, or fake
a record can be spotted right away.

Control of the data is spread out. Each person uses their own cryptographic address to work with the smart contract,and the contract automatically enforces the rules without needing a central authority. The insurer cannot change claim history, the policyholder cannot change premium status, and outsiders cannot rewrite past events. The blockchain’s consensus process verifies every update, ensuring records stay unchanged, clear, and protected from tampering.

This tamper-evident approach meets industry needs for auditability and trust, especially in high-value fields
like insurance, where settling claims, preventing fraud, and following regulations all rely on records that can be checked and verified by others
independently.

In summary, the current model suffers from five linked weaknesses:

| Weakness | Consequence |
|
| Manual, paper-driven workflow | Settlement takes weeks; high administrative cost |
| Multiple intermediaries | Duplicated verification, fee leakage |
| Fraud and document tampering | Inflated premiums for honest policyholders |
| No transparency for the policyholder | Low trust, high complaint and litigation volume |
| Siloed, competitor-owned databases | Cross-insurer fraud is invisible; data sharing stalls |

---

## 2. Blockchain-Based Solution

### 2.1 Actors

The DApp reduces the process to three actors:

The blockchain provides a tamper‑evident record of all insurance operations, ensuring that no
single party, whether it is the insurer or the policyholder, can change historical data. Every action
performed through the DApp, including policy creation, premium payment, claim submission,
approval, rejection, and payout, is written as an immutable transaction on the ledger.

Because the ledger is decentralised and only allows new entries, past records cannot be changed or deleted. Trying to change historical data would mean having to rewrite the whole chain,
which is nearly impossible and would be noticed right away. This feature removes the
traditional reliance on a central administrator or database owner.

Control is shared among participants. The policyholder signs transactions with their own
private key. The insurer uses their assigned address, and the smart contract
automatically enforces business rules. Consensus ensures all nodes agree on the ledger. This means no single person can fake, hide, or change records on their own.

This tamper-evident approach is especially useful in insurance, where disagreements often come up
about claim history, eligibility, and payout conditions. By making sure records are
independently verifiable and hard to change, the system builds trust, cuts down on
fraud, and supports regulatory compliance.


### 2.2 Contract design

The contract keeps two pieces of state and one role:

- solidity
address public insurer;                       // set once, in the constructor
mapping(address => Policy) public policies;   // one policy per holder address
Claim[] public claims;                        // append-only claim ledger


A `Claim` carries a `ClaimStatus` enum (`Submitted`, `Approved`, `Rejected`, `Paid`), which makes
the lifecycle explicit on-chain rather than implicit in an administrator's inbox. Four events —
`PolicyCreated`, `ClaimSubmitted`, `ClaimDecided`, `ClaimPaid` — form the audit trail: they are
written into the transaction logs and can be replayed by a regulator or an auditor without
needing access to any party's internal systems.

Two design decisions are worth defending explicitly:

1. **The claim array is append-only.** Claims are never deleted, only transitioned. A rejected
   claim remains permanently visible, which is what makes the record useful as evidence in a
   dispute.
2. **`payClaim` follows checks-effects-interactions.** The status is set to `Paid` *before*
   `transfer` is called:

   - solidity
   c.status = ClaimStatus.Paid;
   payable(c.claimant).transfer(c.amount);
   

   If the state change came after the transfer, a malicious claimant contract could re-enter
   `payClaim` while the status was still `Approved` and drain the reserve — the pattern behind
   the 2016 DAO incident (Atzei, Bartoletti and Cimoli, 2017). Ordering the operations this way
   makes the re-entrancy impossible, and the 2300-gas stipend of `transfer` gives a second layer
   of protection.

### 2.3 Process flow

1. **Deploy.** The insurer deploys the contract with `value` attached (e.g. 10 ETH), funding the
   claims reserve. `msg.sender` is stored as `insurer`.
2. **`createPolicy(holder, premium, coverage)`.** Insurer-only. Registers a policy with
   `active = false` and emits `PolicyCreated`.
3. **`payPremium()`.** Called by the policyholder with `msg.value == premium`. The contract
   checks `p.holder == msg.sender` and that the amount is exact, then sets `active = true`. The
   premium is not held in escrow by a broker — it lands directly in the reserve that will pay
   claims.
4. **`submitClaim(amount, evidenceHash)`.** Requires an active policy and `amount <= coverage`.
   The claim is pushed with status `Submitted` and `ClaimSubmitted` is emitted. Note that only
   the **hash** of the evidence is stored (see §5.2).
5. **`approveClaim(id)` / `rejectClaim(id)`.** Insurer-only, and only valid from `Submitted`, so
   a decision cannot be silently reversed afterwards. Emits `ClaimDecided`.
6. **`payClaim(id)`.** Insurer-only. Requires status `Approved` and a sufficient contract
   balance, then transfers the amount to the claimant and emits `ClaimPaid`.

The improvement over the current model is not that a human disappears from the loop — the insurer
still adjudicates — but that **every step is sequenced, authenticated and recorded by code that
neither party can edit after the fact**.

### 2.4 UML models

Two diagrams accompany this document. Editable Mermaid source is in `docs/diagrams/`, and
exported images for the poster are in `docs/screenshots/`:

- **Sequence diagram** (`sequence-diagram.svg`) — the interaction between policyholder, insurer
  and contract across the full lifecycle, including the emitted events.
- **State diagram** (`state-diagram.svg`) — the claim state machine:
  `Submitted → Approved → Paid` and `Submitted → Rejected`, with the function call and the guard
  that causes each transition.

---

## 3. Recent Advancements

### 3.1 Decentralised oracle networks

A smart contract is deterministic and cannot read the outside world; it cannot know that a flight
was delayed or that a storm exceeded a wind-speed threshold. This is the **oracle problem**
(Caldarelli, 2020). Decentralised oracle networks such as Chainlink address it by having many
independent nodes retrieve the same off-chain value, aggregating their answers on-chain and
bonding the nodes financially against misreporting (Ellis, Juels and Nazarov, 2017; Breidenbach
et al., 2021).

**Application to this project.** The current DApp requires `approveClaim` to be called by a human
insurer. With an oracle feed, a *parametric* policy could be settled with no adjudication at all:
a flight-delay or crop-weather policy would call `approveClaim` automatically once the oracle
reported that the trigger condition had been met. Etherisc has deployed exactly this model for
flight-delay and crop cover. The trade-off is that the trust assumption moves from the insurer to
the oracle network — a genuine decentralisation gain only if that network really is decentralised.

### 3.2 Layer-2 rollups

Every state change in the contract above costs gas on Ethereum mainnet, which makes a low-value,
high-volume product (travel or gadget insurance) economically absurd. Rollups — optimistic and
zero-knowledge — execute transactions off-chain in batches and post either the compressed data or
a validity proof back to Layer 1, inheriting its security while cutting per-transaction cost by
orders of magnitude (Thibault, Sarry and Hafid, 2022). EIP-4844 blob transactions reduced the
data-availability cost of rollups further.

**Application to this project.** Deploying `InsuranceClaims.sol` unchanged to a ZK-rollup such as
zkSync or Scroll, or an optimistic rollup such as Arbitrum or Optimism, would make micro-premium
products viable: the Solidity source does not need to change, because these rollups are
EVM-equivalent. This is the single most practical change needed to move the prototype from a
demonstration to something commercially usable.

### 3.3 Zero-knowledge proofs

A zero-knowledge proof lets a prover convince a verifier that a statement is true while revealing
nothing beyond its truth (Goldwasser, Micali and Rackoff, 1989). Modern non-interactive
constructions (zk-SNARKs, zk-STARKs) made this practical on-chain, first for private payments
(Ben-Sasson et al., 2014) and now for general computation.

**Application to this project.** Insurance claims are intrinsically sensitive — medical records,
vehicle telematics, home addresses. A ZKP lets the policyholder prove the *predicate* without
disclosing the *data*: "the repair invoice is under the EUR 5,000 coverage limit and was issued by
an approved garage" can be proved and verified on-chain without the invoice ever leaving the
claimant's device. This is directly relevant to §5 — it is the cryptographic answer to the GDPR
tension described in §4.2.

---

## 4. Benefits and Challenges

### 4.1 Benefits

- **Immutability.** Once `ClaimSubmitted` is in a mined block, neither the claimant nor the
  insurer can retroactively change what was claimed, for how much, or against which evidence
  hash. This removes the most common source of claims disputes.
- **Transparency.** The policyholder reads the claim status directly from the chain instead of
  phoning a call centre — `claims(id)` is a public view function.
- **Automation.** `payPremium` activating the policy, and `payClaim` transferring funds, happen
  without a settlement clerk. Combined with an oracle (§3.1), adjudication itself can be
  automated for parametric products.
- **Disintermediation.** The contract performs the coordination role of broker, administrator and
  escrow agent, so the fees attached to those roles are removed from the premium.
- **Auditability.** The event log is a regulator-ready audit trail that exists independently of
  any party's internal systems and cannot be selectively produced.

### 4.2 Challenges

- **GDPR versus immutability.** Article 17's right to erasure is in direct tension with a ledger
  designed to be unerasable, and Article 16's right to rectification is equally awkward (Finck,
  2018). This project mitigates the conflict by storing *only* a Keccak-256 hash on-chain and
  keeping the personal data off-chain (§5.2); deleting the off-chain document makes the on-chain
  hash a meaningless 32-byte value. Whether that satisfies a regulator is still unsettled, and a
  production deployment would need legal sign-off, not just an engineering argument.
- **The oracle problem.** The contract's correctness depends on the accuracy of inputs it cannot
  itself verify. A decentralised oracle reduces but does not eliminate this.
- **Gas cost.** On mainnet, writing a `Claim` struct to storage costs real money, and the cost is
  volatile. Layer-2 (§3.2) is the mitigation.
- **Smart-contract bugs.** Code is law, including buggy code. Re-entrancy, integer handling and
  access-control mistakes have caused large losses (Atzei, Bartoletti and Cimoli, 2017). This
  project applies `onlyInsurer`, explicit `require` guards and checks-effects-interactions, but a
  production contract would also need an external audit, a full test suite and a pause or upgrade
  mechanism.
- **Adoption and regulation.** Insurance is a licensed activity. A contract that pays claims is
  performing a regulated function, and questions of legal personality, dispute resolution and
  solvency reporting for an on-chain reserve are unresolved. The technical barrier is now lower
  than the regulatory one.

---

## 5. Cryptographic Method

### 5.1 ECDSA over secp256k1 — authentication and non-repudiation

Ethereum authenticates every transaction with the Elliptic Curve Digital Signature Algorithm on
the secp256k1 curve (Johnson, Menezes and Vanstone, 2001; Wood, 2014). The sender signs the
transaction hash with their private key; nodes recover the signer's public key from the signature
`(r, s, v)` and derive the address from the last 20 bytes of its Keccak-256 hash. That recovered
address is what the EVM exposes as `msg.sender`.

This is why the contract's access control is sound without any password or login:

```solidity
require(p.holder == msg.sender, "Not policyholder");   // payPremium
require(msg.sender == insurer, "Not insurer");         // onlyInsurer
```

`msg.sender` cannot be spoofed — forging it would mean forging an ECDSA signature. Two properties
follow directly:

- **Authentication.** Only the holder of the private key for the policyholder address can open a
  claim against that policy. A third party cannot submit a claim in someone else's name.
- **Non-repudiation.** Because the signature is verifiable by anyone and only the claimant could
  have produced it, the claimant cannot later deny having submitted the claim — and the insurer
  cannot deny having approved it. In the current paper process, this is exactly what gets
  disputed.

### 5.2 Keccak-256 — integrity and data minimisation

Ethereum's hash function is Keccak-256, the original Keccak submission rather than the
slightly different NIST SHA3-256 padding (Bertoni et al., 2013). The contract uses it in
`submitClaim(uint256 amount, bytes32 evidenceHash)`.

The supporting evidence — photographs, invoices, medical reports — is kept **off-chain**. Only
its 256-bit digest goes on-chain:

```python
evidence_hash = w3.keccak(text=evidence)   # scripts/interact.py
```

This gives two things at once:

- **Integrity.** Keccak-256 is collision- and preimage-resistant, so a claimant cannot swap the
  invoice for a higher one after submission: re-hashing the new document produces a different
  digest, and the original digest is immutably recorded. Equally, the insurer cannot claim that a
  different document was submitted. Verification is a one-line check that anyone can perform.
- **Data protection / minimisation.** Because a digest is a one-way function, the on-chain record
  contains no readable personal data. This supports the GDPR data-minimisation principle
  (Art. 5(1)(c)) and makes the Art. 17 erasure problem tractable: destroy the off-chain file and
  the on-chain hash is unlinkable to any person.

The honest limitation is that hashing is pseudonymisation, not anonymisation: if the input space
is small or guessable, a hash of a known document can be confirmed by re-hashing it. A production
system would salt the document before hashing.

### 5.3 Zero-knowledge proofs — the confidentiality evolution

Hashing proves that a document has not changed, but it cannot prove anything *about* the
document's contents without revealing it. Zero-knowledge proofs close that gap: the policyholder
can prove that the claim satisfies the policy conditions — amount within coverage, event inside
the cover period, provider on the approved list — while disclosing none of the underlying values
(Goldwasser, Micali and Rackoff, 1989). In the architecture above, `submitClaim` would accept a
proof alongside the amount, and a verifier contract would check it on-chain. This is the direction
in which the prototype would be extended, and the cleanest resolution of the
privacy-versus-transparency tension identified in §4.2.

---

## 6. References (Harvard)


Atzei, N., Bartoletti, M. and Cimoli, T. (2017) 'A survey of attacks on Ethereum smart contracts
(SoK)', in *Principles of Security and Trust (POST 2017)*, Lecture Notes in Computer Science.
Berlin: Springer, pp. 164–186. doi: 10.1007/978-3-662-54455-6_8

Ben-Sasson, E., Chiesa, A., Garman, C., Green, M., Miers, I., Tromer, E. and Virza, M. (2014)
'Zerocash: decentralized anonymous payments from Bitcoin', in *2014 IEEE Symposium on Security
and Privacy*. IEEE, pp. 459–474.

Bertoni, G., Daemen, J., Peeters, M. and Van Assche, G. (2013) 'Keccak', in *Advances in
Cryptology – EUROCRYPT 2013*, Lecture Notes in Computer Science 7881. Berlin: Springer,
pp. 313–314. doi: 10.1007/978-3-642-38348-9_19

Breidenbach, L., Cachin, C., Chan, B., Coventry, A., Ellis, S., Juels, A., Koushanfar, F.,
Miller, A., Magauran, B., Moroz, D., Nazarov, S., Topliceanu, A., Tramèr, F. and Zhang, F. (2021)
*Chainlink 2.0: next steps in the evolution of decentralized oracle networks*. Chainlink Labs.

Buterin, V. (2014) *Ethereum white paper: a next generation smart contract and decentralized
application platform*. Available at: https://ethereum.org/en/whitepaper/

Caldarelli, G. (2020) 'Understanding the blockchain oracle problem: a call for action',
*Information*, 11(11), 509. doi: 10.3390/info11110509

Ellis, S., Juels, A. and Nazarov, S. (2017) *ChainLink: a decentralized oracle network*.

European Parliament and Council of the European Union (2016) *Regulation (EU) 2016/679 (General
Data Protection Regulation)*. Official Journal of the European Union, L119.

Finck, M. (2018) 'Blockchains and data protection in the European Union', *European Data
Protection Law Review*, 4(1), pp. 17–35. doi: 10.21552/edpl/2018/1/6

Gatteschi, V., Lamberti, F., Demartini, C., Pranteda, C. and Santamaría, V. (2018) 'Blockchain and
smart contracts for insurance: is the technology mature enough?', *Future Internet*, 10(2), 20.
doi: 10.3390/fi10020020

Goldwasser, S., Micali, S. and Rackoff, C. (1989) 'The knowledge complexity of interactive proof
systems', *SIAM Journal on Computing*, 18(1), pp. 186–208. doi: 10.1137/0218012

Johnson, D., Menezes, A. and Vanstone, S. (2001) 'The elliptic curve digital signature algorithm
(ECDSA)', *International Journal of Information Security*, 1, pp. 36–63.
doi: 10.1007/s102070100002

Nakamoto, S. (2008) *Bitcoin: a peer-to-peer electronic cash system*.

Szabo, N. (1997) 'Formalizing and securing relationships on public networks', *First Monday*,
2(9).

Thibault, L.T., Sarry, T. and Hafid, A.S. (2022) 'Blockchain scaling using rollups: a
comprehensive survey', *IEEE Access*, 10, pp. 93039–93054.

Wood, G. (2014) *Ethereum: a secure decentralised generalised transaction ledger* (Yellow Paper).
