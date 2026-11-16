const assert = require("assert");
const fs = require("fs");
const path = require("path");
const vm = require("vm");

const appPath = path.join(__dirname, "..", "static", "app.js");
const source = fs.readFileSync(appPath, "utf8");
const end = source.indexOf("function indicatorPref");

if (end === -1) {
  throw new Error("Could not isolate signal log policy code from app.js");
}

const storage = new Map();
const sandbox = {
  assert,
  console,
  document: { getElementById: () => null },
  localStorage: {
    getItem: (key) => storage.get(key) || null,
    setItem: (key, value) => storage.set(key, String(value)),
    removeItem: (key) => storage.delete(key),
  },
};

const testScript = `
${source.slice(0, end)}

let renderCount = 0;
const notifications = [];
const toasts = [];

renderLog = () => {
  renderCount += 1;
};

function notify(title, body) {
  notifications.push({ title, body });
}

function toast(message) {
  toasts.push(message);
}

const basePayload = {
  generated_at: "2026-09-14T00:00:00Z",
  market: {
    vix: { latest_time: "2026-09-10" },
    signals: [
      {
        type: "VIX_SPIKE",
        level: "위험",
        category: "MARKET",
        intent: "risk",
        message: "VIX 급등",
        delivery: "push",
      },
    ],
  },
  results: [
    {
      symbol: "PLTR",
      position: { average_entry: 124.94 },
      last_bar: "2026-09-11T04:00:00Z",
      signals: [
        {
          type: "PROFIT_30",
          level: "수익관리",
          category: "POSITION",
          intent: "profit",
          message: "보유 수익관리",
          delivery: "push",
        },
      ],
    },
    {
      symbol: "AAPL",
      last_bar: "2026-09-11T04:00:00Z",
      signals: [
        {
          type: "ICHIMOKU_CLOUD_RECOVERY",
          level: "반등후보",
          category: "CHART",
          intent: "opportunity",
          message: "관심 반등체크",
          delivery: "summary",
        },
        {
          type: "RSI_STATE",
          level: "대기",
          category: "RSI",
          intent: "review",
          message: "꺼진 신호",
          delivery: "off",
        },
      ],
    },
  ],
};

processSignals(basePayload);

assert.strictEqual(state.signalLog.length, 3, "first analysis logs active signals only");
assert.strictEqual(notifications.length, 0, "first analysis should not push notifications");
assert.strictEqual(state.signalLog[0].scope, "position", "held signals should be prioritized first");
assert.strictEqual(state.signalLog[1].scope, "market", "market signals should come before watch signals");
assert.strictEqual(state.signalLog[2].scope, "watch", "watch signals should be after held and market");
assert.strictEqual(state.signalLog[0].tradeDate, "2026-09-11", "stock trading date should use last bar date");
assert.strictEqual(state.signalLog[1].tradeDate, "2026-09-10", "market trading date should use VIX date");
assert.ok(state.signalLog[0].id.startsWith("position:PLTR:PROFIT_30:2026-09-11"));
assert.ok(state.signalLog[2].id.startsWith("watch:AAPL:ICHIMOKU_CLOUD_RECOVERY:2026-09-11"));

processSignals(basePayload);

assert.strictEqual(state.signalLog.length, 3, "same signal should not duplicate on refresh");
assert.strictEqual(notifications.length, 0, "duplicates should not push");

processSignals({
  generated_at: "2026-09-14T00:10:00Z",
  market: { signals: [] },
  results: [
    {
      symbol: "AAPL",
      last_bar: "2026-09-12T04:00:00Z",
      signals: [
        {
          type: "RSI_RECOVERY",
          level: "기회후보",
          category: "RSI",
          intent: "opportunity",
          message: "새 반등 확인",
          delivery: "push",
        },
      ],
    },
  ],
});

assert.strictEqual(state.signalLog.length, 4, "new trading-day signal should be logged");
assert.strictEqual(notifications.length, 1, "new push signal after warm-up should notify");
assert.strictEqual(toasts.length, 1, "new push batch should show one toast");

state.signalLog = [];
state.seenSignals = new Set();
localStorage.removeItem("signalLog");
localStorage.removeItem("seenSignals");

state.seenSignals = new Set(["AAPL:RSI_RECOVERY:" + localDateKey(new Date())]);
processSignals({
  generated_at: "2026-09-14T00:20:00Z",
  market: { signals: [] },
  results: [
    {
      symbol: "AAPL",
      last_bar: "2026-09-12T04:00:00Z",
      signals: [
        {
          type: "RSI_RECOVERY",
          level: "기회후보",
          category: "RSI",
          intent: "opportunity",
          message: "기존 키 이관",
          delivery: "push",
        },
      ],
    },
  ],
});

assert.strictEqual(state.signalLog.length, 0, "legacy seen keys should prevent duplicate migration");
assert.ok(state.seenSignals.has("watch:AAPL:RSI_RECOVERY:2026-09-12"), "legacy duplicate should add the new scoped key");

console.log("signal log policy tests passed");
`;

vm.runInNewContext(testScript, sandbox);
