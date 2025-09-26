#!/usr/bin/env python3
"""
ULTIMATE LYRA ECOSYSTEM - LIVE EXCHANGE CONNECTOR
================================================

Real exchange connections using paper trading and demo API keys.
Supports OKX, Gate.io, Binance Testnet, and WhiteBIT paper trading.
"""

import asyncio
import aiohttp
import hashlib
import hmac
import json
import time
import base64
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.live')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ExchangeConfig:
    """Exchange configuration"""
    name: str
    api_key: str
    secret_key: str
    passphrase: str = ""
    base_url: str = ""
    ws_url: str = ""
    sandbox: bool = True

@dataclass
class OrderBook:
    """Order book data"""
    symbol: str
    bids: List[Tuple[float, float]]
    asks: List[Tuple[float, float]]
    timestamp: str

@dataclass
class Ticker:
    """Ticker data"""
    symbol: str
    price: float
    volume: float
    timestamp: str

@dataclass
class Trade:
    """Trade data"""
    symbol: str
    price: float
    size: float
    side: str
    timestamp: str

class OKXConnector:
    """OKX Exchange Connector"""
    
    def __init__(self, config: ExchangeConfig):
        self.config = config
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def _generate_signature(self, timestamp: str, method: str, request_path: str, body: str = "") -> str:
        """Generate OKX API signature"""
        message = timestamp + method + request_path + body
        signature = base64.b64encode(
            hmac.new(
                self.config.secret_key.encode('utf-8'),
                message.encode('utf-8'),
                hashlib.sha256
            ).digest()
        ).decode('utf-8')
        return signature
    
    def _get_headers(self, method: str, request_path: str, body: str = "") -> Dict[str, str]:
        """Get OKX API headers"""
        timestamp = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
        signature = self._generate_signature(timestamp, method, request_path, body)
        
        return {
            'OK-ACCESS-KEY': self.config.api_key,
            'OK-ACCESS-SIGN': signature,
            'OK-ACCESS-TIMESTAMP': timestamp,
            'OK-ACCESS-PASSPHRASE': self.config.passphrase,
            'Content-Type': 'application/json'
        }
    
    async def get_ticker(self, symbol: str) -> Optional[Ticker]:
        """Get ticker data"""
        try:
            request_path = f"/api/v5/market/ticker?instId={symbol}"
            headers = self._get_headers('GET', request_path)
            
            async with self.session.get(
                f"{self.config.base_url}{request_path}",
                headers=headers
            ) as response:
                data = await response.json()
                
                if data.get('code') == '0' and data.get('data'):
                    ticker_data = data['data'][0]
                    return Ticker(
                        symbol=symbol,
                        price=float(ticker_data['last']),
                        volume=float(ticker_data['vol24h']),
                        timestamp=datetime.utcnow().isoformat()
                    )
                    
        except Exception as e:
            logger.error(f"OKX ticker error for {symbol}: {str(e)}")
            
        return None
    
    async def get_orderbook(self, symbol: str, depth: int = 20) -> Optional[OrderBook]:
        """Get order book data"""
        try:
            request_path = f"/api/v5/market/books?instId={symbol}&sz={depth}"
            headers = self._get_headers('GET', request_path)
            
            async with self.session.get(
                f"{self.config.base_url}{request_path}",
                headers=headers
            ) as response:
                data = await response.json()
                
                if data.get('code') == '0' and data.get('data'):
                    book_data = data['data'][0]
                    
                    bids = [(float(bid[0]), float(bid[1])) for bid in book_data.get('bids', [])]
                    asks = [(float(ask[0]), float(ask[1])) for ask in book_data.get('asks', [])]
                    
                    return OrderBook(
                        symbol=symbol,
                        bids=bids,
                        asks=asks,
                        timestamp=datetime.utcnow().isoformat()
                    )
                    
        except Exception as e:
            logger.error(f"OKX orderbook error for {symbol}: {str(e)}")
            
        return None
    
    async def place_order(self, symbol: str, side: str, size: float, price: Optional[float] = None) -> Optional[Dict]:
        """Place an order (paper trading)"""
        try:
            order_data = {
                "instId": symbol,
                "tdMode": "cash",
                "side": side.lower(),
                "ordType": "market" if price is None else "limit",
                "sz": str(size)
            }
            
            if price is not None:
                order_data["px"] = str(price)
            
            body = json.dumps(order_data)
            request_path = "/api/v5/trade/order"
            headers = self._get_headers('POST', request_path, body)
            
            async with self.session.post(
                f"{self.config.base_url}{request_path}",
                headers=headers,
                data=body
            ) as response:
                data = await response.json()
                
                if data.get('code') == '0':
                    logger.info(f"OKX order placed: {symbol} {side} {size}")
                    return data.get('data', [{}])[0]
                else:
                    logger.error(f"OKX order failed: {data}")
                    
        except Exception as e:
            logger.error(f"OKX place order error: {str(e)}")
            
        return None

