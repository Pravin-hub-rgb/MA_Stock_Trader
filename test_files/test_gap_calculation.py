#!/usr/bin/env python3
"""
Simple test for gap calculation logic without WebSocket dependency
Tests the expert's solution: First tick as opening price
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

class TestReversalStock:
    """Test class for first tick opening price tracking"""
    
    def __init__(self, symbol):
        self.symbol = symbol
        self.prev_close = None
        self.open_price = None
        self.first_tick_captured = False
        self.current_low = float('inf')
        self.gap_calculated = False
        
    def update_tick(self, price, timestamp):
        """Track first tick as opening price"""
        if not self.first_tick_captured:
            self.open_price = price
            self.first_tick_captured = True
            logger.info(f"✅ {self.symbol}: Captured first tick as open = ₹{price:.2f} (bot start time)")
            return True
        return False
    
    def calculate_gap(self):
        """Calculate gap percentage using first tick as opening price"""
        if self.open_price and self.prev_close:
            gap_pct = ((self.open_price - self.prev_close) / self.prev_close) * 100
            logger.info(f"📊 {self.symbol}: Gap % = {gap_pct:.2f}% (Open: ₹{self.open_price:.2f}, Prev Close: ₹{self.prev_close:.2f})")
            self.gap_calculated = True
            return gap_pct
        logger.warning(f"⚠️ {self.symbol}: Missing open or prev_close for gap calculation")
        return None
    
    def check_oops_conditions(self, current_price):
        """Check OOPS reversal conditions"""
        if not self.gap_calculated:
            return False
            
        gap_pct = ((self.open_price - self.prev_close) / self.prev_close) * 100
        crosses_prev_close = current_price > self.prev_close
        
        if gap_pct <= -2.0 and crosses_prev_close:
            logger.info(f"🎯 {self.symbol}: OOPS conditions met! Gap: {gap_pct:.2f}%, Crossed Prev Close: ₹{current_price:.2f}")
            return True
        return False
    
    def check_strong_start_conditions(self, current_low):
        """Check Strong Start conditions"""
        if not self.gap_calculated:
            return False
            
        gap_pct = ((self.open_price - self.prev_close) / self.prev_close) * 100
        open_equals_low = abs(self.open_price - current_low) / self.open_price <= 0.01
        
        if gap_pct >= 2.0 and open_equals_low:
            logger.info(f"🚀 {self.symbol}: Strong Start conditions met! Gap: {gap_pct:.2f}%, Open≈Low: ₹{current_low:.2f}")
            return True
        return False

def test_gap_calculation():
    """Test gap calculation with sample data"""
    logger.info("🧪 Testing Gap Calculation Logic (No WebSocket)")
    logger.info(f"Current time: {datetime.now(IST).strftime('%H:%M:%S')}")
    
    # Test stocks with sample data
    test_stocks = [
        {
            'symbol': 'ELECON',
            'prev_close': 375.10,
            'first_tick': 366.95,  # Gap down
            'current_price': 376.00  # Crosses prev close
        },
        {
            'symbol': 'AVANTEL', 
            'prev_close': 138.14,
            'first_tick': 141.00,  # Gap up 2.07%
            'current_low': 140.50  # Open ≈ Low
        },
        {
            'symbol': 'ARISINFRA',
            'prev_close': 108.44,
            'first_tick': 105.00,  # Gap down
            'current_price': 109.00  # Crosses prev close
        }
    ]
    
    all_tests_passed = True
    
    for test_data in test_stocks:
        logger.info(f"\n{'='*50}")
        logger.info(f"Testing {test_data['symbol']}")
        logger.info(f"{'='*50}")
        
        # Create test stock
        stock = TestReversalStock(test_data['symbol'])
        stock.prev_close = test_data['prev_close']
        
        # Simulate first tick
        logger.info(f"Simulating first tick: ₹{test_data['first_tick']:.2f}")
        first_tick_captured = stock.update_tick(test_data['first_tick'], datetime.now())
        
        if first_tick_captured:
            # Calculate gap
            gap = stock.calculate_gap()
            
            if gap is not None:
                # Test OOPS conditions
                if 'current_price' in test_data:
                    oops_triggered = stock.check_oops_conditions(test_data['current_price'])
                    if oops_triggered:
                        logger.info(f"✅ OOPS test PASSED for {test_data['symbol']}")
                    else:
                        logger.info(f"❌ OOPS test FAILED for {test_data['symbol']}")
                        all_tests_passed = False
                
                # Test Strong Start conditions  
                if 'current_low' in test_data:
                    strong_start_triggered = stock.check_strong_start_conditions(test_data['current_low'])
                    if strong_start_triggered:
                        logger.info(f"✅ Strong Start test PASSED for {test_data['symbol']}")
                    else:
                        logger.info(f"❌ Strong Start test FAILED for {test_data['symbol']}")
                        all_tests_passed = False
            else:
                logger.error(f"❌ Gap calculation FAILED for {test_data['symbol']}")
                all_tests_passed = False
        else:
            logger.error(f"❌ First tick capture FAILED for {test_data['symbol']}")
            all_tests_passed = False
    
    logger.info(f"\n{'='*50}")
    if all_tests_passed:
        logger.info("🎉 ALL TESTS PASSED!")
        logger.info("✅ First tick as opening price logic works correctly")
        logger.info("✅ Gap calculation works correctly")
        logger.info("✅ OOPS detection works correctly")
        logger.info("✅ Strong Start detection works correctly")
    else:
        logger.error("❌ Some tests failed")
    logger.info(f"{'='*50}")
    
    return all_tests_passed

def main():
    """Main test function"""
    logger.info("=" * 60)
    logger.info("TESTING: Gap Calculation Logic (Expert Solution)")
    logger.info("=" * 60)
    
    success = test_gap_calculation()
    
    if success:
        logger.info("🎉 Logic test completed successfully!")
        logger.info("The expert's solution works: First tick = opening price")
        logger.info("Ready to implement in reversal bot!")
    else:
        logger.error("❌ Logic test failed")
    
    logger.info("=" * 60)

if __name__ == "__main__":
    main()
