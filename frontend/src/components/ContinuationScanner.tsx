"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import {
  Box, Typography, Card, CardContent, Button,
  Table, TableBody, TableCell, TableContainer, TableHead,
  TableRow, TableSortLabel, IconButton, Tooltip,
} from "@mui/material";
import {
  Download as DownloadIcon,
  ContentCopy as CopyIcon,
  Assessment as ResultsIcon,
  Add as AddIcon,
  Close as CloseIcon,
  ShowChart as ChartIcon,
  TableChart as TableIcon,
} from "@mui/icons-material";
import { useAppState } from "@/lib/AppStateContext";
import ScannerSplitPane from "./scanner/ScannerSplitPane";
import CandleProgress from "./CandleProgress";
import ToastNotification from "./ToastNotification";

const API = "http://127.0.0.1:8001";

const loadFilter = (key: string, def: number) => {
  if (typeof window === "undefined") return def;
  const v = localStorage.getItem(`cont_${key}`);
  return v ? parseInt(v, 10) : def;
};

export default function ContinuationScanner() {
  const [minPrice, setMinPrice] = useState(() => loadFilter("minPrice", 100));
  const [maxPrice, setMaxPrice] = useState(() => loadFilter("maxPrice", 2000));
  const [nearMa, setNearMa] = useState(() => loadFilter("nearMa", 5));
  const [nearMaDirection, setNearMaDirection] = useState(() => { if (typeof window === "undefined") return "above"; return localStorage.getItem("cont_nearMaDirection") || "above"; });
  const [maxBody, setMaxBody] = useState(() => loadFilter("maxBody", 5));
  const [scanDate, setScanDate] = useState(() => {
    if (typeof window === "undefined") return "";
    return localStorage.getItem("cont_scanDate") || "";
  });
  const [risingMaTol, setRisingMaTol] = useState(() => loadFilter("risingMaTol", 0));
  const { state, setContinuationResults, setContScanProgress, setContinuationViewMode } = useAppState();
  const { contScanProgress: { scanning, progress, status, operationId } } = state;
  const [sortKey, setSortKey] = useState<keyof (typeof state.continuationResults)[number]>("depth_pct");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("desc");
  const [savedSymbols, setSavedSymbols] = useState<string[]>([]);
  const [toasts, setToasts] = useState<{ id: string; message: string; type: "success" | "error" | "warning"; position: number }[]>([]);
  const removeToast = useCallback((id: string) => setToasts(prev => prev.filter(t => t.id !== id)), []);
  const showToast = useCallback((message: string, type: "success" | "error" | "warning") => {
    const id = `t-${Date.now()}-${Math.random()}`;
    setToasts(prev => [...prev, { id, message, type, position: prev.length }]);
    setTimeout(() => removeToast(id), 4000);
  }, [removeToast]);
  const viewMode = state.continuationViewMode;
  const chartCacheRef = useRef<Record<string, any>>({});
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => { localStorage.setItem("cont_minPrice", String(minPrice)); }, [minPrice]);
  useEffect(() => { localStorage.setItem("cont_maxPrice", String(maxPrice)); }, [maxPrice]);
  useEffect(() => { localStorage.setItem("cont_nearMa", String(nearMa)); }, [nearMa]);
  useEffect(() => { localStorage.setItem("cont_nearMaDirection", nearMaDirection); }, [nearMaDirection]);
  useEffect(() => { localStorage.setItem("cont_maxBody", String(maxBody)); }, [maxBody]);
  useEffect(() => { localStorage.setItem("cont_scanDate", scanDate); }, [scanDate]);
  useEffect(() => { localStorage.setItem("cont_risingMaTol", String(risingMaTol)); }, [risingMaTol]);

  useEffect(() => {
    fetch(`${API}/api/settings`)
      .then(r => r.json())
      .then(data => {
        const s: Record<string, string> = {};
        for (const item of data.settings || []) {
          if (item.key) s[item.key] = item.value;
        }
        if (localStorage.getItem("cont_minPrice") === null && s.price_min)
          setMinPrice(parseInt(s.price_min, 10));
        if (localStorage.getItem("cont_maxPrice") === null && s.price_max)
          setMaxPrice(parseInt(s.price_max, 10));
        if (localStorage.getItem("cont_nearMa") === null && s.cont_near_ma_threshold_pct)
          setNearMa(Math.round(parseFloat(s.cont_near_ma_threshold_pct)));
        if (localStorage.getItem("cont_nearMaDirection") === null && s.cont_near_ma_direction)
          setNearMaDirection(s.cont_near_ma_direction);
        if (localStorage.getItem("cont_maxBody") === null && s.cont_max_body_pct)
          setMaxBody(Math.round(parseFloat(s.cont_max_body_pct)));
      })
      .catch(() => {});
  }, []);

  useEffect(() => {
    fetch(`${API}/api/stock-list/continuation`)
      .then(r => r.json())
      .then(d => setSavedSymbols((d.stocks || []).map((s: any) => s.symbol)))
      .catch(() => {});
  }, []);

  useEffect(() => {
    if (!scanning || !operationId) return;
    intervalRef.current = setInterval(async () => {
      try {
        const r = await fetch(`${API}/api/scanner/status/${operationId}`);
        const d = await r.json();
        if (d.detail) {
          if (intervalRef.current) clearInterval(intervalRef.current);
          intervalRef.current = null;
          setContScanProgress({ scanning: false, progress: 0, status: "Scan expired (server was restarted)", operationId: null });
          return;
        }
        setContScanProgress({ scanning: true, progress: d.progress || 0, status: d.message || "Processing...", operationId });

        if (d.status === "completed") {
          if (intervalRef.current) clearInterval(intervalRef.current);
          intervalRef.current = null;
          const rows = (d.result?.results || []).map((r: any) => ({
            ...r, close: r.close ?? 0, adr_pct: r.adr_pct ?? 0,
          }));
          setContinuationResults(rows);
          setContScanProgress({ scanning: false, progress: 100, status: `Scan completed! Found ${rows.length} continuation setups`, operationId: null });
          showToast(`Found ${rows.length} continuation setups`, "success");
        } else if (d.status === "error") {
          if (intervalRef.current) clearInterval(intervalRef.current);
          intervalRef.current = null;
          setContScanProgress({ scanning: false, progress: 0, status: `Scan failed: ${d.message}`, operationId: null });
          showToast(`Scan failed: ${d.message}`, "error");
        }
      } catch {
        if (intervalRef.current) clearInterval(intervalRef.current);
        intervalRef.current = null;
        setContScanProgress({ scanning: false, progress: 0, status: "Lost connection to scan process", operationId: null });
        showToast("Lost connection to scan process", "error");
      }
    }, 1000);

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
      intervalRef.current = null;
    };
  }, [scanning, operationId, setContScanProgress, setContinuationResults]);

  const runScan = async () => {
    setContScanProgress({ scanning: true, progress: 0, status: "Starting continuation scan...", operationId: null });
    setContinuationResults([]);

    try {
      const res = await fetch(`${API}/api/scanner/continuation`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          date: scanDate || null,
          filters: {
            min_price: minPrice,
            max_price: maxPrice,
            near_ma_threshold: nearMa,
            near_ma_direction: nearMaDirection,
            max_body_percentage: maxBody,
            rising_ma_tolerance: risingMaTol,
          },
        }),
      });
      const d = await res.json();
      if (d.status !== "started") throw new Error(d.message || "Failed to start");
      setContScanProgress({ scanning: true, progress: 0, status: "Scan started...", operationId: d.operation_id });
    } catch (e: any) {
      setContScanProgress({ scanning: false, progress: 0, status: `Failed to start scan: ${e.message}`, operationId: null });
    }
  };

  const handleSort = (key: string) => {
    const dir = sortKey === key && sortDir === "asc" ? "desc" : "asc";
    setSortKey(key as any);
    setSortDir(dir);
    const sorted = [...state.continuationResults].sort((a, b) => {
      const av = (a as any)[key] ?? 0; const bv = (b as any)[key] ?? 0;
      return dir === "asc" ? (av < bv ? -1 : 1) : (av > bv ? -1 : 1);
    });
    setContinuationResults(sorted);
  };

  const copyClipboard = () => {
    const syms = state.continuationResults.map(r => r.symbol);
    navigator.clipboard.writeText(syms.map(s => `NSE:${s}-EQ`).join(","));
    showToast(`Copied ${syms.length} symbols`, "success");
  };

  const exportCsv = () => {
    if (!state.continuationResults.length) return;
    const h = "Symbol,Close,SMA20,Dist to MA %,Phase1 High,Phase2 Low,Depth %,ADR %";
    const rows = state.continuationResults.map(r =>
      `${r.symbol},${r.close.toFixed(2)},${(r.sma20 || 0).toFixed(2)},${(r.dist_to_ma_pct || 0).toFixed(1)},${(r.phase1_high || 0).toFixed(2)},${(r.phase2_low || 0).toFixed(2)},${(r.depth_pct || 0).toFixed(1)},${r.adr_pct.toFixed(1)}`
    );
    const blob = new Blob([[h, ...rows].join("\n")], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url; a.download = `continuation_${new Date().toISOString().slice(0, 10)}.csv`;
    a.click(); URL.revokeObjectURL(url);
  };

  const toggleContinuation = useCallback(async (row: any) => {
    const symbol = row.symbol;
    const isIn = savedSymbols.includes(symbol);
    try {
      if (isIn) {
        await fetch(`${API}/api/stock-list/continuation/${symbol}`, { method: "DELETE" });
        setSavedSymbols(prev => prev.filter(s => s !== symbol));
        showToast(`Removed ${symbol} from list`, "success");
      } else {
        await fetch(`${API}/api/stock-list/continuation`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ symbol, close: row.close, depth_pct: row.depth_pct }),
        });
        setSavedSymbols(prev => [...prev, symbol]);
        showToast(`Added ${symbol} to list`, "success");
      }
    } catch {
      showToast(`Failed to update ${symbol}`, "error");
    }
  }, [savedSymbols]);

  const cardSx = {
    background: "linear-gradient(135deg, #111111 0%, #1a1a1a 100%)",
    border: "1px solid rgba(255,255,255,0.1)",
    borderRadius: 3,
  };

  return (
    <Box sx={{ minHeight: "100vh" }}>
      {toasts.map((t) => (
        <Box key={t.id} sx={{ position: "fixed", bottom: 24 + t.position * 60, [viewMode === "chart" ? "left" : "right"]: 24, zIndex: 9999 }}>
          <ToastNotification message={t.message} type={t.type} onClose={() => removeToast(t.id)} slideFrom={viewMode === "chart" ? "left" : "right"} />
        </Box>
      ))}
      <Card sx={{ background: "#0d1117", border: "1px solid #1e293b", borderRadius: 2 }}>
        <CardContent sx={{ px: 3, py: 2 }}>
            <Box sx={{ display: "flex", alignItems: "center", flexWrap: "wrap", gap: "8px 16px" }}>
            <Typography sx={{ fontWeight: 700, color: "#f1f5f9", fontSize: "0.85rem" }}>
              Filters
            </Typography>
            <Box sx={{ height: 20, width: 1, bgcolor: "#1e293b" }} />
            {[
              { label: "Min Price", val: minPrice, set: setMinPrice, min: 10, max: 5000 },
              { label: "Max Price", val: maxPrice, set: setMaxPrice, min: 100, max: 10000 },
              { label: "Near MA %", val: nearMa, set: setNearMa, min: 1, max: 20 },
              { label: "Max Body %", val: maxBody, set: setMaxBody, min: 1, max: 10 },
              { label: "Rising MA Tol %", val: risingMaTol, set: setRisingMaTol, min: 0, max: 5 },
            ].map(f => (
              <Box key={f.label} sx={{ display: "flex", alignItems: "center", gap: 0.75 }}>
                <Typography sx={{ color: "#94a3b8", fontSize: "0.8rem", whiteSpace: "nowrap" }}>
                  {f.label}
                </Typography>
                <Box
                  component="input"
                  type="number"
                  value={f.val}
                  onChange={e => f.set(Number(e.target.value))}
                  min={f.min}
                  max={f.max}
                  sx={{
                    width: 90, px: 2, py: 0.7, borderRadius: 1.5,
                    bgcolor: "#1e293b", color: "#f8fafc",
                    border: "1px solid #334155", outline: "none",
                    fontSize: "0.85rem", fontFamily: '"SF Mono", "Fira Code", monospace',
                    textAlign: "left", transition: "border-color 0.15s",
                    "&:focus": { borderColor: "#6366f1" },
                  }}
                />
              </Box>
            ))}
            <Box sx={{ display: "flex", alignItems: "center", gap: 0.75 }}>
              <Typography sx={{ color: "#94a3b8", fontSize: "0.8rem", whiteSpace: "nowrap" }}>Direction</Typography>
              <Box
                component="select"
                value={nearMaDirection}
                onChange={e => setNearMaDirection(e.target.value)}
                sx={{
                  width: 100, px: 2, py: 0.7, borderRadius: 1.5,
                  bgcolor: "#1e293b", color: "#f8fafc",
                  border: "1px solid #334155", outline: "none",
                  fontSize: "0.85rem", fontFamily: '"SF Mono", "Fira Code", monospace',
                  cursor: "pointer", transition: "border-color 0.15s",
                  "&:focus": { borderColor: "#6366f1" },
                }}
              >
                <option value="above">Above</option>
                <option value="below">Below</option>
                <option value="both">Both</option>
              </Box>
            </Box>
            <Box sx={{ display: "flex", alignItems: "center", gap: 0.75 }}>
              <Typography sx={{ color: "#94a3b8", fontSize: "0.8rem", whiteSpace: "nowrap" }}>Scan Date</Typography>
              <Box
                component="input"
                type="date"
                value={scanDate}
                onChange={e => setScanDate(e.target.value)}
                sx={{
                  width: 150, px: 1.5, py: 0.7, borderRadius: 1.5,
                  bgcolor: "#1e293b", color: "#f8fafc",
                  border: "1px solid #334155", outline: "none",
                  fontSize: "0.85rem", fontFamily: '"SF Mono", "Fira Code", monospace',
                  transition: "border-color 0.15s",
                  "&:focus": { borderColor: "#6366f1" },
                  "&::-webkit-calendar-picker-indicator": { filter: "invert(0.7)" },
                }}
              />
              {scanDate && (
                <Box
                  component="span"
                  onClick={() => setScanDate("")}
                  sx={{ cursor: "pointer", color: "#64748b", fontSize: "0.8rem", "&:hover": { color: "#f1f5f9" } }}
                >
                  ✕
                </Box>
              )}
            </Box>
            <Box sx={{ flex: 1, minWidth: 40 }} />
            <Button
              variant="contained" disableElevation
              disabled={scanning}
              onClick={runScan}
              sx={{
                px: 3, py: 0.8, fontSize: "0.85rem", fontWeight: 600,
                bgcolor: "#6366f1", color: "#fff",
                borderRadius: 1.5, textTransform: "none", minWidth: 120,
                "&:hover": { bgcolor: "#4f46e5" },
                "&:disabled": { bgcolor: "#1e293b", color: "#475569" },
              }}
            >
              {scanning ? "Scanning..." : "Run Scan"}
            </Button>
          </Box>
        </CardContent>
      </Card>

      {scanning && (
        <Box sx={{ mt: 1.5, px: 0.5 }}>
          <CandleProgress progress={progress} />
          <Typography sx={{ color: "#cbd5e1", fontSize: "0.8rem", mt: 1 }}>
            {status}
          </Typography>
        </Box>
      )}

      {state.continuationResults.length > 0 && (
        <Card sx={{ ...cardSx, border: "1px solid rgba(255,255,255,0.06)", borderLeft: "3px solid #10b981" }}>
          <CardContent sx={{ p: 0 }}>
            <Box sx={{
              px: 2.5, py: 1.5,
              display: "flex", justifyContent: "space-between", alignItems: "center",
            }}>
              <Box sx={{ display: "flex", alignItems: "center", gap: 1.5 }}>
                <ResultsIcon sx={{ color: "#10b981", fontSize: 20 }} />
                <Typography sx={{ fontWeight: 600, color: "#f8fafc", fontSize: "0.95rem" }}>
                  Scan Results ({state.continuationResults.length} stocks)
                </Typography>
              </Box>
              <Box sx={{ display: "flex", gap: 0.5, alignItems: "center" }}>
                <Box sx={{
                  display: "flex", bgcolor: "#1e293b", borderRadius: 1.5, p: 0.3, mr: 1,
                }}>
                  <Tooltip title="Table View">
                    <IconButton
                      size="small"
                      onClick={() => setContinuationViewMode("table")}
                      sx={{
                        color: viewMode === "table" ? "#6366f1" : "#475569",
                        bgcolor: viewMode === "table" ? "rgba(99,102,241,0.15)" : "transparent",
                        borderRadius: 1,
                        p: 0.5,
                        "&:hover": { bgcolor: "rgba(99,102,241,0.1)" },
                      }}
                    >
                      <TableIcon sx={{ fontSize: 18 }} />
                    </IconButton>
                  </Tooltip>
                  <Tooltip title="Chart View">
                    <IconButton
                      size="small"
                      onClick={() => setContinuationViewMode("chart")}
                      sx={{
                        color: viewMode === "chart" ? "#10b981" : "#475569",
                        bgcolor: viewMode === "chart" ? "rgba(16,185,129,0.15)" : "transparent",
                        borderRadius: 1,
                        p: 0.5,
                        "&:hover": { bgcolor: "rgba(16,185,129,0.1)" },
                      }}
                    >
                      <ChartIcon sx={{ fontSize: 18 }} />
                    </IconButton>
                  </Tooltip>
                </Box>
                <Tooltip title="Copy to Clipboard (Fyers format)">
                  <IconButton onClick={copyClipboard} sx={{ color: "#475569", "&:hover": { color: "#06b6d4" } }}><CopyIcon sx={{ fontSize: 18 }} /></IconButton>
                </Tooltip>
                <Tooltip title="Export to CSV">
                  <IconButton onClick={exportCsv} sx={{ color: "#475569", "&:hover": { color: "#10b981" } }}><DownloadIcon sx={{ fontSize: 18 }} /></IconButton>
                </Tooltip>
              </Box>
            </Box>
            <Box sx={{ height: 2, bgcolor: "rgba(16,185,129,0.08)" }} />

            {viewMode === "table" ? (
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow sx={{ backgroundColor: "rgba(255,255,255,0.02)" }}>
                      <TableCell sx={{ color: "#94a3b8", fontWeight: 600, width: 80, borderBottom: "1px solid rgba(255,255,255,0.1)" }}>
                        Actions
                      </TableCell>
                      {[
                        { k: "symbol", l: "Symbol" },
                        { k: "close", l: "Close" },
                        { k: "dist_to_ma_pct", l: "Dist to MA %" },
                        { k: "phase1_high", l: "Phase1 High" },
                        { k: "phase2_low", l: "Phase2 Low" },
                        { k: "depth_pct", l: "Depth %" },
                        { k: "adr_pct", l: "ADR %" },
                      ].map(col => (
                        <TableCell key={col.k} sx={{ color: "#94a3b8", fontWeight: 600, borderBottom: "1px solid rgba(255,255,255,0.1)" }}>
                          <TableSortLabel
                            active={sortKey === col.k}
                            direction={sortKey === col.k ? sortDir : "asc"}
                            onClick={() => handleSort(col.k)}
                            sx={{
                              color: "#94a3b8 !important",
                              "&:hover": { color: "#f8fafc !important" },
                              "&.MuiTableSortLabel-active": { color: "#6366f1 !important" },
                            }}
                          >
                            {col.l}
                          </TableSortLabel>
                        </TableCell>
                      ))}
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {state.continuationResults.map((row: any) => {
                      const inList = savedSymbols.includes(row.symbol);
                      return (
                        <TableRow key={row.symbol} hover
                          sx={{ "&:hover": { backgroundColor: "rgba(255,255,255,0.02)" } }}
                        >
                          <TableCell>
                            <Tooltip title={inList ? "Remove from continuation list" : "Add to continuation list"} placement="right">
                              <IconButton size="small" onClick={() => toggleContinuation(row)}
                                sx={{ color: inList ? "#ef4444" : "#10b981" }}>
                                {inList ? <CloseIcon fontSize="small" /> : <AddIcon fontSize="small" />}
                              </IconButton>
                            </Tooltip>
                          </TableCell>
                          <TableCell sx={{ color: "#f8fafc", fontWeight: 600 }}>{row.symbol}</TableCell>
                          <TableCell sx={{ color: "#f8fafc" }}>₹{row.close.toFixed(2)}</TableCell>
                          <TableCell sx={{ color: (row.dist_to_ma_pct ?? 0) <= 5 ? "#10b981" : "#f8fafc" }}>
                            {(row.dist_to_ma_pct ?? 0).toFixed(1)}%
                          </TableCell>
                          <TableCell sx={{ color: "#f8fafc" }}>₹{(row.phase1_high ?? 0).toFixed(2)}</TableCell>
                          <TableCell sx={{ color: "#f8fafc" }}>₹{(row.phase2_low ?? 0).toFixed(2)}</TableCell>
                          <TableCell sx={{ color: "#f8fafc" }}>{(row.depth_pct ?? 0).toFixed(1)}%</TableCell>
                          <TableCell sx={{ color: (row.adr_pct ?? 0) >= 3 ? "#10b981" : "#f8fafc" }}>
                            {row.adr_pct.toFixed(1)}%
                          </TableCell>
                        </TableRow>
                      );
                    })}
                  </TableBody>
                </Table>
              </TableContainer>
            ) : (
              <Box sx={{ p: 2 }}>
                <ScannerSplitPane
                  stocks={state.continuationResults}
                  mode="continuation"
                  savedSymbols={savedSymbols}
                  onToggle={toggleContinuation}
                  chartCacheRef={chartCacheRef}
                />
              </Box>
            )}
          </CardContent>
        </Card>
      )}
    </Box>
  );
}