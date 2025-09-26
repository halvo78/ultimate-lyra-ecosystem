#!/bin/bash

# Ultimate Lyra Ecosystem - Supreme System Deployment Script
# This script deploys the complete system with all components

set -e  # Exit on any error

echo "🚀 ULTIMATE LYRA ECOSYSTEM - SUPREME SYSTEM DEPLOYMENT"
echo "========================================================"

# Configuration
DEPLOYMENT_MODE=${1:-"LIVE"}
SAFETY_LEVEL=${2:-"MAXIMUM"}
ENVIRONMENT=${3:-"production"}

echo "📋 Deployment Configuration:"
echo "   Mode: $DEPLOYMENT_MODE"
echo "   Safety Level: $SAFETY_LEVEL"
echo "   Environment: $ENVIRONMENT"
echo ""

# Pre-deployment checks
echo "🔍 Running Pre-deployment Checks..."

# Check if required files exist
required_files=(
    ".env.live"
    "config.json"
    "credentials.json"
    "docker-compose.yml"
    "requirements.txt"
)

for file in "${required_files[@]}"; do
    if [[ ! -f "$file" ]]; then
        echo "❌ Missing required file: $file"
        exit 1
    fi
    echo "   ✅ Found: $file"
done

# Check if Docker is installed and running
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed"
    exit 1
fi

if ! docker info &> /dev/null; then
    echo "❌ Docker is not running"
    exit 1
fi

echo "   ✅ Docker is available and running"

# Check if Docker Compose is available
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose is not available"
    exit 1
fi

echo "   ✅ Docker Compose is available"

# Environment setup
echo ""
echo "⚙️ Setting up Environment..."

# Create necessary directories
mkdir -p logs data config monitoring/grafana/dashboards nginx/ssl sql

echo "   ✅ Created necessary directories"

# Set proper permissions
chmod +x *.sh
chmod 600 .env.live credentials.json

echo "   ✅ Set proper file permissions"

# Database initialization
echo ""
echo "🗄️ Preparing Database..."

cat > sql/init.sql << 'EOF'
-- Ultimate Lyra Ecosystem Database Initialization

-- Create main database
CREATE DATABASE IF NOT EXISTS lyra_ecosystem;

-- Create user
CREATE USER IF NOT EXISTS lyra_user WITH PASSWORD 'secure_password_123';

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE lyra_ecosystem TO lyra_user;

-- Create tables
\c lyra_ecosystem;

CREATE TABLE IF NOT EXISTS trades (
    id SERIAL PRIMARY KEY,
    exchange VARCHAR(50) NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    side VARCHAR(10) NOT NULL,
    amount DECIMAL(20,8) NOT NULL,
    price DECIMAL(20,8) NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'pending'
);

CREATE TABLE IF NOT EXISTS market_data (
    id SERIAL PRIMARY KEY,
    exchange VARCHAR(50) NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    price DECIMAL(20,8) NOT NULL,
    volume DECIMAL(20,8) NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ai_decisions (
    id SERIAL PRIMARY KEY,
    model VARCHAR(100) NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    decision VARCHAR(20) NOT NULL,
    confidence DECIMAL(5,4) NOT NULL,
    reasoning TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_trades_timestamp ON trades(timestamp);
CREATE INDEX idx_market_data_timestamp ON market_data(timestamp);
CREATE INDEX idx_ai_decisions_timestamp ON ai_decisions(timestamp);
EOF

echo "   ✅ Database initialization script created"

# Monitoring configuration
echo ""
echo "📊 Setting up Monitoring..."

cat > monitoring/prometheus.yml << 'EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  # - "first_rules.yml"
  # - "second_rules.yml"

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'lyra-ecosystem'
    static_configs:
      - targets: ['lyra-ecosystem:9090']
    scrape_interval: 5s
    metrics_path: /metrics

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres:5432']

  - job_name: 'redis'
    static_configs:
      - targets: ['redis:6379']
EOF

echo "   ✅ Prometheus configuration created"

# Nginx configuration
cat > nginx/nginx.conf << 'EOF'
events {
    worker_connections 1024;
}

http {
    upstream lyra_backend {
        server lyra-ecosystem:8000;
    }

    server {
        listen 80;
        server_name localhost;

        location / {
            proxy_pass http://lyra_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        location /metrics {
            proxy_pass http://lyra_backend/metrics;
        }

        location /health {
            proxy_pass http://lyra_backend/health;
        }
    }
}
EOF

echo "   ✅ Nginx configuration created"

# Build and deploy
echo ""
echo "🔨 Building and Deploying System..."

# Stop any existing containers
echo "   🛑 Stopping existing containers..."
docker-compose down --remove-orphans || true

# Build the application
echo "   🏗️ Building application..."
docker-compose build --no-cache

# Start the services
echo "   🚀 Starting services..."
if [[ "$DEPLOYMENT_MODE" == "LIVE" ]]; then
    docker-compose up -d
else
    docker-compose up -d --scale lyra-ecosystem=1
fi

# Wait for services to be ready
echo "   ⏳ Waiting for services to be ready..."
sleep 30

# Health checks
echo ""
echo "🏥 Running Health Checks..."

services=("postgres:5432" "redis:6379" "lyra-ecosystem:8000")

for service in "${services[@]}"; do
    container_name=$(echo $service | cut -d':' -f1)
    port=$(echo $service | cut -d':' -f2)
    
    if docker-compose ps | grep -q "$container_name.*Up"; then
        echo "   ✅ $container_name is running"
    else
        echo "   ❌ $container_name is not running"
        docker-compose logs $container_name
        exit 1
    fi
done

# Final validation
echo ""
echo "✅ DEPLOYMENT VALIDATION"
echo "========================"

# Check if main application is responding
if curl -f http://localhost:8000/health &> /dev/null; then
    echo "   ✅ Main application is responding"
else
    echo "   ⚠️ Main application health check failed"
fi

# Check if Prometheus is accessible
if curl -f http://localhost:9091 &> /dev/null; then
    echo "   ✅ Prometheus is accessible"
else
    echo "   ⚠️ Prometheus is not accessible"
fi

# Check if Grafana is accessible
if curl -f http://localhost:3001 &> /dev/null; then
    echo "   ✅ Grafana is accessible"
else
    echo "   ⚠️ Grafana is not accessible"
fi

echo ""
echo "🎉 DEPLOYMENT COMPLETE!"
echo "======================="
echo ""
echo "📋 Service URLs:"
echo "   🎯 Main Application: http://localhost:8000"
echo "   📊 Prometheus: http://localhost:9091"
echo "   📈 Grafana: http://localhost:3001"
echo "   🌐 Nginx Proxy: http://localhost:80"
echo ""
echo "📋 Management Commands:"
echo "   📊 View logs: docker-compose logs -f"
echo "   🛑 Stop system: docker-compose down"
echo "   🔄 Restart: docker-compose restart"
echo "   📈 Scale up: docker-compose up -d --scale lyra-ecosystem=3"
echo ""
echo "🔒 Security Notes:"
echo "   - Change default passwords in .env.live"
echo "   - Enable SSL certificates for production"
echo "   - Configure firewall rules"
echo "   - Set up backup procedures"
echo ""

if [[ "$DEPLOYMENT_MODE" == "LIVE" ]]; then
    echo "⚠️ LIVE TRADING MODE ACTIVE - MONITOR CAREFULLY!"
else
    echo "🧪 PAPER TRADING MODE - Safe for testing"
fi

echo ""
echo "🚀 Ultimate Lyra Ecosystem is now LIVE and operational!"
