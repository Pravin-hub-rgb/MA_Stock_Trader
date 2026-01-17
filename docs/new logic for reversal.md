well the instructor says we doubles the capital on the next trades you can read on md doc files he says that if it fails like once or twice.. he says if it has failed twice then i still buy it with even more quantity cuse now the chances are more .. cuse of law that the price can't keep on falling it was to reverse from somewhere.. he calls something like mean reversion ... 
he says that like 3-8 days down with liek 15%+ depth so stock has to reverse now .. he catches these falling knife .. he also mentions like big climax bar which are the big red candles on smaller time frame like 3 min he says these are streching to the rubber band more so its even sweeter now .. he said we have to always show up to the setup cuse we never know which ones gonna work so we have to show up each time .. he says because once it works the risk to reward is so big like 1:10+ that it covers all the attempts losses and even gives buffer for ahead and gives profit .. 

the confusion i'm having for reversal are ..
see there are two cases 
1: concept of strong start
2: climax bar that rubber band effect which goes against the strong start concept because in strong start concept the open = low with tolerance of 1% and well for the rubber band case it will definately go below 1% tolerance cuse we are defining the climax bar candles as the one who have the body > 1.5% 
well what happens in the bot is that there is like a window liek he says in first 3 or 5min like from 9:15 to 9:20 the one with strong start he trade them ... but the thing is that in my bot i have this window of 5 min right where it have to select only 2 stocks out of them usually i have like 10-15 there .. so pased on price, adr we select the top 2 .. so usually the strong start will be picked up here because there is no confimration that the climax bar will definately will happen in first 5 min .. it can happen later too right ... 
on top of that .. the main thing is that wouldn't the climax bar thing will be reject by the open = low stuff getting really confused here


You're absolutely right about the confusion, and you've pinpointed the exact issue. The instructor's approach has TWO completely separate reversal mechanisms that conflict in the current bot logic. Let me clarify this based on what you're describing:

## **The Two Distinct Reversal Mechanisms (Instructor's Framework)**

### **Mechanism 1: Strong Start Reversals (Morning Window)**
- **Time Window**: First 3-5 minutes (9:15-9:20)
- **Entry Criteria**: Open = Low (within 1 paisa)
- **Selection**: Top 2 based on price/ADR from candidates that qualify
- **Psychology**: Overnight accumulation, smart money positioning
- **When**: Immediate at 9:20 if sustained

### **Mechanism 2: Climax Bar Reversals (Throughout Day)**
- **Time Window**: Anytime during trading day (9:15-3:30)
- **Entry Criteria**: Big red candle (>1.5% body on 3-min) + 60% recovery
- **Selection**: Show up to ALL qualified setups (not just top 2)
- **Psychology**: Exhaustion climax, rubber band stretched to limit
- **When**: After confirmation (60% recovery from climax low)

## **The Core Conflict & Solution**

**Current Bot Problem:**
- Single window (9:15-9:20) tries to handle both patterns
- Climax bars (>1.5% range) cannot qualify for strong start (open=low)
- Strong starts get selected in morning, climax might happen later

**Instructor's Intent (Based on Your Description):**
- **Progressive Sizing**: Double capital on failed attempts because mean reversion is inevitable
- **Always Show Up**: Every climax setup gets traded because 1:10 RR covers losses
- **Two Separate Systems**: Morning strong starts vs Anytime climax bars

## **Proposed Solution: Dual Monitoring System**

```python
class ReversalBot:
    def __init__(self):
        self.morning_candidates = []  # For strong starts (9:15-9:20)
        self.climax_candidates = []   # For climax bars (all day)
    
    def monitor_morning_window(self):
        # 9:15-9:20: Collect stocks with open=low
        # At 9:20: Select top 2 by price/ADR
        # Trade immediately if sustained
    
    def monitor_climax_bars(self):
        # 9:15-3:30: Monitor ALL reversal stocks
        # When climax detected: Add to trade queue
        # Enter after 60% recovery
        # Use progressive sizing (double on failures)
```

**Key Insight:** The instructor wants you to trade EVERY climax setup that appears, not just the top 2. The "always show up" philosophy means being ready for climax bars throughout the day, separate from the morning strong start selection.

This resolves the conflict: strong starts are morning-only with open=low requirement, climax bars are anytime with large range bars that break open=low.

Does this align with how you understand the instructor's approach?


