# routes/blockchain.py

from flask import Blueprint, jsonify
# CORREÇÃO: Importa a função específica, não a classe que não existe.
from services.blockchain_integration import verify_transaction_on_chain

blockchain_bp = Blueprint('blockchain_bp', __name__, url_prefix='/api/blockchain')

@blockchain_bp.route('/verificar/<string:hash>', methods=['GET'])
def verify_hash(hash: str):
    """Endpoint para verificar um hash de transação na blockchain."""
    # CORREÇÃO: Chama a função diretamente.
    result = verify_transaction_on_chain(hash)
    
    if not result.get("verified"):
        # Pode retornar 404 se não encontrado, ou 400 se o hash for inválido
        status_code = 404 if result.get("status") == "not_found" else 400
        return jsonify(result), status_code
        
    return jsonify(result), 200