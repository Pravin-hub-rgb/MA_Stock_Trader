import { StockStateEnum } from "../types";

export interface StateMachineParams {
  flatGapThreshold: number;
  entrySlPct: number;
  lowViolationPct: number;
  trailingSlThreshold: number;
  gapUpMaxPct: number;
  entryTime?: string;
}

export class StateMachineMixin {
  public state: StockStateEnum = StockStateEnum.INITIALIZED;
  public isSubscribed = true;
  public symbol = "";
  public openPrice: number | null = null;
  public previousClose = 0;
  public dailyLow = Infinity;
  public dailyHigh = -Infinity;
  public situation = "";
  public gapValidated = false;
  public lowViolationChecked = false;
  public entryReady = false;
  public entered = false;
  public isActive = true;
  public entryHigh: number | null = null;
  public entrySl: number | null = null;
  public entryPrice: number | null = null;
  public entryTime: Date | null = null;
  public exitPrice: number | null = null;
  public exitTime: Date | null = null;
  public pnl: number | null = null;
  public rejectionReason: string | null = null;
  public oopsTriggered = false;
  public strongStartTriggered = false;
  public gapPct: number | null = null;
  public vahPrice: number | null = null;
  public earlyVolume = 0;
  public cumulativeVolume = 0;
  public volumeBaseline = 0;

  params: StateMachineParams;

  constructor(params: StateMachineParams) {
    this.params = params;
  }

  transitionTo(newState: StockStateEnum, reason = ""): void {
    const old = this.state;
    this.state = newState;
    const msg = `[${this.symbol}] State: ${old} → ${newState}${reason ? ` (${reason})` : ""}`;
    console.log(msg);
  }

  reject(reason: string): void {
    this.isActive = false;
    this.isSubscribed = false;
    this.rejectionReason = reason;
    this.transitionTo(StockStateEnum.REJECTED, reason);
  }

  validateGap(): boolean {
    if (this.openPrice === null) return false;

    const gapPct = (this.openPrice - this.previousClose) / this.previousClose;
    this.gapPct = gapPct;
    const { flatGapThreshold } = this.params;

    if (Math.abs(gapPct) <= flatGapThreshold) {
      this.reject(`Gap too flat: ${(gapPct * 100).toFixed(1)}% (within ±${(flatGapThreshold * 100).toFixed(1)}% range)`);
      return false;
    }

    // Gap direction overrides pre-classification (per theory: OOPS that gaps up → SS,
    // SS that gaps down → OOPS). Determine situation from actual gap direction FIRST.
    if (gapPct > 0) this.situation = "reversal_s1";
    else this.situation = "reversal_s2";

    if (this.situation === "reversal_s1") {
      if (gapPct > this.params.gapUpMaxPct) {
        this.reject(`Gap up too high: ${(gapPct * 100).toFixed(1)}% > ${(this.params.gapUpMaxPct * 100).toFixed(1)}%`);
        return false;
      }
    }

    this.gapValidated = true;
    this.transitionTo(StockStateEnum.GAP_VALIDATED, "gap validated");
    return true;
  }

  checkLowViolation(): boolean {
    if (this.openPrice === null) return false;

    if (this.situation === "reversal_s2") {
      this.lowViolationChecked = true;
      this.transitionTo(StockStateEnum.QUALIFIED, "low violation check passed (OOPS)");
      return true;
    }

    const threshold = this.openPrice * (1 - this.params.lowViolationPct);

    if (this.dailyLow < threshold) {
      this.reject(`Low violation: ${this.dailyLow.toFixed(2)} < ${threshold.toFixed(2)} (1% below open ${this.openPrice.toFixed(2)})`);
      return false;
    }

    this.lowViolationChecked = true;
    this.transitionTo(StockStateEnum.QUALIFIED, "low violation check passed");

    return true;
  }

  prepareEntry(): void {
    if (!this.isActive) return;

    if (this.state === StockStateEnum.QUALIFIED) {
      this.transitionTo(StockStateEnum.SELECTED, "preparing entry");
    }

    if (this.situation === "reversal_s1") {
      this.prepareStrongStart();
    } else {
      this.prepareOops();
    }
  }

  private prepareStrongStart(): void {
    const threshold = this.openPrice! * (1 - this.params.lowViolationPct);
    if (this.dailyLow < threshold) {
      this.reject(`Low violation at entry time: ${this.dailyLow.toFixed(2)} < ${threshold.toFixed(2)}`);
      return;
    }

    this.entryReady = true;
    this.transitionTo(StockStateEnum.WAITING_FOR_ENTRY, "Strong Start ready");
    // Old behavior: update_entry_levels() only sets entry_high if daily_high > open_price
    // This means s1 cannot trigger if stock never made a new high above open
    this.updateEntryLevels();
  }

  private prepareOops(): void {
    this.entryPrice = this.previousClose;
    this.entrySl = this.entryPrice * (1 - this.params.entrySlPct);
    this.entryReady = true;
    this.transitionTo(StockStateEnum.WAITING_FOR_ENTRY, "OOPS ready");
  }

  updateEntryLevels(): void {
    if (!this.isActive || this.situation !== "reversal_s1" || this.openPrice === null) return;

    const newHigh = this.dailyHigh;
    const newSl = newHigh * (1 - this.params.entrySlPct);

    if (this.entryHigh === null || newHigh > this.entryHigh) {
      this.entryHigh = newHigh;
      this.entrySl = newSl;
      this.entryPrice = newHigh;
      this.entryReady = true;
    }
  }

  enterPosition(price: number, timestamp: Date): void {
    if (this.situation !== "reversal_s2") {
      this.entryPrice = price;
    }
    this.entryTime = timestamp;
    this.entered = true;
    this.transitionTo(StockStateEnum.ENTERED, "position entered");
  }

  exitPosition(price: number, timestamp: Date, reason: string): void {
    this.exitPrice = price;
    this.exitTime = timestamp;
    this.isSubscribed = false;
    this.transitionTo(StockStateEnum.EXITED, reason);

    if (this.entryPrice) {
      this.pnl = ((price - this.entryPrice) / this.entryPrice) * 100;
    }
  }

  markSelected(): void {
    this.transitionTo(StockStateEnum.SELECTED, "selected for trading");
  }
}
