#!/usr/bin/env python3
"""
Test configurable Strong Start gap percentage
Shows how to change the gap percentage in config.py
"""

import sys
import os
import logging
from datetime import datetime
import pytz

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

IST = pytz.timezone('Asia/Kolkata')

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_different_gap_percentages():
    """Test Strong Start with different gap percentages"""
    logger.info("🧪 Testing Configurable Strong Start Gap Percentage")
    logger.info(f"Current time: {datetime.now(IST).strftime('%H:%M:%S')}")
    
    # Test different gap percentages
    test_cases = [
        {'gap_pct': 0.015, 'name': '1.5%'},
        {'gap_pct': 0.020, 'name': '2.0% (default)'},
        {'gap_pct': 0.021, 'name': '2.1%'},
        {'gap_pct': 0.025, 'name': '2.5%'},
    ]
    
    # Test stock data
    test_stock = {
        'symbol': 'AVANTEL',
        'prev_close': 138.14,
        'current_low': 140.50
    }
    
    for test_case in test_cases:
        logger.info(f"\n{'='*50}")
        logger.info(f"Testing Strong Start with {test_case['name']} gap")
        logger.info(f"{'='*50}")
        
        # Calculate required opening price for this gap percentage
        required_open = test_stock['prev_close'] * (1.0 + test_case['gap_pct'])
        logger.info(f"Required opening price for {test_case['name']} gap: ₹{required_open:.2f}")
        
        # Test if current low satisfies Strong Start conditions
        open_equals_low = abs(required_open - test_stock['current_low']) / required_open <= 0.01
        
        if open_equals_low:
            logger.info(f"✅ Strong Start conditions met with {test_case['name']} gap!")
            logger.info(f"   Gap: {test_case['gap_pct']*100:.1f}%, Open≈Low: ₹{test_stock['current_low']:.2f}")
        else:
            logger.info(f"❌ Strong Start conditions NOT met with {test_case['name']} gap")
            logger.info(f"   Gap: {test_case['gap_pct']*100:.1f}%, Open≈Low check failed")

def show_config_usage():
    """Show how to use the configurable gap percentage"""
    logger.info(f"\n{'='*60}")
    logger.info("CONFIGURATION USAGE")
    logger.info(f"{'='*60}")
    logger.info("To change the Strong Start gap percentage:")
    logger.info("1. Edit src/trading/live_trading/config.py")
    logger.info("2. Change STRONG_START_GAP_PCT value:")
    logger.info("   - STRONG_START_GAP_PCT = 0.015  # 1.5%")
    logger.info("   - STRONG_START_GAP_PCT = 0.020  # 2.0% (default)")
    logger.info("   - STRONG_START_GAP_PCT = 0.021  # 2.1%")
    logger.info("   - STRONG_START_GAP_PCT = 0.025  # 2.5%")
    logger.info("3. Save the file")
    logger.info("4. Restart the reversal bot")
    logger.info("5. The bot will use your new gap percentage automatically!")
    logger.info(f"{'='*60}")

def main():
    """Main test function"""
    logger.info("=" * 60)
    logger.info("TESTING: Configurable Strong Start Gap Percentage")
    logger.info("=" * 60)
    
    test_different_gap_percentages()
    show_config_usage()
    
    logger.info("🎉 Configuration test completed!")
    logger.info("You can now easily adjust the Strong Start gap percentage in config.py")

if __name__ == "__main__":
    main()
