import { UpstoxStreamer } from "./streamer";
import { LiveTraderConfig, ScannerResult, ScannerStock, ReversalSituation, StockStateEnum } from "./types";

import { ReversalStockMonitor } from "./reversal/stock-monitor";
import { ReversalIntegration } from "./reversal/integration";

import { StockMonitor as ContinuationStockMonitor } from "./continuation/stock-monitor";
import { ContinuationIntegration } from "./continuation/integration";

import { PaperTrader } from "./paper-trader";
import { sleepUntilIST, PY_API } from "./task-utils";
import { runPreMarketFlow, PreMarketParams } from "./pre-market-flow";
import { loadStocksFromScanner } from "./stocks-loader";

export type BotMode = "reversal" | "continuation";

export class LiveTraderOrchestrator {
  public readonly mode: BotMode;
  public config: LiveTraderConfig | null = null;
  public streamer: UpstoxStreamer | null = null;
  public paperTrader: PaperTrader | null = null;

  public reversalMonitor: ReversalStockMonitor | null = null;
  public reversalIntegration: ReversalIntegration | null = null;

  public continuationMonitor: ContinuationStockMonitor | null = null;
  public continuationIntegration: ContinuationIntegration | null = null;

  public running = false;
  public debugTickCount = 0;
  private sessionId = "";

  public validatedInstrumentKeys: string[] = [];
  public preMarketComplete = false;

  constructor(mode: BotMode) { this.mode = mode; }

  private log(msg: string) {
    console.log(`[ORCHESTRATOR] ${msg}`);
    (globalThis as any).__addLiveLog?.(msg);
  }

  async initialize(
    config: LiveTraderConfig, instruments: string[],
    stocks?: ScannerStock[] | null,
  ): Promise<void> {
    this.config = config;
    this.sessionId = new Date().toISOString().slice(0, 19).replace(/[:-]/g, "_");

    this.streamer = new UpstoxStreamer(config.accessToken, this.mode);
    await this.streamer.init();

    const symbolMap = new Map<string, string>();
    for (const key of instruments) {
      const parts = key.split("|");
      symbolMap.set(key, parts.length >= 2 ? parts[parts.length - 1] : key);
    }
    this.streamer.setSymbolMap(symbolMap);

    if (this.config.paperTrading) {
      this.paperTrader = new PaperTrader(this.config.capital, this.config.riskPerTrade, this.config.entrySlPct, this.sessionId);
    }

    if (instruments.length > 0) this.streamer.updateActiveInstruments(instruments);

    if (this.mode === "reversal") {
      this.reversalMonitor = new ReversalStockMonitor();
      if (stocks) {
        const params = {
          flatGapThreshold: this.config.flatGapThreshold ?? 0.003,
          entrySlPct: this.config.entrySlPct ?? 0.04, lowViolationPct: this.config.lowViolationPct ?? 0.01,
          trailingSlThreshold: this.config.trailingSlThreshold ?? 0.05, gapUpMaxPct: this.config.gapUpMaxPct ?? 0.05,
        };
        for (const s of stocks) {
          if (!s.situation?.startsWith("reversal")) continue;
          this.reversalMonitor.addStock(s.symbol, s.instrumentKey || s.symbol, s.previousClose, s.situation as ReversalSituation, params, s.declineDays || 0);
          this.log(`Loaded reversal stock: ${s.symbol} (prev close: ${s.previousClose}, decline: ${s.declineDays || 0}d)`);
        }
      }
      this.reversalIntegration = new ReversalIntegration(this.streamer, this.reversalMonitor, this.paperTrader, this.config?.maxPositions);
    }

    if (this.mode === "continuation") {
      this.continuationMonitor = new ContinuationStockMonitor();
      if (stocks) {
        const params = {
          flatGapThreshold: this.config.flatGapThreshold ?? 0.003, entrySlPct: this.config.entrySlPct ?? 0.04,
          lowViolationPct: this.config.lowViolationPct ?? 0.01, trailingSlThreshold: this.config.trailingSlThreshold ?? 0.05,
          gapUpMaxPct: this.config.gapUpMaxPct ?? 0.05, entryTime: this.config.entryTime,
        };
        for (const s of stocks) {
          if (s.situation !== "continuation") continue;
          this.continuationMonitor.addStock(s.symbol, s.instrumentKey || s.symbol, s.previousClose, params);
          this.log(`Loaded continuation stock: ${s.symbol} (prev close: ${s.previousClose})`);
        }
      }
      this.continuationIntegration = new ContinuationIntegration(this.streamer, this.continuationMonitor, this.paperTrader, this.config?.maxPositions);
      this.continuationMonitor.marketOpenTime = this.config.marketOpenTime;
    }
  }

