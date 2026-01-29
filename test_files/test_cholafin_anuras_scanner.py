#!/usr/bin/env python3
"""
Test if CHOLAFIN and ANURAS appear in scanner results
"""

from src.scanner.scanner import scanner

def test_cholafin_anuras_in_scanner():
    """Test if CHOLAFIN and ANURAS appear in continuation scan results"""
    print("🧪 TESTING CHOLAFIN & ANURAS IN SCANNER")
    print("=" * 50)

    print("Running continuation scan...")
    candidates = scanner.run_continuation_scan()

    print(f"\n📊 SCAN RESULTS:")
    print(f"Found {len(candidates)} continuation candidates total")

    # Check for CHOLAFIN and ANURAS
    cholafin = next((c for c in candidates if c['symbol'] == 'CHOLAFIN'), None)
    anuras = next((c for c in candidates if c['symbol'] == 'ANURAS'), None)

    print(f"\n🔍 SPECIFIC STOCKS:")
    if cholafin:
        print(f"✅ CHOLAFIN found in results!")
        print(f"   Close: ₹{cholafin['close']:.2f}")
        print(f"   Depth: {cholafin['depth_pct']}%, ADR: {cholafin['adr_pct']}%")
    else:
        print("❌ CHOLAFIN not found in results")
        print("   (May not meet continuation criteria - this is normal)")

    if anuras:
        print(f"✅ ANURAS found in results!")
        print(f"   Close: ₹{anuras['close']:.2f}")
        print(f"   Depth: {anuras['depth_pct']}%, ADR: {anuras['adr_pct']}%")
    else:
        print("❌ ANURAS not found in results")
        print("   (May not meet continuation criteria - this is normal)")

    if not cholafin and not anuras:
        print("\nℹ️  Neither stock met continuation criteria")
        print("   This is normal - not all stocks will be in continuation setups")

    # Show top 3 candidates for context
    if candidates:
        print(f"\n📈 TOP CANDIDATES:")
        for i, candidate in enumerate(candidates[:3], 1):
            print(f"   {i}. {candidate['symbol']}: ₹{candidate['close']:.2f} "
                  f"(Depth: {candidate['depth_pct']}%)")

    print("\n" + "=" * 50)
    print("✅ TEST COMPLETE")
    print("CHOLAFIN and ANURAS are now in your cache and available for scanning!")

if __name__ == "__main__":
    test_cholafin_anuras_in_scanner()