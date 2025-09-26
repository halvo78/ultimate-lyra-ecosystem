#!/usr/bin/env python3
"""
Ultimate Lyra Ecosystem - Automated Deployment Verification
Comprehensive verification script for Ubuntu deployment
"""

import os
import sys
import subprocess
import json
import time
import requests
from pathlib import Path
import importlib.util

class DeploymentVerifier:
    def __init__(self):
        self.results = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "system_info": {},
            "verification_results": {},
            "critical_issues": [],
            "warnings": [],
            "success_rate": 0,
            "overall_status": "UNKNOWN"
        }
        
    def log(self, message, level="INFO"):
        """Log message with timestamp"""
        timestamp = time.strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
        
    def run_command(self, command, capture_output=True):
        """Run shell command and return result"""
        try:
            result = subprocess.run(
                command, 
                shell=True, 
                capture_output=capture_output, 
                text=True, 
                timeout=30
            )
            return result.returncode == 0, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return False, "", "Command timed out"
        except Exception as e:
            return False, "", str(e)
    
    def verify_system_requirements(self):
        """Verify Ubuntu system requirements"""
        self.log("🔍 Verifying system requirements...")
        
        # Check Ubuntu version
        success, output, _ = self.run_command("lsb_release -r")
        if success:
            version = output.split('\t')[1].strip()
            self.results["system_info"]["ubuntu_version"] = version
            if float(version) >= 20.04:
                self.log(f"✅ Ubuntu version: {version}")
            else:
                self.results["critical_issues"].append(f"Ubuntu version {version} < 20.04")
        
        # Check memory
        success, output, _ = self.run_command("free -h | grep Mem")
        if success:
            memory = output.split()[1]
            self.results["system_info"]["memory"] = memory
            self.log(f"✅ Memory: {memory}")
        
        # Check disk space
        success, output, _ = self.run_command("df -h / | tail -1")
        if success:
            disk_info = output.split()
            available = disk_info[3]
            self.results["system_info"]["disk_available"] = available
            self.log(f"✅ Disk available: {available}")
        
        # Check Python version
        success, output, _ = self.run_command("python3.11 --version")
        if success:
            python_version = output.strip()
            self.results["system_info"]["python_version"] = python_version
            self.log(f"✅ Python: {python_version}")
        else:
            self.results["critical_issues"].append("Python 3.11+ not found")
        
        # Check Docker
        success, output, _ = self.run_command("docker --version")
        if success:
            docker_version = output.strip()
            self.results["system_info"]["docker_version"] = docker_version
            self.log(f"✅ Docker: {docker_version}")
        else:
            self.results["critical_issues"].append("Docker not installed")
        
        # Check Git
        success, output, _ = self.run_command("git --version")
        if success:
            git_version = output.strip()
            self.results["system_info"]["git_version"] = git_version
            self.log(f"✅ Git: {git_version}")
        else:
            self.results["critical_issues"].append("Git not installed")
    
    def verify_repository_clone(self):
        """Verify repository is properly cloned"""
        self.log("🔍 Verifying repository clone...")
        
        repo_path = Path("ultimate-lyra-ecosystem")
        if repo_path.exists():
            self.log("✅ Repository directory exists")
            
            # Check main system directory
            system_path = repo_path / "ULTIMATE_LYRA_ECOSYSTEM_FINAL_SEGMENTED"
            if system_path.exists():
                self.log("✅ Main system directory found")
                
                # Count files
                file_count = len(list(system_path.rglob("*")))
                self.results["verification_results"]["total_files"] = file_count
                self.log(f"✅ Total files: {file_count}")
                
                # Check critical files
                critical_files = [
                    "core/ai_orchestra_conductor.py",
                    "core/ultimate_lyra_ecosystem_absolutely_final.py",
                    "trading/smart_execution_engine.py",
                    "NEVER_SELL_AT_LOSS_PROTECTION_SYSTEM.py",
                    "P0_PRE_FLIGHT_CHECKLIST.py",
                    "SECURE_LIVE_TRANSITION_SYSTEM.py",
                    "requirements.txt",
                    ".env.example"
                ]
                
                missing_files = []
                for file_path in critical_files:
                    if (system_path / file_path).exists():
                        self.log(f"✅ Found: {file_path}")
                    else:
                        missing_files.append(file_path)
                        self.log(f"❌ Missing: {file_path}")
                
                if missing_files:
                    self.results["critical_issues"].extend([f"Missing file: {f}" for f in missing_files])
                
                self.results["verification_results"]["critical_files_present"] = len(critical_files) - len(missing_files)
                self.results["verification_results"]["critical_files_total"] = len(critical_files)
            else:
                self.results["critical_issues"].append("Main system directory not found")
        else:
            self.results["critical_issues"].append("Repository not cloned")
    
    def verify_python_dependencies(self):
        """Verify Python dependencies"""
        self.log("🔍 Verifying Python dependencies...")
        
        system_path = Path("ultimate-lyra-ecosystem/ULTIMATE_LYRA_ECOSYSTEM_FINAL_SEGMENTED")
        requirements_file = system_path / "requirements.txt"
        
        if requirements_file.exists():
            self.log("✅ Requirements file found")
            
            # Check if virtual environment exists
            venv_path = Path("lyra-env")
            if venv_path.exists():
                self.log("✅ Virtual environment found")
                
                # Test key imports
                key_packages = [
                    "ccxt", "pandas", "numpy", "requests", 
                    "flask", "fastapi", "asyncio", "aiohttp"
                ]
                
                missing_packages = []
                for package in key_packages:
                    success, _, _ = self.run_command(f"python3 -c 'import {package}'")
                    if success:
                        self.log(f"✅ Package available: {package}")
                    else:
                        missing_packages.append(package)
                        self.log(f"❌ Package missing: {package}")
                
                if missing_packages:
                    self.results["warnings"].extend([f"Missing package: {p}" for p in missing_packages])
                
                self.results["verification_results"]["packages_available"] = len(key_packages) - len(missing_packages)
                self.results["verification_results"]["packages_total"] = len(key_packages)
            else:
                self.results["warnings"].append("Virtual environment not found")
        else:
            self.results["critical_issues"].append("Requirements file not found")
    
    def verify_configuration(self):
        """Verify system configuration"""
        self.log("🔍 Verifying system configuration...")
        
        system_path = Path("ultimate-lyra-ecosystem/ULTIMATE_LYRA_ECOSYSTEM_FINAL_SEGMENTED")
        env_example = system_path / ".env.example"
        env_file = system_path / ".env"
        
        if env_example.exists():
            self.log("✅ Environment example file found")
            
            if env_file.exists():
                self.log("✅ Environment file configured")
                
                # Check critical environment variables
                with open(env_file, 'r') as f:
                    env_content = f.read()
                
                critical_vars = [
                    "LIVE_MODE", "LIVE_TRADING", "PORT",
                    "TRADING_PAIRS", "PERFORMANCE_LEVEL",
                    "NEVER_SELL_AT_LOSS", "MAX_DAILY_LOSS"
                ]
                
                configured_vars = []
                for var in critical_vars:
                    if f"{var}=" in env_content:
                        configured_vars.append(var)
                        self.log(f"✅ Configured: {var}")
                    else:
                        self.log(f"⚠️  Not configured: {var}")
                
                self.results["verification_results"]["env_vars_configured"] = len(configured_vars)
                self.results["verification_results"]["env_vars_total"] = len(critical_vars)
            else:
                self.results["warnings"].append("Environment file not configured")
        else:
            self.results["critical_issues"].append("Environment example file not found")
    
    def verify_protection_systems(self):
        """Verify protection systems"""
        self.log("🔍 Verifying protection systems...")
        
        system_path = Path("ultimate-lyra-ecosystem/ULTIMATE_LYRA_ECOSYSTEM_FINAL_SEGMENTED")
        
        protection_files = [
            "NEVER_SELL_AT_LOSS_PROTECTION_SYSTEM.py",
            "P0_PRE_FLIGHT_CHECKLIST.py", 
            "SECURE_LIVE_TRANSITION_SYSTEM.py"
        ]
        
        protection_status = []
        for file_name in protection_files:
            file_path = system_path / file_name
            if file_path.exists():
                self.log(f"✅ Protection system found: {file_name}")
                
                # Check if file is executable
                if os.access(file_path, os.X_OK):
                    self.log(f"✅ Executable: {file_name}")
                    protection_status.append(True)
                else:
                    self.log(f"⚠️  Not executable: {file_name}")
                    protection_status.append(False)
            else:
                self.log(f"❌ Missing protection system: {file_name}")
                protection_status.append(False)
                self.results["critical_issues"].append(f"Missing protection system: {file_name}")
        
        self.results["verification_results"]["protection_systems_active"] = sum(protection_status)
        self.results["verification_results"]["protection_systems_total"] = len(protection_files)
    
    def verify_ai_components(self):
        """Verify AI components"""
        self.log("🔍 Verifying AI components...")
        
        system_path = Path("ultimate-lyra-ecosystem/ULTIMATE_LYRA_ECOSYSTEM_FINAL_SEGMENTED")
        
        ai_components = [
            "core/ai_orchestra_conductor.py",
            "ai/advanced_strategy_engine.py",
            "ai/commissioning_tool.py"
        ]
        
        ai_status = []
        for component in ai_components:
            file_path = system_path / component
            if file_path.exists():
                self.log(f"✅ AI component found: {component}")
                ai_status.append(True)
            else:
                self.log(f"❌ Missing AI component: {component}")
                ai_status.append(False)
                self.results["critical_issues"].append(f"Missing AI component: {component}")
        
        self.results["verification_results"]["ai_components_present"] = sum(ai_status)
        self.results["verification_results"]["ai_components_total"] = len(ai_components)
    
    def verify_trading_engines(self):
        """Verify trading engines"""
        self.log("🔍 Verifying trading engines...")
        
        system_path = Path("ultimate-lyra-ecosystem/ULTIMATE_LYRA_ECOSYSTEM_FINAL_SEGMENTED")
        
        trading_components = [
            "trading/smart_execution_engine.py",
            "trading/live_exchange_connector.py",
            "trading/btcmarkets_connector.py"
        ]
        
        trading_status = []
        for component in trading_components:
            file_path = system_path / component
            if file_path.exists():
                self.log(f"✅ Trading component found: {component}")
                trading_status.append(True)
            else:
                self.log(f"❌ Missing trading component: {component}")
                trading_status.append(False)
                self.results["critical_issues"].append(f"Missing trading component: {component}")
        
        self.results["verification_results"]["trading_components_present"] = sum(trading_status)
        self.results["verification_results"]["trading_components_total"] = len(trading_components)
    
    def verify_docker_setup(self):
        """Verify Docker setup"""
        self.log("🔍 Verifying Docker setup...")
        
        system_path = Path("ultimate-lyra-ecosystem/ULTIMATE_LYRA_ECOSYSTEM_FINAL_SEGMENTED")
        
        docker_files = ["Dockerfile", "docker-compose.yml"]
        docker_status = []
        
        for file_name in docker_files:
            file_path = system_path / file_name
            if file_path.exists():
                self.log(f"✅ Docker file found: {file_name}")
                docker_status.append(True)
            else:
                self.log(f"❌ Missing Docker file: {file_name}")
                docker_status.append(False)
                self.results["warnings"].append(f"Missing Docker file: {file_name}")
        
        # Test Docker functionality
        success, _, _ = self.run_command("docker ps")
        if success:
            self.log("✅ Docker daemon running")
            docker_status.append(True)
        else:
            self.log("❌ Docker daemon not running")
            docker_status.append(False)
            self.results["warnings"].append("Docker daemon not running")
        
        self.results["verification_results"]["docker_setup_complete"] = sum(docker_status)
        self.results["verification_results"]["docker_setup_total"] = len(docker_files) + 1
    
    def verify_security_measures(self):
        """Verify security measures"""
        self.log("🔍 Verifying security measures...")
        
        system_path = Path("ultimate-lyra-ecosystem/ULTIMATE_LYRA_ECOSYSTEM_FINAL_SEGMENTED")
        
        # Check security directory
        security_path = system_path / "security"
        if security_path.exists():
            self.log("✅ Security directory found")
            
            # Check vault manager
            vault_manager = security_path / "vault_manager.py"
            if vault_manager.exists():
                self.log("✅ Vault manager found")
            else:
                self.results["warnings"].append("Vault manager not found")
        else:
            self.results["warnings"].append("Security directory not found")
        
        # Check file permissions
        env_file = system_path / ".env"
        if env_file.exists():
            file_stat = env_file.stat()
            permissions = oct(file_stat.st_mode)[-3:]
            if permissions == "600":
                self.log("✅ Environment file permissions secure")
            else:
                self.log(f"⚠️  Environment file permissions: {permissions} (should be 600)")
                self.results["warnings"].append("Environment file permissions not secure")
    
    def test_system_startup(self):
        """Test system startup capability"""
        self.log("🔍 Testing system startup capability...")
        
        system_path = Path("ultimate-lyra-ecosystem/ULTIMATE_LYRA_ECOSYSTEM_FINAL_SEGMENTED")
        
        # Check startup scripts
        startup_scripts = [
            "start_ultimate_system.sh",
            "deploy_supreme_system.sh"
        ]
        
        startup_status = []
        for script in startup_scripts:
            script_path = system_path / script
            if script_path.exists():
                if os.access(script_path, os.X_OK):
                    self.log(f"✅ Startup script ready: {script}")
                    startup_status.append(True)
                else:
                    self.log(f"⚠️  Startup script not executable: {script}")
                    startup_status.append(False)
            else:
                self.log(f"❌ Missing startup script: {script}")
                startup_status.append(False)
        
        self.results["verification_results"]["startup_scripts_ready"] = sum(startup_status)
        self.results["verification_results"]["startup_scripts_total"] = len(startup_scripts)
    
    def calculate_success_rate(self):
        """Calculate overall success rate"""
        total_checks = 0
        passed_checks = 0
        
        for key, value in self.results["verification_results"].items():
            if key.endswith("_total"):
                total_checks += value
            elif key.endswith("_present") or key.endswith("_active") or key.endswith("_configured") or key.endswith("_ready") or key.endswith("_complete"):
                passed_checks += value
        
        if total_checks > 0:
            self.results["success_rate"] = round((passed_checks / total_checks) * 100, 2)
        else:
            self.results["success_rate"] = 0
        
        # Determine overall status
        if len(self.results["critical_issues"]) == 0:
            if self.results["success_rate"] >= 95:
                self.results["overall_status"] = "EXCELLENT"
            elif self.results["success_rate"] >= 85:
                self.results["overall_status"] = "GOOD"
            elif self.results["success_rate"] >= 70:
                self.results["overall_status"] = "ACCEPTABLE"
            else:
                self.results["overall_status"] = "NEEDS_IMPROVEMENT"
        else:
            self.results["overall_status"] = "CRITICAL_ISSUES"
    
    def generate_report(self):
        """Generate comprehensive verification report"""
        self.log("📊 Generating verification report...")
        
        report = f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    ULTIMATE LYRA ECOSYSTEM DEPLOYMENT VERIFICATION           ║
