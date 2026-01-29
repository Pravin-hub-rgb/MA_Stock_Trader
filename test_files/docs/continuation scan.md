Yes, let's keep discussing—I'm glad you're clarifying these points, as it helps make the pattern detection more precise and less subjective. I'll summarize my updated understanding based on your refinements, then dive into the tricky areas (like pullback depth), and suggest ways to handle them. We'll brainstorm solutions together without code, focusing on logic that feels right for your trading style (e.g., not too aggressive, but reliable for NSE stocks in the 100-2000 price range).

### Updated Understanding of the Pattern
Based on your feedback, here's how I'm seeing it now (building on our previous discussion):

1. **Phase 1 – Initial Strength (Up Move)**:  
   Price has been trading **above the 20 SMA** recently (not ancient history—more on "recent" below). This shows the stock had a bullish push. The "highs" from this phase become a reference point (e.g., the peak high before the pullback starts).

2. **Phase 2 – Pullback**:  
   Price then corrects downward, and to qualify as a real pullback, the **close must go below the 20 SMA** (not just wicks touching below— that wouldn't feel significant enough, as you said). This dip creates separation from the Phase 1 highs.  
   - Key: It can't be too shallow (just grazing the MA with wicks), but also not defined by a fixed % drop because that varies by stock price (your big concern—₹5 on a ₹100 stock feels big, but on ₹1800 it's tiny).

3. **Phase 3 – Re-approach / Retest**:  
   Price starts recovering upward from the pullback low, but this recovery **high should be below the Phase 1 highs** (yes, I get it now—this creates a "lower high" structure, making it look like a triangle, flag, or consolidation pattern, which is classic for continuations).  
   - "Near" the 20 SMA: Price gets within **5%** (your suggestion—good starting point, as it's forgiving but not too loose). Touching is okay (body can wick down to it), but to avoid aggressive entries, the **close must be above the 20 SMA** on the latest day (or the day you're scanning). Slightly above is fine; below close would invalidate.  
   - This phase confirms the "triangle kinda pattern" you mentioned—price squeezing between the Phase 1 high (resistance) and the rising 20 SMA (support).

4. **Rising 20 SMA Condition**:  
   Must hold during Phase 3 (current 20 SMA > highest 20 SMA of the previous 7 days). This is already in your base filters indirectly, but we'll ensure it's checked at the retest point. It weeds out flat/downtrending MAs like in SBIN.

5. **Overall Filters**:  
   - No additional trend filters (e.g., no 50/200 SMA)—just ensure current close > 20 SMA (which aligns with Phase 3).  
   - If the pullback lasts too long (price stays below MA for weeks), the MA might flatten or decline, so the rising filter naturally rejects those.  
   - Volume/ADR/Price: Handled by your base config (e.g., ADR >3% for volatility, volume >1M on at least 1 recent day, price 100-2000 to focus on liquid mids).

This sounds like a **bull flag or pennant on the 20 SMA**—price breaks up, flags down to MA support, then coils near it for continuation. Your examples fit: Strides had a clear dip below MA then retest above with lower high; SBIN's flat MA rejected it.

Does this still match? Any tweaks to the phases?

### Discussing the Tricky Parts
You're right—this scanner is tough because it's multi-day and contextual (not a simple RSI or pattern like engulfing). The subjectivity (e.g., "deep enough pullback?") makes it hard to code perfectly, but we can objectify it with rules that approximate what your eye sees on charts. Let's break down your questions/concerns:

1. **"Near" in Phase 3 (Your Take: 5%, Touching OK, Close > MA)**:  
   This seems solid—not too tight (1-2% might miss noisy days), but not so loose it catches everything. 5% works for most stocks in your price range (e.g., ₹5-10 on ₹100-200, ₹90-100 on ₹1800-2000).  
   - "Touching": If the body (open/close) hits the MA, or even if low wick touches but close > MA, it's fine—as long as the candle isn't fully below.  
   - Why close > MA? It confirms bullish control at EOD, reducing false positives from intra-day fakes.  
   Suggestion: Make the tolerance asymmetric—e.g., allow up to 5% above MA (for "near from above"), but only 2% below (since you want above bias). Thoughts?

