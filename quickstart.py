#!/usr/bin/env python3
"""
Quick Start Script for F&O Trading Bot

Usage: python quickstart.py
"""

import os
import sys
from pathlib import Path

def print_banner():
    print("\n" + "="*60)
    print(" F&O Trading Bot - Quick Start Setup")
    print("="*60 + "\n")

def check_python_version():
    """Check Python version."""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ required. You have:", sys.version)
        sys.exit(1)
    print("✓ Python version OK:", sys.version.split()[0])

def install_dependencies():
    """Install required packages."""
    print("\nInstalling dependencies...")
    try:
        import subprocess
        result = subprocess.run(
            ["pip", "install", "-r", "requirements.txt"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print("✓ Dependencies installed successfully")
        else:
            print("❌ Failed to install dependencies")
            print(result.stderr)
            sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

def setup_credentials():
    """Setup API credentials."""
    print("\nSetting up Zerodha API Credentials...")
    print("Get these from: https://console.zerodha.com/\n")
    
    api_key = input("Enter KITE_API_KEY: ").strip()
    if not api_key:
        print("❌ API Key cannot be empty")
        return False
    
    api_secret = input("Enter KITE_API_SECRET: ").strip()
    if not api_secret:
        print("❌ API Secret cannot be empty")
        return False
    
    access_token = input("Enter KITE_ACCESS_TOKEN: ").strip()
    if not access_token:
        print("❌ Access Token cannot be empty")
        return False
    
    # Create .env file
    env_content = f"""KITE_API_KEY={api_key}
KITE_API_SECRET={api_secret}
KITE_ACCESS_TOKEN={access_token}
"""
    
    try:
        with open('.env', 'w') as f:
            f.write(env_content)
        print("✓ .env file created successfully")
        print("⚠️  Keep this file secure! Don't commit to git.")
        return True
    except Exception as e:
        print(f"❌ Failed to create .env: {e}")
        return False

def configure_trading_params():
    """Configure trading parameters."""
    print("\nConfigure Trading Parameters...")
    print("(Press Enter to use defaults)\n")
    
    max_profit = input("Max daily profit target [1000]: ").strip() or "1000"
    max_loss = input("Max daily loss allowed [500]: ").strip() or "500"
    symbols = input("Trading symbols [BANKNIFTY,NIFTY]: ").strip() or "BANKNIFTY,NIFTY"
    
    try:
        with open('config/settings.py', 'r') as f:
            content = f.read()
        
        content = content.replace('MAX_DAILY_PROFIT = ', f'MAX_DAILY_PROFIT = {max_profit}\n# ')
        content = content.replace('MAX_DAILY_LOSS = ', f'MAX_DAILY_LOSS = {max_loss}\n# ')
        
        with open('config/settings.py', 'w') as f:
            f.write(content)
        
        print("✓ Trading parameters configured")
        return True
    except Exception as e:
        print(f"❌ Failed to configure: {e}")
        return False

def test_connection():
    """Test API connection."""
    print("\nTesting Zerodha API Connection...")
    
    try:
        from config import settings
        from kiteconnect import KiteConnect
        
        if not settings.KITE_API_KEY or not settings.KITE_ACCESS_TOKEN:
            print("⚠️  Credentials not set. Skipping connection test.")
            return True
        
        kite = KiteConnect(api_key=settings.KITE_API_KEY)
        kite.set_access_token(settings.KITE_ACCESS_TOKEN)
        
        # Try to fetch LTP
        data = kite.ltp(['NSE:BANKNIFTY'])
        print("✓ API connection successful!")
        print(f"  Current BANKNIFTY LTP: {data}")
        return True
    except Exception as e:
        print(f"⚠️  Connection test failed: {e}")
        print("   Make sure market is open (9:15 AM - 3:30 PM)")
        return True

def create_logs_directory():
    """Create logs directory."""
    try:
        Path('logs').mkdir(exist_ok=True)
        print("✓ Logs directory ready")
    except Exception as e:
        print(f"❌ Failed to create logs directory: {e}")
        return False
    return True

def print_next_steps():
    """Print next steps."""
    print("\n" + "="*60)
    print(" Setup Complete! Next Steps:")
    print("="*60)
    print("""
1. Review configuration:
   - Edit config/settings.py for custom parameters
   
2. Backtest the strategy (optional but recommended):
   python -c "
   from src.backtester import Backtester
   from src.strategy import Strategy
   import pandas as pd
   
   # You'll need historical data CSV
   # data = pd.read_csv('historical_data.csv')
   # bt = Backtester(Strategy())
   # results = bt.run_backtest(data)
   # bt.print_results()
   "

3. Run the trading bot:
   python src/main.py

4. Monitor logs:
   tail -f logs/trading.log

5. Check positions in Zerodha web interface
   https://kite.zerodha.com

📖 For more info, read:
   - README.md
   - SETUP_GUIDE.md
   - STRATEGY_GUIDE.md

⚠️  WARNING: 
   - Start with paper trading first!
   - Never leave bot unattended
   - Always use stop losses
   - Risk management is critical!

""")
    print("="*60 + "\n")

def main():
    """Main setup flow."""
    print_banner()
    
    try:
        # Step 1: Check Python
        check_python_version()
        
        # Step 2: Install dependencies
        install_dependencies()
        
        # Step 3: Create logs directory
        create_logs_directory()
        
        # Step 4: Setup credentials
        if not setup_credentials():
            sys.exit(1)
        
        # Step 5: Configure trading parameters
        configure_trading_params()
        
        # Step 6: Test connection
        test_connection()
        
        # Step 7: Print next steps
        print_next_steps()
        
        print("✓ Setup complete! Ready to trade.\n")
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Setup cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
