#!/usr/bin/env python3
"""
GreenClaw NFT Badge Minter — Somnia Shannon Testnet
Deploys and mints ERC-721 achievement badges on-chain.

Usage:
  1. Add MINTER_PRIVATE_KEY to .env (generate one or use existing)
  2. Fund the wallet with testnet STT from https://testnet.somnia.network/
  3. Run: python nft_minter.py deploy   (one-time contract deployment)
  4. The server will auto-mint badges when milestones are hit
"""

import json
import os
import time
from pathlib import Path
from dotenv import load_dotenv
from web3 import Web3

load_dotenv(override=True)

# ──────────────────────────────────────────────
# Somnia Shannon Testnet Config
# ──────────────────────────────────────────────
SOMNIA_RPC = "https://dream-rpc.somnia.network/"
CHAIN_ID = 50312
EXPLORER = "https://shannon.somnia.network"

PRIVATE_KEY = os.getenv("MINTER_PRIVATE_KEY", "")
CONTRACT_FILE = Path(__file__).parent / "data" / "nft_contract.json"

# ──────────────────────────────────────────────
# Minimal ERC-721 Contract (Solidity bytecode + ABI)
# Pre-compiled minimal NFT with: mint(to, tokenId, uri)
# ──────────────────────────────────────────────

# Minimal ERC-721 Solidity source (for reference, pre-compiled below)
SOLIDITY_SOURCE = """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract GreenClawBadge {
    string public name = "GreenClaw Badge";
    string public symbol = "GCLAW";
    address public owner;
    
    uint256 public totalSupply;
    
    mapping(uint256 => address) private _owners;
    mapping(address => uint256) private _balances;
    mapping(uint256 => string) private _tokenURIs;
    
    event Transfer(address indexed from, address indexed to, uint256 indexed tokenId);
    
    constructor() { owner = msg.sender; }
    
    modifier onlyOwner() { require(msg.sender == owner, "Not owner"); _; }
    
    function mint(address to, uint256 tokenId, string memory uri) external onlyOwner {
        require(_owners[tokenId] == address(0), "Already minted");
        _owners[tokenId] = to;
        _balances[to] += 1;
        _tokenURIs[tokenId] = uri;
        totalSupply += 1;
        emit Transfer(address(0), to, tokenId);
    }
    
    function ownerOf(uint256 tokenId) external view returns (address) {
        require(_owners[tokenId] != address(0), "Not exists");
        return _owners[tokenId];
    }
    
    function balanceOf(address account) external view returns (uint256) {
        return _balances[account];
    }
    
    function tokenURI(uint256 tokenId) external view returns (string memory) {
        require(_owners[tokenId] != address(0), "Not exists");
        return _tokenURIs[tokenId];
    }
}
"""

