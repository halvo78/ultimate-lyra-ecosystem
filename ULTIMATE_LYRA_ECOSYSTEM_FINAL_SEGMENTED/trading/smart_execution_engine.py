#!/usr/bin/env python3
"""
ULTIMATE LYRA ECOSYSTEM - SMART EXECUTION ENGINE
===============================================

Advanced execution algorithms for optimal trade execution:
- TWAP (Time-Weighted Average Price)
- VWAP (Volume-Weighted Average Price)  
- Iceberg Orders (hidden size execution)
- Smart Order Routing (best venue selection)
- Adaptive execution based on market conditions

Prevents market impact and ensures optimal fills.
"""

import asyncio
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import threading
from collections import defaultdict, deque
import random
import math

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OrderType(Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP_LOSS = "STOP_LOSS"
    TAKE_PROFIT = "TAKE_PROFIT"

class OrderStatus(Enum):
    PENDING = "PENDING"
    SUBMITTED = "SUBMITTED"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"

class ExecutionAlgorithm(Enum):
    MARKET = "MARKET"
    TWAP = "TWAP"
    VWAP = "VWAP"
    ICEBERG = "ICEBERG"
    POV = "POV"  # Percentage of Volume

@dataclass
class Order:
    """Individual order representation"""
    id: str
    symbol: str
    side: str  # BUY/SELL
    size: float
    price: Optional[float]
    order_type: OrderType
    status: OrderStatus
    exchange: str
    strategy: str
    parent_intent_id: Optional[str] = None
    created_at: str = None
    updated_at: str = None
    filled_size: float = 0.0
    avg_fill_price: float = 0.0
    fees: float = 0.0
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow().isoformat()
        self.updated_at = self.created_at

@dataclass
class ExecutionPlan:
    """Execution plan for a trading intent"""
    intent_id: str
    symbol: str
    side: str
    total_size: float
    algorithm: ExecutionAlgorithm
    exchange: str
    strategy: str
    child_orders: List[Order]
    start_time: str
    end_time: str
    max_participation_rate: float = 0.1  # Max 10% of volume
    price_limit: Optional[float] = None
    urgency: str = "normal"  # low, normal, high
    
    def __post_init__(self):
        if not self.child_orders:
            self.child_orders = []

class MarketData:
    """Market data container for execution decisions"""
    
    def __init__(self):
        self.order_books = {}
        self.trade_data = {}
        self.volume_profiles = {}
        self.last_update = {}
    
    def update_order_book(self, symbol: str, bids: List[Tuple[float, float]], 
                         asks: List[Tuple[float, float]]):
        """Update order book data"""
        self.order_books[symbol] = {
            "bids": bids,  # [(price, size), ...]
            "asks": asks,
            "timestamp": datetime.utcnow().isoformat()
        }
        self.last_update[symbol] = time.time()
    
    def update_trades(self, symbol: str, trades: List[Dict]):
        """Update recent trade data"""
        self.trade_data[symbol] = trades
        self.last_update[symbol] = time.time()
    
    def get_mid_price(self, symbol: str) -> Optional[float]:
        """Get mid price from order book"""
        book = self.order_books.get(symbol)
        if book and book["bids"] and book["asks"]:
            best_bid = book["bids"][0][0]
            best_ask = book["asks"][0][0]
            return (best_bid + best_ask) / 2
        return None
    
    def get_spread(self, symbol: str) -> Optional[float]:
        """Get bid-ask spread"""
        book = self.order_books.get(symbol)
        if book and book["bids"] and book["asks"]:
            best_bid = book["bids"][0][0]
            best_ask = book["asks"][0][0]
            return best_ask - best_bid
        return None
    
    def get_liquidity(self, symbol: str, side: str, depth: int = 5) -> float:
        """Get available liquidity on one side"""
        book = self.order_books.get(symbol)
        if not book:
            return 0.0
        
        levels = book["bids"] if side == "BUY" else book["asks"]
        total_size = sum(size for _, size in levels[:depth])
        return total_size
    
    def estimate_market_impact(self, symbol: str, side: str, size: float) -> float:
        """Estimate market impact of an order"""
        book = self.order_books.get(symbol)
        if not book:
            return 0.05  # Default 5% impact
        
        levels = book["asks"] if side == "BUY" else book["bids"]
        remaining_size = size
        total_cost = 0.0
        
        for price, available_size in levels:
            if remaining_size <= 0:
                break
            
            fill_size = min(remaining_size, available_size)
            total_cost += fill_size * price
            remaining_size -= fill_size
        
        if remaining_size > 0:
            # Not enough liquidity
            return 0.10  # 10% impact for insufficient liquidity
        
        mid_price = self.get_mid_price(symbol)
        if mid_price:
            avg_price = total_cost / size
            impact = abs(avg_price - mid_price) / mid_price
            return impact
        
        return 0.02  # Default 2% impact

class TWAPExecutor:
    """Time-Weighted Average Price execution algorithm"""
    
    def __init__(self, market_data: MarketData):
        self.market_data = market_data
    
    async def execute(self, plan: ExecutionPlan) -> List[Order]:
        """Execute TWAP algorithm"""
        logger.info(f"🕐 Starting TWAP execution for {plan.symbol} - {plan.total_size}")
        
        # Calculate time slices
        start_time = datetime.fromisoformat(plan.start_time)
        end_time = datetime.fromisoformat(plan.end_time)
        duration = (end_time - start_time).total_seconds()
        
        # Default to 10 slices, but adjust based on size and urgency
        num_slices = self._calculate_optimal_slices(plan, duration)
        slice_duration = duration / num_slices
        slice_size = plan.total_size / num_slices
        
        orders = []
        
        for i in range(num_slices):
            # Calculate timing for this slice
            slice_start = start_time + timedelta(seconds=i * slice_duration)
            
            # Adjust size based on market conditions
            adjusted_size = self._adjust_slice_size(plan, slice_size, i, num_slices)
            
            # Create order
            order = Order(
                id=f"twap_{plan.intent_id}_{i}",
                symbol=plan.symbol,
                side=plan.side,
                size=adjusted_size,
                price=None,  # Market order
                order_type=OrderType.MARKET,
                status=OrderStatus.PENDING,
                exchange=plan.exchange,
                strategy=plan.strategy,
                parent_intent_id=plan.intent_id
            )
            
            orders.append(order)
            
            # Simulate execution delay
            if i < num_slices - 1:  # Don't wait after last slice
                await asyncio.sleep(min(slice_duration, 30))  # Max 30 second slices
        
        logger.info(f"✅ TWAP execution plan created: {len(orders)} orders")
        return orders
    
    def _calculate_optimal_slices(self, plan: ExecutionPlan, duration: float) -> int:
        """Calculate optimal number of time slices"""
        base_slices = 10
        
        # Adjust based on urgency
        if plan.urgency == "high":
            base_slices = max(5, base_slices // 2)
        elif plan.urgency == "low":
            base_slices = min(20, base_slices * 2)
        
        # Adjust based on size (larger orders need more slices)
        if plan.total_size > 1.0:
            base_slices = min(30, int(base_slices * math.log(plan.total_size + 1)))
        
        # Adjust based on duration (longer duration allows more slices)
        max_slices_by_duration = max(5, int(duration / 60))  # One slice per minute minimum
        
        return min(base_slices, max_slices_by_duration)
    
    def _adjust_slice_size(self, plan: ExecutionPlan, base_size: float, 
                          slice_index: int, total_slices: int) -> float:
        """Adjust slice size based on market conditions"""
        # Start with base size
        adjusted_size = base_size
        
        # Reduce size if market impact is high
        estimated_impact = self.market_data.estimate_market_impact(
            plan.symbol, plan.side, base_size
        )
        
        if estimated_impact > 0.005:  # 0.5% impact threshold
            adjusted_size *= 0.7  # Reduce by 30%
        
        # Adjust based on available liquidity
        liquidity = self.market_data.get_liquidity(plan.symbol, plan.side)
        if liquidity > 0 and adjusted_size > liquidity * plan.max_participation_rate:
            adjusted_size = liquidity * plan.max_participation_rate
        
        # Ensure minimum order size
        adjusted_size = max(adjusted_size, 0.001)
        
        return adjusted_size

class VWAPExecutor:
    """Volume-Weighted Average Price execution algorithm"""
    
    def __init__(self, market_data: MarketData):
        self.market_data = market_data
    
    async def execute(self, plan: ExecutionPlan) -> List[Order]:
        """Execute VWAP algorithm"""
        logger.info(f"📊 Starting VWAP execution for {plan.symbol} - {plan.total_size}")
        
        # Get historical volume profile (simulated)
        volume_profile = self._get_volume_profile(plan.symbol)
        
        # Calculate volume-weighted slices
        orders = []
        remaining_size = plan.total_size
        
        for i, (time_period, volume_weight) in enumerate(volume_profile):
            if remaining_size <= 0:
                break
            
            # Calculate slice size based on volume weight
            slice_size = min(remaining_size, plan.total_size * volume_weight)
            
            # Adjust for market conditions
            adjusted_size = self._adjust_vwap_size(plan, slice_size, volume_weight)
            
            order = Order(
                id=f"vwap_{plan.intent_id}_{i}",
                symbol=plan.symbol,
                side=plan.side,
                size=adjusted_size,
                price=None,
                order_type=OrderType.MARKET,
                status=OrderStatus.PENDING,
                exchange=plan.exchange,
                strategy=plan.strategy,
                parent_intent_id=plan.intent_id
            )
            
            orders.append(order)
            remaining_size -= adjusted_size
            
            # Wait based on volume profile timing
            await asyncio.sleep(time_period)
        
        logger.info(f"✅ VWAP execution plan created: {len(orders)} orders")
        return orders
    
    def _get_volume_profile(self, symbol: str) -> List[Tuple[float, float]]:
        """Get historical volume profile (time_period, volume_weight)"""
        # Simulated volume profile - in production, use real historical data
        return [
            (30, 0.15),   # First 30 seconds - 15% of volume
            (60, 0.25),   # Next minute - 25% of volume
            (120, 0.30),  # Next 2 minutes - 30% of volume
            (180, 0.20),  # Next 3 minutes - 20% of volume
            (300, 0.10),  # Final 5 minutes - 10% of volume
        ]
    
    def _adjust_vwap_size(self, plan: ExecutionPlan, base_size: float, 
                         volume_weight: float) -> float:
        """Adjust VWAP slice size based on current market conditions"""
        adjusted_size = base_size
        
        # Adjust based on current vs expected volume
        current_liquidity = self.market_data.get_liquidity(plan.symbol, plan.side)
        expected_liquidity = 10000 * volume_weight  # Simulated expected volume
        
        if current_liquidity < expected_liquidity * 0.5:
            # Low volume period - reduce size
            adjusted_size *= 0.6
        elif current_liquidity > expected_liquidity * 1.5:
            # High volume period - can increase size
            adjusted_size *= 1.2
        
        # Respect participation rate limits
        if current_liquidity > 0:
            max_size = current_liquidity * plan.max_participation_rate
            adjusted_size = min(adjusted_size, max_size)
        
        return max(adjusted_size, 0.001)

class IcebergExecutor:
    """Iceberg order execution - hides large order size"""
    
    def __init__(self, market_data: MarketData):
        self.market_data = market_data
    
    async def execute(self, plan: ExecutionPlan) -> List[Order]:
        """Execute Iceberg algorithm"""
        logger.info(f"🧊 Starting Iceberg execution for {plan.symbol} - {plan.total_size}")
        
        # Calculate visible size (tip of iceberg)
        visible_size = self._calculate_visible_size(plan)
        
        orders = []
        remaining_size = plan.total_size
        order_count = 0
        
        while remaining_size > 0:
            # Current slice size
            current_size = min(remaining_size, visible_size)
            
            # Adjust price for limit orders
            limit_price = self._calculate_limit_price(plan, current_size)
            
            order = Order(
                id=f"iceberg_{plan.intent_id}_{order_count}",
                symbol=plan.symbol,
                side=plan.side,
                size=current_size,
                price=limit_price,
                order_type=OrderType.LIMIT,
                status=OrderStatus.PENDING,
                exchange=plan.exchange,
                strategy=plan.strategy,
                parent_intent_id=plan.intent_id
            )
            
            orders.append(order)
            remaining_size -= current_size
            order_count += 1
            
            # Wait between iceberg slices to avoid detection
            await asyncio.sleep(random.uniform(10, 30))
            
            # Adjust visible size based on market conditions
            visible_size = self._adjust_visible_size(plan, visible_size, order_count)
        
        logger.info(f"✅ Iceberg execution plan created: {len(orders)} orders")
        return orders
    
    def _calculate_visible_size(self, plan: ExecutionPlan) -> float:
        """Calculate the visible size for each iceberg slice"""
        # Base visible size as percentage of total
        base_percentage = 0.1  # 10% visible by default
        
        if plan.urgency == "high":
            base_percentage = 0.2  # More aggressive for urgent orders
        elif plan.urgency == "low":
            base_percentage = 0.05  # More hidden for patient orders
        
        visible_size = plan.total_size * base_percentage
        
        # Ensure reasonable bounds
        visible_size = max(0.001, min(visible_size, 1.0))
        
        # Adjust based on market liquidity
        liquidity = self.market_data.get_liquidity(plan.symbol, plan.side)
        if liquidity > 0:
            # Don't exceed 5% of available liquidity
            max_visible = liquidity * 0.05
            visible_size = min(visible_size, max_visible)
        
        return visible_size
    
    def _calculate_limit_price(self, plan: ExecutionPlan, size: float) -> Optional[float]:
        """Calculate limit price for iceberg order"""
        mid_price = self.market_data.get_mid_price(plan.symbol)
        if not mid_price:
            return None
        
        spread = self.market_data.get_spread(plan.symbol)
        if not spread:
            spread = mid_price * 0.001  # Default 0.1% spread
        
        # Place limit order slightly inside the spread
        if plan.side == "BUY":
            # Buy limit slightly below mid price
            limit_price = mid_price - spread * 0.3
        else:
            # Sell limit slightly above mid price
            limit_price = mid_price + spread * 0.3
        
        return round(limit_price, 8)
    
    def _adjust_visible_size(self, plan: ExecutionPlan, current_visible: float, 
                           order_count: int) -> float:
        """Adjust visible size based on execution progress"""
        # Gradually increase visible size as we progress
        progress = 1 - (plan.total_size - sum(o.size for o in plan.child_orders)) / plan.total_size
        
        # Increase visible size by up to 50% as we near completion
        size_multiplier = 1 + (progress * 0.5)
        
        adjusted_size = current_visible * size_multiplier
        
        # Add some randomness to avoid detection
        randomness = random.uniform(0.8, 1.2)
        adjusted_size *= randomness
        
        return max(0.001, adjusted_size)

class SmartOrderRouter:
    """Smart Order Router - selects best execution venue"""
    
    def __init__(self):
        self.exchange_configs = {
            "binance": {
                "fees": {"maker": 0.001, "taker": 0.001},
                "latency": 50,  # ms
                "reliability": 0.99,
                "liquidity_score": 0.95
            },
            "okx": {
                "fees": {"maker": 0.0008, "taker": 0.001},
                "latency": 60,
                "reliability": 0.98,
                "liquidity_score": 0.85
            },
            "coinbase": {
                "fees": {"maker": 0.005, "taker": 0.005},
                "latency": 80,
                "reliability": 0.99,
                "liquidity_score": 0.80
            },
            "gate": {
                "fees": {"maker": 0.002, "taker": 0.002},
                "latency": 70,
                "reliability": 0.97,
                "liquidity_score": 0.75
            }
        }
    
    def select_best_venue(self, symbol: str, side: str, size: float, 
                         urgency: str = "normal") -> str:
        """Select the best execution venue"""
        scores = {}
        
        for exchange, config in self.exchange_configs.items():
            score = self._calculate_venue_score(exchange, config, symbol, side, size, urgency)
            scores[exchange] = score
        
        best_venue = max(scores, key=scores.get)
        logger.info(f"🎯 Best venue for {symbol}: {best_venue} (score: {scores[best_venue]:.3f})")
        
        return best_venue
    
    def _calculate_venue_score(self, exchange: str, config: Dict, symbol: str, 
                              side: str, size: float, urgency: str) -> float:
        """Calculate venue score based on multiple factors"""
        score = 0.0
        
        # Liquidity score (40% weight)
        score += config["liquidity_score"] * 0.4
        
        # Fee score (25% weight) - lower fees = higher score
        fee = config["fees"]["taker"]  # Assume taker for market orders
        fee_score = max(0, 1 - fee * 200)  # Normalize fee impact
        score += fee_score * 0.25
        
        # Latency score (20% weight) - lower latency = higher score
        latency_score = max(0, 1 - config["latency"] / 200)
        if urgency == "high":
            score += latency_score * 0.35  # Higher weight for urgent orders
        else:
            score += latency_score * 0.20
        
        # Reliability score (15% weight)
        score += config["reliability"] * 0.15
        
        # Size-specific adjustments
        if size > 1.0:  # Large orders prefer high liquidity venues
            score += config["liquidity_score"] * 0.1
        
        return score

class SmartExecutionEngine:
    """Main execution engine that coordinates all execution algorithms"""
    
    def __init__(self):
        self.market_data = MarketData()
        self.order_router = SmartOrderRouter()
        self.twap_executor = TWAPExecutor(self.market_data)
        self.vwap_executor = VWAPExecutor(self.market_data)
        self.iceberg_executor = IcebergExecutor(self.market_data)
        
        self.active_plans = {}
        self.completed_orders = []
        self.performance_metrics = {}
        
        # Initialize with mock market data
        self._initialize_mock_data()
        
        logger.info("🚀 Smart Execution Engine initialized")
    
    def _initialize_mock_data(self):
        """Initialize with mock market data for testing"""
        symbols = ["BTCUSDT", "ETHUSDT", "ADAUSDT", "SOLUSDT"]
        
        for symbol in symbols:
            # Mock order book
            mid_price = {"BTCUSDT": 45000, "ETHUSDT": 3000, "ADAUSDT": 0.5, "SOLUSDT": 100}[symbol]
            spread = mid_price * 0.001
            
            bids = [(mid_price - spread/2 - i*spread*0.1, random.uniform(1, 10)) for i in range(10)]
            asks = [(mid_price + spread/2 + i*spread*0.1, random.uniform(1, 10)) for i in range(10)]
            
            self.market_data.update_order_book(symbol, bids, asks)
    
    async def create_execution_plan(self, child_orders: List[Dict], 
                                   algorithm: str = "auto") -> ExecutionPlan:
        """Create an execution plan from child orders"""
        if not child_orders:
            raise ValueError("No child orders provided")
        
        # Aggregate order information
        first_order = child_orders[0]
        total_size = sum(order.get("size", 0) for order in child_orders)
        
        # Auto-select algorithm if not specified
        if algorithm == "auto":
            algorithm = self._select_optimal_algorithm(
                first_order["symbol"], 
                first_order["side"], 
                total_size
            )
        
        # Select best venue
        best_venue = self.order_router.select_best_venue(
            first_order["symbol"],
            first_order["side"],
            total_size,
            first_order.get("urgency", "normal")
        )
        
        # Create execution plan
        plan = ExecutionPlan(
            intent_id=first_order.get("parent_intent_id", f"plan_{int(time.time())}"),
            symbol=first_order["symbol"],
            side=first_order["side"],
            total_size=total_size,
            algorithm=ExecutionAlgorithm(algorithm.upper()),
            exchange=best_venue,
            strategy=first_order.get("strategy", "unknown"),
            child_orders=[],
            start_time=datetime.utcnow().isoformat(),
            end_time=(datetime.utcnow() + timedelta(minutes=10)).isoformat(),
            urgency=first_order.get("urgency", "normal")
        )
        
        return plan
    
    def _select_optimal_algorithm(self, symbol: str, side: str, size: float) -> str:
        """Auto-select the best execution algorithm"""
        # Get market conditions
        liquidity = self.market_data.get_liquidity(symbol, side)
        estimated_impact = self.market_data.estimate_market_impact(symbol, side, size)
        
        # Algorithm selection logic
        if size < 0.1:
            # Small orders - use market execution
            return "market"
        elif estimated_impact > 0.01:
            # High impact orders - use iceberg to hide size
            return "iceberg"
        elif liquidity > size * 20:
            # Good liquidity - use VWAP for optimal execution
            return "vwap"
        else:
            # Default to TWAP for time-based execution
            return "twap"
    
    async def execute_plan(self, plan: ExecutionPlan) -> List[Order]:
        """Execute a trading plan using the specified algorithm"""
        logger.info(f"🎯 Executing plan: {plan.algorithm.value} for {plan.symbol}")
        
        self.active_plans[plan.intent_id] = plan
        
        try:
            # Execute based on algorithm
            if plan.algorithm == ExecutionAlgorithm.TWAP:
                orders = await self.twap_executor.execute(plan)
            elif plan.algorithm == ExecutionAlgorithm.VWAP:
                orders = await self.vwap_executor.execute(plan)
            elif plan.algorithm == ExecutionAlgorithm.ICEBERG:
                orders = await self.iceberg_executor.execute(plan)
            else:
                # Market execution
                orders = await self._execute_market_orders(plan)
            
            # Update plan with generated orders
            plan.child_orders = orders
            
            # Simulate order execution
            for order in orders:
                await self._simulate_order_execution(order)
            
            # Update performance metrics
            self._update_performance_metrics(plan, orders)
            
            logger.info(f"✅ Plan execution completed: {len(orders)} orders")
            return orders
            
        except Exception as e:
            logger.error(f"❌ Plan execution failed: {str(e)}")
            raise e
        finally:
            # Move to completed
            if plan.intent_id in self.active_plans:
                del self.active_plans[plan.intent_id]
    
    async def _execute_market_orders(self, plan: ExecutionPlan) -> List[Order]:
        """Execute simple market orders"""
        order = Order(
            id=f"market_{plan.intent_id}",
            symbol=plan.symbol,
            side=plan.side,
            size=plan.total_size,
            price=None,
            order_type=OrderType.MARKET,
            status=OrderStatus.PENDING,
            exchange=plan.exchange,
            strategy=plan.strategy,
            parent_intent_id=plan.intent_id
        )
        
        return [order]
    
    async def _simulate_order_execution(self, order: Order):
        """Simulate order execution with realistic fills"""
        logger.info(f"📤 Submitting order: {order.id} - {order.side} {order.size} {order.symbol}")
        
        order.status = OrderStatus.SUBMITTED
        order.updated_at = datetime.utcnow().isoformat()
        
        # Simulate execution delay
        await asyncio.sleep(random.uniform(0.1, 2.0))
        
        # Simulate fill
        mid_price = self.market_data.get_mid_price(order.symbol)
        if mid_price:
            # Add some slippage
            slippage = random.uniform(-0.001, 0.001)  # ±0.1% slippage
            fill_price = mid_price * (1 + slippage)
            
            order.status = OrderStatus.FILLED
            order.filled_size = order.size
            order.avg_fill_price = fill_price
            order.fees = order.size * fill_price * 0.001  # 0.1% fee
            order.updated_at = datetime.utcnow().isoformat()
            
            logger.info(f"✅ Order filled: {order.id} at {fill_price:.2f}")
        else:
            order.status = OrderStatus.REJECTED
            logger.warning(f"❌ Order rejected: {order.id} - no market data")
        
        self.completed_orders.append(order)
    
    def _update_performance_metrics(self, plan: ExecutionPlan, orders: List[Order]):
        """Update execution performance metrics"""
        filled_orders = [o for o in orders if o.status == OrderStatus.FILLED]
        
        if filled_orders:
            total_filled_size = sum(o.filled_size for o in filled_orders)
            total_cost = sum(o.filled_size * o.avg_fill_price for o in filled_orders)
            avg_price = total_cost / total_filled_size if total_filled_size > 0 else 0
            total_fees = sum(o.fees for o in filled_orders)
            
            # Calculate VWAP
            vwap = avg_price
            
            # Estimate slippage vs mid price
            mid_price = self.market_data.get_mid_price(plan.symbol)
            slippage = abs(avg_price - mid_price) / mid_price if mid_price else 0
            
            metrics = {
                "plan_id": plan.intent_id,
                "symbol": plan.symbol,
                "algorithm": plan.algorithm.value,
                "total_size": plan.total_size,
                "filled_size": total_filled_size,
                "fill_rate": total_filled_size / plan.total_size,
                "avg_price": avg_price,
                "vwap": vwap,
                "slippage": slippage,
                "total_fees": total_fees,
                "num_orders": len(orders),
                "execution_time": (datetime.utcnow() - datetime.fromisoformat(plan.start_time)).total_seconds(),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            self.performance_metrics[plan.intent_id] = metrics
    
    def get_performance_summary(self) -> Dict:
        """Get execution performance summary"""
        if not self.performance_metrics:
            return {"message": "No execution data available"}
        
        metrics_list = list(self.performance_metrics.values())
        
        return {
            "total_executions": len(metrics_list),
            "avg_fill_rate": sum(m["fill_rate"] for m in metrics_list) / len(metrics_list),
            "avg_slippage": sum(m["slippage"] for m in metrics_list) / len(metrics_list),
            "total_fees": sum(m["total_fees"] for m in metrics_list),
            "avg_execution_time": sum(m["execution_time"] for m in metrics_list) / len(metrics_list),
            "algorithms_used": list(set(m["algorithm"] for m in metrics_list)),
            "last_update": datetime.utcnow().isoformat()
        }

# Example usage and testing
async def main():
    """Example usage of the Smart Execution Engine"""
    engine = SmartExecutionEngine()
    
    # Test execution plan creation and execution
    test_child_orders = [
        {
            "symbol": "BTCUSDT",
            "side": "BUY",
            "size": 0.5,
            "strategy": "SMC_X",
            "parent_intent_id": "test_intent_1",
            "urgency": "normal"
        }
    ]
    
    print("🚀 Testing Smart Execution Engine")
    print("=" * 50)
    
    # Create execution plan
    plan = await engine.create_execution_plan(test_child_orders, algorithm="auto")
    print(f"\n📋 Execution Plan Created:")
    print(f"   Algorithm: {plan.algorithm.value}")
    print(f"   Exchange: {plan.exchange}")
    print(f"   Total Size: {plan.total_size}")
    print(f"   Symbol: {plan.symbol}")
    
    # Execute plan
    orders = await engine.execute_plan(plan)
    print(f"\n📤 Orders Executed: {len(orders)}")
    
    for order in orders:
        print(f"   Order {order.id}: {order.status.value}")
        if order.status == OrderStatus.FILLED:
            print(f"      Filled: {order.filled_size} at {order.avg_fill_price:.2f}")
            print(f"      Fees: {order.fees:.4f}")
    
    # Performance summary
    print(f"\n📊 Performance Summary:")
    summary = engine.get_performance_summary()
    for key, value in summary.items():
        if isinstance(value, float):
            print(f"   {key}: {value:.4f}")
        else:
            print(f"   {key}: {value}")

if __name__ == "__main__":
    asyncio.run(main())