  async start(): Promise<void> {
    if (!this.streamer || !this.config) throw new Error("LiveTrader not initialized. Call initialize() first.");

    this.running = true;

    this.streamer.onTick = (tick) => {
      this.debugTickCount++;
      if (!this.streamer?.activeInstruments.has(tick.instrumentKey)) return;

      if (tick.vtt !== undefined) {
        const stockState = this.reversalMonitor?.stocks.get(tick.instrumentKey)
          ?? this.continuationMonitor?.stocks.get(tick.instrumentKey);
        if (stockState) stockState.cumulativeVolume = tick.vtt;
      }

      if (this.reversalIntegration && this.reversalMonitor?.stocks.has(tick.instrumentKey))
        this.reversalIntegration.simplifiedTickHandler(tick.instrumentKey, tick.symbol, tick.ltp, tick.timestamp, tick.ohlcList);

      if (this.continuationIntegration && this.continuationMonitor?.stocks.has(tick.instrumentKey))
        this.continuationIntegration.simplifiedTickHandler(tick.instrumentKey, tick.symbol, tick.ltp, tick.timestamp, tick.ohlcList);
    };

    this.streamer.onReconnect = (attempt) => this.log(`Reconnecting (attempt ${attempt})...`);
    this.streamer.onClose = () => this.log("Streamer disconnected");

    if (!this.preMarketComplete) {
      const stocks: any[] = [];
      if (this.mode === "continuation") for (const [, s] of this.continuationMonitor?.stocks ?? new Map()) stocks.push(s);
      if (this.mode === "reversal") for (const [, s] of this.reversalMonitor?.stocks ?? new Map()) stocks.push(s);
      if (stocks.length > 0) {
        this.log("Running automatic pre-market validation...");
        try {
          const pmParams: PreMarketParams = { mode: this.mode, config: this.config, continuationMonitor: this.continuationMonitor, reversalMonitor: this.reversalMonitor };
          const result = await runPreMarketFlow(pmParams, stocks, (msg) => this.log(msg));
          this.validatedInstrumentKeys = result.validatedKeys;
          this.preMarketComplete = true;
        } catch (e: any) { this.log(`Pre-market flow failed: ${e.message}`); this.running = false; return; }
      }
    }

    let activeSubKeys: string[] = [];
    if (this.preMarketComplete) {
      if (this.validatedInstrumentKeys.length > 0) {
        this.log(`Activating ${this.validatedInstrumentKeys.length} pre-validated stocks`);
        this.streamer.updateActiveInstruments(this.validatedInstrumentKeys);
        activeSubKeys = this.validatedInstrumentKeys;
      } else { activeSubKeys = []; this.log("No stocks passed pre-market - not subscribing"); }
    } else {
      activeSubKeys = Array.from(this.streamer.activeInstruments);
    }

    if (activeSubKeys.length === 0) { this.log("No stocks to subscribe - stopping"); this.running = false; return; }

    this.log(`Waiting for MARKET_OPEN (${this.config.marketOpen})...`);
    await sleepUntilIST(this.config.marketOpen);
    this.log("MARKET OPEN");

    this.streamer.updateActiveInstruments(activeSubKeys);
    const connected = await this.streamer.connect();
    if (!connected) { this.log("FAILED to connect data stream"); this.running = false; return; }
    this.streamer.subscribe();

    const minRatio = this.config.svroMinVolumeRatio ?? 0.075;

    this.log(`Waiting for ENTRY_TIME (${this.config.entryTime})...`);
    await sleepUntilIST(this.config.entryTime);
    this.log("ENTRY TIME REACHED");

    if (this.mode === "reversal") {
      this.log("Making OOPS stocks ready for immediate trading...");
      for (const [, stock] of this.reversalMonitor?.stocks ?? new Map())
        if (stock.isActive && stock.gapValidated && stock.situation === "reversal_s2") { stock.entryReady = true; this.log(`${stock.symbol} (OOPS): Ready`); }
      this.reversalMonitor?.prepareEntries();
      for (const [, s] of this.reversalMonitor?.stocks ?? new Map()) {
        if (s.state === StockStateEnum.REJECTED && s.rejectionReason) {
          this.log(`${s.symbol}: Rejected during preparation - ${s.rejectionReason}`);
        }
      }
    }

    if (this.mode === "continuation") {
      this.log("Phase 2: checking low violations, volume...");
      this.continuationMonitor?.checkViolations();

      for (const [, s] of this.continuationMonitor?.stocks ?? new Map()) {
        if (s.state === StockStateEnum.REJECTED && s.rejectionReason && this.validatedInstrumentKeys.includes(s.instrumentKey)) {
          this.log(`${s.symbol}: Rejected at entry time - ${s.rejectionReason}`);
        }
      }
      for (const [, s] of this.continuationMonitor?.stocks ?? new Map()) {
        if (s.isActive && s.gapValidated && s.lowViolationChecked && this.validatedInstrumentKeys.includes(s.instrumentKey)) {
          this.log(`${s.symbol}: Low violation passed (low=${s.dailyLow.toFixed(2)})`);
        }
      }

      const qualifiedForVol = Array.from(this.continuationMonitor?.stocks.values() ?? [])
        .filter((s) => s.isActive && s.situation === "continuation" && s.gapValidated && s.lowViolationChecked && !s.volumeValidated);

      if (qualifiedForVol.length > 0 && this.continuationIntegration) {
        const symbols = qualifiedForVol.map((s) => s.symbol);
        try {
          const r = await fetch(`${PY_API}/api/prep/current-volume`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ symbols }) });
          const d = await r.json();
          const volumes: Record<string, number> = d.volumes ?? {};
          for (const stock of qualifiedForVol) {
            const vol = volumes[stock.symbol] ?? 0;
            vol > 0 ? (stock.earlyVolume = vol, stock.validateVolume(minRatio)) : stock.reject("No volume data");
          }
        } catch { for (const stock of qualifiedForVol) stock.reject("Volume fetch failed"); }
        this.continuationIntegration.subscriptionManager.unsubscribeLowViolated();

