// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @title AthenaElection - contrato simples de votação para testes em testnets Ethereum
/// @notice Permite configurar eleições, abrir/fechar votação e registrar votos on-chain
contract AthenaElection {
    struct Candidate {
        string name;
        uint256 voteCount;
    }

    string public electionName;
    address public immutable owner;
    bool public electionOpen;
    uint256 public electionId;

    Candidate[] private _candidates;
    mapping(address => uint256) private _lastVotedElection;

    event ElectionConfigured(uint256 indexed electionId, string name, uint256 candidateCount);
    event ElectionOpened(uint256 indexed electionId, string name);
    event ElectionClosed(uint256 indexed electionId, string name);
    event CandidateAdded(uint256 indexed candidateId, string name);
    event VoteCast(uint256 indexed electionId, address indexed voter, uint256 indexed candidateId);

    modifier onlyOwner() {
        require(msg.sender == owner, "Only owner");
        _;
    }

    constructor(string memory initialName, string[] memory candidateNames) {
        owner = msg.sender;
        _configureElection(initialName, candidateNames);
    }

    /// @notice Permite configurar uma nova eleição (somente owner) enquanto estiver fechada
    /// @param newName Nome amigável da eleição
    /// @param candidateNames Lista inicial de candidatos
    function configureElection(string memory newName, string[] memory candidateNames) external onlyOwner {
        require(!electionOpen, "Close election first");
        _configureElection(newName, candidateNames);
    }

    /// @notice Adiciona um candidato antes da eleição abrir
    function addCandidate(string memory name) external onlyOwner {
        require(!electionOpen, "Election already open");
        _addCandidate(name);
    }

    /// @notice Abre a eleição para votação (somente owner)
    function openElection() external onlyOwner {
        require(!electionOpen, "Election already open");
        require(_candidates.length > 0, "No candidates configured");

        electionOpen = true;
        emit ElectionOpened(electionId, electionName);
    }

    /// @notice Encerra a eleição atual (somente owner)
    function closeElection() external onlyOwner {
        require(electionOpen, "Election already closed");

        electionOpen = false;
        emit ElectionClosed(electionId, electionName);
    }

    /// @notice Registra um voto para um candidato pelo índice
    /// @param candidateId Índice do candidato no array
    function vote(uint256 candidateId) external {
        require(electionOpen, "Election closed");
        require(candidateId < _candidates.length, "Invalid candidate");
        require(_lastVotedElection[msg.sender] != electionId, "Already voted");

        _lastVotedElection[msg.sender] = electionId;
        _candidates[candidateId].voteCount += 1;

        emit VoteCast(electionId, msg.sender, candidateId);
    }

    /// @notice Retorna o total de candidatos configurados
    function candidateCount() external view returns (uint256) {
        return _candidates.length;
    }

    /// @notice Retorna os dados de um candidato específico
    function getCandidate(uint256 candidateId) external view returns (string memory name, uint256 voteCount) {
        require(candidateId < _candidates.length, "Invalid candidate");
        Candidate storage candidate = _candidates[candidateId];
        return (candidate.name, candidate.voteCount);
    }

    /// @notice Retorna todos os candidatos configurados (nome e votos)
    function getCandidates() external view returns (Candidate[] memory) {
        Candidate[] memory candidatesCopy = new Candidate[](_candidates.length);
        for (uint256 i = 0; i < _candidates.length; i++) {
            candidatesCopy[i] = _candidates[i];
        }
        return candidatesCopy;
    }

    /// @notice Verifica se um endereço já votou na eleição atual
    function hasAddressVoted(address account) external view returns (bool) {
        return _lastVotedElection[account] == electionId;
    }

    function _configureElection(string memory newName, string[] memory candidateNames) internal {
        delete _candidates;
        electionName = newName;
        electionId += 1;
        electionOpen = false;

        for (uint256 i = 0; i < candidateNames.length; i++) {
            _addCandidate(candidateNames[i]);
        }

        emit ElectionConfigured(electionId, newName, _candidates.length);
    }

    function _addCandidate(string memory name) internal {
        require(bytes(name).length > 0, "Empty name");
        _candidates.push(Candidate({name: name, voteCount: 0}));
        emit CandidateAdded(_candidates.length - 1, name);
    }
}
