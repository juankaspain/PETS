"""Polymarket CLOB contract interface."""

import logging
from decimal import Decimal

from web3 import Web3

from src.infrastructure.blockchain.web3_client import Web3Client

logger = logging.getLogger(__name__)

# Simplified CLOB ABI (key functions only)
CLOB_ABI = [
    {
        "inputs": [
            {"name": "marketId", "type": "bytes32"},
            {"name": "side", "type": "uint8"},  # 0=BUY, 1=SELL
            {"name": "price", "type": "uint256"},
            {"name": "size", "type": "uint256"},
            {"name": "postOnly", "type": "bool"},
        ],
        "name": "placeOrder",
        "outputs": [{"name": "orderId", "type": "bytes32"}],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [{"name": "orderId", "type": "bytes32"}],
        "name": "cancelOrder",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [{"name": "orderId", "type": "bytes32"}],
        "name": "getOrder",
        "outputs": [
            {"name": "marketId", "type": "bytes32"},
            {"name": "side", "type": "uint8"},
            {"name": "price", "type": "uint256"},
            {"name": "size", "type": "uint256"},
            {"name": "filled", "type": "uint256"},
            {"name": "status", "type": "uint8"},  # 0=OPEN, 1=FILLED, 2=CANCELLED
        ],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "orderId", "type": "bytes32"},
            {"indexed": True, "name": "maker", "type": "address"},
            {"indexed": False, "name": "marketId", "type": "bytes32"},
            {"indexed": False, "name": "side", "type": "uint8"},
            {"indexed": False, "name": "price", "type": "uint256"},
            {"indexed": False, "name": "size", "type": "uint256"},
        ],
        "name": "OrderPlaced",
        "type": "event",
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "orderId", "type": "bytes32"},
            {"indexed": False, "name": "filledSize", "type": "uint256"},
            {"indexed": False, "name": "filledPrice", "type": "uint256"},
        ],
        "name": "OrderFilled",
        "type": "event",
    },
]


class CLOBContract:
    """Polymarket CLOB contract interface.
    
    Handles:
    - Order placement (post-only)
    - Order cancellation
    - Order status queries
    - Event monitoring
    """

    def __init__(self, web3_client: Web3Client, contract_address: str):
        """Initialize CLOB contract.
        
        Args:
            web3_client: Web3 client
            contract_address: CLOB contract address
        """
        self.web3_client = web3_client
        self.contract = web3_client.w3.eth.contract(
            address=Web3.to_checksum_address(contract_address),
            abi=CLOB_ABI,
        )
        
        logger.info(
            "CLOBContract initialized",
            extra={"contract_address": contract_address},
        )

    def build_place_order_tx(
        self,
        market_id: str,
        side: str,
        price: Decimal,
        size: Decimal,
        post_only: bool = True,
    ) -> dict:
        """Build place order transaction.
        
        Args:
            market_id: Market ID (bytes32)
            side: Order side ('BUY' or 'SELL')
            price: Limit price (0-1)
            size: Order size in USDC
            post_only: Post-only flag (maker)
            
        Returns:
            Transaction dict
        """
        # Convert side to uint8
        side_uint = 0 if side == "BUY" else 1
        
        # Convert price to uint256 (scale by 10^18)
        price_uint = int(price * Decimal(10**18))
        
        # Convert size to uint256 (USDC has 6 decimals)
        size_uint = int(size * Decimal(10**6))
        
        # Build transaction
        tx = self.contract.functions.placeOrder(
            Web3.to_bytes(hexstr=market_id),
            side_uint,
            price_uint,
            size_uint,
            post_only,
        ).build_transaction({
            "from": self.web3_client.address,
            "nonce": self.web3_client.w3.eth.get_transaction_count(self.web3_client.address),
        })
        
        logger.info(
            "Place order transaction built",
            extra={
                "market_id": market_id,
                "side": side,
                "price": float(price),
                "size": float(size),
                "post_only": post_only,
            },
        )
        
        return tx

    def build_cancel_order_tx(self, order_id: str) -> dict:
        """Build cancel order transaction.
        
        Args:
            order_id: Order ID (bytes32)
            
        Returns:
            Transaction dict
        """
        tx = self.contract.functions.cancelOrder(
            Web3.to_bytes(hexstr=order_id),
        ).build_transaction({
            "from": self.web3_client.address,
            "nonce": self.web3_client.w3.eth.get_transaction_count(self.web3_client.address),
        })
        
        logger.info("Cancel order transaction built", extra={"order_id": order_id})
        
        return tx

    def get_order_status(self, order_id: str) -> dict:
        """Get order status.
        
        Args:
            order_id: Order ID (bytes32)
            
        Returns:
            Order status dict
        """
        result = self.contract.functions.getOrder(
            Web3.to_bytes(hexstr=order_id),
        ).call()
        
        market_id, side, price, size, filled, status = result
        
        return {
            "market_id": market_id.hex(),
            "side": "BUY" if side == 0 else "SELL",
            "price": Decimal(price) / Decimal(10**18),
            "size": Decimal(size) / Decimal(10**6),
            "filled": Decimal(filled) / Decimal(10**6),
            "status": ["OPEN", "FILLED", "CANCELLED"][status],
        }

    def get_order_placed_events(
        self,
        from_block: int,
        to_block: int | str = "latest",
    ) -> list[dict]:
        """Get OrderPlaced events.
        
        Args:
            from_block: Start block
            to_block: End block
            
        Returns:
            List of OrderPlaced events
        """
        events = self.contract.events.OrderPlaced.get_logs(
            fromBlock=from_block,
            toBlock=to_block,
        )
        
        return [
            {
                "order_id": event['args']['orderId'].hex(),
                "maker": event['args']['maker'],
                "market_id": event['args']['marketId'].hex(),
                "side": "BUY" if event['args']['side'] == 0 else "SELL",
                "price": Decimal(event['args']['price']) / Decimal(10**18),
                "size": Decimal(event['args']['size']) / Decimal(10**6),
                "block": event['blockNumber'],
                "tx_hash": event['transactionHash'].hex(),
            }
            for event in events
        ]

    def get_order_filled_events(
        self,
        from_block: int,
        to_block: int | str = "latest",
    ) -> list[dict]:
        """Get OrderFilled events.
        
        Args:
            from_block: Start block
            to_block: End block
            
        Returns:
            List of OrderFilled events
        """
        events = self.contract.events.OrderFilled.get_logs(
            fromBlock=from_block,
            toBlock=to_block,
        )
        
        return [
            {
                "order_id": event['args']['orderId'].hex(),
                "filled_size": Decimal(event['args']['filledSize']) / Decimal(10**6),
                "filled_price": Decimal(event['args']['filledPrice']) / Decimal(10**18),
                "block": event['blockNumber'],
                "tx_hash": event['transactionHash'].hex(),
            }
            for event in events
        ]
