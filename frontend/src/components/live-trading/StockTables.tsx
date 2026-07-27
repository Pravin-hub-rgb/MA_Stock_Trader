"use client";

import { Box, Typography, Paper, Table, TableBody, TableCell, TableContainer, TableHead, TableRow } from "@mui/material";
import { StockStatus, StateChip } from "./live-trading-utils";

const REVERSAL_ACTIVE_COLS = ["Symbol", "State", "Type", "LTP", "Entry Price", "SL", "Live Vol", "High", "Low", "Prev Close", "Gap%"];
const CONTINUATION_ACTIVE_COLS = ["Symbol", "State", "LTP", "Entry Price", "Exit Price", "Live Vol", "High", "Low", "VAH", "Prev Close", "Gap%", "Base Vol (R)"];
const REVERSAL_REJECTED_COLS = ["Symbol", "Prev Close", "Gap%", "Reason"];
const CONTINUATION_REJECTED_COLS = ["Symbol", "VAH", "Prev Close", "Gap%", "Base Vol (R)", "Reason"];

const hdrSx = {
  color: "#64748b", fontWeight: 700, fontSize: "0.6rem", textTransform: "uppercase",
  letterSpacing: "0.5px", borderBottom: "1px solid rgba(255,255,255,0.08)",
  bgcolor: "#0a0a0a", py: "8px",
};

