from flask import Blueprint, request, jsonify
from dtos.auth_dto import CheckAuthDTO
from web3 import Web3
from dotenv import load_dotenv
import random, string
import os

# Carrega variáveis do .env
load_dotenv()
INFURA_URL = os.getenv("INFURA_URL")

auth_bp = Blueprint("auth", __name__)
nonces = {}

# Conexão com a blockchain via Alchemy/Infura
web3 = Web3(Web3.HTTPProvider(INFURA_URL))

# -----------------------------
# Rota para gerar nonce
# -----------------------------
from dtos.auth_dto import RequestNonceDTO

@auth_bp.route("/auth/request_nonce", methods=["POST"])
def request_nonce():
    try:
        dto = RequestNonceDTO(**request.json)
        address = dto.address
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    # Gera um nonce aleatório
    nonce = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
    nonces[address] = nonce

    return jsonify({"nonce": nonce})



# -----------------------------
# Rota para verificar assinatura
# -----------------------------
from eth_account.messages import encode_defunct

@auth_bp.route("/auth/verify", methods=["POST"])
def verify_signature():
    try:
        dto = CheckAuthDTO(**request.json)
        address = dto.address
        signature = dto.signature
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    message = nonces.get(address)
    if not message:
        return jsonify({"error": "No nonce found for this address"}), 400

    try:
        encoded_message = encode_defunct(text=message)
        recovered_address = web3.eth.account.recover_message(encoded_message, signature=signature)

        if Web3.to_checksum_address(recovered_address) == Web3.to_checksum_address(address):
            del nonces[address]
            return jsonify({"success": True, "address": address})
        else:
            return jsonify({"success": False, "error": "Invalid signature"}), 401
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@auth_bp.route("/auth/logout", methods=["POST"])
def logout():
    try:
        address = request.json.get("address")
        if not address:
            return jsonify({"error": "Address is required"}), 400

        # Remove nonce usado
        nonces.pop(address, None)

        return jsonify({"success": True, "message": "Logged out successfully"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