# Pre-compiled ABI for the contract above
CONTRACT_ABI = [
    {"inputs": [], "stateMutability": "nonpayable", "type": "constructor"},
    {"anonymous": False, "inputs": [
        {"indexed": True, "name": "from", "type": "address"},
        {"indexed": True, "name": "to", "type": "address"},
        {"indexed": True, "name": "tokenId", "type": "uint256"}
    ], "name": "Transfer", "type": "event"},
    {"inputs": [{"name": "account", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"},
    {"inputs": [{"name": "to", "type": "address"}, {"name": "tokenId", "type": "uint256"}, {"name": "uri", "type": "string"}], "name": "mint", "outputs": [], "stateMutability": "nonpayable", "type": "function"},
    {"inputs": [], "name": "name", "outputs": [{"name": "", "type": "string"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "owner", "outputs": [{"name": "", "type": "address"}], "stateMutability": "view", "type": "function"},
    {"inputs": [{"name": "tokenId", "type": "uint256"}], "name": "ownerOf", "outputs": [{"name": "", "type": "address"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "symbol", "outputs": [{"name": "", "type": "string"}], "stateMutability": "view", "type": "function"},
    {"inputs": [{"name": "tokenId", "type": "uint256"}], "name": "tokenURI", "outputs": [{"name": "", "type": "string"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "totalSupply", "outputs": [{"name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"},
]

def get_web3():
    w3 = Web3(Web3.HTTPProvider(SOMNIA_RPC))
    if not w3.is_connected():
        raise Exception(f"Cannot connect to Somnia Shannon at {SOMNIA_RPC}")
    return w3

def get_account(w3):
    if not PRIVATE_KEY:
        raise Exception("MINTER_PRIVATE_KEY not set in .env")
    account = w3.eth.account.from_key(PRIVATE_KEY)
    return account

def get_contract_address():
    """Load the deployed contract address from file."""
    if CONTRACT_FILE.exists():
        data = json.loads(CONTRACT_FILE.read_text())
        return data.get("address")
    return None

def save_contract_address(address):
    CONTRACT_FILE.parent.mkdir(exist_ok=True)
    CONTRACT_FILE.write_text(json.dumps({"address": address, "chain_id": CHAIN_ID, "network": "Somnia Shannon"}, indent=2))

def deploy_contract():
    """Deploy the GreenClawBadge ERC-721 contract to Somnia Shannon."""
    print("🚀 Deploying GreenClawBadge NFT contract to Somnia Shannon...")
    
    w3 = get_web3()
    account = get_account(w3)
    print(f"   Deployer: {account.address}")
    
    balance = w3.eth.get_balance(account.address)
    print(f"   Balance: {w3.from_wei(balance, 'ether')} STT")
    
    if balance == 0:
        print("❌ No STT balance! Get testnet tokens from:")
        print("   https://testnet.somnia.network/")
        print("   https://cloud.google.com/application/web3/faucet/somnia/shannon")
        return None
    
    # Compile with solcx
    try:
        import solcx
        solcx.install_solc("0.8.20")
        compiled = solcx.compile_source(
            SOLIDITY_SOURCE,
            output_values=["abi", "bin"],
            solc_version="0.8.20",
        )
        contract_id, contract_interface = list(compiled.items())[0]
        bytecode = contract_interface["bin"]
        abi = contract_interface["abi"]
    except Exception as e:
        print(f"⚠️ Solc compilation failed ({e}), using pre-compiled fallback...")
        # Fallback: use a minimal bytecode that we provide
        print("❌ Cannot deploy without solc. Please install solc or provide bytecode.")
        return None
    
    Contract = w3.eth.contract(abi=abi, bytecode=bytecode)
    
    nonce = w3.eth.get_transaction_count(account.address)
    tx = Contract.constructor().build_transaction({
        "chainId": CHAIN_ID,
        "from": account.address,
        "nonce": nonce,
        "gas": 2000000,
        "gasPrice": w3.eth.gas_price,
    })
    
    signed = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    print(f"   TX Hash: {tx_hash.hex()}")
    print(f"   Explorer: {EXPLORER}/tx/{tx_hash.hex()}")
    
    print("   ⏳ Waiting for confirmation...")
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
    
    if receipt.status == 1:
        contract_address = receipt.contractAddress
        save_contract_address(contract_address)
        print(f"   ✅ Contract deployed at: {contract_address}")
        print(f"   Explorer: {EXPLORER}/address/{contract_address}")
        return contract_address
    else:
        print("   ❌ Deployment failed!")
        return None

def mint_badge(to_address: str, token_id: int, metadata: dict) -> dict:
    """Mint an NFT badge to a user's address on Somnia Shannon."""
    contract_address = get_contract_address()
    if not contract_address:
        return {"success": False, "error": "Contract not deployed. Run: python nft_minter.py deploy"}
    
    w3 = get_web3()
    account = get_account(w3)
    
    contract = w3.eth.contract(address=contract_address, abi=CONTRACT_ABI)
    
    # Build token URI as JSON metadata string
    token_uri = json.dumps({
        "name": metadata.get("name", "GreenClaw Badge"),
        "description": metadata.get("desc", "Achievement badge for climate action"),
        "image": metadata.get("image", ""),
        "attributes": [
            {"trait_type": "Badge ID", "value": metadata.get("id", "")},
            {"trait_type": "Earned By", "value": metadata.get("user", "anonymous")},
            {"trait_type": "CO2 Saved", "value": metadata.get("co2", 0)},
        ]
    })
    
    try:
        nonce = w3.eth.get_transaction_count(account.address)
        tx = contract.functions.mint(
            Web3.to_checksum_address(to_address),
            token_id,
            token_uri
        ).build_transaction({
            "chainId": CHAIN_ID,
            "from": account.address,
            "nonce": nonce,
            "gas": 300000,
            "gasPrice": w3.eth.gas_price,
        })
        
        signed = account.sign_transaction(tx)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
        
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)
        
        if receipt.status == 1:
            return {
                "success": True,
                "tx_hash": tx_hash.hex(),
                "token_id": token_id,
                "contract": contract_address,
                "explorer_url": f"{EXPLORER}/tx/{tx_hash.hex()}",
                "nft_url": f"{EXPLORER}/token/{contract_address}?a={token_id}",
            }
        else:
            return {"success": False, "error": "Transaction reverted"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_nft_info(token_id: int) -> dict:
    """Get info about a minted NFT."""
    contract_address = get_contract_address()
    if not contract_address:
        return {"error": "Contract not deployed"}
    
    w3 = get_web3()
    contract = w3.eth.contract(address=contract_address, abi=CONTRACT_ABI)
    
    try:
        owner = contract.functions.ownerOf(token_id).call()
        uri = contract.functions.tokenURI(token_id).call()
        return {"token_id": token_id, "owner": owner, "uri": uri, "contract": contract_address}
    except Exception as e:
        return {"error": str(e)}

# ──────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python nft_minter.py deploy       — Deploy the NFT contract")
        print("  python nft_minter.py info          — Show contract info")
        print("  python nft_minter.py balance       — Show wallet balance")
        sys.exit(0)
    
    cmd = sys.argv[1]
    
    if cmd == "deploy":
        deploy_contract()
    elif cmd == "info":
        addr = get_contract_address()
        if addr:
            w3 = get_web3()
            contract = w3.eth.contract(address=addr, abi=CONTRACT_ABI)
            print(f"📋 Contract: {addr}")
            print(f"   Name: {contract.functions.name().call()}")
            print(f"   Symbol: {contract.functions.symbol().call()}")
            print(f"   Total Supply: {contract.functions.totalSupply().call()}")
            print(f"   Explorer: {EXPLORER}/address/{addr}")
        else:
            print("❌ Contract not deployed yet. Run: python nft_minter.py deploy")
    elif cmd == "balance":
        w3 = get_web3()
        account = get_account(w3)
        balance = w3.eth.get_balance(account.address)
        print(f"💰 Wallet: {account.address}")
        print(f"   Balance: {w3.from_wei(balance, 'ether')} STT")
        print(f"   Faucet: https://testnet.somnia.network/")
    else:
        print(f"Unknown command: {cmd}")
