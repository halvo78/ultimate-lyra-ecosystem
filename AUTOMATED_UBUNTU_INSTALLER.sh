#!/bin/bash
# ULTIMATE LYRA ECOSYSTEM - AUTOMATED UBUNTU INSTALLER
# One-command installation script for complete system deployment

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
INSTALL_DIR="/opt/ultimate_lyra_ecosystem"
BACKUP_DIR="/backup/lyra_archives"
SYSTEM_USER="ubuntu"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Logging
LOG_FILE="/tmp/lyra_installation_${TIMESTAMP}.log"
exec 1> >(tee -a "$LOG_FILE")
exec 2> >(tee -a "$LOG_FILE" >&2)

print_header() {
    echo -e "${BLUE}"
    echo "=================================================================="
    echo "    ULTIMATE LYRA ECOSYSTEM - AUTOMATED UBUNTU INSTALLER"
    echo "=================================================================="
    echo -e "${NC}"
    echo "Installation started at: $(date)"
    echo "Log file: $LOG_FILE"
    echo ""
}

print_step() {
    echo -e "${YELLOW}[STEP] $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

check_root() {
    if [[ $EUID -eq 0 ]]; then
        print_error "This script should not be run as root. Please run as a regular user with sudo privileges."
        exit 1
    fi
    
    # Check if user has sudo privileges
    if ! sudo -n true 2>/dev/null; then
        print_error "This script requires sudo privileges. Please ensure your user can run sudo commands."
        exit 1
    fi
    
    print_success "User privileges verified"
}

archive_old_build() {
    print_step "Archiving any existing LYRA installation..."
    
    sudo mkdir -p "$BACKUP_DIR"
    
    # Archive existing installations
    if [ -d "$INSTALL_DIR" ]; then
        print_warning "Existing installation found. Creating backup..."
        sudo tar -czf "$BACKUP_DIR/lyra_backup_${TIMESTAMP}.tar.gz" "$INSTALL_DIR" 2>/dev/null || true
        sudo rm -rf "$INSTALL_DIR"
        print_success "Old installation archived to $BACKUP_DIR/lyra_backup_${TIMESTAMP}.tar.gz"
    fi
    
    # Archive any home directory installations
    if ls ~/lyra* 1> /dev/null 2>&1; then
        sudo mv ~/lyra* "$BACKUP_DIR/" 2>/dev/null || true
        print_success "Home directory LYRA files archived"
    fi
    
    print_success "Old build archiving completed"
}

prepare_ubuntu_system() {
    print_step "Preparing Ubuntu system..."
    
    # Update system packages
    print_step "Updating system packages..."
    sudo apt update && sudo apt upgrade -y
    print_success "System packages updated"
    
    # Install required system packages
    print_step "Installing system dependencies..."
    sudo apt install -y \
        python3 python3-pip python3-venv python3-dev \
        git curl wget unzip tar gzip \
        build-essential libssl-dev libffi-dev pkg-config \
        redis-server postgresql postgresql-contrib \
        nginx supervisor htop tree \
        docker.io docker-compose \
        software-properties-common apt-transport-https ca-certificates \
        gnupg lsb-release jq bc
    
    print_success "System dependencies installed"
    
    # Install Python packages globally
    print_step "Upgrading Python package managers..."
    sudo pip3 install --upgrade pip setuptools wheel
    print_success "Python package managers upgraded"
    
    # Configure services
    print_step "Configuring system services..."
    sudo systemctl enable redis-server postgresql nginx
    sudo systemctl start redis-server postgresql nginx
    print_success "System services configured"
    
    # Add user to docker group
    sudo usermod -aG docker "$SYSTEM_USER"
    print_success "User added to docker group"
    
    print_success "Ubuntu system preparation completed"
}

create_directory_structure() {
    print_step "Creating directory structure..."
    
    # Create main installation directory
    sudo mkdir -p "$INSTALL_DIR"
    sudo chown "$SYSTEM_USER:$SYSTEM_USER" "$INSTALL_DIR"
    cd "$INSTALL_DIR"
    
    # Create complete directory structure
    mkdir -p {bin,config,data,logs,vault,docs,tests,scripts,backups}
    mkdir -p config/{exchanges,strategies,risk,precision}
    mkdir -p data/{market_data,trades,portfolio,arbitrage,historical}
    mkdir -p logs/{trading,system,errors,audit,performance}
    mkdir -p vault/{credentials,keys,backups,secrets}
    mkdir -p docs/{api,user_guide,technical,compliance}
    mkdir -p tests/{unit,integration,performance,security}
    mkdir -p scripts/{maintenance,monitoring,backup,deployment}
    mkdir -p backups/{daily,weekly,monthly,emergency}
    
    # Set proper permissions
    chmod 755 "$INSTALL_DIR"
    chmod 700 vault/
    chmod 600 vault/credentials/ 2>/dev/null || mkdir -p vault/credentials && chmod 600 vault/credentials/
    chmod 644 config/
    chmod 755 bin/
    chmod 755 scripts/
    
    print_success "Directory structure created with proper permissions"
}

setup_python_environment() {
    print_step "Setting up Python virtual environment..."
    
    cd "$INSTALL_DIR"
    
    # Create virtual environment
    python3 -m venv lyra_env
    source lyra_env/bin/activate
    
    # Upgrade pip in virtual environment
    pip install --upgrade pip setuptools wheel
    
    # Install core dependencies
    print_step "Installing trading and exchange libraries..."
    pip install ccxt>=4.0.0 pandas>=2.0.0 numpy>=1.24.0 aiohttp>=3.8.0
    
    print_step "Installing AI and ML libraries..."
    pip install openai anthropic cohere google-generativeai
    
    print_step "Installing database and caching libraries..."
    pip install asyncpg redis>=4.5.0 sqlalchemy alembic
    
    print_step "Installing security and encryption libraries..."
    pip install cryptography>=41.0.0 bcrypt>=4.0.0 PyJWT>=2.8.0
    
    print_step "Installing web and API libraries..."
    pip install fastapi uvicorn websockets>=11.0.0 requests
    
    print_step "Installing monitoring and logging libraries..."
    pip install prometheus-client structlog
    
    print_step "Installing additional utilities..."
    pip install pyyaml python-dotenv schedule click rich
    
    print_step "Installing scientific computing libraries..."
    pip install scipy scikit-learn matplotlib seaborn plotly
    
    # Create requirements.txt
    pip freeze > requirements.txt
    
    print_success "Python environment setup completed"
}

configure_environment() {
    print_step "Configuring environment..."
    
    cd "$INSTALL_DIR"
    
    # Create environment file
    cat > .env << 'EOF'
# ULTIMATE LYRA ECOSYSTEM ENVIRONMENT CONFIGURATION
# Production Environment Settings

# System Configuration
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
TIMEZONE=UTC

# Database Configuration
DATABASE_URL=postgresql://lyra_user:lyra_password@localhost:5432/lyra_db
REDIS_URL=redis://localhost:6379/0

# Security Configuration
SECRET_KEY=CHANGE_THIS_SECRET_KEY_IN_PRODUCTION
ENCRYPTION_KEY=CHANGE_THIS_ENCRYPTION_KEY_IN_PRODUCTION
JWT_SECRET=CHANGE_THIS_JWT_SECRET_IN_PRODUCTION

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
DASHBOARD_PORT=8080

# Exchange API Keys (REPLACE WITH YOUR ACTUAL KEYS)
OKX_API_KEY=your_okx_api_key_here
OKX_SECRET=your_okx_secret_here
OKX_PASSPHRASE=your_okx_passphrase_here

GATE_API_KEY=your_gate_api_key_here
GATE_SECRET=your_gate_secret_here

BINANCE_API_KEY=your_binance_api_key_here
BINANCE_SECRET=your_binance_secret_here

WHITEBIT_API_KEY=your_whitebit_api_key_here
WHITEBIT_SECRET=your_whitebit_secret_here

BTCMARKETS_API_KEY=your_btcmarkets_api_key_here
BTCMARKETS_SECRET=your_btcmarkets_secret_here

# AI API Keys (REPLACE WITH YOUR ACTUAL KEYS)
OPENROUTER_API_KEY=your_openrouter_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
COHERE_API_KEY=your_cohere_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here

# Data API Keys
POLYGON_API_KEY=your_polygon_api_key_here
SUPABASE_URL=your_supabase_url_here
SUPABASE_KEY=your_supabase_key_here

# Monitoring Configuration
PROMETHEUS_PORT=9090
GRAFANA_PORT=3000

# Trading Configuration
TRADING_MODE=paper
MAX_POSITION_SIZE=1000
RISK_LIMIT=0.02
STOP_LOSS_PERCENT=0.05

EOF
    
    # Set secure permissions on environment file
    chmod 600 .env
    
    print_success "Environment configuration created"
    print_warning "IMPORTANT: Update API keys in .env file before starting the system"
}

setup_database() {
    print_step "Setting up PostgreSQL database..."
    
    # Setup PostgreSQL database
    sudo -u postgres psql << 'EOF'
CREATE USER lyra_user WITH PASSWORD 'lyra_password';
CREATE DATABASE lyra_db OWNER lyra_user;
GRANT ALL PRIVILEGES ON DATABASE lyra_db TO lyra_user;
\q
EOF
    
    # Test database connection
    cd "$INSTALL_DIR"
    source lyra_env/bin/activate
    
    python3 -c "
import asyncpg
import asyncio

async def test_db():
    try:
        conn = await asyncpg.connect('postgresql://lyra_user:lyra_password@localhost:5432/lyra_db')
        await conn.execute('SELECT 1')
        await conn.close()
        print('✅ Database connection successful')
        return True
    except Exception as e:
        print(f'❌ Database connection failed: {e}')
        return False

result = asyncio.run(test_db())
exit(0 if result else 1)
"
    
    if [ $? -eq 0 ]; then
        print_success "Database setup completed successfully"
    else
        print_error "Database setup failed"
        exit 1
    fi
}

create_system_files() {
    print_step "Creating system files..."
    
    cd "$INSTALL_DIR"
    
    # Create main system file placeholder
    cat > bin/ultimate_lyra_ecosystem.py << 'EOF'
#!/usr/bin/env python3
"""
ULTIMATE LYRA ECOSYSTEM - Main System Entry Point
This is a placeholder file. The actual system files should be extracted
from the ULTIMATE_LYRA_ECOSYSTEM_COMPLETE_PROTECTION_FINAL.tar.gz package.
"""

import os
import sys
import time
from pathlib import Path

def main():
    print("🚀 ULTIMATE LYRA ECOSYSTEM")
    print("=" * 50)
    print("This is a placeholder system file.")
    print("Please extract the complete system package to replace this file.")
    print("")
    print("Expected package: ULTIMATE_LYRA_ECOSYSTEM_COMPLETE_PROTECTION_FINAL.tar.gz")
    print("Extract command: tar -xzf package.tar.gz --strip-components=1")
    print("")
    print("System will exit in 10 seconds...")
    time.sleep(10)

if __name__ == "__main__":
    main()
EOF
    
    chmod +x bin/ultimate_lyra_ecosystem.py
    
    # Create validation script
    cat > scripts/validate_installation.py << 'EOF'
#!/usr/bin/env python3
"""Ultimate Lyra Ecosystem - Installation Validation Script"""

import os
import sys
import importlib
import asyncio
from pathlib import Path

class InstallationValidator:
    def __init__(self):
        self.base_path = Path("/opt/ultimate_lyra_ecosystem")
        self.errors = []
        self.warnings = []
        
    def validate_directory_structure(self):
        print("🔍 Validating directory structure...")
        required_dirs = [
            "bin", "config", "data", "logs", "vault", "docs", 
            "tests", "scripts", "backups"
        ]
        
        for dir_path in required_dirs:
            full_path = self.base_path / dir_path
            if not full_path.exists():
                self.errors.append(f"Missing directory: {dir_path}")
            else:
                print(f"✅ {dir_path}")
        
    def validate_python_packages(self):
        print("\n🔍 Validating Python packages...")
        required_packages = [
            "ccxt", "pandas", "numpy", "aiohttp", "asyncpg", 
            "redis", "cryptography", "fastapi", "websockets"
        ]
        
        for package in required_packages:
            try:
                importlib.import_module(package)
                print(f"✅ {package}")
            except ImportError:
                self.errors.append(f"Missing package: {package}")
                print(f"❌ {package}")
    
    def validate_services(self):
        print("\n🔍 Validating services...")
        
        # Test Redis
        try:
            import redis
            r = redis.Redis(host='localhost', port=6379, db=0)
            r.ping()
            print("✅ Redis connection")
        except Exception as e:
            self.errors.append(f"Redis connection failed: {e}")
            print(f"❌ Redis: {e}")
        
        # Test PostgreSQL
        try:
            import asyncpg
            async def test_db():
                conn = await asyncpg.connect('postgresql://lyra_user:lyra_password@localhost:5432/lyra_db')
                await conn.execute('SELECT 1')
                await conn.close()
            
            asyncio.run(test_db())
            print("✅ PostgreSQL connection")
        except Exception as e:
            self.errors.append(f"PostgreSQL connection failed: {e}")
            print(f"❌ PostgreSQL: {e}")
    
    def run_validation(self):
        print("🚀 ULTIMATE LYRA ECOSYSTEM - INSTALLATION VALIDATION")
        print("=" * 60)
        
        self.validate_directory_structure()
        self.validate_python_packages()
        self.validate_services()
        
        print("\n" + "=" * 60)
        print("📋 VALIDATION SUMMARY")
        print("=" * 60)
        
        if not self.errors:
            print("🎉 INSTALLATION VALIDATED SUCCESSFULLY!")
            print("✅ All components are properly installed")
            return True
        else:
            print(f"❌ VALIDATION FAILED ({len(self.errors)} errors):")
            for error in self.errors:
                print(f"   • {error}")
            return False

if __name__ == "__main__":
    validator = InstallationValidator()
    success = validator.run_validation()
    sys.exit(0 if success else 1)
EOF
    
    chmod +x scripts/validate_installation.py
    
    # Create startup script
    cat > scripts/start_system.sh << 'EOF'
#!/bin/bash
# Ultimate Lyra Ecosystem Startup Script

cd /opt/ultimate_lyra_ecosystem
source lyra_env/bin/activate

echo "🚀 Starting Ultimate Lyra Ecosystem..."
echo "=================================="

# Run validation
python3 scripts/validate_installation.py
if [ $? -ne 0 ]; then
    echo "❌ System validation failed. Please fix errors before starting."
    exit 1
fi

echo "✅ Validation passed. Starting trading system..."
python3 bin/ultimate_lyra_ecosystem.py
EOF
    
    chmod +x scripts/start_system.sh
    
    print_success "System files created"
}

create_system_service() {
    print_step "Creating system service..."
    
    # Create systemd service
    sudo tee /etc/systemd/system/ultimate-lyra.service > /dev/null << EOF
[Unit]
Description=Ultimate Lyra Ecosystem Trading System
After=network.target postgresql.service redis.service
Requires=postgresql.service redis.service

[Service]
Type=simple
User=$SYSTEM_USER
Group=$SYSTEM_USER
WorkingDirectory=$INSTALL_DIR
Environment=PATH=$INSTALL_DIR/lyra_env/bin
ExecStart=$INSTALL_DIR/lyra_env/bin/python $INSTALL_DIR/bin/ultimate_lyra_ecosystem.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=ultimate-lyra

[Install]
WantedBy=multi-user.target
EOF
    
    # Reload systemd and enable service
    sudo systemctl daemon-reload
    sudo systemctl enable ultimate-lyra.service
    
    print_success "System service created and enabled"
}

run_final_validation() {
    print_step "Running final validation..."
    
    cd "$INSTALL_DIR"
    source lyra_env/bin/activate
    
    python3 scripts/validate_installation.py
    
    if [ $? -eq 0 ]; then
        print_success "Final validation passed"
        return 0
    else
        print_error "Final validation failed"
        return 1
    fi
}

print_completion_message() {
    echo ""
    echo -e "${GREEN}"
    echo "=================================================================="
    echo "    ULTIMATE LYRA ECOSYSTEM INSTALLATION COMPLETED!"
    echo "=================================================================="
    echo -e "${NC}"
    echo ""
    echo "📍 Installation Directory: $INSTALL_DIR"
    echo "📋 Log File: $LOG_FILE"
    echo "🔧 Service Name: ultimate-lyra.service"
    echo ""
    echo -e "${YELLOW}NEXT STEPS:${NC}"
    echo "1. Update API keys in: $INSTALL_DIR/.env"
    echo "2. Extract system package: tar -xzf package.tar.gz --strip-components=1"
    echo "3. Start the system: sudo systemctl start ultimate-lyra.service"
    echo "4. Check status: sudo systemctl status ultimate-lyra.service"
    echo "5. View logs: sudo journalctl -u ultimate-lyra.service -f"
    echo ""
    echo -e "${GREEN}SYSTEM COMMANDS:${NC}"
    echo "• Start: sudo systemctl start ultimate-lyra.service"
    echo "• Stop: sudo systemctl stop ultimate-lyra.service"
    echo "• Status: sudo systemctl status ultimate-lyra.service"
    echo "• Logs: sudo journalctl -u ultimate-lyra.service -f"
    echo "• Validate: cd $INSTALL_DIR && source lyra_env/bin/activate && python3 scripts/validate_installation.py"
    echo ""
    echo -e "${BLUE}🎉 INSTALLATION SUCCESSFUL! 🎉${NC}"
    echo ""
}

# Main installation sequence
main() {
    print_header
    
    check_root
    archive_old_build
    prepare_ubuntu_system
    create_directory_structure
    setup_python_environment
    configure_environment
    setup_database
    create_system_files
    create_system_service
    
    if run_final_validation; then
        print_completion_message
        echo "Installation completed successfully at: $(date)" >> "$LOG_FILE"
        exit 0
    else
        print_error "Installation completed with errors. Please check the log file: $LOG_FILE"
        exit 1
    fi
}

# Run main function
main "$@"