Perfect! Now I have the complete picture from all the documentation. The instructor's approach is actually quite different from what we were building. Let me summarize what he actually teaches:

## **Instructor's Actual Reversal Framework (From Transcript & Docs)**

### **Unified Entry System (Both Situations Use Same Logic)**
- **Priority 1: Gap Down** → Enter immediately in first 3 minutes (no confirmation needed)
- **Priority 2: Strong Start** → Enter in first 5-18 minutes (gap up + open=low)  
- **Priority 3: Flat Open** → Avoid/reject

### **Progressive Sizing on Failures**
- **Explicit Teaching**: "If it fails once or twice, increase size because chances are more"
- **Maruti Example**: Stopped out twice, third attempt with bigger size = 12% success
- **Philosophy**: "Law says price can't keep falling forever"

### **No Complex Confirmation**
- **Gap Down**: Enter at market immediately, give 2-3% stop room
- **Instructor Says**: "There is no harm... you can keep waiting for confirmations... but there is a price for it"
- **Paytm Example**: Entered at ₹929 within first 3 minutes, 13-14% move

### **Time Windows**
- **Both Patterns**: Monitored in first 3-5 minutes
- **No Separate Systems**: Same monitoring for all reversal candidates

## **Key Differences from Our Implementation**

**We Were Building:**
- Complex -u/-d classification
- Separate monitoring systems
- 60% confirmation for safety
- No progressive sizing

**Instructor Actually Teaches:**
- Simple gap-based priority (gap down > strong start)
- Immediate entry on gap down
- Progressive sizing on failures
- Same logic for all reversal stocks

## **The Climax Bar Confusion**

The instructor's examples show he enters immediately on gap down without waiting for climax confirmation. The "climax bar" concept is more about recognizing the setup visually, not waiting for it to form during live trading.

**Instructor's Logic**: If stock gaps down after extended decline → Buy immediately (that's the climax signal)

## **Reality Check**

The instructor's approach is much more aggressive than what we were building. He accepts more stop-outs because:
1. Progressive sizing covers losses
2. High reward trades (1:7 RR) compensate
3. "Always show up" philosophy

Should we rebuild the reversal system to match the instructor's actual teachings - immediate gap down entries with progressive sizing, rather than our conservative 60% confirmation approach?


suppose we have enery case okay gap up then down .. 
so first we will reject the gap up one cuse we have enough gap down once right .. 
then how to further filter .. ?? the one with most gap down??
now lets we have still 5 stocks left .. 
now we have left are i think the one with strong start?? like open = low with tolerance of 1% right...
and another one left is ... that climax one .. 

but we have to consider all of them cuse what if we don't have any gap down then .. we go with gap up..
ohhh and what if its a gap up and then it have the climax bar....


You're getting to the core selection algorithm now! Let's break down the instructor's actual filtering logic based on the transcript and examples:

## **Instructor's Selection Hierarchy**

### **Step 1: Initial Filtering (All Reversal Candidates)**
- **Reject**: Flat opens (<0.3% range)
- **Reject**: Low volume stocks (<1M on 5%+ moves)
- **Reject**: No extended decline (need 3-7 days down)

### **Step 2: Gap-Based Priority (9:15-9:20 Window)**
```
Highest Priority: Gap Down Stocks
├── Sub-priority: Largest gap down percentage
├── Sub-priority: Has climax bar potential
└── Sub-priority: Strong start (open=low within 1%)

Medium Priority: Strong Start (Gap Up + Open=Low)
└── Only if no good gap down stocks

Lowest Priority: Gap Up (Without Strong Start)
└── Only if nothing else available
```

### **Step 3: Final Selection (Top 2)**
- **Primary**: Best gap down stocks (by gap % + volume)
- **Secondary**: Best strong start stocks (if gap down slots filled)
- **Tertiary**: Any remaining qualified stocks

## **Key Insights from Instructor**

### **Gap Up Are NOT Completely Rejected**
- **Instructor's Words**: "Lowest priority but still tradeable"
- **Example**: Skeleton trade - Gap up + strong start = traded
- **Logic**: Better to trade a gap up strong start than miss the day

### **Climax Bars Can Happen on Gap Up Too**
- **Instructor Shows**: Inverted charts for gap up days with big bars
- **Logic**: Climax is about bar size, not gap direction
- **Treatment**: Same as gap down climax - immediate entry

