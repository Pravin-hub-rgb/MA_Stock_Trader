import { StockStateEnum } from "../types";
import { ReversalStockState } from "./stock-monitor";

function parseTime(t: string): number {
  const parts = t.split(":");
  return parseInt(parts[0]) * 60 + parseInt(parts[1]);
}

export class ReversalTickProcessor {
  private stock: ReversalStockState;

  constructor(stock: ReversalStockState) {
    this.stock = stock;
  }

  processTick(price: number, timestamp: Date): void {
    this.stock.updatePrice(price, timestamp);

    if (this.stock.isActive) {
      this.trackEntryLevels(price, timestamp);
    }

    if (this.stock.state === StockStateEnum.WAITING_FOR_ENTRY) {
      this.handleEntryMonitoring(price, timestamp);
    } else if (this.stock.state === StockStateEnum.ENTERED) {
      this.handleExitMonitoring(price, timestamp);
    }
  }

  private trackEntryLevels(price: number, timestamp: Date): void {
    // Real-time low violation check (mirrors old project: tick_processor.py:80-103)
    if (this.stock.openPrice !== null && !this.stock.lowViolationChecked) {
      const lowViolationPct =
        (this.stock.openPrice - this.stock.dailyLow) / this.stock.openPrice;
      if (lowViolationPct >= this.stock.params.lowViolationPct) {
        this.stock.lowViolationChecked = true;
        if (this.stock.situation === "reversal_s1") {
          this.stock.reject(
            `Low violation: ${this.stock.dailyLow.toFixed(2)} < ${(this.stock.openPrice * (1 - this.stock.params.lowViolationPct)).toFixed(2)} (${(lowViolationPct * 100).toFixed(1)}% below open)`,
          );
        }
      }
    }

    if (this.stock.situation === "reversal_s1" && this.stock.openPrice !== null) {
      const newHigh = this.stock.dailyHigh;
      const newSl = newHigh * (1 - this.stock.params.entrySlPct);
      if (this.stock.entryHigh === null || newHigh > this.stock.entryHigh) {
        this.stock.entryHigh = newHigh;
        this.stock.entrySl = newSl;
        // NOTE: entryReady is NOT set here — it must only be set by prepareEntry()
        // at ENTRY_TIME. This prevents premature entry before 09:20.
        // See index.ts start() lines 170-174 where entryReady is set at ENTRY_TIME.
      }
    }
  }

  private handleEntryMonitoring(price: number, timestamp: Date): void {
    if (this.stock.entered || !this.stock.entryReady) return;

    // Defense-in-depth: don't enter before entry time (matches continuation pattern)
    const entryMinutes = this.stock.params.entryTime
      ? parseTime(this.stock.params.entryTime)
      : 9 * 60 + 20;
    const nowMinutes = timestamp.getHours() * 60 + timestamp.getMinutes();
    if (nowMinutes < entryMinutes) return;

    if (this.stock.situation === "reversal_s2") {
      this.checkOopsEntry(price, timestamp);
    } else if (this.stock.situation === "reversal_s1") {
      this.checkStrongStartEntry(price, timestamp);
    }
  }

  private checkOopsEntry(price: number, timestamp: Date): void {
    if (this.stock.oopsTriggered || this.stock.entered) return;
    if (this.stock.openPrice === null || this.stock.previousClose === null) return;

    if (price >= this.stock.previousClose) {
      this.stock.oopsTriggered = true;
      // entryPrice already set to previousClose by prepareOops()
      // entrySl already set to previousClose * (1 - entrySlPct) by prepareOops()
      this.stock.enterPosition(price, timestamp);
    }
  }

  private checkStrongStartEntry(price: number, timestamp: Date): void {
    if (this.stock.strongStartTriggered || this.stock.entered) return;
    if (this.stock.openPrice === null || this.stock.previousClose === null) return;

    if (this.stock.entryHigh !== null && price >= this.stock.entryHigh) {
      this.stock.strongStartTriggered = true;
      this.stock.enterPosition(price, timestamp);
    }
  }

  private handleExitMonitoring(price: number, timestamp: Date): void {
    if (!this.stock.entered || this.stock.entryPrice === null) return;

    if (price <= this.stock.entrySl!) {
      this.stock.exitPosition(price, timestamp, "Stop Loss Hit");
    }
  }
}
