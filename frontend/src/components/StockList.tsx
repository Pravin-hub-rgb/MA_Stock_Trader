"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import {
  Box, Typography, Tabs, Tab, IconButton, Tooltip, Button,
} from "@mui/material";
import {
  Delete as DeleteIcon,
  DeleteSweep as ClearIcon,
  TrendingUp as UpIcon,
  TrendingDown as DownIcon,
} from "@mui/icons-material";
import StockChart from "./scanner/StockChart";
import ToastNotification from "./ToastNotification";

const API = "http://127.0.0.1:8001";

interface StockItem {
  id: number; list_type: string; symbol: string; close: number | null;
  trend_context: string | null; period: number | null;
  depth_pct: number | null; added_at: string;
}

interface CandleData {
  candles: { date: string; open: number; high: number; low: number; close: number; volume: number }[];
  sma: { date: string; value: number }[];
}

type ListType = "continuation" | "reversal";

export default function StockList() {
  const [contStocks, setContStocks] = useState<StockItem[]>([]);
  const [revStocks, setRevStocks] = useState<StockItem[]>([]);
  const [activeTab, setActiveTab] = useState<ListType>("continuation");
  const [selectedIdx, setSelectedIdx] = useState(0);
  const [chartData, setChartData] = useState<Record<string, CandleData>>({});
  const [loaded, setLoaded] = useState(false);
  const listRef = useRef<HTMLDivElement>(null);
  const [toasts, setToasts] = useState<{ id: string; message: string; type: "success" | "error" | "warning"; position: number }[]>([]);
  const removeToast = useCallback((id: string) => setToasts(prev => prev.filter(t => t.id !== id)), []);
  const showToast = useCallback((message: string, type: "success" | "error" | "warning") => {
    const id = `t-${Date.now()}-${Math.random()}`;
    setToasts(prev => [...prev, { id, message, type, position: prev.length }]);
    setTimeout(() => removeToast(id), 4000);
  }, [removeToast]);

  const stocks = activeTab === "continuation" ? contStocks : revStocks;
  const selected = stocks[selectedIdx];
  const tabColor = activeTab === "continuation" ? "#10b981" : "#f59e0b";

  const fetchLists = useCallback(async () => {
    try {
      const [cr, rr] = await Promise.all([
        fetch(`${API}/api/stock-list/continuation`).then(r => r.json()),
        fetch(`${API}/api/stock-list/reversal`).then(r => r.json()),
      ]);
      setContStocks(cr.stocks || []);
      setRevStocks(rr.stocks || []);
    } catch {
      showToast("Failed to load stock lists", "error");
    }
  }, [showToast]);

  useEffect(() => { fetchLists(); }, [fetchLists]);

  useEffect(() => {
    setSelectedIdx(0);
    if (stocks.length === 0) {
      setChartData({});
      setLoaded(true);
      return;
    }
    const symbols = stocks.map(s => s.symbol);
    setLoaded(false);
    setChartData({});
    fetch(`${API}/api/data/batch-stock-history`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ symbols, days: 200 }),
    })
      .then(r => r.json())
      .then(d => setChartData(d.data || {}))
      .catch(() => {})
      .finally(() => setLoaded(true));
  }, [stocks, activeTab]);

  const current = selected ? chartData[selected.symbol] : null;

  const handleKeyDown = useCallback((e: KeyboardEvent) => {
    const len = Math.max(1, stocks.length);
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setSelectedIdx(prev => (prev + 1) % len);
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setSelectedIdx(prev => (prev - 1 + len) % len);
    }
  }, [stocks.length]);

  useEffect(() => {
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [handleKeyDown]);

  useEffect(() => {
    if (listRef.current) {
      const el = listRef.current.children[selectedIdx] as HTMLElement;
      if (el) el.scrollIntoView({ block: "nearest", behavior: "smooth" });
    }
  }, [selectedIdx]);

  const removeStock = async (symbol: string) => {
    try {
      await fetch(`${API}/api/stock-list/${activeTab}/${symbol}`, { method: "DELETE" });
      await fetchLists();
      showToast(`Removed ${symbol}`, "success");
    } catch {
      showToast(`Failed to remove ${symbol}`, "error");
    }
  };

  const clearList = async () => {
    try {
      const r = await fetch(`${API}/api/stock-list/${activeTab}`, { method: "DELETE" });
      const d = await r.json();
      await fetchLists();
      showToast(`Cleared ${d.count} stocks`, "success");
    } catch {
      showToast(`Failed to clear ${activeTab} list`, "error");
    }
  };

  return (
    <Box>
      {toasts.map((t) => (
        <Box key={t.id} sx={{ position: "fixed", bottom: 24 + t.position * 60, right: 24, zIndex: 9999 }}>
          <ToastNotification message={t.message} type={t.type} onClose={() => removeToast(t.id)} slideFrom="right" />
        </Box>
      ))}

      <Box sx={{ display: "flex", gap: 2, height: 720 }}>
        <Box sx={{ flex: 1, minWidth: 0, display: "flex", flexDirection: "column" }}>
          {stocks.length === 0 ? (
            <Box sx={{ color: "#64748b", fontSize: "0.85rem", py: 8, textAlign: "center" }}>
              {activeTab === "continuation"
                ? "No continuation stocks saved. Run a scan and tap + to add."
                : "No reversal stocks saved. Run a scan and tap + to add."}
            </Box>
          ) : !loaded ? (
            <Box sx={{ color: "#64748b", fontSize: "0.85rem", py: 4, textAlign: "center" }}>
              Loading chart data...
            </Box>
          ) : current && current.candles.length > 0 ? (
            <>
              <StockChart symbol={selected.symbol} candles={current.candles} sma={current.sma} height={660} />
              <Box sx={{ px: 1, display: "flex", flexWrap: "wrap", gap: "4px 16px" }}>
                <MiniStat label="Close" value={`₹${(selected.close ?? 0).toFixed(2)}`} />
                {activeTab === "reversal" ? (
                  <>
                    {selected.trend_context && (
                      <MiniStat label="Trend" value={selected.trend_context}
                        color={selected.trend_context === "uptrend" ? "#10b981" : "#f59e0b"} />
                    )}
                    {selected.period != null && (
                      <MiniStat label="Period" value={`${selected.period}d`} />
                    )}
                  </>
                ) : (
                  selected.depth_pct != null && (
                    <MiniStat label="Depth" value={`${selected.depth_pct.toFixed(1)}%`} />
                  )
                )}
                {selected.added_at && (
                  <MiniStat label="Added"
                    value={new Date(selected.added_at).toLocaleDateString("en-IN", { day: "2-digit", month: "short" })} />
                )}
              </Box>
            </>
          ) : (
            <Box sx={{ color: "#64748b", fontSize: "0.85rem", py: 8, textAlign: "center" }}>
              No chart data for {selected?.symbol}
            </Box>
          )}
        </Box>

        <Box sx={{
          width: 300, flexShrink: 0, height: "100%",
          display: "flex", flexDirection: "column",
          bgcolor: "#0d1117", border: "1px solid #1e293b", borderRadius: 2,
          overflow: "hidden",
        }}>
          <Box sx={{ px: 1, pt: 1 }}>
            <Tabs
              value={activeTab}
              onChange={(_e, v) => setActiveTab(v as ListType)}
              sx={{
                minHeight: 38,
                "& .MuiTabs-scroller": { height: 38 },
                "& .MuiTab-root": {
                  fontSize: "0.78rem", fontWeight: 600, textTransform: "none",
                  minHeight: 36, py: 0, borderRadius: 1.5,
                  fontFamily: '"Inter", sans-serif',
                },
                "& .MuiTabs-indicator": { display: "none" },
              }}
            >
              <Tab
                value="continuation"
                label="Continuation"
                icon={<UpIcon sx={{ fontSize: 14 }} />}
                iconPosition="start"
                sx={{
                  flex: 1,
                  bgcolor: activeTab === "continuation" ? "rgba(16,185,129,0.12)" : "transparent",
                  color: activeTab === "continuation" ? "#10b981 !important" : "#64748b",
                }}
              />
              <Tab
                value="reversal"
                label="Reversal"
                icon={<DownIcon sx={{ fontSize: 14 }} />}
                iconPosition="start"
                sx={{
                  flex: 1,
                  bgcolor: activeTab === "reversal" ? "rgba(245,158,11,0.12)" : "transparent",
                  color: activeTab === "reversal" ? "#f59e0b !important" : "#64748b",
                }}
              />
            </Tabs>
          </Box>
          <Box sx={{ height: 2, bgcolor: `${tabColor}18`, mx: 1, mb: 0.5 }} />

          <Box
            ref={listRef}
            sx={{
              flex: 1,
              overflowY: "auto",
              "&::-webkit-scrollbar": { width: 4 },
              "&::-webkit-scrollbar-thumb": { bgcolor: "#334155", borderRadius: 2 },
            }}
          >
            {stocks.map((s, i) => {
              const isSelected = i === selectedIdx;
              return (
                <Box
                  key={s.id}
                  onClick={() => setSelectedIdx(i)}
                  sx={{
                    px: 1.5, py: 1,
                    cursor: "pointer",
                    borderBottom: "1px solid rgba(255,255,255,0.04)",
                    bgcolor: isSelected ? "rgba(99,102,241,0.12)" : "transparent",
                    borderLeft: isSelected ? "3px solid #6366f1" : "3px solid transparent",
                    transition: "all 0.15s",
                    "&:hover": { bgcolor: "rgba(255,255,255,0.04)" },
                  }}
                >
                  <Box sx={{ display: "flex", alignItems: "center", gap: 0.5 }}>
                    <Typography sx={{
                      flex: 1, color: isSelected ? "#f1f5f9" : "#94a3b8",
                      fontWeight: isSelected ? 700 : 500, fontSize: "0.85rem",
                      fontFamily: '"SF Mono", "Fira Code", monospace',
                      overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap",
                    }}>
                      {s.symbol}
                    </Typography>
                    <Typography sx={{ color: "#cbd5e1", fontSize: "0.75rem", fontFamily: '"SF Mono", "Fira Code", monospace' }}>
                      ₹{s.close?.toFixed(2) ?? "—"}
                    </Typography>
                    <Tooltip title={`Remove ${s.symbol}`} placement="left">
                      <IconButton
                        size="small"
                        onClick={(e) => { e.stopPropagation(); removeStock(s.symbol); }}
                        sx={{ color: "#64748b", p: 0.3, "&:hover": { color: "#ef4444", bgcolor: "rgba(239,68,68,0.1)" } }}
                      >
                        <DeleteIcon sx={{ fontSize: 14 }} />
                      </IconButton>
                    </Tooltip>
                  </Box>
                  <Box sx={{ display: "flex", gap: 1.5, pl: 0.5, mt: 0.3 }}>
                    {activeTab === "reversal" ? (
                      <>
                        {s.trend_context && (
                          <Typography sx={{
                            color: s.trend_context === "uptrend" ? "#10b981" : "#f59e0b",
                            fontSize: "0.68rem", fontWeight: 600, letterSpacing: "0.02em",
                          }}>
                            {s.trend_context}
                          </Typography>
                        )}
                        {s.period != null && (
                          <Typography sx={{ color: "#64748b", fontSize: "0.72rem", fontFamily: '"SF Mono", "Fira Code", monospace' }}>
                            {s.period}d
                          </Typography>
                        )}
                      </>
                    ) : (
                      s.depth_pct != null && (
                        <Typography sx={{ color: "#64748b", fontSize: "0.72rem", fontFamily: '"SF Mono", "Fira Code", monospace' }}>
                          {s.depth_pct.toFixed(1)}%
                        </Typography>
                      )
                    )}
                    <Typography sx={{ color: "#475569", fontSize: "0.65rem", whiteSpace: "nowrap" }}>
                      {s.added_at ? new Date(s.added_at).toLocaleDateString("en-IN", { day: "2-digit", month: "short" }) : ""}
                    </Typography>
                  </Box>
                </Box>
              );
            })}
          </Box>

          {stocks.length > 0 && (
            <Box sx={{
              px: 1.5, py: 0.75,
              borderTop: "1px solid rgba(255,255,255,0.04)",
              display: "flex", justifyContent: "space-between", alignItems: "center",
            }}>
              <Typography sx={{ color: "#64748b", fontSize: "0.7rem", fontFamily: '"SF Mono", "Fira Code", monospace' }}>
                {stocks.length} stocks
              </Typography>
              <Button
                size="small"
                onClick={clearList}
                startIcon={<ClearIcon sx={{ fontSize: 14 }} />}
                sx={{
                  color: "#999999", fontSize: "0.7rem", textTransform: "none",
                  fontWeight: 500, minWidth: 0, p: 0.5,
                  "&:hover": { color: "#ef4444", bgcolor: "transparent" },
                }}
              >
                Clear all
              </Button>
            </Box>
          )}
        </Box>
      </Box>
    </Box>
  );
}

function MiniStat({ label, value, color }: { label: string; value: string; color?: string }) {
  return (
    <Box sx={{ display: "flex", alignItems: "center", gap: 0.5 }}>
      <Typography sx={{ color: "#64748b", fontSize: "0.7rem" }}>{label}</Typography>
      <Typography sx={{ color: color ?? "#e2e8f0", fontSize: "0.75rem", fontWeight: 600 }}>
        {value}
      </Typography>
    </Box>
  );
}