╚══════════════════════════════════════════════════════════════════════════════╝

🕐 Verification Time: {self.results['timestamp']}
🎯 Overall Status: {self.results['overall_status']}
📊 Success Rate: {self.results['success_rate']}%

╔══════════════════════════════════════════════════════════════════════════════╗
║                                SYSTEM INFORMATION                            ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
        
        for key, value in self.results["system_info"].items():
            report += f"• {key.replace('_', ' ').title()}: {value}\n"
        
        report += f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                              VERIFICATION RESULTS                            ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
        
        for key, value in self.results["verification_results"].items():
            if not key.endswith("_total"):
                total_key = key.replace("_present", "_total").replace("_active", "_total").replace("_configured", "_total").replace("_ready", "_total").replace("_complete", "_total")
                total = self.results["verification_results"].get(total_key, "N/A")
                percentage = round((value / total * 100), 1) if isinstance(total, int) and total > 0 else 0
                status = "✅" if percentage >= 90 else "⚠️" if percentage >= 70 else "❌"
                report += f"{status} {key.replace('_', ' ').title()}: {value}/{total} ({percentage}%)\n"
        
        if self.results["critical_issues"]:
            report += f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                               CRITICAL ISSUES                                ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
            for issue in self.results["critical_issues"]:
                report += f"❌ {issue}\n"
        
        if self.results["warnings"]:
            report += f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                  WARNINGS                                    ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
            for warning in self.results["warnings"]:
                report += f"⚠️  {warning}\n"
        
        report += f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                              NEXT STEPS                                      ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
        
        if self.results["overall_status"] == "EXCELLENT":
            report += """✅ System is ready for deployment!
✅ All critical components verified
✅ Proceed with Phase 4: Comprehensive Testing
✅ Run: python3 P0_PRE_FLIGHT_CHECKLIST.py
"""
        elif self.results["overall_status"] == "GOOD":
            report += """✅ System is mostly ready for deployment
⚠️  Address warnings before proceeding
✅ Run: python3 P0_PRE_FLIGHT_CHECKLIST.py
"""
        elif self.results["overall_status"] == "ACCEPTABLE":
            report += """⚠️  System needs improvements before deployment
⚠️  Address warnings and missing components
⚠️  Re-run verification after fixes
"""
        elif self.results["overall_status"] == "CRITICAL_ISSUES":
            report += """❌ Critical issues must be resolved before deployment
❌ Address all critical issues listed above
❌ Re-run verification after fixes
❌ Do not proceed to live trading until resolved
"""
        else:
            report += """❌ System requires significant work before deployment
❌ Follow the deployment plan step by step
❌ Re-run verification after each phase
"""
        
        report += f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                              SUPPORT RESOURCES                               ║
