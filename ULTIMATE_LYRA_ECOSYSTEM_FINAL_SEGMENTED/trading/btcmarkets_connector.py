#!/usr/bin/env python3
"""
ULTIMATE LYRA ECOSYSTEM - BTC MARKETS CONNECTOR
==============================================

BTC Markets exchange connector for the Ultimate Lyra Ecosystem.
Based on BTC Markets API v3 specification.
"""

import asyncio
import aiohttp
import base64
import hashlib
import hmac
import json
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
import urllib.parse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class BTCMarketsConfig:
    """BTC Markets configuration"""
    name: str = "btcmarkets"
    api_key: str = ""
    private_key: str = ""
    base_url: str = "https://api.btcmarkets.net"
    sandbox: bool = False

@dataclass
class BTCMarketsTicker:
    """BTC Markets ticker data"""
    symbol: str
    price: float
    volume: float
    high: float
    low: float
    change: float
    timestamp: str

@dataclass
class BTCMarketsOrderBook:
    """BTC Markets order book data"""
    symbol: str
    bids: List[Tuple[float, float]]
    asks: List[Tuple[float, float]]
    timestamp: str

@dataclass
class BTCMarketsOrder:
    """BTC Markets order data"""
    order_id: str
    symbol: str
    side: str
    type: str
    amount: float
    price: Optional[float]
    status: str
    filled: float
    remaining: float
    timestamp: str

