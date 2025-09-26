#!/usr/bin/env python3
"""
ULTIMATE LYRA ECOSYSTEM - SHADOW EXECUTOR
=========================================

The Shadow Executor mirrors every live intent into a no-risk shadow path,
runs full diffing, and proves parity before promotion. This is the safest
bridge from paper to real APIs across all exchanges.

Features:
- Risk-free order mirroring
- Field-level diff analysis
- Parity rate calculation
- Statistical validation
- Comprehensive logging
"""

import asyncio
import json
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import hashlib
import statistics

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OrderSide(Enum):
    BUY = "BUY"
    SELL = "SELL"

class OrderType(Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"
    STOP_LIMIT = "STOP_LIMIT"

class TimeInForce(Enum):
    GTC = "GTC"  # Good Till Cancelled
    IOC = "IOC"  # Immediate Or Cancel
    FOK = "FOK"  # Fill Or Kill

@dataclass
class Intent:
    """Trading intent from AI Orchestra Conductor"""
    id: str
    timestamp: str
    strategy: str
    symbol: str
    side: str
    size_hint: float
    timeframe: str
    confidence: float
    constraints: Dict[str, Any]
    venue_hint: Optional[str] = None
    urgency: str = "normal"

@dataclass
class ShadowOrder:
    """Shadow order generated from intent"""
    venue: str
    symbol: str
    side: str
    qty: float
    price: Optional[float]
    order_type: str
    post_only: bool
    time_in_force: str
    client_order_id: str
    timestamp: str
    intent_id: str
    shadow_id: str

@dataclass
class RealOrder:
    """Real order from execution engine"""
    venue: str
    symbol: str
    side: str
    qty: float
    price: Optional[float]
    order_type: str
    post_only: bool
    time_in_force: str
    client_order_id: str
    timestamp: str

@dataclass
class OrderDiff:
    """Difference between shadow and real order"""
    field: str
    shadow_value: Any
    real_value: Any
    match: bool
    tolerance_met: bool
    severity: str  # "CRITICAL", "WARNING", "INFO"

@dataclass
class ParityResult:
    """Result of shadow vs real order comparison"""
    shadow_order: ShadowOrder
    real_order: RealOrder
    diffs: List[OrderDiff]
    parity_ok: bool
    parity_score: float
    critical_mismatches: int
    warning_mismatches: int

@dataclass
class MirrorRequest:
    """Request to mirror an intent"""
    intent: Intent
    real_orders: List[RealOrder]

@dataclass
class MirrorResponse:
    """Response from mirroring operation"""
    shadow_orders: List[ShadowOrder]
    parity_results: List[ParityResult]
    overall_parity_rate: float
    critical_violations: int
    recommendations: List[str]
    timestamp: str

class ShadowOrderGenerator:
    """Generates shadow orders from trading intents"""
    
    def __init__(self):
        self.venue_configs = {
            "BINANCE": {
                "min_qty": 0.00001,
                "price_precision": 2,
                "qty_precision": 6,
                "tick_size": 0.01
            },
            "OKX": {
                "min_qty": 0.00001,
                "price_precision": 2,
                "qty_precision": 6,
                "tick_size": 0.01
            },
            "GATE": {
                "min_qty": 0.00001,
                "price_precision": 2,
                "qty_precision": 6,
                "tick_size": 0.01
            },
            "BTCMARKETS": {
                "min_qty": 0.00001,
                "price_precision": 2,
                "qty_precision": 6,
                "tick_size": 0.01
            }
        }
        
        # Simulated market data for price calculation
        self.market_prices = {
            "BTC-USDT": 109500.00,
            "ETH-USDT": 3850.00,
            "ADA-USDT": 0.85,
            "SOL-USDT": 220.00,
            "DOGE-USDT": 0.32
        }
    
    def make_shadow_orders(self, intent: Intent, venue_hint: str) -> List[ShadowOrder]:
        """Generate shadow orders from intent"""
        try:
            # Determine venue
            venue = self._determine_venue(intent, venue_hint)
            
            # Get venue config
            config = self.venue_configs.get(venue, self.venue_configs["BINANCE"])
            
            # Calculate order parameters
            orders = []
            
            # Strategy-specific order generation
            if intent.strategy in ["TWAP", "twap"]:
                orders = self._generate_twap_orders(intent, venue, config)
            elif intent.strategy in ["VWAP", "vwap"]:
                orders = self._generate_vwap_orders(intent, venue, config)
            elif intent.strategy in ["ICEBERG", "iceberg"]:
                orders = self._generate_iceberg_orders(intent, venue, config)
            else:
                # Default single order
                orders = self._generate_single_order(intent, venue, config)
            
            return orders
            
        except Exception as e:
            logger.error(f"Error generating shadow orders: {e}")
            return []
    
    def _determine_venue(self, intent: Intent, venue_hint: str) -> str:
        """Determine the best venue for the intent"""
        if venue_hint:
            return venue_hint.upper()
        
        # Simple venue selection logic
        if intent.symbol.endswith("USDT"):
            return "BINANCE"
        elif intent.symbol.endswith("USD"):
            return "COINBASE"
        else:
            return "BINANCE"  # Default
    
    def _generate_single_order(self, intent: Intent, venue: str, config: Dict) -> List[ShadowOrder]:
        """Generate a single shadow order"""
        # Calculate price
        market_price = self.market_prices.get(intent.symbol, 50000.0)
        
        # Adjust price based on side and constraints
        if intent.side.upper() == "BUY":
            # For buy orders, place slightly below market for better fill
            price = market_price * 0.999
        else:
            # For sell orders, place slightly above market
            price = market_price * 1.001
        
        # Round price to venue precision
        price = round(price, config["price_precision"])
        
        # Calculate quantity
        qty = intent.size_hint
        qty = max(qty, config["min_qty"])
        qty = round(qty, config["qty_precision"])
        
        # Determine order type
        order_type = "LIMIT"
        post_only = intent.constraints.get("post_only", True)
        
        # Generate shadow order
        shadow_order = ShadowOrder(
            venue=venue,
            symbol=intent.symbol,
            side=intent.side.upper(),
            qty=qty,
            price=price,
            order_type=order_type,
            post_only=post_only,
            time_in_force="GTC",
            client_order_id=f"shadow_{intent.id}_{int(time.time())}",
            timestamp=datetime.utcnow().isoformat(),
            intent_id=intent.id,
            shadow_id=self._generate_shadow_id(intent)
        )
        
        return [shadow_order]
    
    def _generate_twap_orders(self, intent: Intent, venue: str, config: Dict) -> List[ShadowOrder]:
        """Generate TWAP (Time Weighted Average Price) shadow orders"""
        # Split into 4 child orders for TWAP
        num_orders = 4
        child_qty = intent.size_hint / num_orders
        child_qty = max(child_qty, config["min_qty"])
        child_qty = round(child_qty, config["qty_precision"])
        
        market_price = self.market_prices.get(intent.symbol, 50000.0)
        orders = []
        
        for i in range(num_orders):
            # Stagger prices slightly for TWAP
            price_adjustment = 1.0 + (i - num_orders/2) * 0.0005  # ±0.05% spread
            price = market_price * price_adjustment
            price = round(price, config["price_precision"])
            
            shadow_order = ShadowOrder(
                venue=venue,
                symbol=intent.symbol,
                side=intent.side.upper(),
                qty=child_qty,
                price=price,
                order_type="LIMIT",
                post_only=True,
                time_in_force="GTC",
                client_order_id=f"twap_{intent.id}_{i}_{int(time.time())}",
                timestamp=datetime.utcnow().isoformat(),
                intent_id=intent.id,
                shadow_id=f"{self._generate_shadow_id(intent)}_twap_{i}"
            )
            
            orders.append(shadow_order)
        
        return orders
    
    def _generate_vwap_orders(self, intent: Intent, venue: str, config: Dict) -> List[ShadowOrder]:
        """Generate VWAP (Volume Weighted Average Price) shadow orders"""
        # VWAP with volume-based sizing
        volume_buckets = [0.4, 0.3, 0.2, 0.1]  # Decreasing size
        market_price = self.market_prices.get(intent.symbol, 50000.0)
        orders = []
        
        for i, volume_weight in enumerate(volume_buckets):
            child_qty = intent.size_hint * volume_weight
            child_qty = max(child_qty, config["min_qty"])
            child_qty = round(child_qty, config["qty_precision"])
            
            # Price based on volume weight (larger orders get better prices)
            price_adjustment = 1.0 - (volume_weight - 0.25) * 0.001
            price = market_price * price_adjustment
            price = round(price, config["price_precision"])
            
            shadow_order = ShadowOrder(
                venue=venue,
                symbol=intent.symbol,
                side=intent.side.upper(),
                qty=child_qty,
                price=price,
                order_type="LIMIT",
                post_only=True,
                time_in_force="GTC",
                client_order_id=f"vwap_{intent.id}_{i}_{int(time.time())}",
                timestamp=datetime.utcnow().isoformat(),
                intent_id=intent.id,
                shadow_id=f"{self._generate_shadow_id(intent)}_vwap_{i}"
            )
            
            orders.append(shadow_order)
        
        return orders
    
    def _generate_iceberg_orders(self, intent: Intent, venue: str, config: Dict) -> List[ShadowOrder]:
        """Generate Iceberg shadow orders"""
        # Iceberg with hidden quantity
        visible_qty = intent.size_hint * 0.2  # Show only 20% of total
        visible_qty = max(visible_qty, config["min_qty"])
        visible_qty = round(visible_qty, config["qty_precision"])
        
        market_price = self.market_prices.get(intent.symbol, 50000.0)
        
        # Single iceberg order
        shadow_order = ShadowOrder(
            venue=venue,
            symbol=intent.symbol,
            side=intent.side.upper(),
            qty=visible_qty,
            price=round(market_price * 0.9995, config["price_precision"]),
            order_type="LIMIT",
            post_only=True,
            time_in_force="GTC",
            client_order_id=f"iceberg_{intent.id}_{int(time.time())}",
            timestamp=datetime.utcnow().isoformat(),
            intent_id=intent.id,
            shadow_id=f"{self._generate_shadow_id(intent)}_iceberg"
        )
        
        return [shadow_order]
    
    def _generate_shadow_id(self, intent: Intent) -> str:
        """Generate unique shadow ID"""
        data = f"{intent.id}_{intent.timestamp}_{intent.strategy}_{intent.symbol}"
        return hashlib.md5(data.encode()).hexdigest()[:16]

class ShadowDiffEngine:
    """Compares shadow orders with real orders"""
    
    def __init__(self):
        self.critical_fields = ["venue", "symbol", "side", "order_type"]
        self.warning_fields = ["qty", "price", "post_only", "time_in_force"]
        self.info_fields = ["client_order_id", "timestamp"]
        
        # Tolerance settings
        self.tolerances = {
            "qty": 0.001,  # 0.1% tolerance
            "price": 0.005,  # 0.5% tolerance
        }
    
    def diff_shadow_vs_real(self, shadow_order: ShadowOrder, real_order: RealOrder) -> ParityResult:
        """Compare shadow order with real order"""
        diffs = []
        critical_mismatches = 0
        warning_mismatches = 0
        
        # Compare all fields
        shadow_dict = asdict(shadow_order)
        real_dict = asdict(real_order)
        
        # Only compare common fields
        common_fields = set(shadow_dict.keys()) & set(real_dict.keys())
        
        for field in common_fields:
            shadow_value = shadow_dict[field]
            real_value = real_dict[field]
            
            # Determine match and tolerance
            match = shadow_value == real_value
            tolerance_met = self._check_tolerance(field, shadow_value, real_value)
            
            # Determine severity
            if field in self.critical_fields:
                severity = "CRITICAL"
                if not match and not tolerance_met:
                    critical_mismatches += 1
            elif field in self.warning_fields:
                severity = "WARNING"
                if not match and not tolerance_met:
                    warning_mismatches += 1
            else:
                severity = "INFO"
            
            diff = OrderDiff(
                field=field,
                shadow_value=shadow_value,
                real_value=real_value,
                match=match,
                tolerance_met=tolerance_met,
                severity=severity
            )
            
            diffs.append(diff)
        
        # Calculate parity
        total_important_fields = len(self.critical_fields) + len(self.warning_fields)
        matching_important = sum(1 for d in diffs 
                               if d.field in (self.critical_fields + self.warning_fields) 
                               and (d.match or d.tolerance_met))
        
        parity_score = matching_important / total_important_fields if total_important_fields > 0 else 0.0
        parity_ok = critical_mismatches == 0 and warning_mismatches <= 1
        
        return ParityResult(
            shadow_order=shadow_order,
            real_order=real_order,
            diffs=diffs,
            parity_ok=parity_ok,
            parity_score=parity_score,
            critical_mismatches=critical_mismatches,
            warning_mismatches=warning_mismatches
        )
    
    def _check_tolerance(self, field: str, shadow_value: Any, real_value: Any) -> bool:
        """Check if values are within acceptable tolerance"""
        if field not in self.tolerances:
            return shadow_value == real_value
        
        tolerance = self.tolerances[field]
        
        try:
            if isinstance(shadow_value, (int, float)) and isinstance(real_value, (int, float)):
                if shadow_value == 0 and real_value == 0:
                    return True
                if shadow_value == 0 or real_value == 0:
                    return abs(shadow_value - real_value) <= tolerance
                
                relative_diff = abs(shadow_value - real_value) / max(abs(shadow_value), abs(real_value))
                return relative_diff <= tolerance
        except (TypeError, ZeroDivisionError):
            pass
        
        return shadow_value == real_value

class ShadowExecutor:
    """Main Shadow Executor service"""
    
    def __init__(self):
        self.generator = ShadowOrderGenerator()
        self.diff_engine = ShadowDiffEngine()
        self.execution_history = []
        self.parity_stats = {
            "total_mirrors": 0,
            "successful_mirrors": 0,
            "critical_violations": 0,
            "parity_rates": []
        }
    
    async def mirror_intent(self, request: MirrorRequest) -> MirrorResponse:
        """Mirror an intent and compare with real orders"""
        try:
            start_time = time.time()
            
            # Generate shadow orders
            venue_hint = self._infer_venue_hint(request.intent)
            shadow_orders = self.generator.make_shadow_orders(request.intent, venue_hint)
            
            # Compare with real orders
            parity_results = []
            critical_violations = 0
            
            # Pair shadow and real orders
            for i in range(min(len(shadow_orders), len(request.real_orders))):
                shadow_order = shadow_orders[i]
                real_order = request.real_orders[i]
                
                parity_result = self.diff_engine.diff_shadow_vs_real(shadow_order, real_order)
                parity_results.append(parity_result)
                
                if parity_result.critical_mismatches > 0:
                    critical_violations += 1
            
            # Handle count mismatches
            if len(shadow_orders) != len(request.real_orders):
                logger.warning(f"Order count mismatch: shadow={len(shadow_orders)}, real={len(request.real_orders)}")
                critical_violations += 1
            
            # Calculate overall parity rate
            if parity_results:
                overall_parity_rate = sum(r.parity_score for r in parity_results) / len(parity_results)
            else:
                overall_parity_rate = 0.0
            
            # Generate recommendations
            recommendations = self._generate_recommendations(parity_results, critical_violations)
            
            # Update statistics
            self._update_stats(overall_parity_rate, critical_violations)
            
            # Create response
            response = MirrorResponse(
                shadow_orders=shadow_orders,
                parity_results=parity_results,
                overall_parity_rate=overall_parity_rate,
                critical_violations=critical_violations,
                recommendations=recommendations,
                timestamp=datetime.utcnow().isoformat()
            )
            
            # Log execution
            execution_time = time.time() - start_time
            self._log_execution(request, response, execution_time)
            
            return response
            
        except Exception as e:
            logger.error(f"Error in mirror_intent: {e}")
            return MirrorResponse(
                shadow_orders=[],
                parity_results=[],
                overall_parity_rate=0.0,
                critical_violations=1,
                recommendations=[f"Error: {str(e)}"],
                timestamp=datetime.utcnow().isoformat()
            )
    
    def _infer_venue_hint(self, intent: Intent) -> str:
        """Infer venue from intent"""
        if intent.venue_hint:
            return intent.venue_hint
        
        if intent.symbol.endswith("USDT"):
            return "BINANCE"
        elif intent.symbol.endswith("USD"):
            return "COINBASE"
        else:
            return "BINANCE"
    
    def _generate_recommendations(self, parity_results: List[ParityResult], critical_violations: int) -> List[str]:
        """Generate recommendations based on parity analysis"""
        recommendations = []
        
        if critical_violations > 0:
            recommendations.append("🚨 CRITICAL: Do not promote to live trading - critical field mismatches detected")
            recommendations.append("🔧 Review execution engine logic for symbol, side, venue, or order type generation")
        
        if parity_results:
            avg_parity = sum(r.parity_score for r in parity_results) / len(parity_results)
            
            if avg_parity < 0.8:
                recommendations.append("⚠️ WARNING: Low parity score - review order generation logic")
            elif avg_parity < 0.95:
                recommendations.append("📊 INFO: Good parity but room for improvement")
            else:
                recommendations.append("✅ EXCELLENT: High parity score - ready for promotion consideration")
        
        # Check for common issues
        qty_mismatches = sum(1 for r in parity_results for d in r.diffs if d.field == "qty" and not d.tolerance_met)
        if qty_mismatches > 0:
            recommendations.append(f"📏 Quantity precision issue detected in {qty_mismatches} orders")
        
        price_mismatches = sum(1 for r in parity_results for d in r.diffs if d.field == "price" and not d.tolerance_met)
        if price_mismatches > 0:
            recommendations.append(f"💰 Price calculation issue detected in {price_mismatches} orders")
        
        return recommendations
    
    def _update_stats(self, parity_rate: float, critical_violations: int):
        """Update parity statistics"""
        self.parity_stats["total_mirrors"] += 1
        if critical_violations == 0:
            self.parity_stats["successful_mirrors"] += 1
        else:
            self.parity_stats["critical_violations"] += critical_violations
        
        self.parity_stats["parity_rates"].append(parity_rate)
        
        # Keep only last 1000 rates for memory efficiency
        if len(self.parity_stats["parity_rates"]) > 1000:
            self.parity_stats["parity_rates"] = self.parity_stats["parity_rates"][-1000:]
    
    def _log_execution(self, request: MirrorRequest, response: MirrorResponse, execution_time: float):
        """Log execution details"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "intent_id": request.intent.id,
            "strategy": request.intent.strategy,
            "symbol": request.intent.symbol,
            "shadow_orders_count": len(response.shadow_orders),
            "real_orders_count": len(request.real_orders),
            "parity_rate": response.overall_parity_rate,
            "critical_violations": response.critical_violations,
            "execution_time_ms": execution_time * 1000,
            "recommendations_count": len(response.recommendations)
        }
        
        self.execution_history.append(log_entry)
        
        # Keep only last 10000 entries
        if len(self.execution_history) > 10000:
            self.execution_history = self.execution_history[-10000:]
        
        logger.info(f"Shadow execution: {log_entry}")
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get health status of Shadow Executor"""
        if self.parity_stats["parity_rates"]:
            avg_parity = statistics.mean(self.parity_stats["parity_rates"])
            min_parity = min(self.parity_stats["parity_rates"])
            max_parity = max(self.parity_stats["parity_rates"])
        else:
            avg_parity = min_parity = max_parity = 0.0
        
        success_rate = (self.parity_stats["successful_mirrors"] / 
                       max(1, self.parity_stats["total_mirrors"])) * 100
        
        return {
            "status": "healthy",
            "service": "shadow-executor",
            "uptime_seconds": time.time(),
            "statistics": {
                "total_mirrors": self.parity_stats["total_mirrors"],
                "successful_mirrors": self.parity_stats["successful_mirrors"],
                "success_rate_pct": success_rate,
                "critical_violations": self.parity_stats["critical_violations"],
                "average_parity_rate": avg_parity,
                "parity_range": [min_parity, max_parity],
                "recent_executions": len(self.execution_history)
            },
            "recommendations": {
                "ready_for_promotion": success_rate > 95 and avg_parity > 0.95,
                "needs_review": self.parity_stats["critical_violations"] > 0,
                "performance_good": avg_parity > 0.8
            }
        }

# Global shadow executor instance
shadow_executor = ShadowExecutor()

async def run_shadow_executor_demo():
    """Demonstrate the Shadow Executor with sample data"""
    print("🔮 ULTIMATE LYRA ECOSYSTEM - SHADOW EXECUTOR DEMO")
    print("=" * 70)
    print("🎯 Risk-free order mirroring and parity validation")
    print("📊 Statistical analysis of execution engine accuracy")
    print("🛡️ Safety bridge from paper to live trading")
    print("=" * 70)
    print()
    
    # Create sample intent
    sample_intent = Intent(
        id="intent_001",
        timestamp=datetime.utcnow().isoformat(),
        strategy="TWAP",
        symbol="BTC-USDT",
        side="BUY",
        size_hint=0.5,
        timeframe="5m",
        confidence=0.85,
        constraints={
            "max_slippage_bps": 15,
            "deadline_ms": 30000,
            "post_only": True
        },
        venue_hint="BINANCE"
    )
    
    # Create sample real orders (simulating execution engine output)
    real_orders = [
        RealOrder(
            venue="BINANCE",
            symbol="BTC-USDT",
            side="BUY",
            qty=0.125,
            price=109450.00,
            order_type="LIMIT",
            post_only=True,
            time_in_force="GTC",
            client_order_id="real_001_0",
            timestamp=datetime.utcnow().isoformat()
        ),
        RealOrder(
            venue="BINANCE",
            symbol="BTC-USDT",
            side="BUY",
            qty=0.125,
            price=109475.00,
            order_type="LIMIT",
            post_only=True,
            time_in_force="GTC",
            client_order_id="real_001_1",
            timestamp=datetime.utcnow().isoformat()
        ),
        RealOrder(
            venue="BINANCE",
            symbol="BTC-USDT",
            side="BUY",
            qty=0.125,
            price=109500.00,
            order_type="LIMIT",
            post_only=True,
            time_in_force="GTC",
            client_order_id="real_001_2",
            timestamp=datetime.utcnow().isoformat()
        ),
        RealOrder(
            venue="BINANCE",
            symbol="BTC-USDT",
            side="BUY",
            qty=0.125,
            price=109525.00,
            order_type="LIMIT",
            post_only=True,
            time_in_force="GTC",
            client_order_id="real_001_3",
            timestamp=datetime.utcnow().isoformat()
        )
    ]
    
    # Create mirror request
    request = MirrorRequest(
        intent=sample_intent,
        real_orders=real_orders
    )
    
    print("📋 SAMPLE INTENT:")
    print(f"   Strategy: {sample_intent.strategy}")
    print(f"   Symbol: {sample_intent.symbol}")
    print(f"   Side: {sample_intent.side}")
    print(f"   Size: {sample_intent.size_hint}")
    print(f"   Confidence: {sample_intent.confidence}")
    print()
    
    print("📋 REAL ORDERS FROM EXECUTION ENGINE:")
    for i, order in enumerate(real_orders):
        print(f"   Order {i+1}: {order.qty} {order.symbol} @ ${order.price}")
    print()
    
    # Execute shadow mirroring
    print("🔮 EXECUTING SHADOW MIRRORING...")
    response = await shadow_executor.mirror_intent(request)
    
    print(f"✅ SHADOW EXECUTION COMPLETE!")
    print(f"   Shadow Orders Generated: {len(response.shadow_orders)}")
    print(f"   Overall Parity Rate: {response.overall_parity_rate:.2%}")
    print(f"   Critical Violations: {response.critical_violations}")
    print()
    
    print("🔮 SHADOW ORDERS GENERATED:")
    for i, shadow in enumerate(response.shadow_orders):
        print(f"   Shadow {i+1}: {shadow.qty} {shadow.symbol} @ ${shadow.price}")
        print(f"              Type: {shadow.order_type} | Post-Only: {shadow.post_only}")
    print()
    
    print("📊 PARITY ANALYSIS:")
    for i, result in enumerate(response.parity_results):
        print(f"   Pair {i+1}: Parity Score {result.parity_score:.2%}")
        print(f"           Critical Mismatches: {result.critical_mismatches}")
        print(f"           Warning Mismatches: {result.warning_mismatches}")
        
        # Show key differences
        key_diffs = [d for d in result.diffs if not d.match and d.severity in ["CRITICAL", "WARNING"]]
        if key_diffs:
            for diff in key_diffs[:3]:  # Show first 3 differences
                print(f"           {diff.severity}: {diff.field} - Shadow: {diff.shadow_value}, Real: {diff.real_value}")
        print()
    
    print("💡 RECOMMENDATIONS:")
    for rec in response.recommendations:
        print(f"   {rec}")
    print()
    
    # Show health status
    health = shadow_executor.get_health_status()
    print("🏥 SHADOW EXECUTOR HEALTH:")
    print(f"   Status: {health['status']}")
    print(f"   Total Mirrors: {health['statistics']['total_mirrors']}")
    print(f"   Success Rate: {health['statistics']['success_rate_pct']:.1f}%")
    print(f"   Average Parity: {health['statistics']['average_parity_rate']:.2%}")
    print(f"   Ready for Promotion: {health['recommendations']['ready_for_promotion']}")
    print()
    
    print("🎉 SHADOW EXECUTOR DEMO COMPLETE!")
    print("=" * 70)
    print("🛡️ Shadow Executor provides risk-free validation")
    print("📊 Statistical proof of execution engine accuracy")
    print("🚀 Safe bridge to live trading with confidence")
    print("=" * 70)
    
    return response

if __name__ == "__main__":
    asyncio.run(run_shadow_executor_demo())
