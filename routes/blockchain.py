# -*- coding: utf-8 -*-

# routes/blockchain.py

from flask import Blueprint, jsonify
from services.blockchain_integration import verify_transaction_on_chain

blockchain_bp = Blueprint('blockchain_bp', __name__, url_prefix='/api/blockchain')

@blockchain_bp.route('/verificar/<string:hash>', methods=['GET'])
def verify_hash(hash: str):
    """
    Verifica um hash de transação na blockchain.
    Consulta um nó da blockchain para obter o recibo de uma transação a partir do seu hash.
    ---
    tags:
      - blockchain
    parameters:
      - name: hash
        in: path
        type: string
        required: true
        description: "O hash da transação a ser verificada (ex: 0x...)."
    responses:
      200:
        description: A transação foi encontrada e seu status foi retornado com sucesso.
        schema:
          $ref: '#/definitions/BlockchainSuccessResponse'
      400:
        description: Erro na requisição, como um formato de hash inválido.
        schema:
          $ref: '#/definitions/BlockchainErrorResponse'
      404:
        description: A transação com o hash fornecido não foi encontrada na blockchain.
        schema:
          $ref: '#/definitions/BlockchainErrorResponse'
    definitions:
      BlockchainSuccessResponse:
        type: object
        properties:
          verified:
            type: boolean
            description: True se a transação foi encontrada.
            example: true
          status:
            type: string
            description: "'success' se a transação foi bem-sucedida, 'failed' caso contrário."
            example: "success"
          blockNumber:
            type: integer
            description: O número do bloco onde a transação foi minerada.
          gasUsed:
            type: integer
            description: A quantidade de gás usada pela transação.
          transactionHash:
            type: string
            description: O hash da transação.
      BlockchainErrorResponse:
        type: object
        properties:
          verified:
            type: boolean
            example: false
          status:
            type: string
            example: "not_found"
          message:
            type: string
            example: "Transação não encontrada ou ainda pendente."
    """
    result = verify_transaction_on_chain(hash)
    
    if not result.get("verified"):
        status_code = 404 if result.get("status") == "not_found" else 400
        return jsonify(result), status_code
        
    return jsonify(result), 200
