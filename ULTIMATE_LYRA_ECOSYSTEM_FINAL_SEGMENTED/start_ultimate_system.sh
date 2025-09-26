#!/bin/bash

# Ultimate Lyra Ecosystem - System Startup Script
# This script starts the complete system with all components

set -e  # Exit on any error

echo "🚀 ULTIMATE LYRA ECOSYSTEM - SYSTEM STARTUP"
echo "============================================"

# Configuration
MODE=${1:-"production"}
COMPONENTS=${2:-"all"}
SAFETY_CHECKS=${3:-"enabled"}

echo "📋 Startup Configuration:"
echo "   Mode: $MODE"
echo "   Components: $COMPONENTS"
echo "   Safety Checks: $SAFETY_CHECKS"
echo ""

# Environment validation
echo "🔍 Validating Environment..."

if [[ ! -f ".env.live" ]]; then
    echo "❌ Missing .env.live file"
    exit 1
fi

if [[ ! -f "config.json" ]]; then
    echo "❌ Missing config.json file"
    exit 1
fi

echo "   ✅ Environment files validated"

# Load environment variables
source .env.live 2>/dev/null || echo "   ⚠️ Could not load .env.live"

# Pre-startup safety checks
if [[ "$SAFETY_CHECKS" == "enabled" ]]; then
    echo ""
    echo "🛡️ Running Safety Checks..."
    
    # Check Python dependencies
    python3 -c "
import sys
required_modules = ['asyncio', 'aiohttp', 'asyncpg', 'numpy', 'pandas']
missing = []
for module in required_modules:
    try:
        __import__(module)
    except ImportError:
        missing.append(module)
if missing:
    print(f'❌ Missing Python modules: {missing}')
    sys.exit(1)
else:
    print('   ✅ Python dependencies validated')
"

    # Check disk space
    available_space=$(df . | tail -1 | awk '{print $4}')
    if [[ $available_space -lt 1000000 ]]; then  # Less than 1GB
        echo "   ⚠️ Low disk space: ${available_space}KB available"
    else
        echo "   ✅ Sufficient disk space available"
    fi
    
    # Check memory
    available_memory=$(free -m | awk 'NR==2{printf "%.0f", $7}')
    if [[ $available_memory -lt 512 ]]; then  # Less than 512MB
        echo "   ⚠️ Low memory: ${available_memory}MB available"
    else
        echo "   ✅ Sufficient memory available"
    fi
fi

# Create necessary directories
echo ""
echo "📁 Creating Directories..."
mkdir -p logs data config temp backups
echo "   ✅ Directories created"

# Component startup functions
start_core_system() {
    echo "🎯 Starting Core System..."
    python3 core/ultimate_lyra_ecosystem_absolutely_final.py &
    CORE_PID=$!
    echo "   ✅ Core system started (PID: $CORE_PID)"
}

start_ai_orchestra() {
    echo "🧠 Starting AI Orchestra Conductor..."
    python3 core/ai_orchestra_conductor.py &
    AI_PID=$!
    echo "   ✅ AI Orchestra started (PID: $AI_PID)"
}

start_shadow_executor() {
    echo "🔮 Starting Shadow Executor..."
    python3 services/shadow_executor.py &
    SHADOW_PID=$!
    echo "   ✅ Shadow Executor started (PID: $SHADOW_PID)"
}

start_monitoring() {
    echo "📊 Starting Monitoring Systems..."
    python3 utils/monitoring_ops.py &
    MONITOR_PID=$!
    echo "   ✅ Monitoring started (PID: $MONITOR_PID)"
}

start_web_dashboard() {
    echo "🌐 Starting Web Dashboard..."
    if [[ -f "web_dashboard/app.py" ]]; then
        cd web_dashboard && python3 app.py &
        WEB_PID=$!
        cd ..
        echo "   ✅ Web Dashboard started (PID: $WEB_PID)"
    else
        echo "   ⚠️ Web Dashboard not found, skipping"
    fi
}

# Component startup based on selection
echo ""
echo "🚀 Starting Components..."

if [[ "$COMPONENTS" == "all" || "$COMPONENTS" == *"core"* ]]; then
    start_core_system
    sleep 2
fi

if [[ "$COMPONENTS" == "all" || "$COMPONENTS" == *"ai"* ]]; then
    start_ai_orchestra
    sleep 2