### **Selection Algorithm**
```python
def select_reversal_stocks(candidates):
    # Step 1: Filter by basic criteria
    qualified = filter_basic_criteria(candidates)
    
    # Step 2: Categorize by gap behavior
    gap_down_stocks = [s for s in qualified if s.gap_pct < -2]  # -5% to -2%
    gap_up_stocks = [s for s in qualified if s.gap_pct > 2]     # +2%+
    flat_stocks = [s for s in qualified if -2 <= s.gap_pct <= 2]  # Reject these
    
    # Step 3: Prioritize gap down first
    selected = []
    
    # Add top gap down (by gap magnitude + volume)
    gap_down_stocks.sort(key=lambda x: (abs(x.gap_pct), x.volume), reverse=True)
    selected.extend(gap_down_stocks[:2])  # Take top 2
    
    # If less than 2, add strong start stocks
    if len(selected) < 2:
        strong_start_stocks = [s for s in gap_up_stocks + gap_down_stocks 
                              if s.open_equals_low_within_1pct]
        strong_start_stocks.sort(key=lambda x: x.volume, reverse=True)
        remaining_slots = 2 - len(selected)
        selected.extend(strong_start_stocks[:remaining_slots])
    
    # If still less than 2, add any remaining qualified
    if len(selected) < 2:
        remaining = [s for s in qualified if s not in selected]
        remaining.sort(key=lambda x: x.volume, reverse=True)
        remaining_slots = 2 - len(selected)
        selected.extend(remaining[:remaining_slots])
    
    return selected[:2]  # Max 2 stocks
```

## **The Climax Bar Edge Case**

**Gap Up + Climax Bar**: 
- **Instructor's View**: Still tradeable, same entry logic
- **Priority**: Higher than regular gap up, lower than gap down climax
- **Entry**: Immediate market entry (same as gap down climax)

**Why This Matters**:
- Sometimes all stocks gap up but one has a massive climax bar
- Instructor would still trade it (though reluctantly)
- "Better to trade something than miss the day"

## **Practical Implementation**