╚══════════════════════════════════════════════════════════════════════════════╝
📖 Full Deployment Plan: AI_ASSISTED_UBUNTU_DEPLOYMENT_PLAN.md
🔗 Repository: https://github.com/halvo78/ultimate-lyra-ecosystem
📋 Documentation: ULTIMATE_LYRA_ECOSYSTEM_FINAL_SEGMENTED/DEPLOYMENT_GUIDE.md
🛡️  Security Guide: ULTIMATE_LYRA_ECOSYSTEM_FINAL_SEGMENTED/FINAL_COMPLIANCE_PROOF.md

╔══════════════════════════════════════════════════════════════════════════════╗
║                           VERIFICATION COMPLETE                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
        
        return report
    
    def save_results(self):
        """Save verification results to file"""
        with open("deployment_verification_results.json", "w") as f:
            json.dump(self.results, f, indent=2)
        
        report = self.generate_report()
        with open("deployment_verification_report.txt", "w") as f:
            f.write(report)
        
        self.log("📁 Results saved to deployment_verification_results.json")
        self.log("📁 Report saved to deployment_verification_report.txt")
    
    def run_full_verification(self):
        """Run complete deployment verification"""
        self.log("🚀 Starting Ultimate Lyra Ecosystem Deployment Verification")
        self.log("=" * 80)
        
        try:
            self.verify_system_requirements()
            self.verify_repository_clone()
            self.verify_python_dependencies()
            self.verify_configuration()
            self.verify_protection_systems()
            self.verify_ai_components()
            self.verify_trading_engines()
            self.verify_docker_setup()
            self.verify_security_measures()
            self.test_system_startup()
            
            self.calculate_success_rate()
            
            self.log("=" * 80)
            self.log(f"🎯 Verification Complete - Status: {self.results['overall_status']}")
            self.log(f"📊 Success Rate: {self.results['success_rate']}%")
            
            if self.results["critical_issues"]:
                self.log(f"❌ Critical Issues: {len(self.results['critical_issues'])}")
            
            if self.results["warnings"]:
                self.log(f"⚠️  Warnings: {len(self.results['warnings'])}")
            
            self.save_results()
            
            # Print summary report
            print(self.generate_report())
            
            return self.results["overall_status"] in ["EXCELLENT", "GOOD"]
            
        except Exception as e:
            self.log(f"❌ Verification failed with error: {str(e)}", "ERROR")
            self.results["critical_issues"].append(f"Verification error: {str(e)}")
            self.results["overall_status"] = "VERIFICATION_FAILED"
            return False

def main():
    """Main verification function"""
    verifier = DeploymentVerifier()
    success = verifier.run_full_verification()
    
    if success:
        print("\n🎉 Deployment verification successful! System is ready for the next phase.")
        sys.exit(0)
    else:
        print("\n❌ Deployment verification failed. Please address issues before proceeding.")
        sys.exit(1)

if __name__ == "__main__":
    main()
