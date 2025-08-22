from flask import Blueprint, request, jsonify
from web3 import Web3

auth_bp = Blueprint("auth", __name__)

# Você pode manter um dicionário simples de nonces para cada usuário
nonces = {}

@auth_bp.route("/auth/request_nonce", methods=["POST"])
def request_nonce():
    data = request.json
    address = data.get("address")
    if not address:
        return jsonify({"error": "Address is required"}), 400

    # Gera um nonce aleatório
    import random, string
    nonce = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
    nonces[address] = nonce

    return jsonify({"nonce": nonce})


@auth_bp.route("/auth/verify", methods=["POST"])
def verify_signature():
    data = request.json
    address = data.get("address")
    signature = data.get("signature")
    if not address or not signature:
        return jsonify({"error": "Address and signature are required"}), 400

    message = nonces.get(address)
    if not message:
        return jsonify({"error": "No nonce found for this address"}), 400

    web3 = Web3()
    try:
        recovered_address = web3.eth.account.recover_message(
            text=message,
            signature=signature
        )
        if Web3.toChecksumAddress(recovered_address) == Web3.toChecksumAddress(address):
            # Autenticado com sucesso
            del nonces[address]  # opcional: remove nonce usado
            return jsonify({"success": True, "address": address})
        else:
            return jsonify({"success": False, "error": "Invalid signature"}), 401
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400