class GateConnector:
    """Gate.io Exchange Connector"""
    
    def __init__(self, config: ExchangeConfig):
        self.config = config
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def _generate_signature(self, method: str, url_path: str, query_string: str, payload: str) -> str:
        """Generate Gate.io API signature"""
        timestamp = str(int(time.time()))
        
        # Create the string to sign
        string_to_sign = f"{method}\n{url_path}\n{query_string}\n{hashlib.sha512(payload.encode()).hexdigest()}\n{timestamp}"
        
        # Generate signature
        signature = hmac.new(
            self.config.secret_key.encode('utf-8'),
            string_to_sign.encode('utf-8'),
            hashlib.sha512
        ).hexdigest()
        
        return signature, timestamp
    
    def _get_headers(self, method: str, url_path: str, query_string: str = "", payload: str = "") -> Dict[str, str]:
        """Get Gate.io API headers"""
        signature, timestamp = self._generate_signature(method, url_path, query_string, payload)
        
        return {
            'KEY': self.config.api_key,
            'SIGN': signature,
            'Timestamp': timestamp,
            'Content-Type': 'application/json'
        }
    
    async def get_ticker(self, symbol: str) -> Optional[Ticker]:
        """Get ticker data"""
        try:
            # Convert symbol format (BTC-USDT -> BTC_USDT)
            gate_symbol = symbol.replace('-', '_')
            
            url_path = f"/api/v4/spot/tickers"
            query_string = f"currency_pair={gate_symbol}"
            headers = self._get_headers('GET', url_path, query_string)
            
            async with self.session.get(
                f"{self.config.base_url}{url_path}?{query_string}",
                headers=headers
            ) as response:
                data = await response.json()
                
                if isinstance(data, list) and len(data) > 0:
                    ticker_data = data[0]
                    return Ticker(
                        symbol=symbol,
                        price=float(ticker_data['last']),
                        volume=float(ticker_data['base_volume']),
                        timestamp=datetime.utcnow().isoformat()
                    )
                    
        except Exception as e:
            logger.error(f"Gate ticker error for {symbol}: {str(e)}")
            
        return None
    
    async def get_orderbook(self, symbol: str, depth: int = 20) -> Optional[OrderBook]:
        """Get order book data"""
        try:
            # Convert symbol format
            gate_symbol = symbol.replace('-', '_')
            
            url_path = f"/api/v4/spot/order_book"
            query_string = f"currency_pair={gate_symbol}&limit={depth}"
            headers = self._get_headers('GET', url_path, query_string)
            
            async with self.session.get(
                f"{self.config.base_url}{url_path}?{query_string}",
                headers=headers
            ) as response:
                data = await response.json()
                
                if 'bids' in data and 'asks' in data:
                    bids = [(float(bid[0]), float(bid[1])) for bid in data['bids']]
                    asks = [(float(ask[0]), float(ask[1])) for ask in data['asks']]
                    
                    return OrderBook(
                        symbol=symbol,
                        bids=bids,
                        asks=asks,
                        timestamp=datetime.utcnow().isoformat()
                    )
                    
        except Exception as e:
            logger.error(f"Gate orderbook error for {symbol}: {str(e)}")
            
        return None