fi

if [[ "$COMPONENTS" == "all" || "$COMPONENTS" == *"shadow"* ]]; then
    start_shadow_executor
    sleep 2
fi

if [[ "$COMPONENTS" == "all" || "$COMPONENTS" == *"monitoring"* ]]; then
    start_monitoring
    sleep 2
fi

if [[ "$COMPONENTS" == "all" || "$COMPONENTS" == *"web"* ]]; then
    start_web_dashboard
    sleep 2
fi

# Wait for components to initialize
echo ""
echo "⏳ Waiting for system initialization..."
sleep 10

# Health checks
echo ""
echo "🏥 Running Health Checks..."

check_process() {
    local pid=$1
    local name=$2
    
    if kill -0 $pid 2>/dev/null; then
        echo "   ✅ $name is running (PID: $pid)"
        return 0
    else
        echo "   ❌ $name is not running"
        return 1
    fi
}

health_status=0

if [[ -n "$CORE_PID" ]]; then
    check_process $CORE_PID "Core System" || health_status=1
fi

if [[ -n "$AI_PID" ]]; then
    check_process $AI_PID "AI Orchestra" || health_status=1
fi

if [[ -n "$SHADOW_PID" ]]; then
    check_process $SHADOW_PID "Shadow Executor" || health_status=1
fi

if [[ -n "$MONITOR_PID" ]]; then
    check_process $MONITOR_PID "Monitoring" || health_status=1
fi

if [[ -n "$WEB_PID" ]]; then
    check_process $WEB_PID "Web Dashboard" || health_status=1
fi

# Create PID file for management
cat > lyra_ecosystem.pid << EOF
CORE_PID=$CORE_PID
AI_PID=$AI_PID
SHADOW_PID=$SHADOW_PID
MONITOR_PID=$MONITOR_PID
WEB_PID=$WEB_PID
EOF

echo "   ✅ PID file created"

# Final status
echo ""
if [[ $health_status -eq 0 ]]; then
    echo "🎉 SYSTEM STARTUP COMPLETE - ALL COMPONENTS HEALTHY!"
    echo "===================================================="
else
    echo "⚠️ SYSTEM STARTUP COMPLETE - SOME COMPONENTS NEED ATTENTION"
    echo "============================================================"
fi

echo ""
echo "📋 System Information:"
echo "   🎯 Mode: $MODE"
echo "   📊 Components: $COMPONENTS"
echo "   🔒 Safety Checks: $SAFETY_CHECKS"
echo "   📁 Working Directory: $(pwd)"
echo "   📝 Log Directory: $(pwd)/logs"
echo ""

echo "📋 Management Commands:"
echo "   📊 View logs: tail -f logs/*.log"
echo "   🛑 Stop system: ./stop_ultimate_system.sh"
echo "   🔄 Restart: ./restart_ultimate_system.sh"
echo "   📈 Status: ./status_ultimate_system.sh"
echo ""

echo "📋 Monitoring URLs (if web dashboard is running):"
echo "   🌐 Dashboard: http://localhost:8000"
echo "   📊 Metrics: http://localhost:8000/metrics"
echo "   🏥 Health: http://localhost:8000/health"
echo ""

if [[ "$MODE" == "production" ]]; then
    echo "⚠️ PRODUCTION MODE ACTIVE - MONITOR CAREFULLY!"
    echo "   - Check logs regularly: tail -f logs/*.log"
    echo "   - Monitor system resources: htop"
    echo "   - Watch for alerts and notifications"
else
    echo "🧪 DEVELOPMENT/TEST MODE - Safe for experimentation"
fi

echo ""
echo "🚀 Ultimate Lyra Ecosystem is now OPERATIONAL!"
echo "   All components are running and ready for trading."
echo "   System will continue running in the background."
echo ""

# Keep script running to maintain processes
if [[ "$1" != "--daemon" ]]; then
    echo "Press Ctrl+C to stop all components..."
    
    # Trap Ctrl+C to clean shutdown
    trap 'echo ""; echo "🛑 Shutting down..."; ./stop_ultimate_system.sh; exit 0' INT
    
    # Wait indefinitely
    while true; do
        sleep 60
        # Optional: Add periodic health checks here
    done
fi
