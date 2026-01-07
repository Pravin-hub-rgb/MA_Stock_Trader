so now ... it seems like our scanner is nearly done.. 
it is showing the results ..
now comes the part where
we have to live trade on these stocks ... 
well some refining is needed like manuall intervention cuse see we have 45 candlates right so i have to manually pick the best candidate for tomorrow to trade okay .. 
suppose we have x candidate .. it can be 5,6,7... this is only for continuation scan okay .. we might have reversal scan candidate too 
so at least i'll finalize according to me which are the major candidate to trade tomorrow okay .. so after finalization
so from 9:15 we have to monitor them... for continuation and reversal .. different logic for both ..
we have to monitor them all simulataneosly okay ... 
see suppose roughly speaking ... 
we have this rules for continatuion 
we need gap up or open = low or low is in range of 1% ..... etc etc .. okay
now suppose we have 8 candidate for continuation so .. 
so at market open 9:15 directly 3 did gap down .. so we directly reject them we don't monitor them...
then few seconds later 2 vialated the low in 1% rule we reject them 
now we only have 2 left (8 - 4 - 2)
now these two are best ... we trade them ..... 
this kinda rough rough stuff (need more refinement) is needed to be implemented ...
we might have some documents related to this stuff in ... docs folder 
discuss pleas

Based on what I've read in your docs (parallel live trading.md, continuation scan logic, scan_rules.md, and the trading theory files), I have a good understanding of your scanner setup and the initial plan for live trading. Let's discuss refining this for your described workflow.

From your description, the live trading phase after scanning involves:

1. **Manual Candidate Selection**: From ~45 scan results, you manually pick 5-7 best candidates for tomorrow (continuation focus initially, plus potential reversal candidates).

2. **Real-time Monitoring from 9:15 AM**: Simultaneous monitoring of selected candidates.

3. **Continuation Rules** (rough, as you said):
   - Gap up conditions
   - Open = low (or very close)
   - Low in 1% range (presumably from some reference point)
   - Reject immediately if gap down at open
   - Reject if low violates 1% rule shortly after

4. **Parallel Processing**: Since you mentioned monitoring all simultaneously without lag.

5. **Different Logic for Reversal**: When you add reversal candidates.

Questions to clarify/refine:

- **Continuation Entry Rules**: Can you specify the exact gap up conditions? For example, gap up % from previous close? And the "low in 1% range" - 1% from what (previous close, open, MA)?

- **Rejection Timing**: "Few seconds later" for low rule violation - how soon after open? Within first 1-2 minutes?

- **Number of Candidates**: You mentioned 8 in example, leading to 2 final. How many do you typically want to monitor simultaneously? The parallel trading doc suggests 5, but with your workflow, maybe 10-15 to start, then filter down?

- **Data Feed**: Will use Upstox real-time data as in the parallel trading plan? WebSocket for ticks/1min?

- **Order Execution**: After confirming entry signal, what order type? Market? Limit at certain level? SL/TP setup?

- **Position Sizing/Risk**: Per your existing config, or specific for live trading?

Looking at your existing architecture (parallel live trading.md), it already has a solid foundation with threading for parallel monitoring, Upstox integration, strategy logic, etc. We can build on that, but adapt the rules to your manual selection + real-time filtering workflow.

What are your thoughts on these points? Any specific rules or examples from your trading experience that should be codified?

okay let's focus only on continuation for now...
so see you read every md doc and find stuff to continaution entry logic and list the rules ... 
from what i remember is ..
open = low 
and that low in range of 1% is from open of live daily candle ..
see suppose tommorrow on 8 jan i have to trade so ... there will be some opening price right . that is the referece .. so if price goes below 1% of this opening price of daily candle we reject .. 
gap up: yesterday close reference .. .so if price opens above yesterdays close ..
so so ma stuff here in live ..

now rejection timing .. .. the instructor has said in first few minutes .. .. 3 minute he said ... look it up to double check...

about number of candidate .. i'm not sure though .. what is the max we can monitor easily is the questions .. if 5 then i always have to minimize my sprict to 5 .. 
yes upstox give live tick data .. 
orderexecution .. we do only paper trade for now .. when we will se good result .. then we will trade live ... so we only do paper trade ... we log to files for now ... 
psotion sizing stuff will come when we will make to trade live as we are only doing paper ...

Based on reviewing your docs (continuation_setup.md, theory_day_2.md, parallel live trading.md, technical_specifications.md, user_guide.md, and others), here's the compiled continuation entry logic rules for live trading:

## Continuation Entry Rules

### Primary Entry Signal: Strong Start
- **Open = Low Pattern**: Stock opens at the same price as its low for the day (within 1% tolerance)
- **Gap Up Requirement**: Opening price must be above previous day's close (no specific % mentioned, just above)
- **Confirmation Window**: Must occur within first 3 minutes after market open (9:15 AM)
- **Volume Confirmation**: 25-30% of estimated daily volume should trade in first 3-5 minutes

### Rejection Rules
- **Immediate Rejection**: If stock gaps down at open (opens below previous close) → reject instantly
- **Low Violation**: If price drops below 1% of the opening price during first 3 minutes → reject
- **Timing**: All rejections checked continuously in first 3 minutes

### Additional Filters (Optional Enhancements)
- **Volume Surge**: Early volume significantly above average
- **Price Action**: Clean strong behavior without wicks/minor pullbacks in first 3 minutes

## Implementation Notes
- **Data Source**: Upstox live tick data via WebSocket
- **Monitoring**: Parallel threading for multiple stocks (configurable count)
- **Order Execution**: Paper trading only - log trades to files (no real orders)
- **Entry Method**: Market order at signal confirmation
- **Position Sizing**: Not needed for paper trading phase

## Number of Candidates
Your docs suggest 5 (from parallel live trading plan), but since threading is lightweight, we can make it configurable (e.g., 5-15). You can set based on what you can comfortably monitor manually alongside the automation.

Does this match what you remember? Any adjustments needed? For example:
- Is gap up required, or is open=low sufficient?
- Any additional rules for volume or price action?
- Should we include the pullback-to-open rule from parallel trading doc as an alternative entry?