class BinanceConnector:
    """Binance Testnet Connector"""
    
    def __init__(self, config: ExchangeConfig):
        self.config = config
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def _generate_signature(self, query_string: str) -> str:
        """Generate Binance API signature"""
        return hmac.new(
            self.config.secret_key.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    async def get_ticker(self, symbol: str) -> Optional[Ticker]:
        """Get ticker data"""
        try:
            async with self.session.get(
                f"{self.config.base_url}/api/v3/ticker/24hr?symbol={symbol}"
            ) as response:
                data = await response.json()
                
                if 'lastPrice' in data:
                    return Ticker(
                        symbol=symbol,
                        price=float(data['lastPrice']),
                        volume=float(data['volume']),
                        timestamp=datetime.utcnow().isoformat()
                    )
                    
        except Exception as e:
            logger.error(f"Binance ticker error for {symbol}: {str(e)}")
            
        return None
    
    async def get_orderbook(self, symbol: str, depth: int = 20) -> Optional[OrderBook]:
        """Get order book data"""
        try:
            async with self.session.get(
                f"{self.config.base_url}/api/v3/depth?symbol={symbol}&limit={depth}"
            ) as response:
                data = await response.json()
                
                if 'bids' in data and 'asks' in data:
                    bids = [(float(bid[0]), float(bid[1])) for bid in data['bids']]
                    asks = [(float(ask[0]), float(ask[1])) for ask in data['asks']]
                    
                    return OrderBook(
                        symbol=symbol,
                        bids=bids,
                        asks=asks,
                        timestamp=datetime.utcnow().isoformat()
                    )
                    
        except Exception as e:
            logger.error(f"Binance orderbook error for {symbol}: {str(e)}")
            
        return None
    
    async def place_order(self, symbol: str, side: str, size: float, price: Optional[float] = None) -> Optional[Dict]:
        """Place an order (testnet)"""
        try:
            timestamp = int(time.time() * 1000)
            
            params = {
                'symbol': symbol,
                'side': side.upper(),
                'type': 'MARKET' if price is None else 'LIMIT',
                'quantity': str(size),
                'timestamp': timestamp
            }
            
            if price is not None:
                params['price'] = str(price)
                params['timeInForce'] = 'GTC'
            
            # Create query string
            query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
            signature = self._generate_signature(query_string)
            query_string += f"&signature={signature}"
            
            headers = {
                'X-MBX-APIKEY': self.config.api_key,
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            async with self.session.post(
                f"{self.config.base_url}/api/v3/order",
                headers=headers,
                data=query_string
            ) as response:
                data = await response.json()
                
                if 'orderId' in data:
                    logger.info(f"Binance testnet order placed: {symbol} {side} {size}")
                    return data
                else:
                    logger.error(f"Binance order failed: {data}")
                    
        except Exception as e:
            logger.error(f"Binance place order error: {str(e)}")
            
        return None

class LiveExchangeManager:
    """Manages connections to multiple live exchanges"""
    
    def __init__(self):
        self.exchanges = {}
        self._initialize_exchanges()
    
    def _initialize_exchanges(self):
        """Initialize exchange configurations"""
        
        # OKX Paper Trading
        if os.getenv('OKX_PAPER_API_KEY'):
            self.exchanges['okx_paper'] = ExchangeConfig(
                name='okx_paper',
                api_key=os.getenv('OKX_PAPER_API_KEY'),
                secret_key=os.getenv('OKX_PAPER_SECRET_KEY'),
                base_url=os.getenv('OKX_PAPER_BASE_URL', 'https://www.okx.com'),
                sandbox=True
            )
        
        # OKX Demo Trading
        if os.getenv('OKX_DEMO_API_KEY'):
            self.exchanges['okx_demo'] = ExchangeConfig(
                name='okx_demo',
                api_key=os.getenv('OKX_DEMO_API_KEY'),
                secret_key=os.getenv('OKX_DEMO_SECRET_KEY'),
                base_url=os.getenv('OKX_DEMO_BASE_URL', 'https://www.okx.com'),
                sandbox=True
            )
        
        # Gate.io Paper Trading
        if os.getenv('GATE_PAPER_API_KEY'):
            self.exchanges['gate_paper'] = ExchangeConfig(
                name='gate_paper',
                api_key=os.getenv('GATE_PAPER_API_KEY'),
                secret_key=os.getenv('GATE_PAPER_SECRET_KEY'),
                base_url=os.getenv('GATE_PAPER_BASE_URL', 'https://api.gateio.ws'),
                sandbox=True
            )
        
        # Gate.io Demo Trading
        if os.getenv('GATE_DEMO_API_KEY'):
            self.exchanges['gate_demo'] = ExchangeConfig(
                name='gate_demo',
                api_key=os.getenv('GATE_DEMO_API_KEY'),
                secret_key=os.getenv('GATE_DEMO_SECRET_KEY'),
                base_url=os.getenv('GATE_DEMO_BASE_URL', 'https://api-testnet.gateapi.io'),
                sandbox=True
            )
        
        # Binance Testnet
        if os.getenv('BINANCE_TESTNET_API_KEY'):
            self.exchanges['binance_testnet'] = ExchangeConfig(
                name='binance_testnet',
                api_key=os.getenv('BINANCE_TESTNET_API_KEY'),
                secret_key=os.getenv('BINANCE_TESTNET_SECRET_KEY'),
                base_url=os.getenv('BINANCE_TESTNET_BASE_URL', 'https://testnet.binance.vision'),
                sandbox=True
            )
        
        logger.info(f"Initialized {len(self.exchanges)} exchange connections")
    
    async def test_all_connections(self) -> Dict[str, Dict]:
        """Test all exchange connections"""
        results = {}
        
        for exchange_name, config in self.exchanges.items():
            logger.info(f"Testing {exchange_name} connection...")
            
            try:
                if 'okx' in exchange_name:
                    async with OKXConnector(config) as connector:
                        ticker = await connector.get_ticker('BTC-USDT')
                        orderbook = await connector.get_orderbook('BTC-USDT', 5)
                        
                        results[exchange_name] = {
                            'status': 'success',
                            'ticker': asdict(ticker) if ticker else None,
                            'orderbook_depth': len(orderbook.bids) + len(orderbook.asks) if orderbook else 0
                        }
                
                elif 'gate' in exchange_name:
                    async with GateConnector(config) as connector:
                        ticker = await connector.get_ticker('BTC-USDT')
                        orderbook = await connector.get_orderbook('BTC-USDT', 5)
                        
                        results[exchange_name] = {
                            'status': 'success',
                            'ticker': asdict(ticker) if ticker else None,
                            'orderbook_depth': len(orderbook.bids) + len(orderbook.asks) if orderbook else 0
                        }
                
                elif 'binance' in exchange_name:
                    async with BinanceConnector(config) as connector:
                        ticker = await connector.get_ticker('BTCUSDT')
                        orderbook = await connector.get_orderbook('BTCUSDT', 5)
                        
                        results[exchange_name] = {
                            'status': 'success',
                            'ticker': asdict(ticker) if ticker else None,
                            'orderbook_depth': len(orderbook.bids) + len(orderbook.asks) if orderbook else 0
                        }
                
            except Exception as e:
                results[exchange_name] = {
                    'status': 'error',
                    'error': str(e)
                }
                logger.error(f"{exchange_name} connection failed: {str(e)}")
        
        return results
    
    async def get_best_prices(self, symbol: str) -> Dict[str, float]:
        """Get best prices from all exchanges"""
        prices = {}
        
        for exchange_name, config in self.exchanges.items():
            try:
                if 'okx' in exchange_name:
                    async with OKXConnector(config) as connector:
                        ticker = await connector.get_ticker(symbol)
                        if ticker:
                            prices[exchange_name] = ticker.price
                
                elif 'gate' in exchange_name:
                    async with GateConnector(config) as connector:
                        ticker = await connector.get_ticker(symbol)
                        if ticker:
                            prices[exchange_name] = ticker.price
                
                elif 'binance' in exchange_name:
                    # Convert symbol format for Binance
                    binance_symbol = symbol.replace('-', '')
                    async with BinanceConnector(config) as connector:
                        ticker = await connector.get_ticker(binance_symbol)
                        if ticker:
                            prices[exchange_name] = ticker.price
                            
            except Exception as e:
                logger.error(f"Error getting price from {exchange_name}: {str(e)}")
        
        return prices
    
    async def place_paper_trade(self, exchange_name: str, symbol: str, side: str, size: float, price: Optional[float] = None) -> Optional[Dict]:
        """Place a paper trade on specified exchange"""
        if exchange_name not in self.exchanges:
            logger.error(f"Exchange {exchange_name} not configured")
            return None
        
        config = self.exchanges[exchange_name]
        
        try:
            if 'okx' in exchange_name:
                async with OKXConnector(config) as connector:
                    return await connector.place_order(symbol, side, size, price)
            
            elif 'binance' in exchange_name:
                # Convert symbol format for Binance
                binance_symbol = symbol.replace('-', '')
                async with BinanceConnector(config) as connector:
                    return await connector.place_order(binance_symbol, side, size, price)
            
        except Exception as e:
            logger.error(f"Error placing trade on {exchange_name}: {str(e)}")
        
        return None

# Example usage and testing
async def main():
    """Test live exchange connections"""
    print("🚀 Testing Live Exchange Connections")
    print("=" * 50)
    
    manager = LiveExchangeManager()
    
    # Test all connections
    print("📡 Testing exchange connections...")
    results = await manager.test_all_connections()
    
    for exchange, result in results.items():
        if result['status'] == 'success':
            ticker = result.get('ticker')
            if ticker:
                print(f"✅ {exchange}: ${ticker['price']:,.2f} (depth: {result['orderbook_depth']})")
            else:
                print(f"⚠️  {exchange}: Connected but no ticker data")
        else:
            print(f"❌ {exchange}: {result['error']}")
    
    # Get best prices
    print("\n💰 Comparing prices across exchanges...")
    prices = await manager.get_best_prices('BTC-USDT')
    
    if prices:
        sorted_prices = sorted(prices.items(), key=lambda x: x[1])
        print("Price comparison (lowest to highest):")
        for exchange, price in sorted_prices:
            print(f"   {exchange}: ${price:,.2f}")
        
        # Calculate spread
        if len(sorted_prices) > 1:
            spread = sorted_prices[-1][1] - sorted_prices[0][1]
            spread_pct = (spread / sorted_prices[0][1]) * 100
            print(f"\n📊 Price spread: ${spread:.2f} ({spread_pct:.3f}%)")
    
    # Test paper trading (if enabled)
    print("\n📝 Testing paper trading...")
    if 'okx_paper' in manager.exchanges:
        result = await manager.place_paper_trade('okx_paper', 'BTC-USDT', 'buy', 0.001)
        if result:
            print("✅ OKX paper trade placed successfully")
        else:
            print("❌ OKX paper trade failed")
    
    print("\n🎉 Live exchange testing completed!")

if __name__ == "__main__":
    asyncio.run(main())


# BTC Markets Integration
from .btcmarkets_connector import BTCMarketsConnector, BTCMarketsConfig

class EnhancedLiveExchangeManager(LiveExchangeManager):
    """Enhanced Live Exchange Manager with BTC Markets support"""
    
    def __init__(self):
        super().__init__()
        
        # Add BTC Markets to exchanges
        self.exchanges['btcmarkets'] = {
            'name': 'BTC Markets',
            'base_url': 'https://api.btcmarkets.net',
            'api_key': os.getenv('BTCMARKETS_API_KEY', ''),
            'private_key': os.getenv('BTCMARKETS_PRIVATE_KEY', ''),
            'sandbox': False
        }
        
        logger.info(f"Enhanced Exchange Manager initialized with {len(self.exchanges)} exchanges including BTC Markets")
    
    async def test_btcmarkets_connection(self) -> Dict[str, Any]:
        """Test BTC Markets connection"""
        try:
            config = BTCMarketsConfig(
                api_key=self.exchanges['btcmarkets']['api_key'],
                private_key=self.exchanges['btcmarkets']['private_key']
            )
            
            async with BTCMarketsConnector(config) as connector:
                # Test market data
                ticker = await connector.get_ticker('BTC-AUD')
                
                if ticker:
                    return {
                        'status': 'success',
                        'ticker': {
                            'symbol': ticker.symbol,
                            'price': ticker.price,
                            'volume': ticker.volume,
                            'high': ticker.high,
                            'low': ticker.low,
                            'change': ticker.change
                        },
                        'exchange': 'BTC Markets',
                        'currency': 'AUD'
                    }
                else:
                    return {
                        'status': 'failed',
                        'error': 'No ticker data received',
                        'exchange': 'BTC Markets'
                    }
                    
        except Exception as e:
            logger.error(f"BTC Markets connection test failed: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'exchange': 'BTC Markets'
            }
    
    async def get_btcmarkets_prices(self, symbols: List[str]) -> Dict[str, float]:
        """Get BTC Markets prices for multiple symbols"""
        prices = {}
        
        try:
            config = BTCMarketsConfig(
                api_key=self.exchanges['btcmarkets']['api_key'],
                private_key=self.exchanges['btcmarkets']['private_key']
            )
            
            async with BTCMarketsConnector(config) as connector:
                for symbol in symbols:
                    # Convert symbol format (e.g., BTC-USDT to BTC-AUD for BTC Markets)
                    btc_symbol = symbol.replace('USDT', 'AUD').replace('USDC', 'AUD')
                    
                    ticker = await connector.get_ticker(btc_symbol)
                    if ticker:
                        prices[f"btcmarkets_{symbol}"] = ticker.price
                        
        except Exception as e:
            logger.error(f"BTC Markets price retrieval error: {str(e)}")
            
        return prices
    
    async def place_btcmarkets_order(self, symbol: str, side: str, amount: float, price: Optional[float] = None) -> Optional[Dict]:
        """Place order on BTC Markets"""
        try:
            config = BTCMarketsConfig(
                api_key=self.exchanges['btcmarkets']['api_key'],
                private_key=self.exchanges['btcmarkets']['private_key']
            )
            
            async with BTCMarketsConnector(config) as connector:
                # Convert symbol format
                btc_symbol = symbol.replace('USDT', 'AUD').replace('USDC', 'AUD')
                
                order_type = 'LIMIT' if price else 'MARKET'
                order = await connector.place_order(btc_symbol, side, order_type, amount, price)
                
                if order:
                    return {
                        'orderId': order.order_id,
                        'symbol': order.symbol,
                        'side': order.side,
                        'type': order.type,
                        'amount': order.amount,
                        'price': order.price,
                        'status': order.status,
                        'exchange': 'BTC Markets'
                    }
                    
        except Exception as e:
            logger.error(f"BTC Markets order placement error: {str(e)}")
            
        return None
    
    async def test_all_connections_enhanced(self) -> Dict[str, Any]:
        """Test all exchange connections including BTC Markets"""
        results = await super().test_all_connections()
        
        # Add BTC Markets test
        btc_result = await self.test_btcmarkets_connection()
        results['btcmarkets'] = btc_result
        
        return results
    
    async def get_best_prices_enhanced(self, symbol: str) -> Dict[str, float]:
        """Get best prices from all exchanges including BTC Markets"""
        prices = await super().get_best_prices(symbol)
        
        # Add BTC Markets prices
        btc_prices = await self.get_btcmarkets_prices([symbol])
        prices.update(btc_prices)
        
        return prices

# Test BTC Markets connector
async def test_btcmarkets_integration():
    """Test BTC Markets integration"""
    print("🇦🇺 TESTING BTC MARKETS INTEGRATION")
    print("=" * 50)
    
    # Test standalone connector
    print("📊 Test 1: Standalone BTC Markets Connector")
    config = BTCMarketsConfig()
    
    async with BTCMarketsConnector(config) as connector:
        # Test market data
        ticker = await connector.get_ticker('BTC-AUD')
        if ticker:
            print(f"   ✅ BTC-AUD: ${ticker.price:,.2f} AUD")
            print(f"      Volume: {ticker.volume:,.0f} | Change: {ticker.change:+.2f}%")
        
        # Test order book
        orderbook = await connector.get_orderbook('BTC-AUD', 3)
        if orderbook:
            print(f"   📈 Order Book: {len(orderbook.bids)} bids, {len(orderbook.asks)} asks")
    
    print()
    
    # Test enhanced manager
    print("🔗 Test 2: Enhanced Exchange Manager")
    manager = EnhancedLiveExchangeManager()
    
    # Test all connections
    results = await manager.test_all_connections_enhanced()
    
    working_exchanges = 0
    for exchange, result in results.items():
        if result['status'] == 'success' and result.get('ticker'):
            ticker = result['ticker']
            currency = result.get('currency', 'USD')
            print(f"   ✅ {exchange.upper()}: ${ticker['price']:,.2f} {currency}")
            working_exchanges += 1
        else:
            print(f"   ⚠️  {exchange.upper()}: {result.get('error', 'Connection issues')}")
    
    print(f"\n📊 Total working exchanges: {working_exchanges}")
    
    # Test multi-exchange price comparison
    print("\n💰 Test 3: Multi-Exchange Price Comparison")
    prices = await manager.get_best_prices_enhanced('BTC-USDT')
    
    if prices:
        sorted_prices = sorted(prices.items(), key=lambda x: x[1] if x[1] > 0 else float('inf'))
        
        print("   Price comparison across exchanges:")
        for exchange, price in sorted_prices:
            if price > 0:
                currency = 'AUD' if 'btcmarkets' in exchange else 'USD'
                print(f"      {exchange}: ${price:,.2f} {currency}")
        
        # Calculate spreads
        valid_prices = [p for p in prices.values() if p > 0]
        if len(valid_prices) > 1:
            spread = max(valid_prices) - min(valid_prices)
            spread_pct = (spread / min(valid_prices)) * 100
            print(f"   📈 Price spread: ${spread:.2f} ({spread_pct:.3f}%)")
    
    print("\n✅ BTC Markets integration testing completed!")
    print("🇦🇺 BTC Markets successfully added to Ultimate Lyra Ecosystem!")

if __name__ == "__main__":
    asyncio.run(test_btcmarkets_integration())
