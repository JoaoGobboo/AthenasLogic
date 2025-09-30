# AthenaElection (Solidity)

Contrato pensado para validar os fluxos da API contra uma rede de testes Ethereum. Ele permite configurar eleições simples, abrir/fechar a votação e registrar votos únicos por endereço em cada eleição.

## Funcionalidades principais
- Configuração de eleições com nome e candidatos iniciais.
- Inclusão de novos candidatos enquanto a eleição estiver fechada.
- Abertura/encerramento da votação apenas pelo proprietário (conta que implanta o contrato).
- Registro de votos únicos por endereço, com emissão de eventos (`VoteCast`).
- Reutilização do contrato para múltiplas eleições através do incremento de `electionId`.

## Passo a passo para deploy em testnet (Sepolia/Goerli)
1. Gere uma carteira (ex.: MetaMask) e financie-a com ETH de testnet.
2. Crie/complete o arquivo `.env` na raiz da API com:
   ```bash
   INFURA_URL=https://sepolia.infura.io/v3/<SUA_CHAVE>
   ```
   > Ajuste a URL conforme o provedor (Infura, Alchemy, Ankr, etc.).
3. Acesse [Remix IDE](https://remix.ethereum.org/), importe o arquivo `contracts/AthenaElection.sol` e compile com o compilador `0.8.20`.
4. Na aba **Deploy & Run**, selecione `Injected Provider - MetaMask`, escolha a rede de testes desejada e pressione **Deploy** informando:
   - `initialName`: nome descritivo da eleição (ex.: `"Eleicao Teste"`).
   - `candidateNames`: array com os nomes iniciais (ex.: `['"Alice"', '"Bob"']`).
5. Confirme a transação na carteira e registre o endereço do contrato gerado. Utilize esse endereço para qualquer interação posterior (scripts ou via API).

## Interações úteis para testes
- `configureElection(newName, candidateNames)`: redefine os candidatos e incrementa `electionId` (somente owner).
- `openElection()` / `closeElection()`: controla se novos votos são aceitos.
- `vote(candidateId)`: vota no candidato pelo índice (0, 1, 2...).
- `getCandidates()`: retorna array com nomes e totais de votos, útil para verificações rápidas via web3.

## Exemplo de script web3.py
```python
from web3 import Web3
from pathlib import Path
import json

w3 = Web3(Web3.HTTPProvider("https://sepolia.infura.io/v3/<SUA_CHAVE>"))
contract_address = Web3.to_checksum_address("0x...")
abi = json.loads(Path("contracts/athena_election_abi.json").read_text())
contract = w3.eth.contract(address=contract_address, abi=abi)

print(contract.functions.electionName().call())
print(contract.functions.getCandidates().call())
```

> Você pode exportar o ABI pelo Remix ou gerar automaticamente via Hardhat/Foundry.

## Próximos passos
- Criar scripts (Hardhat/Foundry) para deploy automatizado.
- Adaptar a API Flask para consultar o contrato (ex.: listar candidatos, validar votos).
- Adicionar testes de integração que interajam com um nó local (Ganache, Hardhat) para cobrir regressões.