export default function StockTables({ active, rejected, running, mode }: { active: [string, StockStatus][]; rejected: [string, StockStatus][]; running: boolean; mode: "reversal" | "continuation" }) {
  const isReversal = mode === "reversal";
  const activeCols = isReversal ? REVERSAL_ACTIVE_COLS : CONTINUATION_ACTIVE_COLS;
  const rejectedCols = isReversal ? REVERSAL_REJECTED_COLS : CONTINUATION_REJECTED_COLS;

  return (
    <>
      {active.length > 0 && (
        <Box sx={{ mb: 3 }}>
          <Typography variant="subtitle2" sx={{ color: "#10b981", fontWeight: 700, mb: 1.5, textTransform: "uppercase", letterSpacing: "0.5px", fontSize: "0.75rem" }}>
            Active Stocks ({active.length})
          </Typography>
          <TableContainer component={Paper} sx={{ background: "#111", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 3, overflowX: "auto" }}>
            <Table size="small" stickyHeader sx={{ minWidth: isReversal ? 900 : 1100 }}>
              <TableHead><TableRow>{activeCols.map((h) => <TableCell key={h} sx={hdrSx}>{h}</TableCell>)}</TableRow></TableHead>
              <TableBody>
                {active.map(([key, s]) => (
                  <TableRow key={key} sx={{ "&:hover": { bgcolor: "rgba(255,255,255,0.02)" }, "& td": { borderBottom: "1px solid rgba(255,255,255,0.04)", py: "6px" } }}>
                    <TableCell sx={{ color: "#f1f5f9", fontWeight: 600, fontFamily: "monospace", fontSize: "0.8rem" }}>{s.symbol || key}</TableCell>
                    <TableCell><StateChip state={s.state} /></TableCell>
                    {isReversal && <TableCell sx={{ color: "#a78bfa", fontFamily: "monospace", fontSize: "0.75rem", fontWeight: 600 }}>{s.situation === "reversal_s2" ? "OOPS" : s.situation === "reversal_s1" ? "SS" : "--"}</TableCell>}
                    <TableCell sx={{ color: "#e2e8f0", fontFamily: "monospace", fontSize: "0.8rem" }}>{s.currentPrice?.toFixed(2) ?? "--"}</TableCell>
                    <TableCell sx={{ color: "#34d399", fontFamily: "monospace", fontSize: "0.8rem" }}>{s.entryPrice?.toFixed(2) ?? "--"}</TableCell>
                    <TableCell sx={{ color: "#f59e0b", fontFamily: "monospace", fontSize: "0.8rem" }}>{s.exitPrice?.toFixed(2) ?? s.entrySl?.toFixed(2) ?? "--"}</TableCell>
                    <TableCell sx={{ color: "#60a5fa", fontFamily: "monospace", fontSize: "0.75rem" }}>{s.cumulativeVolume > 0 ? s.cumulativeVolume.toLocaleString() : s.earlyVolume > 0 ? s.earlyVolume.toLocaleString() : "--"}</TableCell>
                    <TableCell sx={{ color: "#10b981", fontFamily: "monospace", fontSize: "0.8rem" }}>{s.dailyHigh != null && isFinite(s.dailyHigh) ? s.dailyHigh.toFixed(2) : "--"}</TableCell>
                    <TableCell sx={{ color: "#ef4444", fontFamily: "monospace", fontSize: "0.8rem" }}>{s.dailyLow != null && isFinite(s.dailyLow) ? s.dailyLow.toFixed(2) : "--"}</TableCell>
                    {!isReversal && <TableCell sx={{ color: "#a78bfa", fontFamily: "monospace", fontSize: "0.8rem" }}>{s.vahPrice?.toFixed(2) ?? "--"}</TableCell>}
                    <TableCell sx={{ color: "#94a3b8", fontFamily: "monospace", fontSize: "0.8rem" }}>{s.previousClose?.toFixed(2) ?? "--"}</TableCell>
                    <TableCell sx={{ fontFamily: "monospace", fontSize: "0.8rem", fontWeight: 600, color: s.gapPct !== null ? (s.gapPct >= 0 ? "#10b981" : "#ef4444") : "#64748b" }}>{s.gapPct !== null ? `${(s.gapPct * 100).toFixed(1)}%` : "--"}</TableCell>
                    {!isReversal && <TableCell sx={{ color: "#f59e0b", fontFamily: "monospace", fontSize: "0.75rem" }}>{s.volumeBaseline > 0 ? s.volumeBaseline.toLocaleString() : "--"}</TableCell>}
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Box>
      )}

      {rejected.length > 0 && (
        <Box sx={{ mb: 3 }}>
          <Typography variant="subtitle2" sx={{ color: "#ef4444", fontWeight: 700, mb: 1.5, textTransform: "uppercase", letterSpacing: "0.5px", fontSize: "0.75rem" }}>
            Rejected Stocks ({rejected.length})
          </Typography>
          <TableContainer component={Paper} sx={{ background: "#111", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 3 }}>
            <Table size="small" stickyHeader>
              <TableHead><TableRow>{rejectedCols.map((h) => <TableCell key={h} sx={hdrSx}>{h}</TableCell>)}</TableRow></TableHead>
              <TableBody>
                  {rejected.map(([key, s]) => (
                    <TableRow key={key} sx={{ "&:hover": { bgcolor: "rgba(255,255,255,0.02)" }, "& td": { borderBottom: "1px solid rgba(255,255,255,0.04)", py: "6px" }, opacity: 0.7 }}>
                      <TableCell sx={{ color: "#f1f5f9", fontWeight: 600, fontFamily: "monospace", fontSize: "0.8rem" }}>{s.symbol || key}</TableCell>
                      {!isReversal && <TableCell sx={{ color: "#a78bfa", fontFamily: "monospace", fontSize: "0.8rem" }}>{s.vahPrice?.toFixed(2) ?? "--"}</TableCell>}
                      <TableCell sx={{ color: "#94a3b8", fontFamily: "monospace", fontSize: "0.8rem" }}>{s.previousClose?.toFixed(2) ?? "--"}</TableCell>
                      <TableCell sx={{ fontFamily: "monospace", fontSize: "0.8rem", fontWeight: 600, color: s.gapPct !== null ? (s.gapPct >= 0 ? "#10b981" : "#ef4444") : "#64748b" }}>{s.gapPct !== null ? `${(s.gapPct * 100).toFixed(1)}%` : "--"}</TableCell>
                      {!isReversal && <TableCell sx={{ color: "#f59e0b", fontFamily: "monospace", fontSize: "0.75rem" }}>{s.volumeBaseline > 0 ? s.volumeBaseline.toLocaleString() : "--"}</TableCell>}
                      <TableCell sx={{ color: "#fca5a5", fontFamily: "monospace", fontSize: "0.75rem", maxWidth: 200, overflow: "hidden", textOverflow: "ellipsis" }}>{s.rejectionReason ?? "--"}</TableCell>
                    </TableRow>
                  ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Box>
      )}

      {active.length === 0 && rejected.length === 0 && (
        <Paper sx={{ p: 4, textAlign: "center", background: "#111", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 3 }}>
          <Typography variant="body2" sx={{ color: "#64748b" }}>
            {running ? "Waiting for stock data..." : "Start the live trader to see stock data"}
          </Typography>
        </Paper>
      )}
    </>
  );
}
