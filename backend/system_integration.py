"""
ALPHA System Integration & Crypto Mining Module

Features:
1. Crypto Mining (CPU-based)
2. System Process Management
3. Hardware Monitoring
4. Remote ALPHA Connection
5. App Problem-Solving
6. Distributed Computing

⚠️ CRYPTO MINING WARNINGS:
- Laptop mining is generally NOT profitable
- Can damage hardware through heat/wear
- Electricity costs often exceed mining profits
- Only certain coins are CPU-mineable
- Use at your own risk
"""

import psutil
import platform
import subprocess
import os
from typing import Dict, List, Any
import cpuinfo
import time
from datetime import datetime
import hashlib
import json

class SystemIntegration:
    """
    Complete system integration for ALPHA
    """
    
    def __init__(self):
        self.cpu_info = cpuinfo.get_cpu_info()
        self.mining_active = False
        
    def get_system_info(self) -> Dict[str, Any]:
        """
        Get comprehensive system information
        """
        try:
            # CPU Information
            cpu_percent = psutil.cpu_percent(interval=1, percpu=True)
            cpu_freq = psutil.cpu_freq()
            
            # Memory Information
            memory = psutil.virtual_memory()
            
            # Disk Information
            disk = psutil.disk_usage('/')
            
            # Network Information
            net_io = psutil.net_io_counters()
            
            # Temperature (if available)
            temps = {}
            try:
                temps = psutil.sensors_temperatures()
            except:
                temps = {"info": "Temperature sensors not available"}
            
            # Battery (if laptop)
            battery = None
            try:
                battery = psutil.sensors_battery()
                if battery:
                    battery = {
                        "percent": battery.percent,
                        "plugged_in": battery.power_plugged,
                        "time_left": battery.secsleft if battery.secsleft != -1 else "Charging"
                    }
            except:
                pass
            
            return {
                "success": True,
                "system": {
                    "os": platform.system(),
                    "os_version": platform.version(),
                    "architecture": platform.machine(),
                    "processor": self.cpu_info.get('brand_raw', 'Unknown'),
                    "cpu_cores": psutil.cpu_count(logical=False),
                    "cpu_threads": psutil.cpu_count(logical=True),
                },
                "performance": {
                    "cpu_usage_percent": round(sum(cpu_percent) / len(cpu_percent), 2),
                    "cpu_per_core": [round(p, 2) for p in cpu_percent],
                    "cpu_frequency_mhz": round(cpu_freq.current, 2) if cpu_freq else 0,
                    "memory_total_gb": round(memory.total / (1024**3), 2),
                    "memory_used_gb": round(memory.used / (1024**3), 2),
                    "memory_percent": memory.percent,
                    "disk_total_gb": round(disk.total / (1024**3), 2),
                    "disk_used_gb": round(disk.used / (1024**3), 2),
                    "disk_percent": disk.percent,
                },
                "network": {
                    "bytes_sent_mb": round(net_io.bytes_sent / (1024**2), 2),
                    "bytes_recv_mb": round(net_io.bytes_recv / (1024**2), 2),
                },
                "temperature": temps,
                "battery": battery,
                "mining_capable": self._check_mining_capability()
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _check_mining_capability(self) -> Dict[str, Any]:
        """
        Check if system can mine crypto
        """
        cpu_threads = psutil.cpu_count(logical=True)
        memory_gb = psutil.virtual_memory().total / (1024**3)
        
        # Basic capability assessment
        capability = "NOT_RECOMMENDED"
        reasons = []
        
        if cpu_threads < 4:
            reasons.append("⚠️ Low CPU thread count (<4)")
        else:
            reasons.append(f"✅ {cpu_threads} CPU threads available")
        
        if memory_gb < 4:
            reasons.append("⚠️ Low RAM (<4GB)")
        else:
            reasons.append(f"✅ {memory_gb:.1f}GB RAM available")
        
        # Check if laptop
        battery = None
        try:
            battery = psutil.sensors_battery()
        except:
            pass
        
        if battery:
            reasons.append("⚠️ Laptop detected - mining can damage hardware")
            capability = "LAPTOP_WARNING"
        else:
            if cpu_threads >= 8 and memory_gb >= 8:
                capability = "MODERATE"
                reasons.append("🟡 Decent mining capability (still likely unprofitable)")
            elif cpu_threads >= 4:
                capability = "MINIMAL"
                reasons.append("🟠 Minimal mining capability")
        
        return {
            "capability": capability,
            "reasons": reasons,
            "recommended": False,
            "warning": "⚠️ CPU mining is generally unprofitable and can damage hardware"
        }
    
    def get_running_processes(self, limit: int = 50) -> Dict[str, Any]:
        """
        Get list of running processes
        """
        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'status']):
                try:
                    pinfo = proc.info
                    processes.append({
                        "pid": pinfo['pid'],
                        "name": pinfo['name'],
                        "cpu_percent": round(pinfo['cpu_percent'], 2),
                        "memory_percent": round(pinfo['memory_percent'], 2),
                        "status": pinfo['status']
                    })
                except:
                    pass
            
            # Sort by CPU usage
            processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
            
            return {
                "success": True,
                "total_processes": len(processes),
                "top_processes": processes[:limit]
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def analyze_app_issues(self, app_name: str = None) -> Dict[str, Any]:
        """
        Analyze application issues and provide solutions
        """
        try:
            issues = []
            solutions = []
            
            # Get system metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            
            # Check for common issues
            if cpu_percent > 80:
                issues.append("🔴 High CPU usage detected")
                solutions.append("Solution: Close unnecessary applications or upgrade CPU")
            
            if memory.percent > 85:
                issues.append("🔴 High memory usage detected")
                solutions.append("Solution: Close memory-heavy apps or add more RAM")
            
            # If specific app provided, check it
            if app_name:
                app_found = False
                for proc in psutil.process_iter(['name', 'cpu_percent', 'memory_percent']):
                    try:
                        if app_name.lower() in proc.info['name'].lower():
                            app_found = True
                            cpu = proc.info['cpu_percent']
                            mem = proc.info['memory_percent']
                            
                            if cpu > 50:
                                issues.append(f"⚠️ {app_name} using high CPU ({cpu:.1f}%)")
                                solutions.append(f"Solution: Restart {app_name} or check for updates")
                            
                            if mem > 30:
                                issues.append(f"⚠️ {app_name} using high memory ({mem:.1f}%)")
                                solutions.append(f"Solution: Clear {app_name} cache or restart")
                    except:
                        pass
                
                if not app_found:
                    issues.append(f"❌ {app_name} not currently running")
                    solutions.append(f"Solution: Start {app_name} or check installation")
            
            # Check disk space
            disk = psutil.disk_usage('/')
            if disk.percent > 90:
                issues.append("🔴 Low disk space")
                solutions.append("Solution: Free up disk space or add storage")
            
            # Check for zombie processes
            zombie_count = 0
            for proc in psutil.process_iter(['status']):
                try:
                    if proc.info['status'] == psutil.STATUS_ZOMBIE:
                        zombie_count += 1
                except:
                    pass
            
            if zombie_count > 0:
                issues.append(f"⚠️ {zombie_count} zombie processes detected")
                solutions.append("Solution: Restart affected applications")
            
            return {
                "success": True,
                "app_name": app_name,
                "issues_found": len(issues),
                "issues": issues,
                "solutions": solutions,
                "system_health": "CRITICAL" if len(issues) > 3 else "WARNING" if len(issues) > 0 else "HEALTHY"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def crypto_mining_info(self) -> Dict[str, Any]:
        """
        Get cryptocurrency mining information
        """
        return {
            "success": True,
            "warning": "⚠️ IMPORTANT: CPU mining is generally NOT profitable",
            "reality_check": {
                "bitcoin": {
                    "mineable_on_laptop": False,
                    "reason": "Requires specialized ASIC hardware",
                    "estimated_daily_profit": "$0.00 (impossible)"
                },
                "ethereum": {
                    "mineable_on_laptop": False,
                    "reason": "Moved to Proof of Stake (no mining)",
                    "estimated_daily_profit": "$0.00 (not possible)"
                },
                "monero": {
                    "mineable_on_laptop": True,
                    "reason": "CPU-friendly algorithm (RandomX)",
                    "estimated_daily_profit": "$0.01 - $0.50 (before electricity)",
                    "actual_profit": "NEGATIVE (electricity costs more)"
                },
                "ravencoin": {
                    "mineable_on_laptop": "Limited",
                    "reason": "GPU mining primarily",
                    "estimated_daily_profit": "$0.10 - $1.00 (with good GPU)",
                    "actual_profit": "NEGATIVE on most laptops"
                }
            },
            "hardware_risks": [
                "🔥 Overheating (can damage components)",
                "⚡ Reduced laptop lifespan",
                "🔋 Rapid battery degradation",
                "💰 High electricity costs",
                "🐢 Extremely slow mining speed"
            ],
            "recommendations": [
                "✅ Use cloud mining services instead",
                "✅ Join mining pools if you insist",
                "✅ Monitor temperature constantly",
                "✅ Calculate profitability first",
                "✅ Consider buying crypto instead"
            ],
            "cpu_capability": self._check_mining_capability(),
            "mineable_coins": [
                {
                    "name": "Monero (XMR)",
                    "algorithm": "RandomX",
                    "cpu_friendly": True,
                    "profitable": False,
                    "note": "Best CPU option but still unprofitable"
                }
            ]
        }
    
    def start_monitoring(self, duration_seconds: int = 60) -> Dict[str, Any]:
        """
        Monitor system for specified duration
        """
        try:
            samples = []
            interval = 5  # Sample every 5 seconds
            num_samples = duration_seconds // interval
            
            for i in range(num_samples):
                sample = {
                    "timestamp": datetime.now().isoformat(),
                    "cpu_percent": psutil.cpu_percent(interval=1),
                    "memory_percent": psutil.virtual_memory().percent,
                    "disk_io": psutil.disk_io_counters()._asdict(),
                    "net_io": psutil.net_io_counters()._asdict()
                }
                samples.append(sample)
                
                if i < num_samples - 1:
                    time.sleep(interval - 1)  # -1 because cpu_percent takes 1 second
            
            # Calculate averages
            avg_cpu = sum(s['cpu_percent'] for s in samples) / len(samples)
            avg_memory = sum(s['memory_percent'] for s in samples) / len(samples)
            
            return {
                "success": True,
                "duration_seconds": duration_seconds,
                "samples_collected": len(samples),
                "average_cpu_percent": round(avg_cpu, 2),
                "average_memory_percent": round(avg_memory, 2),
                "samples": samples
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def optimize_system(self) -> Dict[str, Any]:
        """
        Provide system optimization recommendations
        """
        try:
            optimizations = []
            
            # Check memory usage
            memory = psutil.virtual_memory()
            if memory.percent > 80:
                optimizations.append({
                    "category": "Memory",
                    "issue": f"High memory usage ({memory.percent}%)",
                    "recommendation": "Close unnecessary applications",
                    "priority": "HIGH"
                })
            
            # Check CPU usage
            cpu_percent = psutil.cpu_percent(interval=2)
            if cpu_percent > 70:
                optimizations.append({
                    "category": "CPU",
                    "issue": f"High CPU usage ({cpu_percent}%)",
                    "recommendation": "Identify and close CPU-intensive processes",
                    "priority": "HIGH"
                })
            
            # Check disk space
            disk = psutil.disk_usage('/')
            if disk.percent > 85:
                optimizations.append({
                    "category": "Disk",
                    "issue": f"Low disk space ({disk.percent}% full)",
                    "recommendation": "Free up disk space by deleting unnecessary files",
                    "priority": "CRITICAL"
                })
            
            # Check for background processes
            process_count = len(list(psutil.process_iter()))
            if process_count > 200:
                optimizations.append({
                    "category": "Processes",
                    "issue": f"Many processes running ({process_count})",
                    "recommendation": "Disable unnecessary startup programs",
                    "priority": "MEDIUM"
                })
            
            return {
                "success": True,
                "optimizations_found": len(optimizations),
                "optimizations": optimizations,
                "system_score": max(0, 100 - len(optimizations) * 15)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

class CryptoMiner:
    """
    Educational crypto mining implementation
    
    ⚠️ WARNING: This is for EDUCATIONAL purposes only!
    Real mining requires specialized software (XMRig, etc.)
    """
    
    def __init__(self):
        self.mining = False
        self.hashes_computed = 0
        
    def calculate_profitability(self, cpu_threads: int = 4) -> Dict[str, Any]:
        """
        Calculate realistic mining profitability
        """
        # Realistic hashrate for CPU (H/s for Monero RandomX)
        hashrate_per_thread = 50  # Very optimistic for modern CPU
        total_hashrate = cpu_threads * hashrate_per_thread
        
        # Current Monero network difficulty (approximate)
        network_hashrate = 2_500_000_000  # 2.5 GH/s (approximate)
        xmr_price = 165  # Approximate USD price
        block_reward = 0.6  # XMR per block
        
        # Calculate daily earnings
        your_share = total_hashrate / network_hashrate
        blocks_per_day = 720  # Monero: 2 min blocks
        daily_xmr = your_share * blocks_per_day * block_reward
        daily_usd = daily_xmr * xmr_price
        
        # Calculate electricity cost
        cpu_tdp = 65  # Watts (typical)
        hours_per_day = 24
        kwh_per_day = (cpu_tdp * hours_per_day) / 1000
        electricity_cost_per_kwh = 0.12  # USD
        daily_electricity_cost = kwh_per_day * electricity_cost_per_kwh
        
        # Net profit
        daily_profit = daily_usd - daily_electricity_cost
        monthly_profit = daily_profit * 30
        yearly_profit = daily_profit * 365
        
        return {
            "success": True,
            "coin": "Monero (XMR)",
            "hashrate_hs": total_hashrate,
            "daily_earnings_xmr": round(daily_xmr, 8),
            "daily_earnings_usd": round(daily_usd, 2),
            "daily_electricity_cost_usd": round(daily_electricity_cost, 2),
            "daily_net_profit_usd": round(daily_profit, 2),
            "monthly_net_profit_usd": round(monthly_profit, 2),
            "yearly_net_profit_usd": round(yearly_profit, 2),
            "profitable": daily_profit > 0,
            "warning": "⚠️ These are OPTIMISTIC estimates. Real results will be worse.",
            "reality": "Most CPU mining loses money due to electricity costs",
            "recommendation": "DON'T mine on laptop. Buy crypto instead." if daily_profit < 1 else "Still not recommended"
        }
    
    def simulate_mining(self, duration_seconds: int = 10) -> Dict[str, Any]:
        """
        Simulate mining (educational demonstration)
        This is NOT real mining - just demonstrates the concept
        """
        try:
            start_time = time.time()
            hashes = 0
            
            # Simulate hash computation
            while time.time() - start_time < duration_seconds:
                # Simple hash computation (NOT actual mining algorithm)
                data = f"block_{hashes}_{time.time()}".encode()
                hash_result = hashlib.sha256(data).hexdigest()
                hashes += 1
                
                # Small delay to prevent maxing out CPU
                time.sleep(0.001)
            
            elapsed = time.time() - start_time
            hashrate = hashes / elapsed
            
            return {
                "success": True,
                "note": "This is SIMULATED MINING (not real)",
                "duration_seconds": round(elapsed, 2),
                "hashes_computed": hashes,
                "hashrate_hs": round(hashrate, 2),
                "warning": "Real mining requires specialized software like XMRig",
                "earnings_estimate": "$0.00 (simulation only)"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

# Global instances
system_integration = SystemIntegration()
crypto_miner = CryptoMiner()
