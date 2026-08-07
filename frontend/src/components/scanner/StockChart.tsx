"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import {
  createChart, ColorType, IChartApi, ISeriesApi,
  CandlestickSeries, LineSeries, SeriesType, LineStyle,
} from "lightweight-charts";
import { DrawingManager, DatePriceRange } from "lightweight-charts-drawing";

interface Candle {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

interface SMA {
  date: string;
  value: number;
}

interface Props {
  symbol: string;
  candles: Candle[];
  sma?: SMA[];
  width?: number;
  height?: number;
}

interface OHLCV {
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

interface MeasurePreview {
  startPrice: number;
  startTime: any;
  endPrice: number;
  endTime: any;
  priceChange: number;
  pctChange: number;
  bars: number;
}

let measureCounter = 0;

export default function StockChart({ symbol, candles, sma, width, height = 340 }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const seriesRef = useRef<ISeriesApi<SeriesType> | null>(null);
  const managerRef = useRef<DrawingManager | null>(null);
  const previewLineRef = useRef<ISeriesApi<SeriesType> | null>(null);
  const isUpdatingPreviewRef = useRef(false);
  const [ohlcv, setOhlcv] = useState<OHLCV | null>(null);
  const [measureActive, setMeasureActive] = useState(false);
  const measureActiveRef = useRef(false);
  const measureStartRef = useRef<{ time: any; price: number } | null>(null);
  const [preview, setPreview] = useState<MeasurePreview | null>(null);
  const previewRef = useRef<MeasurePreview | null>(null);
  const [hasMeasurements, setHasMeasurements] = useState(false);
  const perStockRangeRef = useRef<Record<string, { from: number; to: number } | null>>({});
  const lastRangeRef = useRef<{ from: number; to: number } | null>(null);

  const toggleMeasure = useCallback(() => {
    const next = !measureActive;
    setMeasureActive(next);
    measureActiveRef.current = next;
    measureStartRef.current = null;
    setPreview(null);
    previewRef.current = null;
    if (previewLineRef.current) {
      previewLineRef.current.setData([]);
      previewLineRef.current = null;
    }
    managerRef.current?.setActiveTool(next ? "date-price-range" : null);
  }, [measureActive]);

  const clearMeasurements = useCallback(() => {
    managerRef.current?.clearAll();
    setHasMeasurements(false);
  }, []);

  useEffect(() => {
    if (!containerRef.current || candles.length === 0) return;

    const container = containerRef.current;

    const chart = createChart(container, {
      width: width || container.clientWidth,
      height,
      layout: {
        background: { type: ColorType.Solid, color: "#0d1117" },
        textColor: "#94a3b8",
      },
      grid: {
        vertLines: { color: "#1e293b" },
        horzLines: { color: "#1e293b" },
      },
      crosshair: {
        mode: 0,
        vertLine: { color: "#6366f1", width: 1, style: 2, labelBackgroundColor: "#6366f1" },
        horzLine: { color: "#6366f1", width: 1, style: 2, labelBackgroundColor: "#6366f1" },
      },
      timeScale: {
        borderColor: "#334155",
        timeVisible: false,
        tickMarkFormatter: (time: number) => {
          const d = new Date(time * 1000);
          return `${d.getDate()}/${d.getMonth() + 1}`;
        },
      },
      rightPriceScale: {
        borderColor: "#334155",
      },
    });

    chartRef.current = chart;

    const candleSer = chart.addSeries(CandlestickSeries, {
      upColor: "#10b981",
      downColor: "#ef4444",
      borderUpColor: "#10b981",
      borderDownColor: "#ef4444",
      wickUpColor: "#10b981",
      wickDownColor: "#ef4444",
    });

    seriesRef.current = candleSer as ISeriesApi<SeriesType>;

    const formatted = candles.map((c) => ({
      time: Math.floor(new Date(c.date).getTime() / 1000) as any,
      open: c.open,
      high: c.high,
      low: c.low,
      close: c.close,
    }));

    candleSer.setData(formatted);

    if (sma && sma.length > 0) {
      const lineSer = chart.addSeries(LineSeries, {
        color: "#6366f1",
        lineWidth: 2,
        priceLineVisible: false,
        lastValueVisible: false,
      });

      const smaFormatted = sma.map((s) => ({
        time: Math.floor(new Date(s.date).getTime() / 1000) as any,
        value: s.value,
      }));

      lineSer.setData(smaFormatted);
    }

    const savedRange = perStockRangeRef.current[symbol] || lastRangeRef.current;
    if (savedRange) {
      chart.timeScale().setVisibleLogicalRange(savedRange);
    } else {
      chart.timeScale().fitContent();
    }

    const computeBars = (t1: any, t2: any): number => {
      const s1 = typeof t1 === "number" ? t1 : Math.floor(new Date(t1 as string).getTime() / 1000);
      const s2 = typeof t2 === "number" ? t2 : Math.floor(new Date(t2 as string).getTime() / 1000);
      const diff = Math.abs(s2 - s1);
      const daySeconds = 86400;
      return Math.max(1, Math.round(diff / daySeconds));
    };

    chart.subscribeCrosshairMove((param) => {
      const fallback = () => {
        const last = candles[candles.length - 1];
        if (last) setOhlcv({ open: last.open, high: last.high, low: last.low, close: last.close, volume: last.volume });
      };
      if (!param.time || !param.seriesData?.size) { fallback(); return; }
      const data = param.seriesData.get(candleSer) as any;
      if (!data) { fallback(); return; }
      const t = (param.time as number) * 1000;
      const match = candles.find(c => Math.abs(new Date(c.date).getTime() - t) < 30000);
      setOhlcv({
        open: data.open, high: data.high, low: data.low, close: data.close,
        volume: match?.volume ?? 0,
      });

      if (!measureActiveRef.current || !measureStartRef.current || !param.point) return;
      if (isUpdatingPreviewRef.current) return;

      const start = measureStartRef.current;
      const endPrice = data.close;
      const endTime = param.time;

      const priceChange = endPrice - start.price;
      const pctChange = start.price !== 0 ? (priceChange / start.price) * 100 : 0;
      const bars = computeBars(start.time, endTime);

      const p: MeasurePreview = {
        startPrice: start.price,
        startTime: start.time,
        endPrice,
        endTime,
        priceChange,
        pctChange,
        bars,
      };
      previewRef.current = p;
      setPreview(p);

      if (!previewLineRef.current) {
        previewLineRef.current = chart.addSeries(LineSeries, {
          color: "#818cf8",
          lineWidth: 1,
          lineStyle: LineStyle.Dashed,
          priceLineVisible: false,
          lastValueVisible: false,
        });
      }

      const pl = previewLineRef.current;
      if (pl) {
        const toSec = (tm: any) => typeof tm === "number" ? tm : Math.floor(new Date(tm).getTime() / 1000);
        const t1 = toSec(start.time);
        const t2 = toSec(endTime);
        const pt1 = { time: start.time, value: start.price };
        const pt2 = { time: endTime, value: endPrice };
        isUpdatingPreviewRef.current = true;
        pl.setData(t1 <= t2 ? [pt1, pt2] : [pt2, pt1]);
        isUpdatingPreviewRef.current = false;
      }
    });

    const last = candles[candles.length - 1];
    setOhlcv({ open: last.open, high: last.high, low: last.low, close: last.close, volume: last.volume });

    const manager = new DrawingManager();
    manager.attach(chart, candleSer as ISeriesApi<SeriesType>, container);
    managerRef.current = manager;

    manager.on("drawing:added", () => setHasMeasurements(true));
    manager.on("drawing:removed", () => {
      if (manager.getAllDrawings().length === 0) setHasMeasurements(false);
    });

    chart.subscribeClick((param) => {
      if (!measureActiveRef.current || !param.point) return;
      const seriesData = param.seriesData?.get(candleSer) as any;
      if (!seriesData) return;
      const clickedTime = param.time;
      if (!clickedTime) return;

      const clickedPrice = seriesData.close;

      if (!measureStartRef.current) {
        measureStartRef.current = { time: clickedTime, price: clickedPrice };
        return;
      }

      const start = measureStartRef.current;
      const end = { time: clickedTime, price: clickedPrice };

      if (previewLineRef.current) {
        previewLineRef.current.setData([]);
        previewLineRef.current = null;
      }

      const m = new DatePriceRange(
        `measure-${++measureCounter}`,
        [start, end],
        {},
        { showPrices: true, showPercentage: true, showBars: true, showDays: true, filled: true }
      );
      manager.addDrawing(m);

      measureStartRef.current = null;
      previewRef.current = null;
      setPreview(null);
      setMeasureActive(false);
      measureActiveRef.current = false;
      manager.setActiveTool(null);
    });

    const handleResize = () => {
      if (container) {
        chart.applyOptions({ width: container.clientWidth });
      }
    };

    window.addEventListener("resize", handleResize);

    return () => {
      window.removeEventListener("resize", handleResize);
      if (previewLineRef.current) {
        previewLineRef.current.setData([]);
        previewLineRef.current = null;
      }
      manager.detach();
      managerRef.current = null;
      const range = chart.timeScale().getVisibleLogicalRange();
      if (range) {
        perStockRangeRef.current[symbol] = range;
        lastRangeRef.current = range;
      }
      chart.remove();
      chartRef.current = null;
      seriesRef.current = null;
    };
  }, [symbol, candles, sma, height, width]);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape" && measureActiveRef.current) {
        setMeasureActive(false);
        measureActiveRef.current = false;
        measureStartRef.current = null;
        previewRef.current = null;
        setPreview(null);
        if (previewLineRef.current) {
          previewLineRef.current.setData([]);
          previewLineRef.current = null;
        }
        managerRef.current?.setActiveTool(null);
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, []);

  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.style.cursor = measureActive ? "crosshair" : "";
    }
  }, [measureActive]);

  return (
    <div style={{ position: "relative" }}>
      {ohlcv && (
        <div
          style={{
            position: "absolute",
            top: 8,
            left: 8,
            zIndex: 10,
            background: "rgba(13,17,23,0.85)",
            border: "1px solid #334155",
            borderRadius: 6,
            padding: "6px 10px",
            fontFamily: '"SF Mono", "Fira Code", monospace',
            fontSize: 11,
            lineHeight: "16px",
            pointerEvents: "none",
          }}
        >
          <div style={{ display: "flex", gap: 10 }}>
            <span style={{ color: "#e2e8f0" }}>O: <b>{ohlcv.open.toFixed(2)}</b></span>
            <span style={{ color: "#10b981" }}>H: <b>{ohlcv.high.toFixed(2)}</b></span>
            <span style={{ color: "#ef4444" }}>L: <b>{ohlcv.low.toFixed(2)}</b></span>
            <span style={{ color: "#e2e8f0" }}>C: <b>{ohlcv.close.toFixed(2)}</b></span>
            {ohlcv.volume > 0 && <span style={{ color: "#94a3b8" }}>Vol: <b>{ohlcv.volume.toLocaleString()}</b></span>}
          </div>
        </div>
      )}

      {measureActive && (
        <div
          style={{
            position: "absolute",
            top: 40,
            left: 42,
            zIndex: 10,
            background: preview ? "rgba(13,17,23,0.92)" : "rgba(99,102,241,0.15)",
            border: preview ? "1px solid #334155" : "1px solid rgba(99,102,241,0.3)",
            borderRadius: 6,
            padding: "4px 10px",
            fontFamily: '"SF Mono", "Fira Code", monospace',
            fontSize: 10,
            color: "#e2e8f0",
            pointerEvents: "none",
            whiteSpace: "nowrap",
            transition: "all 0.1s ease",
          }}
        >
          {preview ? (
            <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
              <span style={{ color: preview.priceChange >= 0 ? "#10b981" : "#ef4444", fontWeight: 700 }}>
                {preview.priceChange >= 0 ? "+" : ""}{preview.priceChange.toFixed(2)}
              </span>
              <span style={{ color: preview.pctChange >= 0 ? "#10b981" : "#ef4444", fontWeight: 700 }}>
                {preview.pctChange >= 0 ? "+" : ""}{preview.pctChange.toFixed(2)}%
              </span>
              <span style={{ color: "#94a3b8" }}>{preview.bars} bars</span>
              <span style={{ color: "#64748b", fontSize: 9 }}>[ click to place ]</span>
            </div>
          ) : (
            <span style={{ color: "#818cf8" }}>Click start point</span>
          )}
        </div>
      )}

      <button
        onClick={toggleMeasure}
        title={measureActive ? "Cancel (Esc)" : "Measure price & time"}
        style={{
          position: "absolute",
          top: 40,
          left: 8,
          zIndex: 10,
          width: 28,
          height: 28,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          background: measureActive ? "rgba(99,102,241,0.3)" : "rgba(13,17,23,0.85)",
          border: measureActive ? "1px solid #6366f1" : "1px solid #334155",
          borderRadius: 6,
          cursor: "pointer",
          padding: 0,
          fontSize: 14,
          transition: "all 0.15s",
        }}
      >
        📏
      </button>

      {hasMeasurements && (
        <button
          onClick={clearMeasurements}
          title="Clear all measurements"
          style={{
            position: "absolute",
            top: 72,
            left: 8,
            zIndex: 10,
            width: 28,
            height: 28,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            background: "rgba(13,17,23,0.85)",
            border: "1px solid #334155",
            borderRadius: 6,
            cursor: "pointer",
            padding: 0,
            fontSize: 12,
            color: "#ef4444",
            transition: "all 0.15s",
          }}
        >
          ✕
        </button>
      )}

      <div
        ref={containerRef}
        style={{ width: "100%", height }}
      />
    </div>
  );
}
