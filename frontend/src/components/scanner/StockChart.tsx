"use client";

import { useEffect, useRef, useState } from "react";
import { createChart, ColorType, IChartApi, CandlestickSeries, LineSeries } from "lightweight-charts";

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

export default function StockChart({ symbol, candles, sma, width, height = 340 }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const [ohlcv, setOhlcv] = useState<OHLCV | null>(null);
  const perStockRangeRef = useRef<Record<string, { from: number; to: number } | null>>({});
  const lastRangeRef = useRef<{ from: number; to: number } | null>(null);

  useEffect(() => {
    if (!containerRef.current || candles.length === 0) return;

    const chart = createChart(containerRef.current, {
      width: width || containerRef.current.clientWidth,
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
    });

    const last = candles[candles.length - 1];
    setOhlcv({ open: last.open, high: last.high, low: last.low, close: last.close, volume: last.volume });

    const handleResize = () => {
      if (containerRef.current) {
        chart.applyOptions({ width: containerRef.current.clientWidth });
      }
    };

    window.addEventListener("resize", handleResize);

    return () => {
      window.removeEventListener("resize", handleResize);
      const range = chart.timeScale().getVisibleLogicalRange();
      if (range) {
        perStockRangeRef.current[symbol] = range;
        lastRangeRef.current = range;
      }
      chart.remove();
      chartRef.current = null;
    };
  }, [symbol, candles, sma, height, width]);

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
      <div
        ref={containerRef}
        style={{ width: "100%", height }}
      />
    </div>
  );
}