2. **Pullback Depth (Your Concern: Hard to % Because of Price Variation)**:  
   Yeah, this is the hardest part—fixed % doesn't scale (5% on low-price stocks = big move, on high-price = small wiggle). If too shallow (just wicks below), it doesn't "feel" like a real correction; if too deep, it might be a reversal, not continuation.  
   - Your "mannn I don't know" is valid—many traders struggle with this in scanners.  
   - Better way: Normalize with **volatility** (using your ADR filter). E.g., require the pullback depth to be at least **1x ADR** (since ADR is ~3% min in your base, this means ~3%+ drop from Phase 1 high to pullback low, but scaled to the stock's normal range).  
     - Why ADR? It's percentage-based but per-stock (a ₹200 stock with 5% ADR needs ~₹10 drop; ₹1800 with 3% ADR needs ~₹54). This covers your confusion—high-price stocks often have lower % volatility, so it adjusts.  
     - Alternative: Use ATR (Average True Range)—similar to ADR, but includes gaps (ATR = avg of max(high-low, |high-prev close|, |low-prev close|)). 1-2x ATR min depth feels "significant" without fixed %.  
   - Min depth: Start with 1x ADR/ATR to filter out shallow wicks-only pullbacks. We can test on your examples (Strides had a decent dip; SBIN too shallow/flat?).  
   What do you think—ADR or ATR? Or skip depth and just require "at least 3-5 closes below MA" (time-based instead of depth)?

3. **Recentness of Phase 1 (Your Take: Recently, Obviously)**:  
   Agreed—not from 6 months ago. To make it concrete: Look back **30-60 trading days** (~1.5-3 months) for the Phase 1 up move and pullback.  
   - Why? Too short (e.g., 10 days) misses setups building over weeks; too long includes stale patterns. 45 days splits the difference.  
   - In practice: Scan backward from today—find the most recent Phase 1 high, then check if pullback and retest happened within that window.  
   Your view: 20-30 days too short, or longer OK?

4. **Volume/Strength (Your Take: Already Covered)**:  
   Cool—your base (1M+ volume on at least 1 day) ensures liquidity. Maybe add "volume spike during Phase 1 up" later if too many weak setups, but skip for now.

5. **Overall Trend / Rising Filter (Your Take: Leave It, Handled by Rising Check)**:  
   Makes sense—the 7-day rising filter at Phase 3 will naturally avoid downtrends (if price lingered below MA, MA would flatten/decline). Plus, current close > 20 MA is built into Phase 3. No need for longer MAs unless you see false positives in tests.

### Next Steps in Discussion
- This pattern detection will involve **scanning backward** from the latest day: Find recent Phase 1 (above MA, set high), confirm Phase 2 (closes below MA, depth >1x ADR), then Phase 3 (recovery high < Phase 1 high, close > MA, within 5%, rising MA).  
- To make the scanner "difficult but doable": Start loose (e.g., 5% near, 1x ADR depth), then tighten based on backtests on 10-20 stocks (like Strides, SBIN, others you like).  
- Potential adds: Require "lower high" in Phase 3 to be at least 2-3 candles (not just 1-day spike).  

What do you think of the ADR/ATR idea for depth? Too complicated, or worth it?  
Any other examples (stocks/dates) to test the logic mentally?  
Let's keep refining—I'm here! 😊



Yes, absolutely—let's keep the discussion going. We're indeed very close to nailing this scanner logic, and your clarification on recentness for Phase 1 is super helpful. It shows the pattern can unfold over varying timeframes, so the code needs to be flexible without being too rigid. I'll summarize how I'm incorporating this, then suggest a practical way to handle it, and we can tweak from there.

### Updated View on Recentness for Phase 1 (and Overall Pattern Timing)
I get it now—when I asked about Phase 1 recentness, you initially thought I meant Phase 3 (the retest, which should be very recent, like the last few days for a fresh setup). But Phase 1 itself can be further back, as long as the whole pattern (Phases 1-3) fits within a reasonable window.

From your Strides example:
- Phase 1 started end of Oct 2025 (price breaking above 20 SMA in early Nov).
- Phase 2 pullback lasted about 1 month (below MA in Dec).
- Phase 3 retest in late Dec / early Jan 2026.
- Total span: ~2-3 months.

You suggest a **max of 4 months** for the entire pattern (from start of Phase 1 to end of Phase 3). That's smart—it prevents catching "ancient" patterns where the momentum has died, but allows for longer pullbacks (e.g., Phase 2 lasting 1-2 months in choppy markets). And yes, it can compress into 1 month or less (e.g., Phase 1: first week, Phase 2: next week, Phase 3: end of month).

Why this matters: In code, we can't have an infinite lookback (too many false positives from old data), but 4 months (~80-100 trading days) is a good cap—covers your examples without overkill. It also fits NSE stocks, where trends can drag in volatile sectors like pharma (Strides) or banking (SBIN).

Suggestion: 
- Set the lookback to **90 trading days** (about 4 months, accounting for holidays/weekends). 
- Scan backward from today: Find the **most recent** qualifying Phase 1 (price above 20 SMA, establishing a high). Then check if Phase 2 (close below MA) and Phase 3 (recovery with lower high, near/above MA) happened after it, all within those 90 days.
- If the pattern spans longer than 90 days, reject it (e.g., Phase 1 from 5 months ago = stale).
- Flexibility: If Phase 2 is long (3-4 months below MA), the rising filter in Phase 3 will likely reject it anyway (MA would flatten), but the cap ensures efficiency.

Does 90 days feel right, or bump to 120 (5-6 months) for safety? Too short might miss slow-builders like Strides.

### Tying It Back to Other Phases
- **Phase 2 Pullback**: With the 4-month cap, a long Phase 2 (e.g., 2-3 months below MA) is OK as long as the retest is fresh and MA starts rising again. But if it drags, your 7-day rising check will filter it out—perfect natural gate.
- **Phase 3 Retest**: This should be **very recent** (last 1-5 days) for tradeability—e.g., the "near MA" and close > MA on the scan day or previous 1-2 days. We can require the recovery to have started within the last 10-20 days after Phase 2 low.
- **Lower High in Phase 3**: To enforce the "triangle kinda pattern," we'll track the Phase 1 high and ensure the Phase 3 peak so far is < that high (e.g., no new highs yet—keeps it consolidated).

### Addressing the Pullback Depth Confusion (From Last Message)
You're spot on—fixed % doesn't work across prices (5% on ₹100 = ₹5, feels deep; on ₹1800 = ₹90, might be normal noise). Using ADR (from your base filter) is a great fit:
- Require Phase 2 depth >= **1-1.5x ADR** (e.g., distance from Phase 1 high to Phase 2 low >= average daily range). Since ADR is ~3%+ in your scans, this ensures "significant" dips without fixed numbers.
- Why? It scales: Volatile low-price stocks need bigger % moves; stable high-price ones need less. Rejects wick-only pullbacks (as you want closes below MA anyway).
- Alternative if ADR feels too variable: Count **min number of closes below MA** (e.g., at least 3-5 days below to confirm "came down"). Time-based is simpler and avoids price bias.

Which do you prefer for depth: ADR-multiple, min days below, or skip and let closes below + rising filter handle it?

### Base Filters Integration
Your config looks good—ADR >3% ensures volatility for the move, volume >1M adds liquidity, price 100-2000 keeps it to your sweet spot (avoids pennies or ultra-expensive). We'll apply these first (pre-pattern check) to filter the universe down, then run the pattern logic on survivors.

### Overall Scanner Flow (High-Level, No Code)
1. Base filters (ADR, volume, price, current close > 20 SMA).
2. Compute 20 SMA + rising check.
3. Look back 90 days: Find recent Phase 1 (above MA period, record high).
4. Check Phase 2 after it (closes below MA, depth >=1x ADR).
5. Check Phase 3 now (recovery high < Phase 1 high, within 5% of MA, close > MA, rising MA).

This should catch Strides (2-3 month span, good depth) and reject SBIN (flat MA).

Thoughts on the lookback/duration? Depth option? Any other filters (e.g., no big gaps in Phase 2)? We're almost there—once we lock this, code will be easy! 😊


Yes, let's continue the discussion—I'm with you on keeping things simple and efficient. You're right; we're super close, and these refinements are helping us avoid overcomplicating it. I'll incorporate your latest points (simple Phase 1, 80-day lookback, fast scanning, rough zig-zag catch with manual cleanup, no sub-limits, 1x ADR for depth) and brainstorm how to make it work practically. No code—just talking through the logic and trade-offs.

### Aligning on Phase 1 Simplicity
Absolutely agree—keep Phase 1 basic: Just identify a period where price was above the 20 SMA (e.g., at least a few closes above to show strength). No need for "breakout" detection (like crossing above with volume or momentum)—that adds complexity and might miss subtle starts like in Strides (end-Oct/early-Nov above MA). Simple = better for a rough scan, and your manual review can judge if the "up" felt strong enough.

### Lookback: 80 Trading Days for the Whole Pattern
Your calculation is spot on—22 trading days/month * 3-4 months ≈ 66-88, so 80 days is a nice round number (covers ~3.5-4 months). It allows for:
- Quick patterns (all in 1 month: Phase 1 first week, Phase 2 mid-month, Phase 3 end).
- Slower ones (like Strides: Phase 1 Oct/Nov, Phase 2 ~1 month, Phase 3 late Dec—total ~2-3 months).
- Max span: Up to 4 months without feeling stale (e.g., Phase 1 Month 1, long Phase 2 Months 2-3, Phase 3 Month 4).

No sub-limits inside (e.g., no forcing Phase 2 to 2 months or Phase 3 after 10-20 days)—that would be too strict and miss variations. Just ensure the **entire sequence (start of Phase 1 to end of Phase 3)** fits within those 80 days. If Phase 1 is older than 80 days, reject (stale momentum). This keeps it simple and flexible.

### Best Way for Scanning: Start from Phase 3 Backward (Efficient for Speed)
You're smart to worry about speed—with 2000+ NSE stocks, looping naively could take minutes/hours if not optimized. Since it's a rough scan (catch zig-zag "up-down-up near" relative to MA, manual filter later), we can make it fast by:

- **Start from Phase 3 (Today Backward)**: Don't begin at Phase 1 and work forward—that could mean checking every day in the 80-day window for every stock (slow for bulk). Instead:
  - Check Phase 3 first on the latest day (or last 1-3 days for freshness): Is close > 20 SMA, within 5% near, and MA rising (current > max of last 7)?
  - If yes, look backward 80 days to find if there was a Phase 2 (closes below MA, with depth >=1x ADR from some prior high).
  - Then, confirm Phase 1 before that (period above MA, establishing the high for "lower high" check in Phase 3).
  - Why backward? Most stocks won't pass Phase 3 (your base filters + rising/near/close > MA are strict), so 80-90% get rejected instantly without deep history checks. For the few that pass, the backward loop is quick (80 days = tiny data).

- **Efficiency Tips**:
  - Pre-load only the last 80+20 days per stock (for SMA calc)—your cache already has this, so no extra fetches.
  - Use vectorized Pandas ops (no slow for-loops inside per-stock checks)—e.g., flags for above/below MA, find most recent below period, calc depth in one go.
  - Rough zig-zag: To catch the "horizontal zig-zag" feel, just verify the sequence exists (up above → down below → up near/above), no fancy wave counting. If multiple zig-zags in 80 days, take the most recent one.
  - Time estimate: On a normal laptop, scanning 2000 stocks should take seconds to 1-2 minutes (Pandas is fast; your base filters cut it to ~200-500 candidates first).

Starting backward from Phase 3 is best—it's "fail-fast" (reject early), keeps it simple, and matches your "rough" goal (catches most zig-zags, you manually remove non-triangle ones).

### Depth: 1x ADR Multiplier (Loose to Catch Most, Refine Later)
Yes, 1x ADR is a good start—since your base is ADR >3%, this means pullback depth >= ~3% (scaled to stock: bigger absolute on high-price, but feels "significant" without rejecting too many). It passes most (avoids over-filtering shallow but valid dips), and as you said, you'll judge/reject manually, then tweak to 1.2x or 1.5x if too many wick-only or tiny pullbacks sneak in.
- How to measure: From the Phase 1 high to the Phase 2 low (as % or absolute / ADR).
- Bonus: Since it's rough, if no clear depth (e.g., very shallow), but closes below MA happened, still pass—let manual eyes decide.

### Overall Simplicity for the Zig-Zag
Love your "simplest zig-zag filter relevant to MA"—that's the spirit. The "up then down then up and near" is essentially:
- Up (Phase 1: above MA sometime in last 80 days).
- Down (Phase 2: closes below after, with mild depth).
- Up and near (Phase 3: recovery to above/near, lower high than Phase 1, rising MA).
No more bells—keeps it fast and catches the horizontal consolidation feel without strict triangle rules.

Does this flow feel right? 80 days too much/too little? Backward start make sense for speed? Any other "rough" rules (e.g., min 2-3 days in each phase)? Let's lock it down! 😊

### Continuation Pullback Scan – Final Specification Document

This document captures the **exact agreed logic** for the new “Continuation Pullback” scan after our full discussion. It is a **rough, fast, multi-day zig-zag pattern** relative to the rising 20-day SMA. The goal is to catch stocks that went up (above 20 SMA), pulled back (closed below 20 SMA), and are now coming back up near or above the 20 SMA with a still-rising MA — creating a horizontal zig-zag or triangle-like consolidation for potential continuation.

The scan is intentionally **rough** — it will catch most candidates, and you will manually review the shortlist (charts + price action) to remove false positives.

#### Base Filters (Applied First – Your Existing Config)
These run on every stock before the pattern logic:
```python
self.continuation_params = {
    'min_volume_days': 1,            # At least 1 day with volume > threshold
    'volume_threshold': 1000000,     # 1M shares
    'min_adr': 0.03,                 # ADR > 3%
    'price_min': 100,                # ₹100 minimum
    'price_max': 2000,               # ₹2000 maximum
}
```
Only stocks passing these go to the pattern check.

#### Pattern Logic – Phase-by-Phase (Efficient Order: Phase 3 First)

**Overall Lookback Window**: Last **80 trading days** (~3.5-4 months). The entire pattern (start of Phase 1 to today) must fit inside this window.

We check in this order for speed (fail-fast):

1. **Phase 3 – Current Retest / Re-approach (Checked First)**
   - Current close **> 20 SMA**
   - Current close is **within 5%** of the 20 SMA (near or touching is fine; body can touch the MA)
   - Current 20 SMA value **> highest 20 SMA of the previous 5 days**  
     (We changed from 7 to 5 days as you requested — more responsive rising filter)
   - If any of these fail → reject immediately (most stocks will fail here)

2. **Phase 2 – Pullback (Checked Second)**
   - Within the last 80 trading days (before today), there must be **at least one close below the 20 SMA**
   - Depth check: Distance from the highest high during the “above MA” period (Phase 1 high) to the lowest low during the “below MA” period must be **≥ 1 × ADR**  
     (Uses the same ADR calculated for the base filter — scalable and fair across price levels)

3. **Phase 1 – Initial Strength (Checked Last)**
   - Within the last 80 trading days (before Phase 2), there must be a period where price was **above the 20 SMA**  
     (Simple — no breakout requirement, just evidence of prior strength above the MA)
   - The recovery high in the last few days (Phase 3) should be **lower than the Phase 1 high**  
     (Gives the triangle / lower-high consolidation feel)

#### Summary Flow (For Coder Reference)
1. Apply base filters (volume, ADR >3%, price range)
2. Compute 20 SMA on last ~100 days (for buffer)
3. **Phase 3 check** on latest day → if fail, skip stock
4. Slice last 80 days
5. **Phase 2 check** → closes below MA + depth ≥1×ADR
6. **Phase 1 check** → prior period above MA + current recovery high < Phase 1 high
7. All yes → add to results with useful columns:
   - Symbol
   - Close
   - SMA20
   - Distance to MA (%)
   - Phase 1 High
   - Phase 2 Low
   - Depth (%)
   - ADR (%)

#### Why This is Fast and Rough
- Phase 3 first → 90%+ stocks rejected instantly
- Vectorized Pandas operations (no slow loops inside per-stock)
- Only ~100 days of data needed per stock (already in cache)
- Full NSE scan should finish in under 1-2 minutes
- Intentionally loose to over-catch → you manually clean the list

#### Future Tweaks (After Testing)
- Rising filter: 5 days now → change to 7 or 10 later if too many flat MAs pass
- Depth multiplier: 1×ADR now → increase to 1.2-1.5 if too many shallow pullbacks
- Near threshold: 5% now → tighten to 3-4% if needed
- Add min days below MA (e.g., 3 closes below) if wick-only pullbacks slip through

This is the **final agreed specification** — no more changes until we test it on real data.

Your coder can now implement this exactly as described. Once done, run it on historical dates (e.g., late Dec 2025 / early Jan 2026) to see if STRIDES (STAR.NS) appears and SBIN is correctly rejected.

Let me know when you want the actual code module based on this doc — we won’t jump ahead until you say go! 😊


Yes, you're right—let's not jump to code at all. I apologize for that; I got ahead because I thought we were aligned, but clearly we need to discuss these details more to get on the same page. We're very close, and I appreciate you pointing out the gaps. Let's break it down point by point, starting with **depth** (the big one you raised), then Phase 1 conditions, and the lower high check. I'll share what I learned from quick research on trading strategies (without code—just ideas), compare our options, and ask questions to refine. Goal: Common ground on reliable, non-strict rules that catch the zig-zag feel without over-filtering.

### Discussing Depth in Phase 2 (The Key Confusion)
You mentioned you were thinking of depth as from the **20 SMA level to the Phase 2 low** (e.g., how far below the MA the price dipped during the pullback). I had suggested from the **Phase 1 high to the Phase 2 low** (full swing from the peak before pullback to the bottom). That's a good catch—we need to agree on which is better for your "significant" but not too strict filter.

From research on pullback/re-test strategies (e.g., in MA continuation like 20 SMA pullbacks):
- Traders often measure depth as the **% retracement from the prior high** (Phase 1 peak) to the low during pullback. This captures the "amplitude" of the zig-zag (how much correction happened). Common thresholds: 38-50% retracement (Fibonacci style) for healthy pullbacks—not too deep (reversal risk) or shallow (no room for entry).
- Some MA-specific strategies (like 20 SMA retests) focus on distance **from the MA itself** (e.g., how far below the MA the low went, as % or ATR multiple). This emphasizes the "separation" from the MA during Phase 2.
- For scanners: Volatility-adjusted (like ADR multiple) is best to avoid price bias (your earlier concern). Fixed % is unreliable; e.g., books like "Trading Pullbacks" suggest 1-2x ATR/ADR for "significant" without strict %.

**Which is more non-strict (loose to catch more) and reliable?**
- **From MA to Phase 2 low**: This is **more non-strict** (looser)—the distance is shorter (only the dip below MA, not the full drop from high). It would pass more stocks, including shallower pullbacks where price just dips a bit below MA (e.g., 3-5% below on a ₹500 stock). Reliable for zig-zag picture? Yes, as you said—it focuses on the "came down to/below MA" feel without requiring a huge swing. Less risk of rejecting good setups in low-vol stocks.
- **From Phase 1 high to Phase 2 low**: This is **stricter**—captures the full correction amplitude (e.g., if Phase 1 rallied 10%, pullback might need 4-5% depth). More reliable for "significant" moves (avoids tiny wiggles), but might reject too many (e.g., if Phase 1 high was close to MA, depth feels small). From research, this is common in "flag/pullback scanners" for momentum stocks.

My take: **From MA to Phase 2 low** aligns better with your vision (better zig-zag picture, as price must cross below MA anyway). It's non-strict enough for rough scan (1x ADR = ~3%+ dip below MA, scalable), and reliable because it ensures the pullback "separated" meaningfully from the MA without being aggressive. We can start with 1x ADR here—loose to over-catch, you manual reject shallow ones, then tighten multiplier later.

What do you think—MA to low, or high to low? Or hybrid (e.g., min from MA, but check full too)?

### Phase 1 Conditions
Yes, keep it simple as we agreed: Phase 1 is just a period in the 80 days where **closes > 20 SMA** (not highs/wicks—closes confirm control above MA). No min days above (loose for rough scan), but must be before Phase 2. Research shows this is standard for "uptrend confirmation" in MA pullback strategies—closes above signal strength without overcomplicating.

Question: How many min closes above for Phase 1 to "count"? 1-2 (very loose), or 3-5 (bit more reliable to avoid 1-day spikes)?

### Lower High Check (Phase 1 High > Phase 3 High)
Got it—use **highs** for this comparison (not closes). Phase 1 high = max high during above-MA period. Phase 3 high = max high in recent recovery (last 3-5 days, since Phase 3 is fresh). This ensures "lower high" for triangle feel, without strict structure.

Yes, Phase 3 is where price is **above MA** (close > MA, within 5%). Question: For Phase 3 high, use just today's high, or max over last few days (e.g., 5, to catch the recovery peak)?

### Other Quick Clarifications
- Rising filter: 5 days as you said—more sensitive than 7, good for catching early rises. We can test and adjust.
- Whole pattern in 80 days: Yes, start of Phase 1 to today.
- Efficiency: Phase 3 first keeps it fast.

We're aligned on 90% now—let's agree on depth method, min closes for Phase 1, and Phase 3 high window. Your thoughts? What feels most reliable/non-strict for your examples (Strides/SBIN)? Ask away if I missed something! 😊

Yes, let's stay in discussion mode—sorry if it felt like jumping; I want us on the same ground too. We're super close, and your points are spot on. The depth complexity is a good one to hash out, and I agree we need to agree on it fully. I'll share what I think based on our talk and some quick research insights (no code—just ideas from pullback/MA strategies like 20 SMA retests). Then, we'll compare the two depth options (from MA vs. from high), why from high feels more logical/reliable as you said, and refine Phase 1 + lower high.

### Quick Research Insights on Depth (To Help Us Decide)
From strategies like 20 MA pullbacks (e.g., "20 SMA Pullback Strategy" or "EMA retest setups"):
- Depth is often measured as the **% retracement from the prior swing high** (Phase 1 peak) to the pullback low. This captures the "full correction size" — e.g., shallow (30-50% retrace = strong trend), deep (60-80% = riskier but still continuation if MA holds).
- Why? It shows how much "giveback" happened before the retest, ensuring it's a real zig-zag, not noise. Combined with "must touch/reach MA," it avoids shallow wicks.
- For MA-focused depth: Some use distance below the MA (e.g., how far the low undershot the MA as % or ATR multiple), but it's rarer because the MA is dynamic (your exact concern: "which day's MA?"). They often pick the MA at the pullback start or average during the dip.
- Reliability: From high is more common/reliable for "significant" (avoids tiny dips), but non-strict if threshold low (1x ADR). From MA is looser but can miss if MA moved a lot during pullback.

This backs your thinking—from high is logical and fixed.

### Depth: From High (Phase 1) to Phase 2 Low Seems Better (As You Said)
I never thought of from MA initially either—your original idea was good, but yes, the complexity is real: "Which MA value?" The MA is moving daily, so do we take the MA on the day price first crosses below (start of Phase 2)? The average MA during the below period? The MA at the Phase 2 low? It's ambiguous, and could lead to inconsistent zig-zags (e.g., if MA rose during pullback, depth feels smaller; if fell, bigger).

Your point on from high: Totally agree—it's **fixed** (one clear Phase 1 high), logical (measures full zig from up peak to down trough), and **not too strict** because:
- Combined with "must close below MA" (your Phase 2 rule), it rejects non-zigzags (e.g., big drop but never below MA = no pullback to MA).
- 1x ADR keeps it loose/non-strict (catches more, as ~3%+ drop from high is common in volatile stocks; manual review rejects if too shallow/deep).
- Reliable for zig-zag picture: Ensures the "down" leg has amplitude (not just a flat wiggle), creating that horizontal consolidation feel. In examples like Strides, the ~50% drop from high was deep (passes easily); SBIN's small dip might fail if <1x ADR, but flat MA rejects anyway.

From MA would be **more non-strict** (shorter distance, passes even tiny undershoots), but less reliable (could catch wicks-only if we mispick the MA day, or ignore the full swing). Solution for MA method: Pick the **MA on the day price first closes below** (simple anchor), but I think from high wins—it's what most MA pullback strategies use, and fixes your complexity worry.

What do you think—stick with from high (logical/fixed/reliable with below MA safeguard)? Or MA with anchored day?

### Phase 1: Judging by Closes > MA
Yes, 100%—use **closes > 20 SMA** for Phase 1 (confirms sustained strength above, not just intra-day spikes). Highs/wicks don't count for "above" — closes show end-of-day control. Min 2-3 closes above? Or 1 (looser for rough scan)?

### Lower High Check: Phase 1 High > Phase 3 High
Got it—use **highs** (not closes) for comparison: Max high in Phase 1 period > max high in Phase 3 recovery. This captures the "lower high" triangle without being strict.

Phase 3 is indeed where price is **above MA** (close > MA, within 5%). For Phase 3 high, last 3-5 days' max high feels right (recent recovery peak, not just today).

### Wrapping Up for Agreement
This refines to common ground: Depth from high (fixed, logical, reliable with 1x ADR non-strict), Phase 1 by closes > MA, lower high by highs. Ask more? Your examples—would Strides pass from high depth (yes, big drop)? SBIN fail (small depth + flat MA)? Let's lock once you say! 😊

Yes, perfect — we are fully aligned now.

**Depth from Phase 1 high to Phase 2 low** is the way to go.  
Your reasoning is spot on:
- The high is a **fixed, unambiguous point** — no "which day's MA?" confusion.
- The **close below MA** condition in Phase 2 already guarantees the price actually came down to the MA zone and crossed it.
- Together they create a real zig-zag: up to a high (Phase 1), meaningful drop from that high (depth ≥ 1×ADR), closes below MA (real pullback), then back up near/above the still-rising MA (Phase 3).
- It’s not too strict because 1×ADR is a low bar for your filtered stocks (ADR >3%), and the manual review will clean up anything that feels too shallow or too deep.

This combination gives the cleanest, most reliable zig-zag picture without overcomplicating.

### Anything Else to Discuss?
Let me quickly check the remaining pieces to make sure nothing is left hanging:

1. **Phase 1 identification**  
   → Just need at least one close > 20 SMA before the Phase 2 (below) period. No minimum number of days above — keep it loose (even 1-2 days above is enough for rough scan).

2. **Phase 3 high for lower-high check**  
   → Max high in the last 5 trading days (captures the recent recovery peak without being too narrow).

3. **Rising MA filter**  
   → Current 20 SMA > highest 20 SMA of the previous 5 days (as you wanted — more sensitive than 7).

4. **Near threshold**  
   → 5% (close can be above or slightly below but within band, but close must be > 20 SMA overall).

5. **Lookback**  
   → 80 trading days total span.

6. **Depth**  
   → Phase 1 high → Phase 2 low ≥ 1×ADR.

I don’t see any other open points. Everything else is already handled by base filters or the fail-fast Phase 3 first approach.

If nothing comes to your mind either — we are truly done with the logic.

So… your call:  
Anything else you want to discuss or tweak?  
Or are you ready to say “create the doc now”?

I’m waiting for your green light. 😊



Yes, you’re absolutely right — thank you for catching that. I was adding an unnecessary restriction with “last 5 days”. That’s too arbitrary and strict for a rough scan.

Let’s correct it properly and keep it simple and logical:

### Lower-High Check (Final Version)
- **Phase 1 high**: The highest high reached during the entire period where price was above the 20 SMA (before Phase 2 pullback started). This is fixed and clear.
- **Phase 3 high**: The highest high reached **from the start of the recovery (the first day price closed back above the 20 SMA after Phase 2) up to today**.

In other words:
- We identify the **most recent close above 20 SMA after the last Phase 2 close below**.
- From that recovery day to today → take the max high in this recovery segment.
- Compare: **Recovery high (Phase 3) < Phase 1 high**

This way:
- No fixed “last 5 days” limit.
- It naturally captures the entire current up-leg in Phase 3.
- Gives the exact “lower high” triangle/consolidation feel you want.
- Still rough and flexible — if the recovery has been going on for 10-15 days, it includes all of it.
- Automatically rejects if price has already broken to new highs (which would mean breakout, not continuation setup).

This matches your thinking perfectly: the high after coming back up to the MA should still be below the previous high from Phase 1.

### Updated Summary (No Other Changes Needed)
- Phase 3 first: close > 20 SMA, within 5%, rising MA (current > max of prev 5 days)
- Phase 2: at least one close below 20 SMA in last 80 days
- Depth: Phase 1 high → Phase 2 low ≥ 1×ADR
- Phase 1: period with close(s) > 20 SMA before Phase 2
- Lower high: max high in recovery segment (from first close back above MA to today) < Phase 1 high
- Whole pattern within 80 trading days

No other open points from my side.

We are now **100% done** with the logic — clean, rough, fast, and exactly matching your zig-zag vision.

Anything else you want to add or adjust?  
Or are you ready to say “create the doc now”?  

Waiting for your final go-ahead. 😊

# Continuation Pullback Scan – Final Specification Document

This document fully captures **every agreed point** from our entire discussion on the "Continuation Pullback" scan. It is a **rough, fast, multi-day zig-zag pattern** relative to the rising 20-day Simple Moving Average (SMA). The goal is to catch stocks that went up (above 20 SMA), pulled back (closed below 20 SMA), and are now coming back up near or above the 20 SMA with a still-rising MA — creating a horizontal zig-zag or triangle-like consolidation for potential continuation.

The scan is intentionally **rough and loose** to over-catch candidates (e.g., no minimum days in phases, low thresholds) — you will manually review the shortlist (e.g., check charts for perfect triangle feel, wick quality, or overall significance) to remove false positives or non-ideal setups.

No sub-limits on individual phases (e.g., no "Phase 2 must be X days" or "Phase 3 after Y days") — the only restriction is the overall 80 trading days for the entire pattern.

## Base Filters (Applied First – Your Existing Config)
These run on every stock before the pattern logic to filter for liquid, volatile stocks in your price range. Only survivors proceed to pattern checks.

```python
self.continuation_params = {
    'min_volume_days': 1,            # At least 1 day with volume > threshold in recent data
    'volume_threshold': 1000000,     # 1M shares
    'min_adr': 0.03,                 # ADR > 3% (calculated over 14 days)
    'price_min': 100,                # ₹100 minimum current price
    'price_max': 2000,               # ₹2000 maximum current price
}
```

- **ADR Calculation**: Average of (High - Low) over last 14 days, as % of current close. (Matches your existing scanner logic.)

## Pattern Overview
- **Timeframe**: Daily EOD OHLCV data (from your cache, e.g., NSEpy or yfinance).
- **SMA**: 20-day Simple Moving Average on Close prices.
- **Overall Lookback Window**: Last **80 trading days** (~3.5-4 months, accounting for ~22 trading days/month). The **entire pattern** (start of Phase 1 to today) must fit inside this window — no exceptions. This prevents stale patterns but allows flexibility (e.g., quick 1-month patterns or slower 3-4 month ones like Strides).
- **Zig-Zag Definition**: Rough "up (above MA) → down (below MA) → up near/above (retest)" relative to rising 20 SMA. No strict structure (e.g., no required triangle perfection) — catch most, manual filter later.
- **Efficiency**: Check Phase 3 first (fail-fast — most stocks rejected instantly). Use vectorized Pandas operations (no slow loops inside per-stock checks). Pre-load only last ~100 days per stock from cache. Full NSE scan (~2000 stocks after base filters) should take <1-2 minutes on a normal laptop.

## Pattern Logic – Phase-by-Phase (Checked in This Order for Speed)
Phases are checked backward from today (efficient). No minimum days or sub-limits in any phase — keep loose for rough over-catch.

1. **Phase 3 – Current Retest / Re-approach (Checked First – Fail-Fast)**
   - Current (latest day) close **> 20 SMA**.
   - Current close is **within 5%** of the 20 SMA (near or touching is fine; body can touch the MA; allows slight above or below but with above bias).
   - Current 20 SMA value **> highest 20 SMA of the previous 5 days** (rising filter — more responsive than 7; tweak later if needed).
   - If any fail → reject the stock immediately (90%+ will fail here, keeping scan fast).

2. **Phase 2 – Pullback (Checked Second)**
   - Within the last 80 trading days (before today), there must be **at least one close below the 20 SMA** (not just wicks — confirms significant dip).
   - Depth check: Distance from **Phase 1 high** to **Phase 2 low** must be **≥ 1 × ADR** (scalable, non-strict threshold; uses ADR from base filter).
     - Phase 2 low = lowest low during the below-MA period.
     - This ensures "significant" zig-zag amplitude without fixed % (avoids price bias — bigger absolute on high-price stocks, but feels meaningful).
     - Combined with "close below MA," it rejects non-pullbacks (e.g., big drop but never below MA = invalid).

3. **Phase 1 – Initial Strength (Checked Last)**
   - Within the last 80 trading days (before Phase 2), there must be a period where price had **close(s) > 20 SMA** (simple evidence of prior strength above MA; no minimum days — even 1 close above is enough for rough scan; no breakout or volume requirements).
   - Phase 1 high = highest high during this above-MA period (used for depth and lower-high checks).

4. **Lower-High Check (Integrated with Phase 3)**
   - The max high in the **recovery segment** (from the first close back above 20 SMA after Phase 2 to today) must be **< Phase 1 high**.
   - This ensures the "lower high" triangle/consolidation feel without strict limits — captures the entire recent up-leg naturally.

## Summary Flow (For Coder Reference – High-Level, No Code)
1. Apply base filters (volume, ADR >3%, price 100-2000, etc.).
2. Compute 20 SMA and indicators on last ~100 days (for buffer).
3. **Phase 3 check** on latest day → if fail, skip stock.
4. Slice last 80 days.
5. **Phase 2 check** → at least one close below MA + depth ≥1×ADR (from Phase 1 high to Phase 2 low).
6. **Phase 1 check** → prior period with close(s) > 20 SMA.
7. **Lower-high check** → recovery max high < Phase 1 high.
8. All yes → add to results.

## Results Output (For GUI/Table)
- Shortlist candidates with these columns (for manual review):
  - Symbol
  - Close
  - SMA20
  - Distance to MA (%)
  - Phase 1 High
  - Phase 2 Low
  - Depth (% from Phase 1 high)
  - ADR (%)
- Save to CSV (e.g., "continuation_hits.csv") or show in table.

## Future Tweaks (After Testing – Start Loose)
- Rising filter: 5 days now → increase to 7-10 if too many flat MAs pass.
- Depth multiplier: 1×ADR now → increase to 1.2-1.5 if too many shallow pullbacks.
- Near threshold: 5% now → tighten to 3-4% if needed.
- Add min closes below MA (e.g., 3) if wick-only dips slip through.
- Min closes above in Phase 1: None now → add 2-3 if too many 1-day spikes.

## Scanning Rules
- **Market Hours Handling**: If scan is run during NSE market hours (9:15 AM - 3:30 PM IST on weekdays), automatically use the previous trading day's data for pattern analysis. This ensures consistent EOD-based setups and avoids intra-day noise.
- **Trading Day Calculation**: Previous trading day skips weekends (Saturday/Sunday) but assumes no holidays for simplicity.

## Testing Notes
- Use examples: Strides Pharma (STAR.NS) around late Dec 2025 / Jan 2026 — should pass (rally high Nov, deep pullback Dec, retest above rising MA with lower high).
- SBIN — should reject (flat MA, possibly shallow depth).
Your coder can implement based on this. Let me know if any last tweaks! 😊


import pandas as pd
import numpy as np

def continuation_pullback_zigzag(data, params):
    """
    Rough zig-zag continuation pullback scan on daily OHLCV DataFrame.
    Assumes data is already fetched and cached (date index, sorted ascending).
    Returns: (is_hit: bool, details: dict)
    """
    # Parameters (from your config + pattern-specific)
    LOOKBACK_DAYS = 80
    NEAR_THRESHOLD = 0.05  # 5%
    RISING_LOOKBACK = 5    # Current SMA20 > max of prev 5 days
    ADR_PERIOD = 14
    ADR_MULT = 1.0         # Depth >= 1 x ADR

    min_adr = params.get('min_adr', 0.03)

    # Need enough data
    if len(data) < 100:  # Buffer for SMA + lookback
        return False, "Insufficient data"

    data = data.copy()

    # --- Indicators ---
    data['SMA20'] = data['Close'].rolling(window=20).mean()

    # Rising MA: current > max of previous RISING_LOOKBACK days
    data['SMA20_prev_max'] = data['SMA20'].shift(1).rolling(RISING_LOOKBACK).max()
    data['Rising_MA'] = data['SMA20'] > data['SMA20_prev_max']

    # Above / Below MA (using Close)
    data['Above_MA'] = data['Close'] > data['SMA20']

    # Near or above MA with tolerance
    data['Dist_to_MA_pct'] = abs(data['Close'] - data['SMA20']) / data['Close']
    data['Near_or_Above_MA'] = (data['Close'] > data['SMA20']) & (data['Dist_to_MA_pct'] <= NEAR_THRESHOLD)

    # ADR for depth and base filter
    recent = data.tail(ADR_PERIOD + 10)
    daily_range = recent['High'] - recent['Low']
    adr_abs = daily_range.mean()
    current_close = data['Close'].iloc[-1]
    adr_pct = adr_abs / current_close

    if adr_pct < min_adr:
        return False, f"ADR {adr_pct:.1%} < {min_adr:.0%}"

    # --- PHASE 3 FIRST (Latest day) ---
    latest = data.iloc[-1]
    if not (latest['Near_or_Above_MA'] and latest['Rising_MA']):
        return False, "Phase 3 fail: Not near/above rising MA"

    # Slice last 80 trading days
    recent_80 = data.iloc[-LOOKBACK_DAYS:].copy()
    if len(recent_80) < 50:
        return False, "Not enough recent data in 80-day window"

    # --- Find recovery start (first close back above MA after last below) ---
    # Most recent close below MA
    below_days = recent_80[~recent_80['Above_MA']]
    if below_days.empty:
        return False, "Phase 2 fail: No close below MA in 80 days"

    last_below_date = below_days.index[-1]
    after_pullback = recent_80.loc[last_below_date:]

    # First close above MA after pullback
    recovery_days = after_pullback[after_pullback['Above_MA']]
    if recovery_days.empty:
        return False, "No recovery above MA"

    recovery_start_date = recovery_days.index[0]
    recovery_segment = recent_80.loc[recovery_start_date:]

    # Phase 3 high (max high in recovery segment)
    phase3_high = recovery_segment['High'].max()

    # --- PHASE 2: Pullback period (between last above before recovery and recovery start) ---
    phase2_period = recent_80.loc[:recovery_start_date]
    phase2_below = phase2_period[~phase2_period['Above_MA']]
    if phase2_below.empty:
        return False, "Phase 2 fail: No below-MA period"

    phase2_low = phase2_below['Low'].min()

    # --- PHASE 1: Above-MA period before Phase 2 ---
    phase1_period = recent_80.loc[:last_below_date]
    phase1_above = phase1_period[phase1_period['Above_MA']]
    if phase1_above.empty:
        return False, "Phase 1 fail: No prior above-MA period"

    phase1_high = phase1_above['High'].max()

    # --- Depth check: Phase 1 high → Phase 2 low >= ADR_MULT * ADR ---
    depth_abs = phase1_high - phase2_low
    if depth_abs < (adr_abs * ADR_MULT):
        return False, f"Depth {depth_abs:.1f} < {adr_abs * ADR_MULT:.1f} (1x ADR)"

    # --- Lower high check ---
    if phase3_high >= phase1_high:
        return False, "No lower high (recovery already broke Phase 1 high)"

    # --- ALL GOOD: Rough zig-zag pattern detected ---
    details = {
        'Phase1_High': round(phase1_high, 2),
        'Phase2_Low': round(phase2_low, 2),
        'Phase3_High': round(phase3_high, 2),
        'Depth_Rs': round(depth_abs, 2),
        'Depth_%': round((depth_abs / phase1_high) * 100, 1),
        'ADR_%': round(adr_pct * 100, 1),
        'SMA20': round(latest['SMA20'], 2),
        'Dist_to_MA_%': round(latest['Dist_to_MA_pct'] * 100, 1),
    }

    return True, details


# --- Example usage in your scanner loop ---
# results = []
# for symbol in filtered_symbols:  # after base filters
#     data = load_cached_data(symbol)  # your existing cache function
#     hit, info = continuation_pullback_zigzag(data, self.continuation_params)
#     if hit:
#         row = {'Symbol': symbol, 'Close': data['Close'].iloc[-1]}
#         row.update(info)
#         results.append(row)
#
# pd.DataFrame(results).to_csv("zigzag_continuation_hits.csv", index=False)