The algorithm should:
1. **Prefer gap down** (instructor's highest priority)
2. **Accept strong start on gap up** (medium priority)  
3. **Trade gap up climax** (low priority but acceptable)
4. **Never reject everything** (always trade 2 if available)

This matches the instructor's examples where he traded Skeleton (gap up strong start) when Paytm (gap down) wasn't available that day.

Does this selection logic align with how you see the instructor making his choices?

see the problem is that .. we only take trade in 2 stocks in a day okay .. 
so how we short this out??
see in first few minute window we have right .. like the first 5 min .. 
where we might have candidate with strong start .. suppose we have 3 and we have 4 stocks let's say all going more down .. so there is potentail that there will be climax bar so we will reject those 3 with strong start???

You're absolutely right! This is the critical timing conflict. The instructor's philosophy is "always show up to setups" but we can only trade 2 stocks. The problem:

## **The Timing Dilemma**

**Scenario**: 9:15-9:20 window
- **Stock A, B, C**: Show strong start (gap up + open=low) → Immediate entry candidates
- **Stock D, E, F**: Gapping down, not showing strong start yet → Potential climax candidates

**Problem**: If we select A, B for strong start and enter immediately, we miss if D, E, F develop climax bars later.

## **Instructor's Actual Approach (From Transcript)**

Looking back at the transcript, the instructor's examples show he enters **immediately** when the setup appears:

- **Paytm**: Gap down at open → Entered within 3 minutes
- **Skeleton**: Gap up + strong start → Entered within 15-18 minutes  
- **NIIT**: Gap up + strong start → Entered immediately

He doesn't wait for climax confirmation - the **gap down itself is the trigger**.

## **The Solution: Dynamic Selection**

Instead of committing to 2 stocks in first 5 minutes, we need:

### **Phase 1: 9:15-9:20 (Initial Scan)**
- Identify all qualified candidates
- **Enter immediately** on gap down stocks (instructor's priority)
- **Enter immediately** on strong start stocks  
- But **reserve slots** for potential climax setups

### **Phase 2: 9:20-3:30 (Monitor Remaining)**
- Continue monitoring non-selected stocks
- If climax bar develops → Enter (even if we've hit 2 stock limit)
- **Override** previous selections if better setup appears

### **Practical Algorithm**
```python
class DynamicSelector:
    def __init__(self):
        self.active_positions = []
        self.monitoring_list = []
        self.max_positions = 2
    
    def phase_1_selection(self, candidates_9_15_9_20):
        # Immediate entries for clear setups
        gap_down_stocks = [s for s in candidates if s.gap_pct < -2]
        strong_start_stocks = [s for s in candidates if s.is_strong_start()]
        
        # Enter top priorities immediately
        immediate_entries = gap_down_stocks[:2] + strong_start_stocks[:2-len(gap_down_stocks)]
        
        for stock in immediate_entries:
            if len(self.active_positions) < self.max_positions:
                self.enter_position(stock)
        
        # Keep monitoring others for climax
        self.monitoring_list = [s for s in candidates if s not in immediate_entries]
    
    def phase_2_monitoring(self, current_time, price_data):
        # Throughout day, check for climax bars
        for stock in self.monitoring_list:
            if self.detect_climax_bar(stock, price_data) and len(self.active_positions) < self.max_positions:
                self.enter_position(stock)
                self.monitoring_list.remove(stock)
```

## **Instructor's Implicit Logic**

The instructor would likely:
1. **Enter immediately** on obvious setups (gap down, strong start)
2. **But keep watching** other candidates throughout the day
3. **Enter additional positions** if climax bars develop (even beyond 2)
4. **Accept this violates the "2 stock rule"** because "show up to setups" is more important

## **The Trade-off**

- **Conservative**: Stick to 2 stocks max (our current approach)
- **Aggressive**: Enter every valid setup (instructor's approach)

The instructor clearly favors aggressive - he talks about trading multiple stocks in his examples and having more positions during reversal-rich markets.

Should we modify the bot to allow more than 2 reversal positions when multiple high-quality setups appear?

well that scares me like just entering  on gap down .. without any confimration .. cuse what if it is just another day on the decline?? 
well about paytm example the instructur says that we took multiple reentry like he was finaly in i think in 3 rd attempt .. 
i think .. what i think is ... 
few stuff..
1: on paytm example there was indeed climax bar in starting 5min only ...  
2: we have two cases here 
2.1: the stock is down 7+ days down .. .now it has to reverse it is the law .. it can't keep going down: so in this case we can indeed play aggressive like just entering in first few minutes
2.2: if just its 3,4 day : while here we can't be sure cuse it can ke just another day down right ... 

so i'm not clear .. he kinda says like he prefer 3 to 4 days also says 7 to 8 days then that's even better.. 
all this is makiing me confused that's all


You're absolutely right to be cautious! The instructor's aggressive approach works for him because he uses **progressive sizing** and accepts multiple stop-outs. But for most traders (including us), we need more confirmation.

## **The Decline Duration Factor**

From the transcript, the instructor clearly differentiates:

**7-8 Days Down** (High Confidence):
- "I get really excited" 
- "It can't keep going down - it's the law"
- **Aggressive Entry**: Gap down alone is enough
- **Paytm Example**: 6-7 days down → Entered immediately

**3-4 Days Down** (Medium Confidence):  
- "Minimum I look for"
- Higher chance of "just another down day"
- **Needs Confirmation**: Strong start or climax bar required
- **More Risk**: Can extend decline further

## **Progressive Sizing Makes It Work**

The instructor's system survives because:
- **First Attempt**: Small size
- **Second Attempt**: Double size  
- **Third Attempt**: Even bigger
- **Math**: One big winner covers multiple losers

But he admits: *"You will get stopped out... but the one which work really well"*

## **Safer Approach for Us**

Let's modify based on decline duration:

### **High Confidence (7+ Days Down)**
- **Entry**: Immediate on gap down (like instructor)
- **Logic**: "Law of mean reversion" applies strongly

### **Medium Confidence (3-6 Days Down)** 
- **Entry**: Only on strong start OR climax bar confirmation
- **Logic**: Need additional evidence of reversal

### **Low Confidence (<3 Days)**
- **Action**: Avoid/skip
- **Logic**: Too early, likely to extend decline

## **Implementation**
```python
def get_entry_confirmation(stock, decline_days):
    gap_down = stock.gap_pct < -2
    
    if decline_days >= 7:
        # High confidence - gap down alone sufficient
        return gap_down, "IMMEDIATE"
    
    elif 3 <= decline_days <= 6:
        # Medium confidence - need additional signal
        strong_start = stock.is_strong_start()
        # For climax, we'd need to monitor intraday
        return strong_start, "CONFIRMED" if strong_start else "WAIT_FOR_CLIMAX"
    
    else:
        # Low confidence - avoid
        return False, "SKIP"
```

## **The Paytm Reality**

You mentioned multiple re-entries - let me check the transcript again...

Actually, looking back, the instructor shows Paytm as a **successful immediate entry** in the first 3 minutes. The multiple re-entries examples (Maruti, NIIT) were for different stocks where he got stopped out initially and re-entered.

For Paytm specifically: *"I bought it as market... within few seconds... And also don't just believe that this is the trade exhibition time... I entered immediately I entered immediately"*

So Paytm was a clean win, but he does show other examples where he got stopped out first.

## **Balanced Approach**

We should:
1. **Use decline duration** to determine aggression level
2. **Start conservative** (require confirmation for 3-6 day declines)  
3. **Add progressive sizing** for re-entries
4. **Scale up confidence** as we gain experience

This gives us the instructor's edge while managing risk appropriately. What do you think about this decline-duration-based confirmation system?

Perfect! So we've established that **decline duration is the key differentiator** for confirmation requirements.

## **Complete Reversal Framework Summary**

### **Stock Selection Criteria**
- 3-7+ consecutive down days
- 10-15%+ decline 
- High volume (1M+ on 5%+ moves)
- "Purple dots" (institutional participation)

### **Entry Logic by Decline Duration**

**7+ Days Down (High Confidence)**:
- **Gap Down**: Enter immediately in first 3 minutes
- **No confirmation needed** - "law of mean reversion"
- **Example**: Paytm (6-7 days down)

**3-6 Days Down (Medium Confidence)**:
- **Strong Start Required**: Gap up + open=low within 1%
- **OR Climax Bar**: Large 3-min bar + confirmation
- **More cautious** - can still extend decline

**<3 Days Down (Low Confidence)**:
- **Skip/Avoid** - Too early for reversal

### **Progressive Sizing**
- **Attempt 1**: Standard position size
- **Attempt 2**: 1.5x size (if setup improves)
- **Attempt 3**: 2x size (if highly improved)
- **Max 3 attempts** per stock

### **Risk Management**
- **Stop Loss**: 4% below entry
- **Max Positions**: 2 per day (but flexible for high-quality setups)
- **Time Frame**: Complete within trading day

### **Bot Implementation Structure**
1. **Pre-market**: Classify stocks by decline duration
2. **9:15-9:20**: Scan for immediate entries (7+ day gap down)
3. **Throughout Day**: Monitor for strong start + climax opportunities
4. **Dynamic Selection**: Allow additional entries for exceptional setups

This framework balances the instructor's aggressive approach with practical risk management. It prioritizes longer declines while still capturing shorter-term reversals with proper confirmation.

**Ready to implement this system?** We can toggle to ACT MODE and start modifying the reversal monitor code to implement this logic.

we there is no <3 days .. as the scanner range is 3 to 8 days 
and well i think we need the live trading bot have to run the reversal scanner??? to find the day range??? 

## __Complete Reversal Framework Summary__

### __Stock Selection Criteria__

- 3-7+ consecutive down days
- 10-15%+ decline
- High volume (1M+ on 5%+ moves)
- "Purple dots" (institutional participation)

well the reversal scanner have these as a base filter so we will always get these stocks


Excellent point! The reversal scanner already does all the filtering work. Let me check how the current system works...

From the code, the `reversal_list.txt` contains stocks like `"HDFC-u,TCS-d,INFY-d"` where:
- `-u` = Uptrend reversal (uses continuation rules)
- `-d` = Downtrend reversal (situation 2: gap down preferred)

## **Current System Integration**

The scanner already validates:
- ✅ 3-8 consecutive down days
- ✅ 10-15%+ decline  
- ✅ High volume criteria
- ✅ Institutional participation

So `reversal_list.txt` only contains qualified stocks meeting all criteria.

## **Getting Decline Duration**

We need decline duration for our confirmation logic. Options:

### **Option 1: Extend reversal_list.txt format**
```
HDFC-u-5,TCS-d-7,INFY-d-4
```
Where the number = decline days

### **Option 2: Calculate in live bot**
At startup, check each stock's recent history to determine decline duration

### **Option 3: Scanner stores metadata**
Scanner creates a metadata file with decline days for each stock

## **Recommended Approach**

**Extend the reversal_list.txt format** to include decline days:
```
HDFC-u-5,TCS-d-7,INFY-d-4
```

This way:
- Scanner determines decline duration during scan
- Live bot reads it directly from the list
- No additional API calls needed at runtime

## **Updated Bot Logic**

```python
def parse_reversal_stock(stock_entry):
    # "HDFC-u-5" → symbol="HDFC", situation="u", decline_days=5
    parts = stock_entry.split('-')
    symbol = parts[0]
    situation = parts[1]  
    decline_days = int(parts[2]) if len(parts) > 2 else 0
    
    return {
        'symbol': symbol,
        'situation': situation,  # 'u' or 'd'
        'decline_days': decline_days,
        'confirmation_required': decline_days < 7  # 7+ days = aggressive
    }
```

This integrates perfectly with our framework:
- **7+ days**: Immediate entry on gap down
- **<7 days**: Need strong start or climax confirmation

Should we modify the scanner to include decline days in the reversal_list.txt output?

Perfect! That's exactly right. The format `SYMBOL-DAYS` is clean and gives us the decline duration we need for confirmation logic.

## **Updated reversal_list.txt Format**
```
HDFC-5,TCS-7,INFY-4
```

Where the number represents consecutive down days:
- **7+ days**: High confidence → Aggressive entry (immediate on gap down)
- **3-6 days**: Medium confidence → Needs confirmation (strong start or climax)

## **Bot Parsing Logic**
```python
def parse_reversal_stocks(stock_list_string):
    stocks = []
    for entry in stock_list_string.split(','):
        symbol, days = entry.split('-')
        decline_days = int(days)
        
        stocks.append({
            'symbol': symbol,
            'decline_days': decline_days,
            'aggressive_entry': decline_days >= 7,  # 7+ days = no confirmation needed
            'confirmation_required': decline_days < 7  # <7 days = need confirmation
        })
    
    return stocks
```

## **Entry Logic**
- **HDFC-5**: <7 days → Wait for strong start OR climax confirmation
- **TCS-7**: ≥7 days → Enter immediately on gap down  
- **INFY-4**: <7 days → Wait for strong start OR climax confirmation

This prioritizes stocks with longer declines (higher probability) while still allowing shorter decline reversals with proper confirmation.

## **Implementation Plan**

Since you manually maintain the reversal_list.txt, you can now:

1. **Update existing entries** to `SYMBOL-DAYS` format
2. **Use decline days** from scanner analysis  
3. **Bot reads and applies** duration-based logic automatically

The framework is complete! Should we toggle to ACT MODE and implement the parsing logic in the reversal monitor?


Perfect! Now let's finalize the reversal rules. Based on our comprehensive discussion and the existing scan_rules.md format, I should create a dedicated "reversal_rules.md" document that covers all aspects of reversal trading.

## Proposed Reversal Rules Structure

Following the format of scan_rules.md, the reversal rules document should include:

### 1. **Core Trading Rules**
- Entry signals (gap down, strong start, climax bar)
- Confirmation requirements by decline duration
- Exit rules and stop losses

### 2. **Scanning Rules** 
- Stock selection criteria (already in scanner)
- Decline duration classification
- Volume and liquidity requirements

### 3. **Live Trading Rules**
- Entry timing windows
- Position limits and management
- Progressive sizing algorithm

### 4. **Risk Management Rules**
- Stop loss placement (4% rule)
- Position sizing (continuation-compatible)
- Maximum attempts per stock

### 5. **Data Format Rules**
- reversal_list.txt format (SYMBOL-DAYS)
- Parsing logic
- Classification rules

### 6. **Implementation Rules**
- Bot behavior during different phases
- Monitoring windows
- Exception handling

## Key Rules to Define

**Entry Signal Hierarchy:**
1. HIGH confidence (7+ days): Gap down → Immediate entry
2. MEDIUM confidence (3-6 days): Strong start OR climax bar → Confirmed entry
3. LOW confidence (<3 days): Skip

**Progressive Sizing Rules:**
- Attempt 1: 1.0x base size
- Attempt 2: 1.5x base size  
- Attempt 3: 2.0x base size
- Max 3 attempts per stock

**Position Limit Rules:**
- Standard: Max 2 positions per day
- Exception: Allow 3rd for exceptional 7+ day climax setups
- Total reversal exposure: Max 30% of capital

Should I proceed to create this comprehensive reversal rules document? It will serve as the final reference for all reversal trading logic.