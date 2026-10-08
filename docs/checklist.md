# Progress Checklist

## Week 1 — Environment & repository (Stage 1)

- [x] GitHub repository created — `MikeAlme13/CA--InsuranceClaims`
- [ ] Add Dr. Muhammad Iqbal as collaborator
- [x] Cloned locally in VS Code
- [x] Folder structure (`contracts/`, `scripts/`, `abi/`, `docs/screenshots/`, `README.md`, `requirements.txt`)
- [x] Commit 1 — `Initial project structure`
- [x] Ganache GUI installed and running on `http://127.0.0.1:7545`
- [ ] Remix connected to Ganache (Deploy & Run → Environment → Custom External HTTP Provider → `http://127.0.0.1:7545`)
- [ ] Ganache accounts visible in Remix
- [x] `pip install web3`
- [x] `requirements.txt` lists `web3`
- [x] Commit — `Add web3 dependency`

## Weeks 1–2 — Proposal & design (Stage 2 — 40%)

- [x] `docs/design.md` — problem, blockchain solution, recent advancements, benefits/challenges, cryptographic method
- [x] Sequence diagram — `docs/screenshots/sequence-diagram.svg` (source: `docs/diagrams/sequence-diagram.mmd`)
- [x] State diagram — `docs/screenshots/state-diagram.svg` (source: `docs/diagrams/state-diagram.mmd`)
- [x] Harvard references with DOIs
- [x] Fill in the two `[INSERT]` placeholders in `design.md`
- [ ] Verify the Insurance Ireland claims figure and add it to the Harvard list in §6
- [x] Commit 2 — `Add design notes and UML diagram`

## Weeks 2–4 — Smart contract (Stage 3 — 40%)

- [x] `contracts/InsuranceClaims.sol` fully implemented (structs, enum, events, constructor, modifier,
      `createPolicy`, `payPremium`, `submitClaim`, `approveClaim`, `rejectClaim`, `payClaim`)
- [ ] Compile in Remix → screenshot of the green check
- [ ] Deploy from Ganache account 0 with `value: 10 ether` → screenshot
- [ ] Happy path from account 1: `payPremium`, `submitClaim(keccak256(doc))` → screenshot
- [ ] Back on account 0: `approveClaim`, `payClaim` → screenshot of account 1 balance rising in Ganache
- [ ] Failure tests → screenshots of the reverts:
      - account 1 calls `approveClaim` → `"Not insurer"`
      - `submitClaim` with `amount > coverage` → `"Amount exceeds coverage"`
      - `payPremium` with the wrong value → `"Incorrect premium"`
- [ ] Screenshots of the Ganache **Transactions**, **Blocks** and **Events** tabs
- [ ] All screenshots saved in `docs/screenshots/` — see `docs/screenshot-guide.md` for the exact steps

## Weeks 3–4 — Python & shell (Stage 3.4)

- [x] ABI saved to `abi/InsuranceClaims.json`
- [x] `scripts/interact.py` runs the full lifecycle
- [x] Contract address is now configurable (`CONTRACT_ADDRESS` env var / `run_demo.sh` argument)
- [x] `interact.py` rewritten in English, prints balances before/after and decoded events
- [x] `scripts/run_demo.sh` — Ganache check, pip install, runs the lifecycle
- [x] `chmod +x scripts/run_demo.sh` (exec bit also set in git)
- [x] Commit 6 — `Add Python interaction script and demo shell script`
- [x] `README.md` — setup, Ganache, Remix deploy, running the demo, expected reverts
- [x] Commit 7 — `Add README with usage instructions and documentation`

## Week 5 — Poster (Stage 4 — 20%)

- [ ] Header: title, name, student number, GitHub link
- [ ] Abstract (4–5 sentences)
- [ ] Research Questions ← `design.md` §1
- [ ] Conceptual Framework ← `design.md` §2 + UML diagrams
- [ ] Research Paradigm ← `design.md` §3 (oracles, L2, ZKP)
- [ ] Research Methods ← `design.md` §5 (ECDSA + Keccak-256) + off-chain/on-chain mini-diagram
- [ ] Findings ← screenshots
- [ ] Conclusions ← `design.md` §4 + future work
- [ ] References (Harvard) ← `design.md` §6
- [ ] Appendix A/B — AI declaration (~100 words) + CCT cover
- [ ] Body text ≤ 700 words (excluding titles, code, references)

## Week 6 — Video (Stage 5 — 20%)

- [ ] 0:00–0:30 problem
- [ ] 0:30–1:30 solution + cryptography (ECDSA, Keccak-256, GDPR)
- [ ] 1:30–3:30 live demo (Remix + Ganache, then `run_demo.sh`)
- [ ] 3:30–4:00 conclusion
- [ ] Recorded with own voice (OBS or PowerPoint)
- [ ] Uploaded to Google Drive, link shared with the lecturer

## Moodle submission

- [ ] `.pptx` (poster) — separate file
- [ ] `.sol` (contract) — separate file
- [ ] `.py` (Python script) — separate file
- [ ] `.sh` (shell script) — separate file
- [ ] No PDF, no ZIP
