//@version=5
indicator("Oops Reversal-Updated", overlay=true)

// Previous day's low
prevLow = low[1]
prevhigh = high[1]

// 1% breach level above previous low
targetCross = prevhigh * 1.001

// Conditions
openedBelowPrevLow = open < prevLow
smallDip = low >= open * 0.99  // Low is not more than 1% below open
strongReversal = close >= targetCross

// Final condition
bullishOops = openedBelowPrevLow and smallDip and strongReversal

// Plot signal
plotshape(bullishOops, title="Bullish Oops", location=location.belowbar, style=shape.labelup, color=color.green, text="Oops↑")
