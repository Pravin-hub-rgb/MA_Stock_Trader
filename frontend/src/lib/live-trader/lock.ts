import * as fs from "fs";
import * as path from "path";

export type BotType = "reversal" | "continuation";

function lockFileFor(type: BotType): string {
  // data/ is at project root (MA_Stock_Trader_NA/data/)
  // Next.js runs from frontend/, so we go up one level
  const local = path.join(process.cwd(), "data");
  const parent = path.resolve(process.cwd(), "..", "data");
  const dir = fs.existsSync(local) ? local : parent;
  return path.join(dir, `${type}_bot.lock`);
}

export class LockManager {
  private lockAcquired = false;
  private botType: BotType | null = null;
  private lockFile = "";

  setBotType(type: BotType): void {
    this.botType = type;
    this.lockFile = lockFileFor(type);
  }

  acquire(): boolean {
    if (!this.botType) throw new Error("LockManager: bot type not set");
    if (this.lockAcquired) return true;

    try {
      this.ensureDataDir();
      this.cleanupStaleLock();

      const fd = fs.openSync(this.lockFile, "wx");
      const content = `${process.pid}\n${Date.now()}\n`;
      fs.writeSync(fd, content, 0, "utf-8");
      fs.closeSync(fd);

      this.lockAcquired = true;
      const label = this.botType === "reversal" ? "Reversal" : "Continuation";
      console.log(`[LOCK] ${label} bot singleton lock acquired`);
      (globalThis as any).__addLiveLog?.(`[LOCK] ${label} bot singleton lock acquired`);
      return true;
    } catch (err: any) {
      const label = this.botType === "reversal" ? "reversal" : "continuation";
      if (err.code === "EEXIST") {
        console.log(`ERROR: Another ${label} bot instance is already running - refusing to connect`);
        console.log(`[LOCK] Lock file exists: ${this.lockFile}`);
        (globalThis as any).__addLiveLog?.(`[LOCK] ERROR: Another ${label} bot instance is already running`);
      } else {
        console.log(`WARNING: Could not acquire ${label} bot lock: ${err.message}`);
      }
      return false;
    }
  }

  release(): void {
    if (!this.lockAcquired) return;

    try {
      this.lockAcquired = false;
      if (fs.existsSync(this.lockFile)) {
        fs.unlinkSync(this.lockFile);
        const label = this.botType === "reversal" ? "Reversal" : "Continuation";
        console.log(`[UNLOCK] ${label} bot singleton lock released`);
        (globalThis as any).__addLiveLog?.(`[UNLOCK] ${label} bot singleton lock released`);
      }
    } catch (err: any) {
      console.log(`WARNING: Could not cleanup lock: ${err.message}`);
    }
  }

  private ensureDataDir(): void {
    const dir = path.dirname(this.lockFile);
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }
  }

  private cleanupStaleLock(): void {
    if (!fs.existsSync(this.lockFile)) return;

    try {
      const content = fs.readFileSync(this.lockFile, "utf-8").trim();
      const lines = content.split("\n");
      const pid = parseInt(lines[0], 10);
      const timestamp = parseInt(lines[1], 10);

      if (pid && !this.isProcessAlive(pid)) {
        const label = this.botType === "reversal" ? "Reversal" : "Continuation";
        console.log(`[LOCK] Found stale ${label} lock from dead process ${pid}, removing`);
        fs.unlinkSync(this.lockFile);
        return;
      }

      // Backup: on Windows, PIDs can be recycled quickly. If the lock file
      // is older than 1 hour, treat it as stale even if the PID is alive.
      if (timestamp && Date.now() - timestamp > 3600000) {
        const label = this.botType === "reversal" ? "Reversal" : "Continuation";
        console.log(`[LOCK] Found stale ${label} lock (older than 1h, PID ${pid} may be recycled), removing`);
        fs.unlinkSync(this.lockFile);
      }
    } catch {
      try { fs.unlinkSync(this.lockFile); } catch {}
    }
  }

  private isProcessAlive(pid: number): boolean {
    try {
      process.kill(pid, 0);
      return true;
    } catch {
      return false;
    }
  }
}

export function createLockManager(type: BotType): LockManager {
  const lm = new LockManager();
  lm.setBotType(type);
  return lm;
}