class BTCMarketsConnector:
    """BTC Markets Exchange Connector"""
    
    def __init__(self, config: BTCMarketsConfig):
        self.config = config
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def _build_headers(self, method: str, api_key: str, private_key: str, path: str, data: str = None) -> Dict[str, str]:
        """Build authentication headers for BTC Markets API"""
        timestamp = str(int(time.time() * 1000))
        
        if data is None:
            data = ""
        
        # Create the string to sign
        string_to_sign = method + path + timestamp + data
        
        # Decode the private key from base64
        private_key_bytes = base64.b64decode(private_key)
        
        # Create the signature
        signature = base64.b64encode(
            hmac.new(
                private_key_bytes,
                string_to_sign.encode('utf-8'),
                hashlib.sha512
            ).digest()
        ).decode('utf-8')
        
        return {
            'Accept': 'application/json',
            'Accept-Charset': 'UTF-8',
            'Content-Type': 'application/json',
            'BM-AUTH-APIKEY': api_key,
            'BM-AUTH-TIMESTAMP': timestamp,
            'BM-AUTH-SIGNATURE': signature
        }
    
    def _make_http_call(self, method: str, api_key: str, private_key: str, path: str, query_string: str = "", data: str = None):
        """Make HTTP call helper (for reference - async version used in practice)"""
        if data is not None:
            data = json.dumps(data)
        
        headers = self._build_headers(method, api_key, private_key, path, data)
        
        if query_string:
            full_path = path + '?' + query_string
        else:
            full_path = path
        
        return {
            'url': self.config.base_url + full_path,
            'headers': headers,
            'data': data
        }
    
    async def get_markets(self) -> Optional[List[Dict]]:
        """Get all available markets"""
        try:
            path = "/v3/markets"
            
            async with self.session.get(f"{self.config.base_url}{path}") as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"BTC Markets: Retrieved {len(data)} markets")
                    return data
                else:
                    logger.error(f"BTC Markets markets error: {response.status}")
                    
        except Exception as e:
            logger.error(f"BTC Markets markets error: {str(e)}")
            
        return None
    
    async def get_ticker(self, symbol: str) -> Optional[BTCMarketsTicker]:
        """Get ticker data for a symbol"""
        try:
            # BTC Markets uses format like BTC-AUD
            path = f"/v3/markets/{symbol}/ticker"
            
            async with self.session.get(f"{self.config.base_url}{path}") as response:
                if response.status == 200:
                    data = await response.json()
                    
                    return BTCMarketsTicker(
                        symbol=symbol,
                        price=float(data.get('lastPrice', 0)),
                        volume=float(data.get('volume24h', 0)),
                        high=float(data.get('high24h', 0)),
                        low=float(data.get('low24h', 0)),
                        change=float(data.get('change24h', 0)),
                        timestamp=datetime.utcnow().isoformat()
                    )
                else:
                    logger.error(f"BTC Markets ticker error for {symbol}: {response.status}")
                    
        except Exception as e:
            logger.error(f"BTC Markets ticker error for {symbol}: {str(e)}")
            
        return None
    
    async def get_orderbook(self, symbol: str, depth: int = 20) -> Optional[BTCMarketsOrderBook]:
        """Get order book data for a symbol"""
        try:
            path = f"/v3/markets/{symbol}/orderbook"
            params = {'level': 2}  # Level 2 for aggregated order book
            
            async with self.session.get(
                f"{self.config.base_url}{path}",
                params=params
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Parse bids and asks
                    bids = [(float(bid[0]), float(bid[1])) for bid in data.get('bids', [])[:depth]]
                    asks = [(float(ask[0]), float(ask[1])) for ask in data.get('asks', [])[:depth]]
                    
                    return BTCMarketsOrderBook(
                        symbol=symbol,
                        bids=bids,
                        asks=asks,
                        timestamp=datetime.utcnow().isoformat()
                    )
                else:
                    logger.error(f"BTC Markets orderbook error for {symbol}: {response.status}")
                    
        except Exception as e:
            logger.error(f"BTC Markets orderbook error for {symbol}: {str(e)}")
            
        return None
    
    async def get_trades(self, symbol: str, limit: int = 50) -> Optional[List[Dict]]:
        """Get recent trades for a symbol"""
        try:
            path = f"/v3/markets/{symbol}/trades"
            params = {'limit': limit}
            
            async with self.session.get(
                f"{self.config.base_url}{path}",
                params=params
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"BTC Markets: Retrieved {len(data)} trades for {symbol}")
                    return data
                else:
                    logger.error(f"BTC Markets trades error for {symbol}: {response.status}")
                    
        except Exception as e:
            logger.error(f"BTC Markets trades error for {symbol}: {str(e)}")
            
        return None
    
    async def get_account_balance(self) -> Optional[List[Dict]]:
        """Get account balances (requires authentication)"""
        if not self.config.api_key or not self.config.private_key:
            logger.warning("BTC Markets: API credentials not configured for account balance")
            return None
        
        try:
            path = "/v3/accounts/me/balances"
            method = "GET"
            
            headers = self._build_headers(method, self.config.api_key, self.config.private_key, path)
            
            async with self.session.get(
                f"{self.config.base_url}{path}",
                headers=headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"BTC Markets: Retrieved balances for {len(data)} assets")
                    return data
                else:
                    logger.error(f"BTC Markets balance error: {response.status}")
                    error_text = await response.text()
                    logger.error(f"BTC Markets balance error details: {error_text}")
                    
        except Exception as e:
            logger.error(f"BTC Markets balance error: {str(e)}")
            
        return None
    
    async def place_order(self, symbol: str, side: str, order_type: str, amount: float, price: Optional[float] = None) -> Optional[BTCMarketsOrder]:
        """Place an order (requires authentication)"""
        if not self.config.api_key or not self.config.private_key:
            logger.warning("BTC Markets: API credentials not configured for order placement")
            return None
        
        try:
            path = "/v3/orders"
            method = "POST"
            
            # Build order payload
            payload = {
                'marketId': symbol,
                'side': side.upper(),
                'type': order_type.upper(),
                'amount': str(amount)
            }
            
            if price is not None and order_type.upper() == 'LIMIT':
                payload['price'] = str(price)
            
            data = json.dumps(payload)
            headers = self._build_headers(method, self.config.api_key, self.config.private_key, path, data)
            
            async with self.session.post(
                f"{self.config.base_url}{path}",
                headers=headers,
                data=data
            ) as response:
                if response.status in [200, 201]:
                    result = await response.json()
                    
                    logger.info(f"BTC Markets order placed: {symbol} {side} {amount}")
                    
                    return BTCMarketsOrder(
                        order_id=result.get('orderId', ''),
                        symbol=symbol,
                        side=side.upper(),
                        type=order_type.upper(),
                        amount=amount,
                        price=price,
                        status=result.get('status', 'UNKNOWN'),
                        filled=float(result.get('filled', 0)),
                        remaining=float(result.get('remaining', amount)),
                        timestamp=datetime.utcnow().isoformat()
                    )
                else:
                    logger.error(f"BTC Markets order failed: {response.status}")
                    error_text = await response.text()
                    logger.error(f"BTC Markets order error details: {error_text}")
                    
        except Exception as e:
            logger.error(f"BTC Markets place order error: {str(e)}")
            
        return None
    
    async def get_orders(self, symbol: Optional[str] = None, status: Optional[str] = None) -> Optional[List[BTCMarketsOrder]]:
        """Get orders (requires authentication)"""
        if not self.config.api_key or not self.config.private_key:
            logger.warning("BTC Markets: API credentials not configured for order retrieval")
            return None
        
        try:
            path = "/v3/orders"
            method = "GET"
            
            params = {}
            if symbol:
                params['marketId'] = symbol
            if status:
                params['status'] = status
            
            query_string = urllib.parse.urlencode(params) if params else ""
            
            headers = self._build_headers(method, self.config.api_key, self.config.private_key, path)
            
            url = f"{self.config.base_url}{path}"
            if query_string:
                url += f"?{query_string}"
            
            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    orders = []
                    for order_data in data:
                        orders.append(BTCMarketsOrder(
                            order_id=order_data.get('orderId', ''),
                            symbol=order_data.get('marketId', ''),
                            side=order_data.get('side', ''),
                            type=order_data.get('type', ''),
                            amount=float(order_data.get('amount', 0)),
                            price=float(order_data.get('price', 0)) if order_data.get('price') else None,
                            status=order_data.get('status', ''),
                            filled=float(order_data.get('filled', 0)),
                            remaining=float(order_data.get('remaining', 0)),
                            timestamp=order_data.get('creationTime', datetime.utcnow().isoformat())
                        ))
                    
                    logger.info(f"BTC Markets: Retrieved {len(orders)} orders")
                    return orders
                else:
                    logger.error(f"BTC Markets orders error: {response.status}")
                    
        except Exception as e:
            logger.error(f"BTC Markets get orders error: {str(e)}")
            
        return None
    
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel an order (requires authentication)"""
        if not self.config.api_key or not self.config.private_key:
            logger.warning("BTC Markets: API credentials not configured for order cancellation")
            return False
        
        try:
            path = f"/v3/orders/{order_id}"
            method = "DELETE"
            
            headers = self._build_headers(method, self.config.api_key, self.config.private_key, path)
            
            async with self.session.delete(
                f"{self.config.base_url}{path}",
                headers=headers
            ) as response:
                if response.status in [200, 204]:
                    logger.info(f"BTC Markets order cancelled: {order_id}")
                    return True
                else:
                    logger.error(f"BTC Markets cancel order failed: {response.status}")
                    
        except Exception as e:
            logger.error(f"BTC Markets cancel order error: {str(e)}")
            
        return False

# Example usage and testing
async def main():
    """Test BTC Markets connector"""
    print("🇦🇺 Testing BTC Markets Connector")
    print("=" * 40)
    
    # Initialize connector (no credentials needed for public endpoints)
    config = BTCMarketsConfig()
    
    async with BTCMarketsConnector(config) as connector:
        
        # Test 1: Get available markets
        print("📊 Test 1: Available Markets")
        markets = await connector.get_markets()
        if markets:
            print(f"   Found {len(markets)} markets")
            # Show first few markets
            for market in markets[:5]:
                print(f"   - {market.get('marketId', 'Unknown')}: {market.get('baseAsset', '')}/{market.get('quoteAsset', '')}")
        print()
        
        # Test 2: Get ticker data
        print("💰 Test 2: Ticker Data")
        symbols = ['BTC-AUD', 'ETH-AUD', 'ADA-AUD']
        
        for symbol in symbols:
            ticker = await connector.get_ticker(symbol)
            if ticker:
                print(f"   {symbol}: ${ticker.price:,.2f} AUD (Vol: {ticker.volume:,.0f})")
                print(f"      24h: High ${ticker.high:,.2f} | Low ${ticker.low:,.2f} | Change {ticker.change:+.2f}%")
            else:
                print(f"   {symbol}: No data available")
        print()
        
        # Test 3: Get order book
        print("📈 Test 3: Order Book Data")
        orderbook = await connector.get_orderbook('BTC-AUD', 5)
        if orderbook:
            print(f"   {orderbook.symbol} Order Book:")
            print("   Bids (Buy Orders):")
            for price, volume in orderbook.bids[:3]:
                print(f"      ${price:,.2f} - {volume:.4f} BTC")
            print("   Asks (Sell Orders):")
            for price, volume in orderbook.asks[:3]:
                print(f"      ${price:,.2f} - {volume:.4f} BTC")
        print()
        
        # Test 4: Get recent trades
        print("📊 Test 4: Recent Trades")
        trades = await connector.get_trades('BTC-AUD', 5)
        if trades:
            print(f"   Recent {len(trades)} trades for BTC-AUD:")
            for trade in trades[:3]:
                print(f"      ${float(trade.get('price', 0)):,.2f} - {float(trade.get('amount', 0)):.4f} BTC ({trade.get('side', 'Unknown')})")
        print()
        
        # Test 5: Account operations (would require API keys)
        print("🔐 Test 5: Account Operations")
        print("   Account balance: Requires API credentials")
        print("   Order placement: Requires API credentials")
        print("   Order management: Requires API credentials")
        print()
        
        print("✅ BTC Markets connector testing completed!")
        print("🇦🇺 Ready for integration with Ultimate Lyra Ecosystem!")

if __name__ == "__main__":
    asyncio.run(main())