        for (const [, s] of this.continuationMonitor?.stocks ?? new Map()) {
          if (s.state === StockStateEnum.REJECTED && s.rejectionReason && this.validatedInstrumentKeys.includes(s.instrumentKey)) {
            this.log(`${s.symbol}: Rejected at entry time - ${s.rejectionReason}`);
          }
        }
        for (const stock of qualifiedForVol) {
          if (stock.volumeValidated) {
            this.log(`${stock.symbol}: Volume validated (ratio=${(stock.earlyVolume / stock.volumeBaseline * 100).toFixed(1)}%, min=${(minRatio * 100).toFixed(1)}%)`);
          }
        }
      }
      this.continuationMonitor?.prepareEntries();
      for (const [, s] of this.continuationMonitor?.stocks ?? new Map()) {
        if (s.state === StockStateEnum.WAITING_FOR_ENTRY && this.validatedInstrumentKeys.includes(s.instrumentKey)) {
          this.log(`${s.symbol}: Monitoring for entry (entryHigh=${s.entryHigh?.toFixed(2)}, entrySl=${s.entrySl?.toFixed(2)})`);
        }
      }
    }

    if (this.mode === "reversal") {
      this.log("Phase 2b: checking low violations...");
      this.reversalMonitor?.checkViolations();
      for (const [, s] of this.reversalMonitor?.stocks ?? new Map()) {
        if (s.state === StockStateEnum.REJECTED && s.rejectionReason) {
          this.log(`${s.symbol}: Rejected - ${s.rejectionReason}`);
        }
      }
      for (const [, s] of this.reversalMonitor?.stocks ?? new Map()) {
        if (s.isActive && s.gapValidated && s.lowViolationChecked) {
          this.log(`${s.symbol}: Low violation passed`);
        }
      }
      this.reversalIntegration?.subscriptionManager.unsubscribeLowViolated();

      const selResult = this.reversalMonitor?.selectStocks(this.config?.maxPositions ?? 2) ?? { selected: [], rejectedSS: [], notSelected: [] };

      for (const stock of selResult.selected) {
        this.log(`${stock.symbol}: Selected for trading`);
      }
      if (selResult.rejectedSS.length > 0) {
        for (const key of selResult.rejectedSS) {
          const stock = this.reversalMonitor?.stocks.get(key);
          if (stock) { stock.rejectionReason = "VIP OOPS selected instead"; this.log(`${stock.symbol}: Not selected - VIP OOPS prioritized`); }
        }
        this.reversalIntegration?.subscriptionManager.safeUnsubscribe(selResult.rejectedSS, "ss_rejected_vip_oops");
        this.reversalIntegration?.subscriptionManager.markStocksUnsubscribed(selResult.rejectedSS);
      }
      if (selResult.notSelected.length > 0) {
        for (const key of selResult.notSelected) {
          const stock = this.reversalMonitor?.stocks.get(key);
          if (stock) { stock.rejectionReason = "Not selected (max positions filled)"; this.log(`${stock.symbol}: Not selected - max positions filled`); }
        }
        this.reversalIntegration?.subscriptionManager.safeUnsubscribe(selResult.notSelected, "not_selected");
        this.reversalIntegration?.subscriptionManager.markStocksUnsubscribed(selResult.notSelected);
      }
      this.reversalIntegration?.subscriptionManager.markSelected(selResult.selected);
    }

    this.log(`Bot started (mode: ${this.mode}), ${this.streamer.activeInstruments.size} stocks subscribed`);
  }

  async loadStocksFromScanner(scannerResult: ScannerResult): Promise<void> {
    if (!this.streamer || !this.config) return;
    if (!this.reversalMonitor && !this.continuationMonitor) return;
    const result = loadStocksFromScanner(
      this.mode, this.config, this.streamer, this.paperTrader,
      this.reversalMonitor!, this.continuationMonitor!, scannerResult,
      (msg) => this.log(msg),
    );
    if (result.reversalIntegration) this.reversalIntegration = result.reversalIntegration;
    if (result.continuationIntegration) this.continuationIntegration = result.continuationIntegration;
  }

  async stop(): Promise<void> {
    this.running = false;
    this.preMarketComplete = false;
    this.validatedInstrumentKeys = [];
    this.log("Stopping bot...");
    this.reversalIntegration?.cleanup();
    this.continuationIntegration?.cleanup();
    this.streamer?.disconnect();
    if (this.paperTrader) this.log(this.paperTrader.getSummary());
    this.log("Bot stopped");
  }

  getStatus(): Record<string, unknown> {
    return {
      running: this.running, mode: this.mode, preMarketComplete: this.preMarketComplete,
      connected: this.streamer?.connected ?? false, subscribed: this.streamer?.activeInstruments.size ?? 0,
      validatedCount: this.validatedInstrumentKeys.length, ticksReceived: this.debugTickCount,
      config: this.config ? { marketOpen: this.config.marketOpen, prepStart: this.config.prepStart, entryTime: this.config.entryTime } : null,
      reversal: this.reversalMonitor?.getSummary() ?? {}, continuation: this.continuationMonitor?.getSummary() ?? {},
      paperTrader: this.paperTrader?.getStats() ?? {},
    };
  }
}
