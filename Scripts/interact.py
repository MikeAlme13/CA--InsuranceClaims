from web3 import Web3
import json

# -----------------------------
# 1. Conectar ao Ganache
# -----------------------------
w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:7545"))
print("Conectado ao Ganache?", w3.is_connected())

# -----------------------------
# 2. Definir contas
# -----------------------------
insurer = w3.eth.accounts[0]   # seguradora
holder = w3.eth.accounts[1]    # segurado

print("Insurer:", insurer)
print("Holder:", holder)

# -----------------------------
# 3. Carregar ABI
# -----------------------------
with open("abi/InsuranceClaims.json") as f:
    abi = json.load(f)

# -----------------------------
# 4. Endereço do contrato
# -----------------------------
contract_address = w3.to_checksum_address("0x0687ab54002cd89be3c30da43252d4752f70e9fd")

contract = w3.eth.contract(address=contract_address, abi=abi)

# -----------------------------
# 5. Criar apólice
# -----------------------------
print("\n=== Criando apólice ===")
tx_create = contract.functions.createPolicy(holder, 10, 100).transact({
    "from": insurer
})
receipt_create = w3.eth.wait_for_transaction_receipt(tx_create)
print("Apólice criada. Tx:", tx_create.hex())

# -----------------------------
# 6. Pagar prêmio
# -----------------------------
print("\n=== Pagando prêmio ===")
tx_premium = contract.functions.payPremium().transact({
    "from": holder,
    "value": 10
})
receipt_premium = w3.eth.wait_for_transaction_receipt(tx_premium)
print("Prêmio pago. Tx:", tx_premium.hex())

# -----------------------------
# 7. Criar hash da evidência
# -----------------------------
evidence = "documento_exemplo"
evidence_hash = w3.keccak(text=evidence)
print("\nHash da evidência:", evidence_hash.hex())

# -----------------------------
# 8. Submeter sinistro
# -----------------------------
print("\n=== Submetendo sinistro ===")
tx_claim = contract.functions.submitClaim(50, evidence_hash).transact({
    "from": holder
})
receipt_claim = w3.eth.wait_for_transaction_receipt(tx_claim)
print("Sinistro submetido. Tx:", tx_claim.hex())

# -----------------------------
# 9. Aprovar sinistro
# -----------------------------
print("\n=== Aprovando sinistro ===")
tx_approve = contract.functions.approveClaim(0).transact({
    "from": insurer
})
receipt_approve = w3.eth.wait_for_transaction_receipt(tx_approve)
print("Sinistro aprovado. Tx:", tx_approve.hex())

# -----------------------------
# 10. Pagar sinistro
# -----------------------------
print("\n=== Pagando sinistro ===")
tx_pay = contract.functions.payClaim(0).transact({
    "from": insurer
})
receipt_pay = w3.eth.wait_for_transaction_receipt(tx_pay)
print("Sinistro pago. Tx:", tx_pay.hex())

# -----------------------------
# 11. Saldos finais
# -----------------------------
print("\n=== Saldos finais ===")
print("Saldo do segurado:", w3.eth.get_balance(holder))
print("Saldo da seguradora:", w3.eth.get_balance(insurer))

print("\nFluxo completo executado com sucesso!")
