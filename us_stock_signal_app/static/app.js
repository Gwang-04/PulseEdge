const CLIENT_ID_STORAGE_KEY = "pulseedgeClientId";
const GUEST_ACCESS_STORAGE_KEY = "pulseedgeGuestAccess";
const NOTIFICATIONS_ENABLED_STORAGE_KEY = "pulseedgeNotificationsEnabled";

const state = {
  clientId: ensureClientId(),
  profile: null,
  config: null,
  signalGroups: {},
  latestPayload: null,
  refreshTimer: null,
  initialAnalysisComplete: false,
  chartPrefs: JSON.parse(localStorage.getItem("chartPrefs") || "{}"),
  indicatorPrefs: JSON.parse(localStorage.getItem("indicatorPrefs") || "{}"),
  chartDrawings: JSON.parse(localStorage.getItem("chartDrawings") || "{}"),
  chartDrag: {},
  drawingModes: {},
  drawingDrafts: {},
  seenSignals: new Set(JSON.parse(localStorage.getItem("seenSignals") || "[]")),
  signalLog: JSON.parse(localStorage.getItem("signalLog") || "[]"),
  credentials: null,
  detailSymbol: null,
  detailChartMode: localStorage.getItem("detailChartMode") || "tradingview",
  watchFilter: localStorage.getItem("watchFilter") || "all",
  watchSort: localStorage.getItem("watchSort") || "score_desc",
  signalLogFilter: localStorage.getItem("signalLogFilter") || "all",
  signalLogRange: localStorage.getItem("signalLogRange") || "today",
  installInfo: null,
  deferredInstallPrompt: null,
  detailView: null,
  backtestPayload: null,
  dataHealth: null,
  authConfig: null,
  authClient: null,
  authSession: null,
  authError: "",
  accountDeletionInProgress: false,
};

const SUPABASE_JS_MODULE = "https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2.57.4/+esm";
const TRADINGVIEW_WIDGET_URL = "https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js";
const TRADINGVIEW_EXCHANGE_BY_SYMBOL = {
  AAPL: "NASDAQ",
  AMD: "NASDAQ",
  AMZN: "NASDAQ",
  ARM: "NASDAQ",
  AVGO: "NASDAQ",
  COST: "NASDAQ",
  GOOGL: "NASDAQ",
  GOOG: "NASDAQ",
  INTC: "NASDAQ",
  META: "NASDAQ",
  MSFT: "NASDAQ",
  MU: "NASDAQ",
  NFLX: "NASDAQ",
  NVDA: "NASDAQ",
  PLTR: "NASDAQ",
  QQQ: "NASDAQ",
  TEM: "NASDAQ",
  TSLA: "NASDAQ",
  ARKK: "AMEX",
  DIA: "AMEX",
  IWM: "AMEX",
  SPY: "AMEX",
  VOO: "AMEX",
  VTI: "AMEX",
  XLE: "AMEX",
  XLF: "AMEX",
  XLK: "AMEX",
  BAC: "NYSE",
  BRK_B: "NYSE",
  CVX: "NYSE",
  DIS: "NYSE",
  IBM: "NYSE",
  JPM: "NYSE",
  KO: "NYSE",
  NKE: "NYSE",
  ORCL: "NYSE",
  WMT: "NYSE",
  XOM: "NYSE",
};

const RISK_CONSENT_VERSION = "2026-09-16-risk-v2";
const RISK_CONSENT_STORAGE_KEY = "pulseedgeRiskConsent";

const SIGNAL_LABELS = {
  RSI_OVERSOLD: "RSI 30 이하",
  RSI_DEEP_OVERSOLD: "RSI 25 이하",
  RSI_RECOVERY: "RSI 회복",
  RSI_OVERHEATED: "RSI 과열",
  RSI_OVERHEAT_COOLING: "RSI 과열 식음",
  RSI_STATE: "RSI 상태",
  VOLUME_SPIKE: "거래량 2배",
  VOLUME_SPIKE_LARGE_CAP: "대형주 거래량",
  BULLISH_VOLUME_SPIKE: "상승 거래량",
  BEARISH_VOLUME_SPIKE: "하락 거래량",
  VOLUME_STATE: "거래량 상태",
  MA20_BREAKDOWN: "20일선 이탈",
  MA60_BREAKDOWN: "60일선 이탈",
  MA120_BREAKDOWN: "120일선 이탈",
  MA20_RECOVERY: "20일선 회복",
  MA60_RECOVERY: "60일선 회복",
  MA120_RECOVERY: "120일선 회복",
  MA20_OVERSOLD_DISTANCE: "20일선 이격 과매도",
  MA60_OVERSOLD_DISTANCE: "60일선 이격 과매도",
  MA120_OVERSOLD_DISTANCE: "120일선 이격 과매도",
  MA20_OVEREXTENDED: "20일선 과열 이격",
  MA60_OVEREXTENDED: "60일선 과열 이격",
  GOLDEN_CROSS_20_60: "20/60 골든크로스",
  DEAD_CROSS_20_60: "20/60 데드크로스",
  MA_TREND_STATE: "이평 추세",
  MA_DISTANCE_STATE: "이평 이격",
  HIGH_60_BREAKOUT: "60일 신고가",
  LOW_60_BREAKDOWN: "60일 신저가",
  HIGH_120_BREAKOUT: "120일 신고가",
  LOW_120_BREAKDOWN: "120일 신저가",
  VOLUME_CONFIRMED_BREAKOUT: "거래량 돌파",
  GAP_UP: "갭상승",
  GAP_DOWN: "갭하락",
  GAP_DOWN_VOLUME_SPIKE: "갭하락 거래량",
  BOLLINGER_LOWER_TOUCH: "볼린저 하단",
  BOLLINGER_LOWER_RECOVERY: "볼린저 회복",
  BOLLINGER_STATE: "볼린저 위치",
  ICHIMOKU_CLOUD_RECOVERY: "일목 구름 회복",
  ICHIMOKU_CLOUD_BREAKDOWN: "일목 구름 이탈",
  ICHIMOKU_STATE: "일목 위치",
  SUPPORT_RESISTANCE_STATE: "자동 S/R",
  LOSS_WARNING: "손실 주의",
  STOP_REVIEW: "방어 검토",
  RISK_EXIT_REVIEW: "위험 축소 검토",
  STOP_BUFFER_WARNING: "위험선 주의",
  STOP_BUFFER_REVIEW: "위험선 근접",
  POSITION_SUPPORT_BUFFER_WARNING: "S1 지지선 근접",
  POSITION_SUPPORT_BREAKDOWN: "S1 지지선 이탈",
  POSITION_SUPPORT_VOLUME_BREAKDOWN: "지지선 이탈+거래량",
  POSITION_MA60_CONFIRM_BREAKDOWN: "60일선 2일 이탈",
  POSITION_STRUCTURE_EXIT_REVIEW: "구조 방어 검토",
  POSITION_STOP_STATE: "방어 기준",
  POSITION_TRAILING_STATE: "트레일링 기준",
  POSITION_MA20_BREAKDOWN: "보유 20일선 이탈",
  POSITION_MA60_BREAKDOWN: "보유 60일선 이탈",
  POSITION_MA120_BREAKDOWN: "보유 120일선 이탈",
  PROFIT_10: "수익 +10%",
  PROFIT_20: "수익 +20%",
  PROFIT_30: "수익 +30%",
  TRAILING_STOP_WARNING: "고점 대비 주의",
  TRAILING_STOP_REVIEW: "트레일링 검토",
  TRAILING_BUFFER_WARNING: "트레일링 근접",
  RSI_OVERHEAT_COOLING_HELD: "보유 RSI 꺾임",
  POSITION_RETURN_STATE: "평단 손익",
  EARNINGS_7D: "실적 7일 전",
  EARNINGS_1D: "실적 1일 전",
  EARNINGS_TODAY: "실적 당일",
  EARNINGS_AFTER: "실적 다음날",
  SPY_BELOW_MA120: "SPY 120일선 아래",
  QQQ_BELOW_MA120: "QQQ 120일선 아래",
  MARKET_RISK_ON: "시장 리스크온",
  MARKET_RISK_OFF: "시장 리스크오프",
  MARKET_FILTER_DOWNGRADE: "시장 필터",
  VIX_ELEVATED: "VIX 주의",
  VIX_FEAR: "VIX 공포",
  VIX_PANIC: "VIX 극단공포",
  VIX_SPIKE: "VIX 급등",
  VIX_CALMING: "VIX 진정",
  VIX_POSITION_RISK: "보유 VIX 위험",
};

const GROUP_LABELS = {
  RSI: "RSI",
  VOLUME: "거래량",
  MOVING_AVERAGE: "이평선",
  BREAKOUT: "돌파/이탈",
  GAP: "갭",
  CHART: "차트패턴",
  POSITION: "보유종목",
  EARNINGS: "실적",
  MARKET: "시장상태",
};

const DELIVERY_LABELS = {
  push: "즉시",
  summary: "요약",
  log: "기록",
  off: "끔",
};

const WATCH_FILTERS = {
  all: "전체",
  buy: "진입검토",
  rebound: "반등체크",
  interest: "관심",
  caution: "주의",
  hide_waiting: "대기숨김",
};

const SIGNAL_LOG_FILTERS = {
  all: "전체",
  push: "즉시",
  opportunity: "진입",
  position: "보유",
  market: "시장",
  risk: "위험",
};

const SIGNAL_LOG_RANGES = {
  today: "오늘",
  week: "7일",
  all: "전체",
};

const ALERT_DIGEST_GROUPS = [
  { scope: "position", label: "보유" },
  { scope: "market", label: "시장" },
  { scope: "watch", label: "관심" },
];

const SIGNAL_LOG_LIMIT = 160;
const SIGNAL_MEMORY_LIMIT = 600;

const SIGNAL_SCOPE_LABELS = {
  watch: "관심",
  position: "보유",
  market: "시장",
};

const SIGNAL_DELIVERY_PRIORITY = {
  push: 0,
  summary: 1,
  log: 2,
};

const SIGNAL_INTENT_PRIORITY = {
  risk: 0,
  profit: 1,
  opportunity: 2,
  review: 3,
};

const SIGNAL_LEVEL_PRIORITY = {
  위험: 0,
  방어검토: 1,
  수익보호검토: 2,
  수익관리: 3,
  주의: 4,
  돌파후보: 5,
  기회후보: 5,
  반등후보: 6,
  공포관심: 7,
  관심: 8,
  정상: 9,
  대기: 10,
};

const LEVEL_ALIASES = {
  매수검토: "진입검토",
  판매검토: "방어검토",
  익절검토: "수익보호검토",
  손절검토: "방어검토",
  손절근접: "위험선근접",
  구조손절검토: "구조방어검토",
  위험탈출검토: "위험축소검토",
  비중축소검토: "비중점검",
};

const BACKTEST_RULE_COPY = {
  hold90: "90일 보유형: 다음날 시가 진입 · 중간 청산 없이 90거래일 보유",
  growth: "수익형: 다음날 시가 진입 · -8% 방어 기준 · +15%/+25% 분할 수익실현 · -10% 트레일링 · 최대 90거래일",
  growth_structure: "수익형+구조방어: 수익형 룰에 S1 이탈 + 손실 -6% 확인, 60일선 2일 이탈 + 손실 -6% 확인 청산을 추가",
  balanced: "균형형: 다음날 시가 진입 · -7% 방어 기준 · +12%/+20% 분할 수익실현 · -8% 트레일링 · 최대 60거래일",
};

const $ = (id) => document.getElementById(id);

async function apiGet(path) {
  const response = await fetch(path, { headers: apiHeaders() });
  const payload = await response.json();
  if (!response.ok || payload.error) {
    throw new Error(payload.error || `HTTP ${response.status}`);
  }
  return payload;
}

async function apiPost(path, body) {
  const response = await fetch(path, {
    method: "POST",
    headers: apiHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify(body),
  });
  const payload = await response.json();
  if (!response.ok || payload.error) {
    throw new Error(payload.error || `HTTP ${response.status}`);
  }
  return payload;
}

async function apiDelete(path) {
  const response = await fetch(path, { method: "DELETE", headers: apiHeaders() });
  const payload = await response.json();
  if (!response.ok || payload.error) {
    throw new Error(payload.error || `HTTP ${response.status}`);
  }
  return payload;
}

function apiHeaders(extra = {}) {
  const headers = {
    "X-PulseEdge-Client-Id": state.clientId,
    ...extra,
  };
  const accessToken = state.authSession?.access_token;
  if (accessToken) {
    headers.Authorization = `Bearer ${accessToken}`;
  }
  return headers;
}

function ensureClientId() {
  const existing = localStorage.getItem(CLIENT_ID_STORAGE_KEY);
  if (/^guest-[A-Za-z0-9_-]{8,57}$/.test(existing || "")) {
    return existing;
  }
  const clientId = `guest-${randomClientSuffix()}`;
  localStorage.setItem(CLIENT_ID_STORAGE_KEY, clientId);
  return clientId;
}

function randomClientSuffix() {
  const cryptoApi = typeof window !== "undefined" ? window.crypto : globalThis.crypto;
  if (cryptoApi?.getRandomValues) {
    const bytes = new Uint8Array(12);
    cryptoApi.getRandomValues(bytes);
    return Array.from(bytes, (byte) => byte.toString(36).padStart(2, "0")).join("").slice(0, 24);
  }
  return `${Date.now().toString(36)}${Math.random().toString(36).slice(2, 14)}`.slice(0, 24);
}

async function initAuth() {
  try {
    const payload = await apiGet("/api/auth/config");
    state.authConfig = payload.auth || { enabled: false };
  } catch (error) {
    state.authConfig = { enabled: false, status: "unavailable" };
    state.authError = error.message;
    renderAccountPanel();
    return;
  }

  if (!state.authConfig.enabled) {
    renderAccountPanel();
    return;
  }

  try {
    const { createClient } = await import(SUPABASE_JS_MODULE);
    state.authClient = createClient(
      state.authConfig.project_url,
      state.authConfig.publishable_key,
      {
        auth: {
          autoRefreshToken: true,
          persistSession: true,
          detectSessionInUrl: true,
          flowType: "pkce",
        },
      }
    );
    const { data, error } = await state.authClient.auth.getSession();
    if (error) throw error;
    if (data.session) {
      await syncAuthenticatedSession(data.session);
    }
    state.authClient.auth.onAuthStateChange((event, session) => {
      if (event === "INITIAL_SESSION") return;
      window.setTimeout(() => handleAuthStateChange(event, session), 0);
    });
  } catch (error) {
    state.authError = error.message || "로그인 모듈을 불러오지 못했습니다.";
  }
  renderAccountPanel();
}

async function handleAuthStateChange(event, session) {
  try {
    if (session) {
      await syncAuthenticatedSession(session);
      await loadConfig();
      await analyze();
      if (event === "SIGNED_IN") toast("계정 동기화 완료");
      return;
    }
    state.authSession = null;
    state.profile = null;
    localStorage.removeItem(GUEST_ACCESS_STORAGE_KEY);
    renderAccountPanel();
    if (state.accountDeletionInProgress) return;
    if (event === "SIGNED_OUT") {
      await loadConfig();
      await analyze();
      toast("게스트 모드로 전환됨");
    }
  } catch (error) {
    state.authError = error.message;
    renderAccountPanel();
    toast(error.message);
  }
}

async function syncAuthenticatedSession(session) {
  state.authSession = session;
  const payload = await apiPost("/api/auth/session", {});
  state.profile = payload.profile || null;
  state.authError = "";
  localStorage.removeItem(GUEST_ACCESS_STORAGE_KEY);
  renderAccountPanel();
}

async function signInWithGoogle(buttonId = "googleLoginButton") {
  if (!state.authClient || !state.authConfig?.google_enabled) return;
  const button = $(buttonId);
  button.disabled = true;
  try {
    const { error } = await state.authClient.auth.signInWithOAuth({
      provider: "google",
      options: { redirectTo: authRedirectUrl() },
    });
    if (error) throw error;
  } catch (error) {
    button.disabled = false;
    toast(error.message || "Google 로그인을 시작하지 못했습니다.");
  }
}

async function sendEmailLoginLink(
  inputId = "accountEmail",
  buttonId = "emailLoginButton",
  messageId = ""
) {
  if (!state.authClient || !state.authConfig?.email_enabled) return;
  const input = $(inputId);
  const button = $(buttonId);
  const message = messageId ? $(messageId) : null;
  const email = input.value.trim();
  if (!input.checkValidity() || !email) {
    input.reportValidity();
    return;
  }
  const defaultLabel = button.dataset.defaultLabel || button.textContent;
  button.dataset.defaultLabel = defaultLabel;
  if (message) message.textContent = "";
  button.disabled = true;
  button.textContent = "보내는 중";
  try {
    const { error } = await state.authClient.auth.signInWithOtp({
      email,
      options: {
        emailRedirectTo: authRedirectUrl(),
        shouldCreateUser: true,
      },
    });
    if (error) throw error;
    if (message) message.textContent = "이메일을 확인해 로그인 링크를 열어주세요.";
    toast("이메일로 로그인 링크를 보냈습니다.");
  } catch (error) {
    if (message) message.textContent = error.message || "로그인 링크를 보내지 못했습니다.";
    toast(error.message || "로그인 링크를 보내지 못했습니다.");
  } finally {
    button.disabled = false;
    button.textContent = defaultLabel;
  }
}

async function signOutAccount() {
  if (!state.authClient) return;
  const button = $("logoutButton");
  button.disabled = true;
  try {
    const { error } = await state.authClient.auth.signOut();
    if (error) throw error;
  } catch (error) {
    button.disabled = false;
    toast(error.message || "로그아웃하지 못했습니다.");
  }
}

function openAccountDeleteDialog() {
  if (!state.profile?.authenticated) return;
  if (!state.authConfig?.account_deletion_enabled) {
    toast("서버의 계정 삭제 설정이 아직 완료되지 않았습니다.");
    return;
  }
  const email = state.profile.email || state.authSession?.user?.email || "";
  const overlay = $("accountDeleteOverlay");
  const input = $("accountDeleteEmail");
  input.value = "";
  input.placeholder = email;
  $("accountDeleteMessage").textContent = "";
  $("accountDeleteMessage").dataset.state = "";
  $("accountDeleteConfirmButton").disabled = true;
  overlay.classList.add("active");
  overlay.setAttribute("aria-hidden", "false");
  document.body.classList.add("account-delete-open");
  window.setTimeout(() => input.focus(), 0);
}

function closeAccountDeleteDialog() {
  if (state.accountDeletionInProgress) return;
  const overlay = $("accountDeleteOverlay");
  overlay.classList.remove("active");
  overlay.setAttribute("aria-hidden", "true");
  document.body.classList.remove("account-delete-open");
}

function updateAccountDeleteConfirmation() {
  const expected = String(state.profile?.email || state.authSession?.user?.email || "").trim().toLowerCase();
  const entered = $("accountDeleteEmail").value.trim().toLowerCase();
  $("accountDeleteConfirmButton").disabled = !expected || entered !== expected || state.accountDeletionInProgress;
}

async function deleteAccountAndData() {
  const confirmation = $("accountDeleteEmail").value.trim();
  const button = $("accountDeleteConfirmButton");
  const message = $("accountDeleteMessage");
  if (button.disabled) return;
  state.accountDeletionInProgress = true;
  button.disabled = true;
  button.textContent = "삭제 중";
  message.dataset.state = "";
  message.textContent = "계정과 데이터를 삭제하고 있습니다.";
  try {
    await apiPost("/api/account/delete", { confirmation });
    try {
      await state.authClient?.auth.signOut({ scope: "local" });
    } catch {
      // The remote account is already gone; local app data is cleared below.
    }
    clearPulseEdgeLocalData();
    message.textContent = "삭제가 완료됐습니다.";
    toast("계정과 데이터가 삭제됐습니다.");
    window.setTimeout(() => window.location.replace(window.location.pathname), 700);
  } catch (error) {
    state.accountDeletionInProgress = false;
    button.textContent = "영구 삭제";
    message.dataset.state = "error";
    message.textContent = error.message || "계정 삭제를 완료하지 못했습니다.";
    updateAccountDeleteConfirmation();
  }
}

function clearPulseEdgeLocalData() {
  [
    CLIENT_ID_STORAGE_KEY,
    GUEST_ACCESS_STORAGE_KEY,
    NOTIFICATIONS_ENABLED_STORAGE_KEY,
    RISK_CONSENT_STORAGE_KEY,
    "chartPrefs",
    "indicatorPrefs",
    "chartDrawings",
    "seenSignals",
    "signalLog",
    "detailChartMode",
    "watchFilter",
    "watchSort",
    "signalLogFilter",
    "signalLogRange",
  ].forEach((key) => localStorage.removeItem(key));
  state.signalLog = [];
  state.seenSignals = new Set();
  state.chartPrefs = {};
  state.indicatorPrefs = {};
  state.chartDrawings = {};
  state.clientId = ensureClientId();
}

function authRedirectUrl() {
  return `${window.location.origin}${window.location.pathname}`;
}

function renderAuthGate() {
  const gate = $("authGate");
  if (!gate) return;

  const authenticated = Boolean(state.authSession && state.profile?.authenticated);
  const configured = Boolean(state.authConfig?.enabled && state.authClient);
  const providerAvailable = Boolean(
    state.authConfig?.google_enabled || state.authConfig?.email_enabled
  );
  const guestAccess = localStorage.getItem(GUEST_ACCESS_STORAGE_KEY) === "true";
  const shouldShow = configured && providerAvailable && !authenticated && !guestAccess;

  gate.classList.toggle("active", shouldShow);
  gate.setAttribute("aria-hidden", String(!shouldShow));
  document.body.classList.toggle("auth-gate-open", shouldShow);
  document.querySelectorAll(".app-shell, .bottom-nav").forEach((element) => {
    element.inert = shouldShow;
    element.setAttribute("aria-hidden", String(shouldShow));
  });
  if (!shouldShow) return;

  $("authGateStatus").textContent = "이메일 링크로 안전하게 계속하세요.";
  $("authGateControls").hidden = false;
  $("authGateGoogleButton").hidden = !state.authConfig.google_enabled;
  $("authGateEmailRow").hidden = !state.authConfig.email_enabled;
  $("authGateGuestButton").hidden = false;
}

function continueAsGuest() {
  localStorage.setItem(GUEST_ACCESS_STORAGE_KEY, "true");
  renderAccountPanel();
  toast("게스트 모드로 시작합니다.");
}

function renderAccountPanel() {
  renderAuthGate();
  const badge = $("accountBadge");
  const status = $("accountStatus");
  const setupNote = $("accountSetupNote");
  const guestActions = $("accountGuestActions");
  const signedInActions = $("accountSignedInActions");
  if (!badge || !status || !setupNote || !guestActions || !signedInActions) return;

  const authenticated = Boolean(state.authSession && state.profile?.authenticated);
  if (authenticated) {
    const email = state.profile.email || state.authSession.user?.email || "로그인 계정";
    badge.textContent = "로그인됨";
    badge.dataset.state = "ready";
    status.textContent = `${email} · 서버 동기화`;
    setupNote.hidden = true;
    guestActions.hidden = true;
    signedInActions.hidden = false;
    $("logoutButton").disabled = false;
    const deletionEnabled = Boolean(state.authConfig?.account_deletion_enabled);
    $("deleteAccountButton").disabled = !deletionEnabled;
    $("accountDeletionNote").hidden = deletionEnabled;
    return;
  }

  badge.textContent = "게스트";
  badge.dataset.state = "guest";
  status.textContent = "이 브라우저의 전용 공간에 저장 중";
  signedInActions.hidden = true;
  const configured = Boolean(state.authConfig?.enabled && state.authClient);
  setupNote.hidden = configured;
  if (!configured) {
    setupNote.textContent = state.authError
      ? `로그인 연결 확인 필요 · ${state.authError}`
      : "로그인 서버 설정 전입니다. 현재 데이터는 이 브라우저의 게스트 공간에 저장됩니다.";
    guestActions.hidden = true;
    return;
  }

  const googleButton = $("googleLoginButton");
  const emailRow = $("emailLoginRow");
  googleButton.hidden = !state.authConfig.google_enabled;
  emailRow.hidden = !state.authConfig.email_enabled;
  guestActions.hidden = !(state.authConfig.google_enabled || state.authConfig.email_enabled);
}

function initTabs() {
  document.querySelectorAll(".tab-btn").forEach((button) => {
    button.addEventListener("click", () => {
      const tab = button.dataset.tab;
      document.querySelectorAll(".tab-btn").forEach((item) => item.classList.toggle("active", item === button));
      document.querySelectorAll(".tab-page").forEach((page) => page.classList.toggle("active", page.id === `tab-${tab}`));
    });
  });
}

function providerText(payload = {}) {
  const meta = dataSourceMeta({
    provider: payload.provider,
    feed: payload.feed,
    config: payload.config,
  });
  return `TradingView 차트 · ${meta.short}`;
}

function dataSourceMeta({ provider, feed, config } = {}) {
  const resolvedProvider = String(provider || config?.provider || state.config?.provider || "demo").toLowerCase();
  if (resolvedProvider === "alpaca") {
    const resolvedFeed = String(feed || config?.alpaca?.feed || state.config?.alpaca?.feed || "iex").toUpperCase();
    const adjustment = String(config?.alpaca?.adjustment || state.config?.alpaca?.adjustment || "split").toLowerCase();
    const adjustmentLabel = adjustment === "split" ? "분할조정" : adjustment === "all" ? "전체조정" : adjustment === "raw" ? "원시가격" : adjustment;
    return {
      label: "Alpaca",
      short: `실제 일봉 · ${resolvedFeed} · ${adjustmentLabel}`,
      note: "서버의 개인용 Alpaca 연결에서 완료된 일봉만 사용합니다. 공개 배포용 데이터 권리는 별도로 확인해야 합니다.",
    };
  }
  return {
    label: "Sample",
    short: "분석 샘플",
    note: "공개 시세 공급원 연결 전 기능 확인용 데이터입니다. 실제 매매 판단에는 사용하지 않습니다.",
  };
}

function vixSourceMeta(config = state.config) {
  const source = String(config?.fear?.source || "cboe").toLowerCase();
  if (source === "off") return "VIX 꺼짐";
  if (source === "demo") return "VIX Demo 샘플";
  if (source === "fred") return "FRED VIXCLS · 일봉 종가";
  return "CBOE VIX · 공식 일봉 종가";
}

function vixActualSourceLabel(vix, config = state.config) {
  const source = String(vix?.source || config?.fear?.source || "cboe").toLowerCase();
  if (source === "fred") return vix?.fallback ? "FRED 대체" : "FRED";
  if (source === "demo") return vix?.fallback ? "Demo 대체" : "Demo";
  if (source === "off") return "꺼짐";
  return "CBOE";
}

async function loadConfig() {
  const payload = await apiGet("/api/config");
  state.config = payload.config;
  state.signalGroups = payload.signal_groups || {};
  state.credentials = payload.credentials || {};
  state.profile = payload.profile || null;
  renderAccountPanel();
  renderSettings(payload.config);
  renderBacktestControls(payload.config);
  $("providerStatus").textContent = providerText(payload);
  updateDataStatus(dataStatusFromConfig(payload.config, state.credentials));
  scheduleRefresh();
  renderInstallPanel();
  loadInstallInfo();
  renderLog();
}

function renderSettings(config) {
  $("refreshMinutes").value = config.alerts.auto_refresh_minutes;
  $("defaultTimeframe").value = config.chart?.default_timeframe || "D";
  $("defaultRange").value = config.chart?.default_range || "6M";
  $("watchlist").value = config.watchlist.join("\n");
  const stockMeta = dataSourceMeta({ config });
  $("analysisDataSource").textContent = stockMeta.short;
  $("analysisDataNote").textContent = stockMeta.note;
  $("rsiOversold").value = config.alerts.rsi_oversold;
  $("rsiDeepOversold").value = config.alerts.rsi_deep_oversold;
  $("rsiRecovery").value = config.alerts.rsi_recovery;
  $("rsiOverheated").value = config.alerts.rsi_overheated;
  $("volumeSpike").value = config.alerts.volume_spike_multiple;
  $("gapPct").value = config.alerts.gap_pct;
  $("vixElevated").value = config.fear?.elevated_threshold || 20;
  $("vixFear").value = config.fear?.fear_threshold || 30;
  $("vixPanic").value = config.fear?.panic_threshold || 40;
  $("vixSpike").value = config.fear?.spike_5d_pct || 20;
  renderWatchlistPills(config.watchlist);
  renderPositionEditor(config);
  renderAlertPreferences(config);
  renderDataDisclosure(config);
  renderDataHealthOverview(config, state.credentials, state.dataHealth);
  renderBacktestControls(config);
  renderSettingsSummaries(config);
}

function renderSettingsSummaries(config) {
  const alerts = config.alerts || {};
  const fear = config.fear || {};
  const signalMeta = $("signalCriteriaMeta");
  if (signalMeta) {
    signalMeta.textContent = `RSI ${alerts.rsi_oversold}/${alerts.rsi_recovery} · 거래량 ${Number(alerts.volume_spike_multiple || 0).toFixed(1)}x · VIX ${fear.fear_threshold || 30}`;
  }

  updatePositionSettingsMeta(config);
  updateAlertSettingsMeta(config);
}

function updatePositionSettingsMeta(config) {
  const host = $("positionSettingsMeta");
  if (!host) return;
  const positions = Array.isArray(config.positions) ? config.positions : [];
  const heldCount = positions.filter((position) => position.held).length;
  const watchCount = Array.isArray(config.watchlist) ? config.watchlist.length : currentWatchlistSymbols().length;
  host.textContent = heldCount ? `보유 ${heldCount}개 · 관심 ${watchCount}개` : `보유 없음 · 관심 ${watchCount}개`;
}

function updateAlertSettingsMeta(config) {
  const host = $("alertSettingsMeta");
  if (!host) return;
  const preferences = config.alert_preferences || {};
  const signalTypes = [...new Set(Object.values(state.signalGroups || {}).flat())];
  const types = signalTypes.length ? signalTypes : Object.keys(preferences);
  const counts = { push: 0, summary: 0, log: 0, off: 0 };
  for (const type of types) {
    const delivery = preferences[type] || "summary";
    counts[delivery] = (counts[delivery] || 0) + 1;
  }
  host.textContent = `즉시 ${counts.push} · 요약 ${counts.summary} · 끔 ${counts.off}`;
}

function renderDataDisclosure(config) {
  const host = $("dataDisclosurePanel");
  if (!host) return;
  const stock = dataSourceMeta({ config });
  host.innerHTML = `
    <div>
      <span>주식 데이터</span>
      <strong>${escapeHtml(stock.short)}</strong>
      <small>${escapeHtml(stock.note)}</small>
    </div>
    <div>
      <span>공포지수</span>
      <strong>${escapeHtml(vixSourceMeta(config))}</strong>
      <small>VIX는 현재 일봉 종가 기준이라 실시간 공포지수가 아닙니다.</small>
    </div>
    <div>
      <span>사용 목적</span>
      <strong>스윙 점검용</strong>
      <small>초단타나 실시간 주문 판단용이 아니라 일봉/주봉 기반 관찰 도구입니다.</small>
    </div>
  `;
}

function renderDataHealthOverview(config = state.config, credentials = state.credentials, health = state.dataHealth) {
  const host = $("dataHealthOverview");
  if (!host || !config) return;
  host.innerHTML = dataHealthTiles(config, credentials, health).map((tile) => `
    <div class="data-health-tile" data-state="${escapeHtml(tile.state)}">
      <span>${escapeHtml(tile.label)}</span>
      <strong>${escapeHtml(tile.value)}</strong>
      <small>${escapeHtml(tile.note)}</small>
    </div>
  `).join("");
}

function dataHealthTiles(config = state.config, credentials = state.credentials, health = state.dataHealth) {
  const stockMeta = dataSourceMeta({ config });
  const stockStatus = health?.stock?.data_status || null;
  const usage = health?.usage || state.latestPayload?.usage || null;
  const stockTile = {
    label: "PulseEdge 분석",
    value: stockStatus?.stale ? "캐시 데이터" : stockMeta.short,
    note: stockStatus?.stale ? dataStatusText(stockStatus) : stockMeta.note,
    state: String(config?.provider || "demo").toLowerCase() === "alpaca"
      ? stockStatus?.stale ? "warning" : health?.stock?.ok ? "ok" : "warning"
      : "info",
  };
  return [stockTile, vixHealthTile(config, health?.vix), usageHealthTile(config, usage)];
}

function vixHealthTile(config, vix) {
  if (vix) {
    if (vix.ok) {
      const value = vix.value === null || vix.value === undefined ? vix.label || vixSourceMeta(config) : `VIX ${fmt(vix.value)}`;
      const freshness = vix.freshness_label || "일봉 종가";
      return {
        label: "공포지수",
        value,
        note: `${vixActualSourceLabel(vix, config)} · ${freshness}`,
        state: vix.fallback ? "warning" : String(vix.source || "").toLowerCase() === "demo" ? "info" : "ok",
      };
    }
    return {
      label: "공포지수",
      value: "확인 필요",
      note: friendlyDataError(vix.error),
      state: "warning",
    };
  }
  return {
    label: "공포지수",
    value: vixSourceMeta(config),
    note: "일봉 종가라 장중 실시간 값이 아닙니다.",
    state: "info",
  };
}

function connectionTestTile(health) {
  if (!health) {
    return {
      label: "연결 테스트",
      value: "테스트 전",
      note: "AAPL 주식 데이터와 VIX를 확인합니다.",
      state: "info",
    };
  }
  if (health.health_level === "ok") {
    return {
      label: "연결 테스트",
      value: "정상",
      note: dataHealthShortText(health),
      state: "ok",
    };
  }
  return {
    label: "연결 테스트",
    value: health.health_level === "error" ? "실패" : "부분 확인",
    note: dataHealthShortText(health),
    state: health.health_level === "error" ? "error" : "warning",
  };
}

function dataHealthShortText(health) {
  const stock = health?.stock || {};
  const vix = health?.vix || {};
  const stockText = stock.ok
    ? `${stock.symbol || "AAPL"} ${stock.bars || 0}개 · ${dataStatusText(stock.data_status)}`
    : friendlyDataError(stock.error);
  const vixText = vix.ok
    ? vix.value === null || vix.value === undefined ? vix.label || "VIX 확인" : `VIX ${fmt(vix.value)}`
    : friendlyDataError(vix.error);
  return `${stockText} · ${vixText}`;
}

function usageHealthTile(config, usage) {
  const refreshMinutes = Number(config?.alerts?.auto_refresh_minutes || 30);
  if (!usage) {
    return {
      label: "API 보호",
      value: "캐시 대기",
      note: `자동 새로고침 ${refreshMinutes}분 이상`,
      state: "info",
    };
  }
  const barCache = usage.bar_cache || {};
  const vix = usage.vix || {};
  const externalRequests = Number(usage.alpaca?.requests || 0) + Number(vix.requests || 0);
  const hitRate = barCache.hit_rate_pct === null || barCache.hit_rate_pct === undefined ? "-" : `${fmt(barCache.hit_rate_pct)}%`;
  return {
    label: "API 보호",
    value: `캐시 ${hitRate}`,
    note: `외부요청 ${externalRequests}회 · 바캐시 ${barCache.entries || 0}개`,
    state: "ok",
  };
}

async function loadInstallInfo() {
  try {
    state.installInfo = await apiGet("/api/install-info");
  } catch {
    state.installInfo = null;
  }
  renderInstallPanel();
}

function renderInstallPanel() {
  const host = $("installPanel");
  if (!host) return;
  const standalone = isStandaloneApp();
  const info = state.installInfo || {};
  const phoneUrls = Array.isArray(info.local_urls) ? info.local_urls : [];
  const phoneUrl = phoneUrls[0] || "";
  const currentUrl = `${location.origin}/`;
  const loopback = isLoopbackHost(location.hostname);
  const phoneReady = Boolean(info.phone_ready && phoneUrl);
  const installCopy = standalone
    ? "홈 화면 앱 모드로 실행 중입니다."
    : isIOS()
      ? "iPhone은 Safari 공유 버튼에서 홈 화면에 추가를 선택합니다."
      : state.deferredInstallPrompt
        ? "이 브라우저에서 설치 버튼을 사용할 수 있습니다."
        : "브라우저 메뉴에서 설치 또는 홈 화면에 추가를 선택합니다.";
  const phoneCopy = phoneReady
    ? "폰과 PC가 같은 와이파이에 있을 때 아래 주소로 접속합니다."
    : loopback
      ? "폰에서는 127.0.0.1이 PC가 아니라 폰 자신입니다. 서버를 0.0.0.0으로 켠 뒤 PC 와이파이 IP로 접속합니다."
      : "폰 접속 주소를 찾지 못했습니다. PC와 폰이 같은 와이파이에 있는지 확인합니다.";
  host.innerHTML = `
    <div class="install-status-grid">
      <div>
        <span>실행</span>
        <strong>${standalone ? "앱 모드" : "브라우저"}</strong>
      </div>
      <div>
        <span>현재 주소</span>
        <code>${escapeHtml(currentUrl)}</code>
      </div>
      <div>
        <span>폰 접속</span>
        <code>${escapeHtml(phoneUrl || "PC 와이파이 IP 필요")}</code>
      </div>
    </div>
    <p>${escapeHtml(installCopy)} ${escapeHtml(phoneCopy)}</p>
    <button id="installAppButton" class="ghost-btn small" type="button">${state.deferredInstallPrompt ? "설치" : "설치 안내"}</button>
  `;
}

function isStandaloneApp() {
  return Boolean(
    window.matchMedia?.("(display-mode: standalone)")?.matches ||
    window.navigator?.standalone === true
  );
}

function isIOS() {
  return /iphone|ipad|ipod/i.test(window.navigator?.userAgent || "");
}

function isLoopbackHost(hostname) {
  return hostname === "localhost" || hostname === "127.0.0.1" || hostname === "::1";
}

function updateDataStatus(status) {
  const host = $("dataStatusPanel");
  if (!host) return;
  if (!status || status.level === "ok") {
    host.hidden = true;
    host.innerHTML = "";
    return;
  }
  const items = Array.isArray(status.items) ? status.items.filter(Boolean).slice(0, 4) : [];
  host.hidden = false;
  host.dataset.level = status.level || "info";
  host.innerHTML = `
    <div>
      <strong>${escapeHtml(status.title || "데이터 확인 필요")}</strong>
      <p>${escapeHtml(status.message || "")}</p>
    </div>
    ${items.length ? `<div class="data-status-items">${items.map((item) => `<span>${escapeHtml(item)}</span>`).join("")}</div>` : ""}
  `;
}

function dataStatusFromConfig(config = state.config, credentials = state.credentials) {
  if (String(config?.provider || "demo").toLowerCase() === "alpaca" && !credentials?.market_data_server_ready) {
    return {
      level: "error",
      title: "실제 일봉 연결 확인 필요",
      message: "개인 개발 모드가 켜졌지만 서버에서 Alpaca API 키를 찾지 못했습니다.",
      items: ["서버의 .env에서 APCA_API_KEY_ID와 APCA_API_SECRET_KEY를 확인하세요."],
    };
  }
  return null;
}

function dataStatusFromPayload(payload) {
  const configStatus = dataStatusFromConfig(state.config, state.credentials);
  if (configStatus) return configStatus;

  const stockErrors = stockDataErrors(payload);
  const stockCount = new Set([...(payload.results || []), ...(payload.watch_results || [])].map((result) => result.symbol).filter(Boolean)).size;
  const vix = payload.market?.vix || null;
  const issues = [];

  const staleResults = new Map();
  for (const result of [...(payload.results || []), ...(payload.watch_results || [])]) {
    if (result?.data_status?.stale && !staleResults.has(result.symbol)) {
      staleResults.set(result.symbol, result.data_status);
    }
  }
  if (staleResults.size) {
    issues.push({
      level: "warning",
      title: "마지막 정상 데이터 사용 중",
      message: "시세 공급자 연결이 일시적으로 끊겨 저장된 일봉으로 분석했습니다.",
      items: [...staleResults.entries()].slice(0, 4).map(([symbol, status]) => `${symbol} · ${dataStatusText(status)}`),
    });
  }

  if (stockErrors.length) {
    const allFailed = stockCount > 0 && stockErrors.length >= stockCount;
    issues.push({
      level: allFailed ? "error" : "warning",
      title: allFailed ? "주식 데이터 수신 실패" : "일부 종목 데이터 확인 필요",
      message: allFailed
        ? "관심종목 일봉을 불러오지 못했습니다."
        : `${stockErrors.length}개 종목은 제외하고 나머지만 분석했습니다.`,
      items: stockErrors.slice(0, 3).map((item) => `${item.symbol}: ${friendlyDataError(item.error)}`),
    });
  }

  if (vix?.error) {
    issues.push({
      level: "warning",
      title: "VIX 데이터 확인 필요",
      message: friendlyDataError(vix.error),
      items: ["시장 공포 필터가 약해질 수 있음"],
    });
  } else if (vix?.fallback) {
    const demoFallback = String(vix.source || "").toLowerCase() === "demo";
    issues.push({
      level: "warning",
      title: "VIX 대체값 사용 중",
      message: demoFallback
        ? "CBOE와 FRED VIX를 모두 못 받아 데모 대체값으로 시장 상태를 계산했습니다."
        : "CBOE VIX를 못 받아 FRED 일봉 종가로 시장 상태를 계산했습니다.",
      items: [demoFallback ? "실제 공포지수와 다를 수 있음" : "FRED 공개 일정에 따라 최신값이 늦을 수 있음"],
    });
  } else if (vix?.latest_time && staleCalendarDays(vix.latest_time) > 5) {
    issues.push({
      level: "warning",
      title: "VIX 날짜 확인 필요",
      message: `VIX 최신값이 ${formatBarTime(vix.latest_time)} 기준입니다.`,
      items: [`${String(vix.source || "VIX").toUpperCase()} 일봉 종가 지연 가능`],
    });
  }

  if (!issues.length) return null;
  const main = issues.some((issue) => issue.level === "error")
    ? issues.find((issue) => issue.level === "error")
    : issues[0];
  const extraItems = issues.flatMap((issue) => issue.items || []);
  return {
    level: main.level,
    title: main.title,
    message: main.message,
    items: extraItems,
  };
}

function dataStatusFromHealth(payload) {
  if (!payload || payload.health_level === "ok") return null;
  const stock = payload.stock || {};
  const vix = payload.vix || {};
  const items = [];
  if (!stock.ok) items.push(`주식: ${friendlyDataError(stock.error)}`);
  if (stock.data_status?.stale) items.push(`주식: ${dataStatusText(stock.data_status)}`);
  if (!vix.ok) items.push(`VIX: ${friendlyDataError(vix.error)}`);
  if (vix.fallback) items.push("VIX 대체값 사용 중");
  return {
    level: payload.health_level === "error" ? "error" : "warning",
    title: payload.health_level === "error" ? "데이터 연결 실패" : "데이터 일부 확인 필요",
    message: payload.health_level === "error" ? "주식/VIX 데이터를 모두 확인하지 못했습니다." : "일부 데이터만 정상 확인됐습니다.",
    items,
  };
}

function stockDataErrors(payload) {
  const errors = new Map();
  for (const result of [...(payload?.results || []), ...(payload?.watch_results || [])]) {
    if (result?.error && !errors.has(result.symbol)) {
      errors.set(result.symbol || "UNKNOWN", result.error);
    }
  }
  return [...errors.entries()].map(([symbol, error]) => ({ symbol, error }));
}

function friendlyDataError(message = "") {
  const text = String(message || "");
  if (!text) return "데이터를 불러오지 못했습니다.";
  if (/api key|Alpaca 키|서버 Alpaca 키|환경변수/i.test(text)) {
    return "서버 Alpaca API 키를 확인해야 합니다.";
  }
  if (/HTTP 401|HTTP 403|unauthorized|forbidden/i.test(text)) {
    return "Alpaca 키 권한이나 데이터 피드 설정을 확인해야 합니다.";
  }
  if (/HTTP 429|rate limit/i.test(text)) {
    return "데이터 요청 한도에 걸렸습니다. 잠시 뒤 다시 시도합니다.";
  }
  if (/No bars returned|유효한 값이 없습니다|값 없음/i.test(text)) {
    return "해당 데이터가 비어 있습니다. 티커나 데이터 소스를 확인합니다.";
  }
  if (/CBOE|FRED|VIXCLS/i.test(text)) {
    return "VIX 일봉 데이터를 불러오지 못했습니다.";
  }
  if (/Failed to fetch|Network|timed out|timeout|URLError/i.test(text)) {
    return "네트워크나 데이터 서버 연결을 확인해야 합니다.";
  }
  return text.replace(/^Alpaca request failed for ([A-Z0-9.-]+):\s*/i, "$1 ");
}

function dataErrorHint(message = "") {
  const text = String(message || "");
  if (/api key|Alpaca 키|환경변수/i.test(text)) return "Settings의 연결 테스트와 서버 .env를 확인합니다.";
  if (/No bars returned/i.test(text)) return "티커가 맞는지, IEX 무료 데이터에서 지원되는지 확인합니다.";
  if (/HTTP 401|HTTP 403/i.test(text)) return "Alpaca 대시보드의 키 권한과 feed 설정을 확인합니다.";
  if (/HTTP 429|rate limit/i.test(text)) return "요청 한도일 수 있어 잠시 뒤 다시 분석합니다.";
  return "다른 종목은 계속 분석하고, 문제 종목만 설정에서 확인합니다.";
}

function staleCalendarDays(value) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return 0;
  const today = new Date();
  const dateOnly = new Date(date.getFullYear(), date.getMonth(), date.getDate());
  const todayOnly = new Date(today.getFullYear(), today.getMonth(), today.getDate());
  return Math.floor((todayOnly - dateOnly) / 86400000);
}

function renderWatchlistPills(symbols) {
  const host = $("watchlistPills");
  host.innerHTML = symbols.map((symbol) => `
    <span class="watchlist-pill">
      ${escapeHtml(symbol)}
      <button class="remove-symbol" type="button" data-symbol="${escapeHtml(symbol)}" title="${escapeHtml(symbol)} 삭제">×</button>
    </span>
  `).join("");
}

function renderPositionEditor(config) {
  const positions = new Map((config.positions || []).map((position) => [position.symbol, position]));
  const host = $("positionEditor");
  host.innerHTML = config.watchlist.map((symbol) => {
    const position = positions.get(symbol) || {};
    const hasDetails = Boolean(
      position.held ||
      position.average_entry_price ||
      position.quantity ||
      position.entry_date ||
      position.next_earnings_date ||
      position.notes
    );
    return `
      <div class="position-row ${position.held ? "is-held" : ""} ${hasDetails ? "has-position-details" : ""}" data-symbol="${escapeHtml(symbol)}">
        <label>
          종목
          <input class="position-symbol" value="${escapeHtml(symbol)}" readonly>
        </label>
        <label class="check-label">
          <input class="position-held" type="checkbox" ${position.held ? "checked" : ""}>
          보유
        </label>
        <div class="position-detail-fields">
          <label>
            평단가
            <input class="position-average" type="number" min="0" step="0.01" value="${valueOrEmpty(position.average_entry_price)}">
          </label>
          <label>
            수량
            <input class="position-quantity" type="number" min="0" step="0.0001" value="${valueOrEmpty(position.quantity)}">
          </label>
          <label>
            매수일
            <input class="position-entry-date" type="date" value="${escapeHtml(position.entry_date || "")}">
          </label>
          <label>
            실적일
            <input class="position-earnings-date" type="date" value="${escapeHtml(position.next_earnings_date || "")}">
          </label>
          <label>
            메모
            <input class="position-notes" value="${escapeHtml(position.notes || "")}">
          </label>
        </div>
      </div>
    `;
  }).join("");
}

function renderAlertPreferences(config) {
  const host = $("alertPreferenceEditor");
  const preferences = config.alert_preferences || {};
  host.innerHTML = Object.entries(state.signalGroups).map(([group, signalTypes]) => {
    const counts = signalTypes.reduce((acc, type) => {
      const delivery = preferences[type] || "summary";
      acc[delivery] = (acc[delivery] || 0) + 1;
      return acc;
    }, {});
    const summary = Object.entries(DELIVERY_LABELS)
      .map(([value, label]) => `${label} ${counts[value] || 0}`)
      .join(" · ");
    return `
    <details class="alert-group">
      <summary class="alert-group-title">
        <span>
          <strong>${escapeHtml(GROUP_LABELS[group] || group)}</strong>
          <small>${escapeHtml(summary)}</small>
        </span>
        <em>${signalTypes.length}개</em>
      </summary>
      <div class="alert-rows">
        ${signalTypes.map((type) => `
          <label class="alert-row">
            <span>
              <strong>${escapeHtml(SIGNAL_LABELS[type] || type)}</strong>
            </span>
            <select class="alert-pref" data-signal="${escapeHtml(type)}">
              ${Object.entries(DELIVERY_LABELS).map(([value, label]) => `<option value="${value}" ${preferences[type] === value ? "selected" : ""}>${label}</option>`).join("")}
            </select>
          </label>
        `).join("")}
      </div>
    </details>
  `;
  }).join("");
}

function readForm() {
  return {
    provider: "demo",
    watchlist: currentWatchlistSymbols(),
    positions: readPositions(),
    chart: {
      default_timeframe: $("defaultTimeframe").value,
      default_range: $("defaultRange").value,
      zoom_enabled: true,
    },
    fear: {
      source: "cboe",
      lookback_days: 180,
      elevated_threshold: Number($("vixElevated").value),
      fear_threshold: Number($("vixFear").value),
      panic_threshold: Number($("vixPanic").value),
      spike_5d_pct: Number($("vixSpike").value),
      calming_5d_pct: -12,
      fallback_to_demo: true,
    },
    alerts: {
      rsi_period: 14,
      rsi_oversold: Number($("rsiOversold").value),
      rsi_deep_oversold: Number($("rsiDeepOversold").value),
      rsi_recovery: Number($("rsiRecovery").value),
      rsi_overheated: Number($("rsiOverheated").value),
      ma_periods: [20, 60, 120],
      volume_period: 20,
      volume_spike_multiple: Number($("volumeSpike").value),
      large_cap_volume_spike_multiple: 1.5,
      gap_pct: Number($("gapPct").value),
      high_low_periods: [60, 120],
      ma_distance_pct: {
        "20_oversold": -7,
        "60_oversold": -12,
        "120_oversold": -20,
        "20_overextended": 12,
        "60_overextended": 20,
      },
      auto_refresh_minutes: Number($("refreshMinutes").value),
    },
    alert_preferences: readAlertPreferences(),
  };
}

function readPositions() {
  return [...document.querySelectorAll(".position-row")].map((row) => {
    const symbol = row.dataset.symbol;
    const held = row.querySelector(".position-held").checked;
    const average = row.querySelector(".position-average").value;
    const quantity = row.querySelector(".position-quantity").value;
    const entryDate = row.querySelector(".position-entry-date").value;
    const earningsDate = row.querySelector(".position-earnings-date").value;
    const notes = row.querySelector(".position-notes").value.trim();
    if (!held && !average && !quantity && !entryDate && !earningsDate && !notes) {
      return null;
    }
    return {
      symbol,
      held,
      average_entry_price: average ? Number(average) : null,
      quantity: quantity ? Number(quantity) : null,
      entry_date: entryDate,
      target_return_pct: 15,
      stop_loss_pct: -7,
      trailing_stop_pct: -8,
      holding_style: "swing",
      next_earnings_date: earningsDate,
      notes,
    };
  }).filter(Boolean);
}

function readAlertPreferences() {
  const preferences = {};
  document.querySelectorAll(".alert-pref").forEach((select) => {
    preferences[select.dataset.signal] = select.value;
  });
  return preferences;
}

function currentWatchlistSymbols() {
  return normalizeSymbols($("watchlist").value);
}

function normalizeSymbols(value) {
  const raw = Array.isArray(value) ? value : String(value).split(/[\s,]+/);
  const seen = new Set();
  const symbols = [];
  for (const item of raw) {
    const symbol = String(item).trim().toUpperCase();
    if (!symbol) continue;
    if (!/^[A-Z][A-Z0-9.-]{0,9}$/.test(symbol)) {
      throw new Error(`티커 형식이 이상합니다: ${symbol}`);
    }
    if (!seen.has(symbol)) {
      symbols.push(symbol);
      seen.add(symbol);
    }
  }
  if (!symbols.length) {
    throw new Error("관심종목을 1개 이상 넣어주세요.");
  }
  return symbols.slice(0, 30);
}

function setWatchlistSymbols(symbols) {
  const normalized = normalizeSymbols(symbols);
  const previewConfig = { ...(state.config || {}), watchlist: normalized, positions: readPositions() };
  $("watchlist").value = normalized.join("\n");
  renderWatchlistPills(normalized);
  renderPositionEditor(previewConfig);
  renderBacktestControls(previewConfig);
  updatePositionSettingsMeta(previewConfig);
}

function syncWatchlistPreview() {
  try {
    const symbols = currentWatchlistSymbols();
    const previewConfig = { ...(state.config || {}), watchlist: symbols, positions: readPositions() };
    renderWatchlistPills(symbols);
    renderPositionEditor(previewConfig);
    renderBacktestControls(previewConfig);
    updatePositionSettingsMeta(previewConfig);
  } catch {
    // Keep the previous valid preview while the user is still typing.
  }
}

function addSymbolFromInput() {
  try {
    const input = $("symbolAddInput");
    const symbol = input.value.trim().toUpperCase();
    if (!symbol) return;
    const symbols = currentWatchlistSymbols();
    if (!symbols.includes(symbol)) {
      symbols.push(symbol);
    }
    setWatchlistSymbols(symbols);
    input.value = "";
    toast(`${symbol} 추가됨`);
  } catch (error) {
    toast(error.message);
  }
}

async function addWatchSymbolsQuick() {
  const button = $("watchQuickAddButton");
  const input = $("watchQuickAddInput");
  const originalText = button.textContent;
  try {
    const incoming = normalizeSymbols(input.value);
    const current = currentWatchlistSymbols();
    const added = incoming.filter((symbol) => !current.includes(symbol));
    if (!added.length) {
      toast("이미 관심목록에 있습니다.");
      input.value = "";
      return;
    }
    const next = [...current, ...added];
    if (next.length > 30) {
      throw new Error("관심종목은 최대 30개까지 가능합니다.");
    }
    button.disabled = true;
    button.textContent = "추가 중";
    setWatchlistSymbols(next);
    input.value = "";
    await saveConfig({ toastMessage: `${added.join(", ")} 추가됨` });
  } catch (error) {
    toast(error.message);
  } finally {
    button.disabled = false;
    button.textContent = originalText;
  }
}

function removeSymbol(symbol) {
  try {
    const protectedSymbols = new Set(["SPY", "QQQ"]);
    if (protectedSymbols.has(symbol)) {
      toast(`${symbol}는 시장 필터라 유지됩니다.`);
      return;
    }
    const symbols = currentWatchlistSymbols().filter((item) => item !== symbol);
    setWatchlistSymbols(symbols);
    toast(`${symbol} 삭제됨`);
  } catch (error) {
    toast(error.message);
  }
}

async function removeWatchSymbolQuick(symbol) {
  try {
    if (isProtectedMarketSymbol(symbol)) {
      toast(`${symbol}는 시장 필터라 유지됩니다.`);
      return;
    }
    if (isHeldConfigSymbol(symbol)) {
      toast(`${symbol}는 보유종목이라 Hold에서 보유 해제 후 삭제할 수 있습니다.`);
      return;
    }
    const current = currentWatchlistSymbols();
    if (!current.includes(symbol)) {
      toast("이미 삭제된 종목입니다.");
      return;
    }
    setWatchlistSymbols(current.filter((item) => item !== symbol));
    await saveConfig({ toastMessage: `${symbol} 삭제됨` });
  } catch (error) {
    toast(error.message);
  }
}

function isProtectedMarketSymbol(symbol) {
  return ["SPY", "QQQ"].includes(String(symbol).toUpperCase());
}

function isHeldConfigSymbol(symbol) {
  return (state.config?.positions || []).some(
    (position) => position.held && position.symbol === String(symbol).toUpperCase()
  );
}

function initInteractiveControls() {
  $("addSymbolButton").addEventListener("click", addSymbolFromInput);
  $("watchQuickAddButton").addEventListener("click", addWatchSymbolsQuick);
  $("resetRiskConsentButton").addEventListener("click", () => showRiskConsent({ force: true }));
  $("googleLoginButton")?.addEventListener("click", () => signInWithGoogle());
  $("emailLoginButton")?.addEventListener("click", () => sendEmailLoginLink());
  $("logoutButton")?.addEventListener("click", signOutAccount);
  $("deleteAccountButton")?.addEventListener("click", openAccountDeleteDialog);
  $("accountDeleteCancelButton")?.addEventListener("click", closeAccountDeleteDialog);
  $("accountDeleteConfirmButton")?.addEventListener("click", deleteAccountAndData);
  $("accountDeleteEmail")?.addEventListener("input", updateAccountDeleteConfirmation);
  $("accountEmail")?.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      sendEmailLoginLink();
    }
  });
  $("authGateGoogleButton")?.addEventListener("click", () => signInWithGoogle("authGateGoogleButton"));
  $("authGateEmailButton")?.addEventListener("click", () => {
    sendEmailLoginLink("authGateEmail", "authGateEmailButton", "authGateMessage");
  });
  $("authGateGuestButton")?.addEventListener("click", continueAsGuest);
  $("authGateEmail")?.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      sendEmailLoginLink("authGateEmail", "authGateEmailButton", "authGateMessage");
    }
  });
  $("watchSort").value = state.watchSort;
  renderWatchTools();
  $("watchSort").addEventListener("change", (event) => {
    state.watchSort = event.target.value;
    localStorage.setItem("watchSort", state.watchSort);
    renderCards(state.latestPayload?.results || [], currentWatchResults());
  });
  const backtestButton = $("backtestRunButton");
  if (backtestButton) {
    backtestButton.addEventListener("click", runBacktest);
    $("backtestMinScore")?.addEventListener("keydown", (event) => {
      if (event.key === "Enter") {
        event.preventDefault();
        runBacktest();
      }
    });
    $("backtestRule")?.addEventListener("change", updateBacktestRuleCopy);
  }
  $("symbolAddInput").addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      addSymbolFromInput();
    }
  });
  $("watchQuickAddInput").addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      addWatchSymbolsQuick();
    }
  });
  $("watchlist").addEventListener("input", syncWatchlistPreview);

  document.addEventListener("click", (event) => {
    const installButton = event.target.closest("#installAppButton");
    if (installButton) {
      installApp();
      return;
    }

    const detailChartModeButton = event.target.closest("[data-detail-chart-mode]");
    if (detailChartModeButton && state.detailSymbol) {
      state.detailChartMode = detailChartModeButton.dataset.detailChartMode === "pulseedge" ? "pulseedge" : "tradingview";
      localStorage.setItem("detailChartMode", state.detailChartMode);
      const detailResult = findResult(state.detailSymbol, state.detailView || "position");
      if (detailResult && !detailResult.error) renderStockDetail(detailResult);
      return;
    }

    const signalLogRangeButton = event.target.closest(".filter-chip[data-signal-log-range]");
    if (signalLogRangeButton) {
      state.signalLogRange = signalLogRangeButton.dataset.signalLogRange;
      localStorage.setItem("signalLogRange", state.signalLogRange);
      renderLog();
      return;
    }

    const signalLogFilterButton = event.target.closest(".filter-chip[data-signal-log-filter]");
    if (signalLogFilterButton) {
      state.signalLogFilter = signalLogFilterButton.dataset.signalLogFilter;
      localStorage.setItem("signalLogFilter", state.signalLogFilter);
      renderLog();
      return;
    }

    const indicatorControl = event.target.closest(".chart-btn[data-indicator]");
    if (indicatorControl) {
      toggleIndicator(indicatorControl.dataset.symbol, indicatorControl.dataset.indicator);
      return;
    }

    const drawingControl = event.target.closest(".chart-btn[data-drawing-action]");
    if (drawingControl) {
      const symbol = drawingControl.dataset.symbol;
      if (drawingControl.dataset.drawingAction === "toggle") {
        toggleDrawingMode(symbol);
      } else if (drawingControl.dataset.drawingAction === "undo") {
        undoChartLine(symbol);
      }
      return;
    }

    const chartControl = event.target.closest(".chart-btn[data-chart-kind]");
    if (chartControl) {
      setChartPref(chartControl.dataset.symbol, {
        [chartControl.dataset.chartKind]: chartControl.dataset.value,
      });
      return;
    }

    const removeButton = event.target.closest(".remove-symbol[data-symbol]");
    if (removeButton) {
      removeSymbol(removeButton.dataset.symbol);
      return;
    }

    const quickRemoveButton = event.target.closest(".quick-remove-symbol[data-symbol]");
    if (quickRemoveButton) {
      removeWatchSymbolQuick(quickRemoveButton.dataset.symbol);
      return;
    }

    const positionToggle = event.target.closest(".position-held");
    if (positionToggle) {
      const row = positionToggle.closest(".position-row");
      if (row) {
        row.classList.toggle("is-held", positionToggle.checked);
      }
      try {
        updatePositionSettingsMeta({
          ...(state.config || {}),
          watchlist: currentWatchlistSymbols(),
          positions: readPositions(),
        });
      } catch {
        // The watchlist preview can be temporarily invalid while typing.
      }
      return;
    }

    const filterButton = event.target.closest(".filter-chip[data-watch-filter]");
    if (filterButton) {
      state.watchFilter = filterButton.dataset.watchFilter;
      localStorage.setItem("watchFilter", state.watchFilter);
      renderWatchTools();
      renderCards(state.latestPayload?.results || [], currentWatchResults());
      return;
    }

    const closeButton = event.target.closest("[data-close-detail]");
    if (closeButton) {
      closeStockDetail();
      return;
    }

    if (event.target.id === "stockDetailOverlay") {
      closeStockDetail();
      return;
    }

    const card = event.target.closest(".stock-card[data-symbol]");
    if (card && !event.target.closest("button, canvas, input, select, textarea, a")) {
      openStockDetail(card.dataset.symbol, card.dataset.view || "position");
    }
  });

  document.addEventListener("change", (event) => {
    if (event.target.closest(".alert-pref")) {
      updateAlertSettingsMeta({
        ...(state.config || {}),
        alert_preferences: readAlertPreferences(),
      });
    }
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && $("accountDeleteOverlay")?.classList.contains("active")) {
      closeAccountDeleteDialog();
    } else if (event.key === "Escape" && state.detailSymbol) {
      closeStockDetail();
    }
  });
}

function dataConfigKey(config) {
  if (!config) return "";
  return [
    String(config.provider || "demo").toLowerCase(),
    String(config.fear?.source || "cboe").toLowerCase(),
  ].join(":");
}

function renderWatchTools() {
  document.querySelectorAll(".filter-chip[data-watch-filter]").forEach((button) => {
    const active = button.dataset.watchFilter === state.watchFilter;
    button.classList.toggle("active", active);
    button.setAttribute("aria-pressed", active ? "true" : "false");
  });
  if ($("watchSort")) {
    $("watchSort").value = state.watchSort;
  }
}

function renderBacktestControls(config) {
  const select = $("backtestSymbol");
  if (!select || !config) return;
  const symbols = config.watchlist || [];
  const current = select.value || state.backtestPayload?.symbol || symbols[0] || "";
  select.innerHTML = symbols.map((symbol) => `<option value="${escapeHtml(symbol)}">${escapeHtml(symbol)}</option>`).join("");
  select.value = symbols.includes(current) ? current : symbols[0] || "";
  if ($("backtestResults") && !$("backtestResults").innerHTML) {
    $("backtestSummary").innerHTML = "";
    $("backtestResults").innerHTML = emptyState("아직 백테스트 결과 없음");
  }
  updateBacktestRuleCopy();
}

async function runBacktest() {
  if (!$("backtestSymbol")) {
    toast("백테스트 화면은 숨겨져 있습니다.");
    return;
  }
  const symbol = $("backtestSymbol").value || state.config?.watchlist?.[0];
  if (!symbol) {
    toast("백테스트할 종목이 없습니다.");
    return;
  }
  const minScore = clamp(Number($("backtestMinScore").value || 85), 0, 100);
  const lookback = Number($("backtestLookback").value || 252);
  const cooldownDays = Number($("backtestCooldown").value || 10);
  const rule = $("backtestRule").value || "hold90";
  const button = $("backtestRunButton");
  button.disabled = true;
  button.textContent = "실행 중";
  $("backtestStatus").textContent = `${symbol} 테스트 중`;
  try {
    const params = new URLSearchParams({
      symbol,
      min_score: String(minScore),
      lookback: String(lookback),
      cooldown_days: String(cooldownDays),
      rule,
    });
    const payload = await apiGet(`/api/backtest?${params.toString()}`);
    state.backtestPayload = payload;
    renderBacktest(payload);
    toast(`${symbol} 백테스트 완료`);
  } catch (error) {
    $("backtestStatus").textContent = "실패";
    $("backtestResults").innerHTML = emptyState(error.message);
    toast(error.message);
  } finally {
    button.disabled = false;
    button.textContent = "실행";
  }
}

function renderBacktest(payload) {
  const summary = payload.summary || {};
  const events = payload.events || [];
  const ruleLabel = payload.rule?.label || BACKTEST_RULE_LABELS[payload.rule_key] || "90일 보유형";
  $("backtestStatus").textContent = `${payload.symbol} · ${ruleLabel} · ${payload.min_score}점 이상`;
  if (payload.rule_key && $("backtestRule")) {
    $("backtestRule").value = payload.rule_key;
    updateBacktestRuleCopy();
  }
  $("backtestSummary").innerHTML = `
    ${backtestSummaryTile("신호 수", summary.signals ?? 0)}
    ${backtestSummaryTile("전략 승률", rateValue(summary.win_rate_rule))}
    ${backtestSummaryTile("전략 평균", percentValue(summary.avg_rule_return), classForNumber(summary.avg_rule_return))}
    ${backtestSummaryTile("평균 MDD", percentValue(summary.avg_rule_mdd), summary.avg_rule_mdd === null || summary.avg_rule_mdd === undefined ? "" : "negative")}
    ${backtestSummaryTile("방어", `${summary.stop_count ?? 0}회`)}
    ${backtestSummaryTile("구조", `${summary.structure_stop_count ?? 0}회`)}
  `;
  $("backtestResults").innerHTML = events.length ? `
    <p class="backtest-note">${escapeHtml(payload.note || "")}</p>
    ${events.map(backtestEventRow).join("")}
  ` : emptyState("조건에 맞는 과거 신호 없음");
}

const BACKTEST_RULE_LABELS = {
  hold90: "90일 보유형",
  growth: "수익형",
  growth_structure: "수익형+구조방어",
  balanced: "균형형",
};

function updateBacktestRuleCopy() {
  const copy = $("backtestRuleCopy");
  if (!copy) return;
  const value = $("backtestRule")?.value || "hold90";
  copy.textContent = BACKTEST_RULE_COPY[value] || BACKTEST_RULE_COPY.hold90;
}

function backtestSummaryTile(label, value, className = "") {
  return `
    <div class="metric-tile">
      <span>${escapeHtml(label)}</span>
      <strong class="${escapeHtml(className)}">${escapeHtml(value)}</strong>
    </div>
  `;
}

function backtestEventRow(event) {
  const score = event.score || {};
  const rule = event.rule_result || {};
  return `
    <article class="backtest-row">
      <div class="backtest-row-top">
        <div>
          <strong>신호 ${escapeHtml(event.date)} · 진입 ${escapeHtml(event.entry_date || "-")} $${fmt(event.entry_price)}</strong>
          <span>RSI ${nullable(event.rsi14)} · VOL ${nullable(event.volume_ratio)}x · ${escapeHtml(rule.exit_reason || "-")} ${escapeHtml(rule.holding_days || "-")}일</span>
        </div>
        <div class="backtest-score">
          <span class="badge" data-level="${escapeHtml(event.alert_level)}">${escapeHtml(score.stage || event.alert_level)}</span>
          <strong>${escapeHtml(score.value ?? "-")}점</strong>
        </div>
      </div>
      <div class="backtest-return-grid">
        ${backtestReturnCell("룰 수익", rule.return_pct)}
        ${backtestValueCell("청산", rule.exit_reason || "-")}
        ${backtestReturnCell("룰 MDD", rule.max_drawdown_pct)}
        ${backtestReturnCell("20D 고정", event.returns?.["20d"])}
        ${backtestReturnCell("60D 고정", event.returns?.["60d"])}
        ${backtestReturnCell("90D 고정", event.returns?.["90d"])}
      </div>
      ${backtestTradeParts(rule)}
      ${backtestStructureReason(rule)}
      ${backtestTags(event)}
    </article>
  `;
}

function backtestReturnCell(label, value) {
  return `
    <div>
      <span>${escapeHtml(label)}</span>
      <strong class="${classForNumber(value)}">${escapeHtml(percentValue(value))}</strong>
    </div>
  `;
}

function backtestValueCell(label, value, className = "") {
  return `
    <div>
      <span>${escapeHtml(label)}</span>
      <strong class="${escapeHtml(className)}">${escapeHtml(value)}</strong>
    </div>
  `;
}

function backtestTradeParts(rule) {
  const parts = rule.parts || [];
  if (!parts.length) return "";
  return `
    <div class="backtest-parts">
      ${parts.map((part) => `<span>${escapeHtml(part.label)} ${escapeHtml(part.sell_pct)}% · ${percentValue(part.return_pct)}</span>`).join("")}
    </div>
  `;
}

function backtestStructureReason(rule) {
  if (!rule.structure_reason) return "";
  return `<div class="backtest-parts"><span>구조 기준 · ${escapeHtml(rule.structure_reason)}</span></div>`;
}

function backtestTags(event) {
  const signalTags = (event.signals || []).map((signal) => SIGNAL_LABELS[signal.type] || signal.type).filter(Boolean);
  const driverTags = (event.drivers || []).map((driver) => {
    const points = Number(driver.points || 0);
    const prefix = points > 0 ? "+" : "";
    return `${SIGNAL_LABELS[driver.type] || driver.type} ${prefix}${points}`;
  });
  const tags = (signalTags.length ? signalTags : driverTags).slice(0, 5);
  if (!tags.length) return "";
  return `<div class="backtest-tags">${tags.map((tag) => `<span>${escapeHtml(tag)}</span>`).join("")}</div>`;
}

function percentValue(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "-";
  return `${signed(value)}%`;
}

function rateValue(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "-";
  return `${Number(value).toFixed(1)}%`;
}

function analysisStamp(payload) {
  const stamp = new Date(payload.generated_at).toLocaleString();
  const elapsed = formatElapsed(payload.elapsed_ms);
  return elapsed ? `${stamp} · ${elapsed}` : stamp;
}

function formatElapsed(value) {
  const ms = Number(value);
  if (!Number.isFinite(ms) || ms <= 0) return "";
  if (ms >= 1000) {
    const seconds = ms / 1000;
    return `분석 ${seconds >= 10 ? seconds.toFixed(0) : seconds.toFixed(1)}초`;
  }
  return `분석 ${Math.round(ms)}ms`;
}

function dataHealthStatusText(payload) {
  const stock = payload.stock || {};
  const vix = payload.vix || {};
  const stockText = stock.ok
    ? `주식 ${stock.data_status?.stale ? "캐시" : "정상"} · ${stock.symbol || "AAPL"} ${stock.bars || 0}개 · ${formatBarTime(stock.latest_time)} · ${dataStatusText(stock.data_status)}`
    : `주식 확인 필요 · ${friendlyDataError(stock.error)}`;
  const vixText = vix.ok
    ? `VIX 정상 · ${vix.value === null || vix.value === undefined ? vix.label || "-" : fmt(vix.value)} · ${vixActualSourceLabel(vix)} · ${vix.freshness_label || "일봉 종가"}`
    : `VIX 확인 필요 · ${friendlyDataError(vix.error)}`;
  return `${stockText} / ${vixText}`;
}

function openStockDetail(symbol, view = "position") {
  const result = findResult(symbol, view);
  if (!result || result.error) {
    toast("상세 데이터를 열 수 없습니다.");
    return;
  }
  state.detailSymbol = symbol;
  state.detailView = view;
  renderStockDetail(result);
  $("stockDetailOverlay").classList.add("active");
  $("stockDetailOverlay").setAttribute("aria-hidden", "false");
  document.body.classList.add("detail-open");
  requestAnimationFrame(() => {
    $("detailCloseButton")?.focus();
  });
}

function closeStockDetail() {
  state.detailSymbol = null;
  state.detailView = null;
  $("stockDetailOverlay").classList.remove("active");
  $("stockDetailOverlay").setAttribute("aria-hidden", "true");
  $("stockDetailSheet").innerHTML = "";
  document.body.classList.remove("detail-open");
}

function currentWatchResults() {
  return state.latestPayload?.watch_results || state.latestPayload?.results || [];
}

function findResult(symbol, view = "position") {
  const source = view === "watch" ? currentWatchResults() : state.latestPayload?.results || [];
  return source.find((item) => item.symbol === symbol);
}

function renderStockDetail(result) {
  const displayLevel = result.position ? result.alert_level : result.score?.stage || result.alert_level || "대기";
  const pulseEdgeChart = state.detailChartMode === "pulseedge";
  const stockMeta = dataSourceMeta({
    provider: result.provider,
    feed: state.latestPayload?.feed,
  });
  $("stockDetailSheet").innerHTML = `
    <div class="detail-header">
      <div>
        <p class="eyebrow">${result.position ? "held position" : "watchlist"}</p>
        <h2 id="detailSymbol">${escapeHtml(result.symbol)} <span class="badge" data-level="${escapeHtml(displayLevel)}">${escapeHtml(displayLevel)}</span></h2>
        <p class="detail-price">$${fmt(result.price)} · 1D ${signed(result.change_pct_1d)}%</p>
      </div>
      <button id="detailCloseButton" class="detail-close" type="button" aria-label="닫기" data-close-detail>×</button>
    </div>

    <div class="detail-chart-zone">
      <div class="detail-chart-source">
        <div class="detail-chart-source-copy">
          <strong>${pulseEdgeChart ? "PulseEdge 분석 차트" : "TradingView 차트 · RSI(14)"}</strong>
          <span>${pulseEdgeChart ? "RSI · 20/60/120일선 · 자동 S/R" : `PulseEdge 계산 ${escapeHtml(stockMeta.short)} 일봉`}</span>
        </div>
        <div class="chart-mode-switch" role="group" aria-label="차트 종류">
          <button type="button" data-detail-chart-mode="tradingview" class="${pulseEdgeChart ? "" : "active"}" aria-pressed="${pulseEdgeChart ? "false" : "true"}">TV</button>
          <button type="button" data-detail-chart-mode="pulseedge" class="${pulseEdgeChart ? "active" : ""}" aria-pressed="${pulseEdgeChart ? "true" : "false"}">S/R</button>
        </div>
      </div>
      <div class="detail-chart-wrap tradingview-chart-wrap" data-tradingview-host data-symbol="${escapeHtml(result.symbol)}">
        <div class="chart-loading" role="status">차트 불러오는 중</div>
      </div>
      ${chartSupportResistanceStrip(result.support_resistance)}
    </div>

    <div class="detail-content-grid">
      <section class="detail-panel">
        <h3>${escapeHtml(result.score?.label || "신호점수")}</h3>
        ${detailScorePanel(result.score)}
      </section>

      <section class="detail-panel">
        <h3>핵심 지표</h3>
        <div class="detail-metrics">
          ${detailMetric("RSI(14)", nullable(result.rsi14))}
          ${detailMetric("5일 등락", `${signed(result.change_pct_5d)}%`, classForNumber(result.change_pct_5d))}
          ${detailMetric("20일 등락", `${signed(result.change_pct_20d)}%`, classForNumber(result.change_pct_20d))}
          ${detailMetric("VOL", `${nullable(result.volume_ratio)}x`)}
          ${detailMetric("20일선 이격", maDistanceText(result, "20"), maDistanceClass(result, "20"))}
          ${detailMetric("60일선 이격", maDistanceText(result, "60"), maDistanceClass(result, "60"))}
          ${detailMetric("120일선 이격", maDistanceText(result, "120"), maDistanceClass(result, "120"))}
        </div>
      </section>

      ${detailPositionPanel(result.position, result)}

      <section class="detail-panel">
        <h3>신호 이유</h3>
        <div class="detail-signal-list">${detailSignalRows(result.signals)}</div>
      </section>

      <section class="detail-panel">
        <h3>최근 흐름</h3>
        <div class="detail-flow">${recentFlowRows(result)}</div>
      </section>
    </div>
    <p class="detail-disclaimer">신호는 참고용입니다. 매수/매도 결정 전 차트, 공시, 기업 상황을 직접 확인하세요.</p>
  `;
  requestAnimationFrame(() => mountDetailChart(result));
}

function mountDetailChart(result) {
  const host = document.querySelector("#stockDetailSheet [data-tradingview-host]");
  if (!host || host.dataset.symbol !== result.symbol) return;
  if (state.detailChartMode === "pulseedge") {
    renderPulseEdgeFallbackChart(host, result, "analysis");
    return;
  }
  mountTradingViewChart(result);
}

function mountTradingViewChart(result) {
  const host = document.querySelector("#stockDetailSheet [data-tradingview-host]");
  if (!host || host.dataset.symbol !== result.symbol) return;

  const widgetSymbol = tradingViewSymbol(result.symbol);
  const mountId = `${result.symbol}-${Date.now()}-${Math.random().toString(36).slice(2)}`;
  host.dataset.mountId = mountId;
  host.innerHTML = `
    <div class="tradingview-widget-container">
      <div class="tradingview-widget-container__widget"></div>
      <div class="tradingview-widget-copyright">
        <a href="${escapeHtml(tradingViewAttributionUrl(widgetSymbol))}" rel="noopener nofollow" target="_blank"><span class="blue-text">${escapeHtml(result.symbol)} 차트</span></a><span class="trademark"> by TradingView</span>
      </div>
    </div>
  `;

  const container = host.querySelector(".tradingview-widget-container");
  const script = document.createElement("script");
  script.src = TRADINGVIEW_WIDGET_URL;
  script.type = "text/javascript";
  script.async = true;
  script.textContent = JSON.stringify({
    autosize: true,
    symbol: widgetSymbol,
    interval: chartPref(result.symbol).timeframe === "W" ? "W" : "D",
    timezone: "exchange",
    theme: "dark",
    backgroundColor: "rgba(15, 18, 22, 1)",
    style: "1",
    locale: "kr",
    withdateranges: true,
    hide_side_toolbar: false,
    allow_symbol_change: true,
    save_image: false,
    studies: ["RSI@tv-basicstudies"],
    calendar: false,
    support_host: "https://www.tradingview.com",
  });

  let settled = false;
  const showFallback = () => {
    if (settled || !document.contains(host) || host.dataset.mountId !== mountId) return;
    settled = true;
    renderPulseEdgeFallbackChart(host, result);
  };
  const confirmWidget = () => {
    window.setTimeout(() => {
      if (!document.contains(host) || host.dataset.mountId !== mountId) return;
      if (host.querySelector("iframe")) {
        settled = true;
      } else {
        showFallback();
      }
    }, 5000);
  };

  script.addEventListener("load", confirmWidget, { once: true });
  script.addEventListener("error", showFallback, { once: true });
  container.appendChild(script);
  window.setTimeout(showFallback, 12000);
}

function tradingViewSymbol(symbol) {
  const normalized = String(symbol || "").trim().toUpperCase().replace(".", "_");
  if (!normalized || normalized.includes(":")) return normalized;
  const exchange = TRADINGVIEW_EXCHANGE_BY_SYMBOL[normalized];
  return exchange ? `${exchange}:${normalized}` : normalized;
}

function tradingViewAttributionUrl(widgetSymbol) {
  const pathSymbol = widgetSymbol.replace(":", "-");
  return `https://www.tradingview.com/symbols/${encodeURIComponent(pathSymbol)}/?utm_source=pulseedge&utm_medium=widget&utm_campaign=advanced-chart`;
}

function renderPulseEdgeFallbackChart(host, result, reason = "fallback") {
  const pref = chartPref(result.symbol);
  host.classList.add("is-fallback");
  host.innerHTML = `
    <div class="chart-fallback-note">${reason === "analysis" ? "PulseEdge 계산 차트 · 자동 S/R 표시" : "TradingView 연결 실패 · PulseEdge 기본 차트"}</div>
    <div class="chart-toolbar detail-toolbar">
      <div class="chart-control-group">
        ${chartButton(result.symbol, "timeframe", "D", "일", pref.timeframe === "D")}
        ${chartButton(result.symbol, "timeframe", "W", "주", pref.timeframe === "W")}
      </div>
      <div class="chart-control-group">
        ${["3M", "6M", "1Y", "ALL"].map((range) => chartButton(result.symbol, "range", range, rangeLabel(range), pref.range === range && !pref.customCount)).join("")}
      </div>
      ${chartOverlayButtons(result.symbol)}
    </div>
    <div class="fallback-canvas-wrap">
      <canvas data-symbol="${escapeHtml(result.symbol)}" data-view="${result.position ? "position" : "watch"}" width="1120" height="620"></canvas>
    </div>
  `;
  const canvas = host.querySelector("canvas");
  drawTradingChart(canvas, result);
  attachChartInteractions(canvas, result);
}

function detailMetric(label, value, className = "") {
  return `
    <div>
      <span>${escapeHtml(label)}</span>
      <strong class="${escapeHtml(className)}">${escapeHtml(value)}</strong>
    </div>
  `;
}

function detailScorePanel(score) {
  if (!score) {
    return '<p class="detail-muted">점수 데이터 없음</p>';
  }
  return `
    <div class="detail-score-box" data-mode="${escapeHtml(score.mode)}">
      <div class="detail-score-top">
        <strong>${escapeHtml(score.value)}점</strong>
        <span>${escapeHtml(score.stage)}</span>
      </div>
      ${scoreBar(score)}
      ${positionScoreComponents(score, false)}
      <div class="score-drivers">${scoreDriverRows(score.drivers)}</div>
    </div>
  `;
}

function scoreText(score) {
  if (!score) return "-";
  return `${score.value}점`;
}

function scoreBar(score) {
  const value = clamp(Number(score?.value || 0), 0, 100);
  return `<div class="score-bar" aria-label="${escapeHtml(score?.label || "신호점수")} ${value}점"><span style="width:${value}%"></span></div>`;
}

function scoreDriverRows(drivers = []) {
  if (!drivers.length) return '<span class="score-driver">근거 없음</span>';
  return drivers.slice(0, 4).map((driver) => `
    <span class="score-driver" data-direction="${driver.points >= 0 ? "plus" : "minus"}">
      ${escapeHtml(SIGNAL_LABELS[driver.type] || driver.type)} ${driver.points >= 0 ? "+" : ""}${escapeHtml(driver.points)}
    </span>
  `).join("");
}

function positionScoreComponents(score, compact = false) {
  const components = score?.components || [];
  if (!components.length) return "";
  return `
    <div class="${compact ? "score-components compact" : "score-components"}">
      ${components.map((component) => `
        <div class="score-component" data-key="${escapeHtml(component.key)}">
          <span>${escapeHtml(component.label)}</span>
          <strong>${escapeHtml(component.value)}점</strong>
          <em>${escapeHtml(component.stage)}</em>
          ${compact ? "" : componentDriverList(component)}
        </div>
      `).join("")}
    </div>
  `;
}

function componentDriverList(component) {
  const drivers = component.drivers || [];
  if (!drivers.length) {
    return '<small>특이 신호 없음</small>';
  }
  return `
    <small>
      ${drivers.slice(0, 2).map((driver) =>
        `${escapeHtml(SIGNAL_LABELS[driver.type] || driver.type)} ${driver.points >= 0 ? "+" : ""}${escapeHtml(driver.points)}`
      ).join(" · ")}
    </small>
  `;
}

function maState(result, period) {
  const value = result.sma?.[period];
  if (value === null || value === undefined) return "-";
  return result.price >= value ? "위" : "아래";
}

function maDistanceValue(result, period) {
  const value = result.ma_distance_pct?.[period];
  if (value === null || value === undefined || Number.isNaN(Number(value))) return null;
  return Number(value);
}

function maDistanceText(result, period) {
  const value = maDistanceValue(result, period);
  return value === null ? "-" : `${signed(value)}%`;
}

function maDistanceClass(result, period) {
  const value = maDistanceValue(result, period);
  return value === null ? "" : classForNumber(value);
}

function chartSupportResistanceStrip(levels) {
  const support = levels?.nearest_support;
  const resistance = levels?.nearest_resistance;
  if (!support && !resistance) return "";
  const scopeLabel = levels?.scope_label || "최근 180일";
  return `
    <div class="chart-sr-strip">
      <strong>PulseEdge S/R</strong>
      <span class="chart-sr-scope">${escapeHtml(scopeLabel)}</span>
      ${support ? chartSrChip("support", support) : ""}
      ${resistance ? chartSrChip("resistance", resistance) : ""}
    </div>
  `;
}

function chartSrChip(kind, level) {
  return `
    <span class="chart-sr-chip" data-kind="${escapeHtml(kind)}">
      ${escapeHtml(level.label || (kind === "support" ? "S" : "R"))}
      $${fmt(level.price)}
      <em>${signed(level.distance_pct)}%</em>
    </span>
  `;
}

function detailSupportResistancePanel(levels) {
  const supports = levels?.supports || [];
  const resistances = levels?.resistances || [];
  const scopeLabel = levels?.scope_label || "최근 180일";
  return `
    <section class="detail-panel">
      <div class="panel-title-row">
        <h3>자동 지지/저항</h3>
        <span>${escapeHtml(scopeLabel)}</span>
      </div>
      <div class="sr-grid">
        ${supportResistanceRows("지지", supports)}
        ${supportResistanceRows("저항", resistances)}
      </div>
    </section>
  `;
}

function supportResistanceRows(title, levels) {
  if (!levels.length) {
    return `
      <div class="sr-column">
        <strong>${escapeHtml(title)}</strong>
        <p class="detail-muted">감지 없음</p>
      </div>
    `;
  }
  return `
    <div class="sr-column">
      <strong>${escapeHtml(title)}</strong>
      ${levels.slice(0, 3).map((level) => `
        <div class="sr-level" data-kind="${escapeHtml(level.kind)}">
          <span>${escapeHtml(level.label || "")}</span>
          <b>$${fmt(level.price)}</b>
          <em>${signed(level.distance_pct)}% · ${escapeHtml(level.strength)}강</em>
        </div>
      `).join("")}
    </div>
  `;
}

function detailPositionPanel(position, result = {}) {
  if (!position) {
    return `
      <section class="detail-panel">
        <h3>관심 상태</h3>
        <p class="detail-muted">일반 진입점수 기준</p>
      </section>
    `;
  }
  if (position.missing_average_entry) {
    return `
      <section class="detail-panel">
        <h3>보유 정보</h3>
        <p class="detail-muted">평단가 입력 필요</p>
      </section>
    `;
  }
  return `
    <section class="detail-panel">
      <h3>보유 정보</h3>
      ${positionGuardrails(result)}
      <div class="detail-position-grid">
        ${detailMetric("평단", `$${fmt(position.average_entry_price)}`)}
        ${detailMetric("수익률", `${signed(position.return_pct)}%`, classForNumber(position.return_pct))}
        ${detailMetric("고점대비", `${signed(position.drawdown_from_high_pct)}%`, classForNumber(position.drawdown_from_high_pct))}
        ${detailMetric("상태", normalizeSignalLevel(position.suggested_action || "보유점검"))}
      </div>
    </section>
  `;
}

function detailSignalRows(signals) {
  if (!signals?.length) {
    return '<p class="detail-muted">신호 없음</p>';
  }
  return signals.map((signal) => `
    <article class="detail-signal-row" data-level="${escapeHtml(signal.level)}">
      <div>
        <strong>${escapeHtml(SIGNAL_LABELS[signal.type] || signal.type)}</strong>
        <span>${escapeHtml(signal.message)}</span>
      </div>
      <small>${escapeHtml(DELIVERY_LABELS[signal.delivery] || signal.delivery)}</small>
    </article>
  `).join("");
}

function recentFlowRows(result) {
  const bars = result.bars || [];
  const latest = bars[bars.length - 1];
  if (!latest) return '<p class="detail-muted">데이터 부족</p>';
  const stockMeta = dataSourceMeta({
    provider: result.provider,
    feed: state.latestPayload?.feed,
  });
  const rows = [
    ["최근 종가", `$${fmt(latest.close)}`],
    ["마지막 봉", formatBarTime(result.last_bar || latest.time)],
    ["20일선", latest.sma20 ? `$${fmt(latest.sma20)} · ${maDistanceText(result, "20")}` : "-"],
    ["60일선", latest.sma60 ? `$${fmt(latest.sma60)} · ${maDistanceText(result, "60")}` : "-"],
    ["120일선", latest.sma120 ? `$${fmt(latest.sma120)} · ${maDistanceText(result, "120")}` : "-"],
    ["MACD", latest.macd === null || latest.macd === undefined ? "-" : `${Number(latest.macd).toFixed(2)} / ${latest.macd_signal === null || latest.macd_signal === undefined ? "-" : Number(latest.macd_signal).toFixed(2)}`],
    ["데이터 기준", stockMeta.short],
    ["데이터 상태", dataStatusText(result.data_status)],
    ["데이터 갱신", formatRefreshTime(result.data_status?.fetched_at)],
  ];
  return rows.map(([label, value]) => `
    <div class="flow-row">
      <span>${escapeHtml(label)}</span>
      <strong>${escapeHtml(value)}</strong>
    </div>
  `).join("");
}

function cssEscape(value) {
  if (window.CSS?.escape) return CSS.escape(value);
  return String(value).replace(/[^a-zA-Z0-9_-]/g, "\\$&");
}

async function saveConfig(options = {}) {
  if (typeof Event !== "undefined" && options instanceof Event) {
    options = {};
  }
  const toastMessage = Object.prototype.hasOwnProperty.call(options, "toastMessage")
    ? options.toastMessage
    : "설정 저장 완료";
  try {
    const previousDataKey = dataConfigKey(state.config);
    const payload = await apiPost("/api/config", readForm());
    if (previousDataKey !== dataConfigKey(payload.config)) {
      state.dataHealth = null;
    }
    state.config = payload.config;
    state.signalGroups = payload.signal_groups || state.signalGroups;
    state.credentials = payload.credentials || state.credentials;
    state.profile = payload.profile || state.profile;
    renderAccountPanel();
    renderSettings(payload.config);
    $("providerStatus").textContent = providerText(payload);
    updateDataStatus(dataStatusFromConfig(payload.config, state.credentials));
    scheduleRefresh();
    if (toastMessage) {
      toast(toastMessage);
    }
    await analyze();
  } catch (error) {
    toast(error.message);
  }
}

async function analyze() {
  $("analyzeButton").disabled = true;
  $("analyzeButton").textContent = "분석 중";
  if ($("lastUpdated")) {
    $("lastUpdated").textContent = "분석 중...";
  }
  try {
    const payload = await apiGet("/api/analyze");
    state.latestPayload = payload;
    renderDashboard(payload);
    processSignals(payload);
  } catch (error) {
    updateDataStatus({
      level: "error",
      title: "분석 실패",
      message: friendlyDataError(error.message),
      items: ["서버 실행 상태 확인", "네트워크 확인", "공개 시세 공급원 상태 확인"],
    });
    toast(error.message);
  } finally {
    $("analyzeButton").disabled = false;
    $("analyzeButton").textContent = "분석";
  }
}

function scheduleRefresh() {
  if (state.refreshTimer) {
    clearInterval(state.refreshTimer);
  }
  const minutes = Number(state.config?.alerts?.auto_refresh_minutes || 30);
  state.refreshTimer = setInterval(analyze, minutes * 60 * 1000);
}

function renderDashboard(payload) {
  updateDataStatus(dataStatusFromPayload(payload));
  $("providerStatus").textContent = providerText(payload);
  renderDataHealthOverview(state.config, state.credentials, state.dataHealth);
  renderMarket(payload.market, payload);
  renderCounts(payload.watch_results || payload.results);
  renderHomeLists(payload);
  renderCards(payload.results, payload.watch_results || payload.results);
  $("lastUpdated").textContent = analysisStamp(payload);
}

function renderMarket(market, payload = {}) {
  const host = $("marketPanel");
  if (!market) {
    host.innerHTML = "";
    return;
  }
  const vix = market.vix || null;
  const stockMeta = dataSourceMeta(payload);
  const freshnessText = dataFreshnessSummaryText(payload.data_freshness);
  host.innerHTML = `
    <article class="market-card">
      <div class="market-top">
        <div>
          <h2>시장 상태</h2>
          <p>${escapeHtml(market.summary)}</p>
        </div>
        <span class="badge" data-level="${escapeHtml(market.level)}">${escapeHtml(market.label)}</span>
      </div>
      ${vix ? vixPanel(vix) : ""}
      <div class="metrics market-metrics">
        <div><span>SPY 120일선</span><strong class="${classForNumber(market.spy_ma120_distance_pct)}">${trendPctText(market.spy_ma120_distance_pct)}</strong></div>
        <div><span>QQQ 120일선</span><strong class="${classForNumber(market.qqq_ma120_distance_pct)}">${trendPctText(market.qqq_ma120_distance_pct)}</strong></div>
        <div><span>모드</span><strong>${escapeHtml(market.regime)}</strong></div>
        <div><span>신호</span><strong>${market.signals?.length || 0}</strong></div>
      </div>
      <p class="market-source data-source-note">주식 ${escapeHtml(stockMeta.short)}${freshnessText ? ` · ${escapeHtml(freshnessText)}` : ""} · ${escapeHtml(stockMeta.note)}</p>
    </article>
  `;
}

function vixPanel(vix) {
  const thresholds = normalizedVixThresholds(vix.thresholds);
  return `
    <div class="vix-panel" data-level="${escapeHtml(vix.level)}" style="--vix-pos: ${vixGaugePosition(vix.value, thresholds)}%;">
      <div class="vix-top">
        <div class="vix-value">
          <span>VIX</span>
          <strong>${Number(vix.value).toFixed(1)}</strong>
        </div>
        <div class="vix-state">
          <strong>${escapeHtml(vix.label)}</strong>
          <span class="${classForVixChange(vix.change_pct_5d)}">${vix.change_pct_5d === null || vix.change_pct_5d === undefined ? "-" : `${signed(vix.change_pct_5d)}% 5D`}</span>
        </div>
      </div>
      <div class="vix-meter" aria-label="PulseEdge VIX 기준 게이지">
        <span class="vix-pointer"></span>
      </div>
      <div class="vix-scale">
        <span>보통 &lt;${fmtThreshold(thresholds.elevated)}</span>
        <span>주의 ${fmtThreshold(thresholds.elevated)}~${fmtThreshold(thresholds.fear)}</span>
        <span>공포 ${fmtThreshold(thresholds.fear)}~${fmtThreshold(thresholds.panic)}</span>
        <span>극단 ${fmtThreshold(thresholds.panic)}+</span>
      </div>
      <p class="vix-standard">PulseEdge 기준 · 공식 등급이 아닌 시장 해석용 구간</p>
      <p class="market-source">VIX ${escapeHtml(vix.freshness_label || vix.latest_time || "-")} · ${escapeHtml(vix.data_note || vix.source || "-")}</p>
    </div>
  `;
}

function normalizedVixThresholds(thresholds = {}) {
  const elevated = Number(thresholds.elevated) || 20;
  const fear = Math.max(elevated, Number(thresholds.fear) || 30);
  const panic = Math.max(fear, Number(thresholds.panic) || 40);
  return { elevated, fear, panic };
}

function fmtThreshold(value) {
  return Number.isInteger(value) ? String(value) : Number(value).toFixed(1);
}

function vixGaugePosition(value, thresholds = {}) {
  const { elevated, fear, panic } = normalizedVixThresholds(thresholds);
  const normalSpan = Math.max(fear - elevated, 10);
  const lower = Math.max(0, elevated - normalSpan);
  const upper = panic + Math.max(panic - fear, 10);
  const numericValue = Number(value);
  if (!Number.isFinite(numericValue)) return "0.0";

  const bands = [lower, elevated, fear, panic, upper];
  for (let index = 0; index < bands.length - 1; index += 1) {
    if (numericValue <= bands[index + 1]) {
      const bandProgress = (numericValue - bands[index]) / Math.max(bands[index + 1] - bands[index], 1);
      return clamp((index + bandProgress) * 25, 0, 100).toFixed(1);
    }
  }
  return "100.0";
}

function trendText(value) {
  if (value === true) return "위";
  if (value === false) return "아래";
  return "-";
}

function trendPctText(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "-";
  return `${signed(value)}%`;
}

function classForVixChange(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "";
  return Number(value) > 0 ? "negative" : "positive";
}

function renderCounts(results) {
  const counts = { 대기: 0, 관심: 0, 기회: 0, 주의: 0, 위험: 0 };
  for (const result of results) {
    if (result.error) {
      counts.위험 += 1;
      continue;
    }
    const bucket = watchCountBucket(result);
    if (bucket === "기회") {
      counts.기회 += 1;
    } else if (bucket === "관심") {
      counts.관심 += 1;
    } else if (bucket === "주의") {
      counts.주의 += 1;
    } else if (bucket === "위험") {
      counts.위험 += 1;
    } else {
      counts.대기 += 1;
    }
  }
  $("countNormal").textContent = counts.대기;
  $("countInterest").textContent = counts.관심;
  $("countOpportunity").textContent = counts.기회;
  $("countCaution").textContent = counts.주의;
  $("countDanger").textContent = counts.위험;
}

function watchCountBucket(result) {
  const stage = result.score?.stage || "";
  const level = result.alert_level || "";
  if (["위험", "오류"].includes(level) || stage === "진입금지") return "위험";
  if (["주의", "수익관리", "수익보호검토", "익절검토", "방어검토", "판매검토"].includes(level) || stage === "주의") return "주의";
  if (["진입검토", "매수검토"].includes(stage) || ["기회후보", "돌파후보"].includes(level)) return "기회";
  if (["자리검토", "반등체크", "관찰"].includes(stage) || ["공포관심", "관심", "반등후보"].includes(level)) return "관심";
  return "대기";
}

function renderHomeLists(payload) {
  const watchResults = payload.watch_results || payload.results || [];
  const todayPicks = rankTodayPicks(watchResults, payload.market);
  const alertDigest = buildAlertDigest(payload);
  const opportunities = watchResults
    .filter((result) => !result.error && isWatchReviewResult(result))
    .slice(0, 5);
  if ($("todayPicks")) {
    $("todayPickCount").textContent = todayPicks.length ? `상위 ${todayPicks.length}개` : "대기";
    $("todayPicks").innerHTML = todayPicks.length ? todayPicks.map(todayPickCard).join("") : emptyState("오늘 볼 종목 없음");
  }
  $("topAlerts").innerHTML = renderAlertDigest(alertDigest);
  $("opportunityList").innerHTML = opportunities.length ? opportunities.map((result) => `
    <article class="compact-item">
      <strong>${escapeHtml(result.symbol)} · ${escapeHtml(watchReviewLabel(result))}</strong>
      <p>${escapeHtml(result.summary)}</p>
    </article>
  `).join("") : emptyState("진입 관찰 없음");
}

function isWatchReviewResult(result) {
  const score = numberOrZero(result.score?.value);
  const stage = result.score?.stage || "";
  const level = result.alert_level || "";
  return (
    score >= 55 ||
    ["관찰", "반등체크", "자리검토", "진입검토"].includes(stage) ||
    ["관심", "공포관심", "반등후보", "기회후보", "돌파후보"].includes(level)
  );
}

function watchReviewLabel(result) {
  const stage = result.score?.stage || "";
  if (stage) return stage;
  return result.alert_level || "대기";
}

function rankTodayPicks(results, market) {
  return [...results]
    .filter((result) => !result.error)
    .map((result) => ({
      result,
      rankScore: todayPickRankScore(result, market),
      action: todayPickAction(result, market),
    }))
    .sort((a, b) =>
      compareDesc(a.rankScore, b.rankScore) ||
      compareDesc(numberOrZero(a.result.score?.value), numberOrZero(b.result.score?.value)) ||
      String(a.result.symbol).localeCompare(String(b.result.symbol))
    )
    .slice(0, 3);
}

function todayPickRankScore(result, market) {
  const score = numberOrZero(result.score?.value);
  const levelBonus = {
    돌파후보: 8,
    기회후보: 8,
    반등후보: 5,
    공포관심: 3,
    관심: 2,
  };
  let rank = score + (levelBonus[result.alert_level] || 0);
  const rsi = Number(result.rsi14);
  if (Number.isFinite(rsi)) {
    if (rsi >= 75) rank -= 16;
    else if (rsi >= 70) rank -= 10;
    else if (rsi >= 65) rank -= 5;
    else if (rsi >= 40) rank += 5;
    else if (rsi >= 30) rank += 7;
    else if (rsi >= 25) rank += 5;
    else rank += 2;
  }
  const volume = Number(result.volume_ratio);
  if (Number.isFinite(volume)) {
    if (volume >= 2) rank += 5;
    else if (volume >= 1.5) rank += 4;
    else if (volume >= 1.2) rank += 2;
  }
  const signalTypes = new Set((result.signals || []).map((signal) => signal.type));
  if (signalTypes.has("VOLUME_CONFIRMED_BREAKOUT")) rank += 6;
  if (signalTypes.has("BULLISH_VOLUME_SPIKE")) rank += 5;
  if (signalTypes.has("BEARISH_VOLUME_SPIKE")) rank += Number.isFinite(rsi) && rsi < 45 ? 3 : -3;
  if (signalTypes.has("ICHIMOKU_CLOUD_RECOVERY")) rank += 4;
  if (signalTypes.has("ICHIMOKU_CLOUD_BREAKDOWN")) rank -= 5;

  const supportDistance = nearestDistance(result, "nearest_support");
  if (supportDistance <= 2) rank += 7;
  else if (supportDistance <= 4) rank += 5;
  else if (supportDistance <= 7) rank += 2;

  const resistanceDistance = nearestDistance(result, "nearest_resistance");
  if (resistanceDistance <= 1.5) rank -= 10;
  else if (resistanceDistance <= 3) rank -= 5;

  if (isMarketRiskOff(market)) rank -= 6;
  return clamp(Math.round(rank), 0, 100);
}

function todayPickAction(result, market) {
  const score = numberOrZero(result.score?.value);
  const rsi = Number(result.rsi14);
  const resistanceDistance = nearestDistance(result, "nearest_resistance");
  if (resistanceDistance <= 1.5 || (Number.isFinite(rsi) && rsi >= 70)) {
    return { label: "추격주의", kind: "caution" };
  }
  if (isMarketRiskOff(market) && score < 85) {
    return { label: "시장확인", kind: "caution" };
  }
  if (score >= 85) {
    return { label: "진입검토", kind: "buy" };
  }
  if (score >= 70) {
    return { label: "자리검토", kind: "confirm" };
  }
  if (score >= 62) {
    return { label: "반등체크", kind: "confirm" };
  }
  if (score >= 55) {
    return { label: "관찰", kind: "watch" };
  }
  return { label: "대기", kind: "wait" };
}

function todayPickCard(item, index) {
  const result = item.result;
  const support = result.support_resistance?.nearest_support;
  const resistance = result.support_resistance?.nearest_resistance;
  const displayScore = clamp(numberOrZero(result.score?.value), 0, 100);
  const driver = todayPickDriver(result);
  return `
    <article class="today-pick stock-card" data-level="${escapeHtml(item.action.label)}" data-symbol="${escapeHtml(result.symbol)}" data-view="watch">
      <div class="today-pick-rank">#${index + 1}</div>
      <div class="today-pick-body">
        <div class="today-pick-top">
          <div>
            <strong>${escapeHtml(result.symbol)}</strong>
            <span>$${fmt(result.price)} · 1D ${signed(result.change_pct_1d)}%</span>
          </div>
          <div class="today-pick-status">
            <span data-kind="${escapeHtml(item.action.kind)}">${escapeHtml(item.action.label)}</span>
            <strong>${escapeHtml(scoreText(result.score))}</strong>
          </div>
        </div>
        <div class="today-pick-meter" aria-label="진입점수 ${escapeHtml(displayScore)}점"><span style="width:${displayScore}%"></span></div>
        <p>${escapeHtml(driver)}</p>
        <div class="today-pick-tags">
          <span>RSI ${nullable(result.rsi14)}</span>
          <span>VOL ${nullable(result.volume_ratio)}x</span>
          ${support ? `<span>S1 ${signed(support.distance_pct)}%</span>` : ""}
          ${resistance ? `<span>R1 ${signed(resistance.distance_pct)}%</span>` : ""}
        </div>
      </div>
    </article>
  `;
}

function todayPickDriver(result) {
  const driver = result.score?.drivers?.[0];
  if (driver) {
    return `${SIGNAL_LABELS[driver.type] || driver.type} ${driver.points >= 0 ? "+" : ""}${driver.points}점이 가장 크게 반영됐습니다.`;
  }
  if (result.signals?.length) {
    return result.signals[0].message;
  }
  return result.score?.stage ? `${result.score.stage} 구간입니다. 상세 차트에서 자리 확인이 필요합니다.` : "뚜렷한 신호는 약하고 대기 관찰이 우선입니다.";
}

function isMarketRiskOff(market) {
  return market?.regime === "risk_off" || market?.level === "위험";
}

function compactSignalItem(item) {
  return `
    <article class="compact-item">
      <strong>${escapeHtml(item.symbol)} · ${escapeHtml(SIGNAL_LABELS[item.type] || item.type)}</strong>
      <p>${escapeHtml(item.message)}</p>
    </article>
  `;
}

function renderCards(results, watchResults = results) {
  const held = results.filter((result) => !result.error && result.position);
  const watchlist = watchResults.filter((result) => !result.error);
  const errors = watchResults.filter((result) => result.error);
  const visibleWatchlist = sortWatchlist(filterWatchlist(watchlist));
  const visibleErrors = state.watchFilter === "all" ? errors : [];
  $("watchlistCount").textContent = visibleWatchlist.length === watchlist.length ? `${watchlist.length}개` : `${visibleWatchlist.length}/${watchlist.length}개`;
  $("positionCount").textContent = `${held.length}개`;
  $("watchlistCards").innerHTML = visibleWatchlist.length || visibleErrors.length ? [...visibleWatchlist, ...visibleErrors].map((result) => stockCard(result, "watch")).join("") : emptyState("필터에 맞는 종목 없음");
  $("positionCards").innerHTML = held.length ? held.map((result) => stockCard(result, "position")).join("") : emptyState("보유종목 없음");
  if (state.detailSymbol) {
    const detailResult = findResult(state.detailSymbol, state.detailView || "position");
    if (detailResult && !detailResult.error) {
      renderStockDetail(detailResult);
    } else {
      closeStockDetail();
    }
  }
  requestAnimationFrame(() => {
    [...document.querySelectorAll("canvas[data-symbol]")].forEach((canvas) => {
      const result = results.find((item) => item.symbol === canvas.dataset.symbol);
      if (result && !result.error) {
        drawTradingChart(canvas, result);
        attachChartInteractions(canvas, result);
      }
    });
  });
}

function filterWatchlist(results) {
  return results.filter((result) => {
    const held = Boolean(result.position);
    const stage = result.score?.stage || "";
    const level = result.alert_level || "";
    const score = Number(result.score?.value || 0);
    switch (state.watchFilter) {
      case "buy":
        if (held) return false;
        return score >= 85 || ["기회후보", "돌파후보"].includes(level) || ["진입검토", "매수검토"].includes(stage);
      case "rebound":
        if (held) return false;
        return (score >= 62 && score < 70) || level === "반등후보" || stage === "반등체크";
      case "interest":
        if (held) return false;
        return (score >= 55 && score < 85) || ["관심", "공포관심"].includes(level) || ["관찰", "자리검토"].includes(stage);
      case "caution":
        return held ? score >= 60 || ["주의", "수익보호검토", "익절검토", "방어검토", "판매검토", "위험", "수익관리"].includes(level) : score < 45 || ["주의", "위험"].includes(level) || ["주의", "진입금지"].includes(stage);
      case "hide_waiting":
        return held || !["대기", "정상"].includes(level) || score >= 55;
      default:
        return true;
    }
  });
}

function sortWatchlist(results) {
  const sorted = [...results];
  sorted.sort((a, b) => {
    let value = 0;
    switch (state.watchSort) {
      case "support_near":
        value = compareAsc(nearestDistance(a, "nearest_support"), nearestDistance(b, "nearest_support"));
        break;
      case "resistance_near":
        value = compareAsc(nearestDistance(a, "nearest_resistance"), nearestDistance(b, "nearest_resistance"));
        break;
      case "rsi_low":
        value = compareAsc(numberOrInfinity(a.rsi14), numberOrInfinity(b.rsi14));
        break;
      case "volume_high":
        value = compareDesc(numberOrNegativeInfinity(a.volume_ratio), numberOrNegativeInfinity(b.volume_ratio));
        break;
      case "change_abs":
        value = compareDesc(Math.abs(numberOrZero(a.change_pct_1d)), Math.abs(numberOrZero(b.change_pct_1d)));
        break;
      case "symbol_asc":
        value = 0;
        break;
      case "score_desc":
      default:
        value = compareDesc(numberOrZero(a.score?.value), numberOrZero(b.score?.value));
        break;
    }
    return value || String(a.symbol).localeCompare(String(b.symbol));
  });
  return sorted;
}

function compareAsc(a, b) {
  return a - b;
}

function compareDesc(a, b) {
  return b - a;
}

function numberOrZero(value) {
  const number = Number(value);
  return Number.isFinite(number) ? number : 0;
}

function numberOrInfinity(value) {
  const number = Number(value);
  return Number.isFinite(number) ? number : Number.POSITIVE_INFINITY;
}

function numberOrNegativeInfinity(value) {
  const number = Number(value);
  return Number.isFinite(number) ? number : Number.NEGATIVE_INFINITY;
}

function nearestDistance(result, key) {
  const distance = result.support_resistance?.[key]?.distance_pct;
  const number = Math.abs(Number(distance));
  return Number.isFinite(number) ? number : Number.POSITIVE_INFINITY;
}

function stockCard(result, view = "position") {
  if (result.error) {
    const friendly = friendlyDataError(result.error);
    return `
      <article class="stock-card" data-level="오류">
        <div class="card-top">
          <div>
            <h3 class="symbol">${escapeHtml(result.symbol)}</h3>
            <p class="price error">${escapeHtml(friendly)}</p>
            <p class="summary data-error-note">${escapeHtml(dataErrorHint(result.error))}</p>
          </div>
          <span class="badge" data-level="오류">데이터 오류</span>
        </div>
      </article>
    `;
  }
  const position = result.position;
  const heldInConfig = view === "watch" && isHeldConfigSymbol(result.symbol);
  const decision = position && !position.missing_average_entry ? positionManagementDecision(position, result) : null;
  const displayLevel = decision?.tone || cardDisplayLevel(result, view);
  const badgeLabel = decision?.label || displayLevel;
  const quickRemoveTitle = isProtectedMarketSymbol(result.symbol)
    ? "시장 필터 종목은 유지됩니다"
    : heldInConfig
      ? "보유종목은 Hold에서 보유 해제 후 삭제"
      : "관심목록 삭제";
  const quickRemoveAriaLabel = `${result.symbol} ${quickRemoveTitle}`;
  return `
    <article class="stock-card compact-stock-card" data-level="${escapeHtml(displayLevel)}" data-symbol="${escapeHtml(result.symbol)}" data-view="${escapeHtml(view)}">
      <div class="card-top">
        <div>
          <h3 class="symbol">
            ${escapeHtml(result.symbol)}
            ${position ? '<span class="held-pill">보유</span>' : ""}
            ${heldInConfig ? '<span class="watch-basis-pill">관심기준</span>' : ""}
          </h3>
          <p class="price">$${fmt(result.price)} · 1D ${signed(result.change_pct_1d)}%</p>
        </div>
        <div class="card-status">
          ${view === "watch" ? `<button class="quick-remove-symbol" type="button" data-symbol="${escapeHtml(result.symbol)}" title="${escapeHtml(quickRemoveTitle)}" aria-label="${escapeHtml(quickRemoveAriaLabel)}">×</button>` : ""}
          <span class="badge" data-level="${escapeHtml(displayLevel)}">${escapeHtml(badgeLabel)}</span>
          <strong class="score-value">${escapeHtml(position ? `관리 ${scoreText(result.score)}` : scoreText(result.score))}</strong>
        </div>
      </div>
      ${scoreStrip(result.score)}
      ${positionScoreComponents(result.score, true)}
      ${positionPanel(position, result)}
      <div class="metrics">
        <div><span>RSI</span><strong>${nullable(result.rsi14)}</strong></div>
        <div><span>5일등락</span><strong class="${classForNumber(result.change_pct_5d)}">${signed(result.change_pct_5d)}%</strong></div>
        <div><span>20일등락</span><strong class="${classForNumber(result.change_pct_20d)}">${signed(result.change_pct_20d)}%</strong></div>
        <div><span>VOL</span><strong>${nullable(result.volume_ratio)}x</strong></div>
      </div>
      ${compactSupportResistance(result.support_resistance)}
      <p class="summary">${escapeHtml(cardSummary(result))}</p>
      <div class="signals">${signalChips(result.signals, 4)}</div>
    </article>
  `;
}

function cardDisplayLevel(result, view = "position") {
  if (view === "watch") {
    return result.score?.stage || result.alert_level || "대기";
  }
  return result.alert_level || result.score?.stage || "대기";
}

function compactSupportResistance(levels) {
  const support = levels?.nearest_support;
  const resistance = levels?.nearest_resistance;
  if (!support && !resistance) return "";
  const scopeLabel = levels?.scope_label || "최근 180일";
  return `
    <div class="compact-sr">
      <span class="sr-scope">${escapeHtml(scopeLabel)}</span>
      ${support ? compactSrItem("support", support) : ""}
      ${resistance ? compactSrItem("resistance", resistance) : ""}
    </div>
  `;
}

function compactSrItem(kind, level) {
  return `
    <span data-kind="${escapeHtml(kind)}">
      <b>${escapeHtml(level.label || (kind === "support" ? "S" : "R"))}</b>
      $${fmt(level.price)}
      <em>${signed(level.distance_pct)}%</em>
    </span>
  `;
}

function cardSummary(result) {
  if (result.signals?.length) {
    return result.signals.slice(0, 2).map((signal) => signal.message).join(" ");
  }
  if (result.position) {
    return "보유 리스크 신호는 없고 계속 점검 구간입니다.";
  }
  if (result.score?.stage && !["대기", "주의", "진입금지"].includes(result.score.stage)) {
    return `${result.score.stage} 구간입니다. 상세 차트에서 지지선과 저항선을 확인합니다.`;
  }
  return "아직 뚜렷한 진입 근거가 없어 대기합니다.";
}

function buildAlertDigest(payload) {
  const items = collectSignalItems(payload)
    .filter((item) => item.delivery === "push" || item.delivery === "summary");
  const counts = {
    push: items.filter((item) => item.delivery === "push").length,
    summary: items.filter((item) => item.delivery === "summary").length,
    position: items.filter((item) => item.scope === "position").length,
    market: items.filter((item) => item.scope === "market").length,
    watch: items.filter((item) => item.scope === "watch").length,
  };
  const rows = ALERT_DIGEST_GROUPS
    .map((group) => {
      const groupItems = items.filter((item) => item.scope === group.scope);
      if (!groupItems.length) return null;
      return {
        group,
        item: groupItems[0],
        extraCount: Math.max(0, groupItems.length - 1),
      };
    })
    .filter(Boolean);
  return { counts, rows, topItem: rows[0]?.item || null };
}

function renderAlertDigest(digest) {
  const total = digest.counts.push + digest.counts.summary;
  const statusLabel = digest.counts.push ? "즉시" : digest.counts.summary ? "요약" : "평온";
  const statusLevel = normalizeSignalLevel(digest.topItem?.level || (digest.counts.summary ? "관심" : "대기"));
  const title = digest.counts.push
    ? `즉시 확인 ${digest.counts.push}개`
    : digest.counts.summary
      ? `요약 확인 ${digest.counts.summary}개`
      : "특이 알림 없음";
  const subtitle = total
    ? `기록/끔 제외 · 보유 ${digest.counts.position} · 시장 ${digest.counts.market} · 관심 ${digest.counts.watch}`
    : "새 즉시/요약 신호는 없고 Watch와 Hold만 천천히 보면 됩니다.";
  return `
    <article class="alert-digest" data-state="${total ? "active" : "quiet"}">
      <div class="alert-digest-head">
        <div class="alert-digest-copy">
          <strong>${escapeHtml(title)}</strong>
          <span>${escapeHtml(subtitle)}</span>
        </div>
        <span class="badge" data-level="${escapeHtml(statusLevel)}">${escapeHtml(statusLabel)}</span>
      </div>
      ${digest.rows.length ? `<div class="alert-digest-rows">${digest.rows.map(alertDigestRow).join("")}</div>` : ""}
    </article>
  `;
}

function alertDigestRow(row) {
  const item = row.item;
  const level = normalizeSignalLevel(item.level);
  const delivery = DELIVERY_LABELS[item.delivery] || item.delivery;
  const category = GROUP_LABELS[item.category] || item.category || row.group.label;
  return `
    <div class="alert-digest-row" data-level="${escapeHtml(level)}" data-scope="${escapeHtml(row.group.scope)}">
      <span class="alert-digest-scope">${escapeHtml(row.group.label)}</span>
      <div class="alert-digest-main">
        <strong>${escapeHtml(item.symbol)} · ${escapeHtml(SIGNAL_LABELS[item.type] || item.type)}</strong>
        <p>${escapeHtml(item.message)}</p>
      </div>
      <div class="alert-digest-meta">
        <span class="delivery-badge" data-delivery="${escapeHtml(item.delivery)}">${escapeHtml(delivery)}</span>
        ${row.extraCount ? `<small>${escapeHtml(category)} 외 ${row.extraCount}개</small>` : `<small>${escapeHtml(category)}</small>`}
      </div>
    </div>
  `;
}

function scoreStrip(score) {
  if (!score) return "";
  return `
    <div class="score-row" data-mode="${escapeHtml(score.mode)}">
      <div class="score-row-copy">
        <span>${escapeHtml(score.label)}</span>
        <strong>${escapeHtml(score.stage)}</strong>
      </div>
      ${scoreBar(score)}
    </div>
  `;
}

function chartButton(symbol, kind, value, label, active) {
  return `<button class="chart-btn ${active ? "active" : ""}" type="button" data-chart-kind="${kind}" data-symbol="${escapeHtml(symbol)}" data-value="${escapeHtml(value)}">${escapeHtml(label)}</button>`;
}

function chartOverlayButtons(symbol) {
  const indicators = indicatorPref(symbol);
  return `
    <div class="chart-control-group overlay-controls">
      ${indicatorButton(symbol, "bollinger", "BB", indicators.bollinger, "볼린저밴드")}
      ${indicatorButton(symbol, "ichimoku", "일목", indicators.ichimoku, "일목균형표")}
      ${drawingModeButton(symbol)}
      ${drawingUndoButton(symbol)}
    </div>
  `;
}

function indicatorButton(symbol, key, label, active, title) {
  return `<button class="chart-btn ${active ? "active" : ""}" type="button" data-indicator="${escapeHtml(key)}" data-symbol="${escapeHtml(symbol)}" aria-pressed="${active ? "true" : "false"}" title="${escapeHtml(title)}">${escapeHtml(label)}</button>`;
}

function drawingModeButton(symbol) {
  const active = isDrawingMode(symbol);
  return `<button class="chart-btn draw-btn ${active ? "active" : ""}" type="button" data-drawing-action="toggle" data-symbol="${escapeHtml(symbol)}" aria-pressed="${active ? "true" : "false"}" title="추세선 그리기">선</button>`;
}

function drawingUndoButton(symbol) {
  return `<button class="chart-btn" type="button" data-drawing-action="undo" data-symbol="${escapeHtml(symbol)}" title="최근 선 삭제">삭제</button>`;
}

function rangeLabel(range) {
  return { "3M": "3M", "6M": "6M", "1Y": "1Y", ALL: "ALL" }[range] || range;
}

function positionPanel(position, result = {}) {
  if (!position) return "";
  if (position.missing_average_entry) {
    return `
      <div class="position-panel">
        <div class="position-top">
          <strong>평단 필요</strong>
          <span class="badge" data-level="주의">평단입력</span>
        </div>
      </div>
    `;
  }
  const decision = positionManagementDecision(position, result);
  const items = positionGuardrailItems(result);
  return `
    <div class="position-panel" data-tone="${escapeHtml(decision.tone)}">
      <div class="position-top">
        <div class="position-return">
          <span>평단 손익</span>
          <strong class="${classForNumber(position.return_pct)}">${signed(position.return_pct)}%</strong>
        </div>
        <div class="position-action">
          <span>우선 판단</span>
          <strong>${escapeHtml(decision.label)}</strong>
        </div>
      </div>
      <p class="position-note">${escapeHtml(decision.message)}</p>
      <div class="position-decision-grid">
        <div data-state="${escapeHtml(decision.defenseState)}">
          <span>방어등급</span>
          <strong>${escapeHtml(decision.defenseLabel)}</strong>
        </div>
        <div data-state="${escapeHtml(items[0]?.state || "wait")}">
          <span>기준선</span>
          <strong>${escapeHtml(guardrailBrief(items[0]))}</strong>
        </div>
        <div data-state="${escapeHtml(items[2]?.state || "wait")}">
          <span>수익보호</span>
          <strong>${escapeHtml(guardrailBrief(items[2]))}</strong>
        </div>
      </div>
      <p class="position-note">평단 $${fmt(position.average_entry_price)} · 고점대비 ${signed(position.drawdown_from_high_pct)}%${position.pnl_amount !== null && position.pnl_amount !== undefined ? ` · 손익 $${fmt(position.pnl_amount)}` : ""}</p>
      ${positionGuardrails(result, true, items)}
    </div>
  `;
}

function positionManagementDecision(position, result = {}) {
  const score = result.score || {};
  const defense = positionComponentValue(score, "defense");
  const profit = positionComponentValue(score, "profit");
  const items = positionGuardrailItems(result);
  const defenseLine = items[0];
  const stopLine = items[1];
  const trailingLine = items[2];
  const returnPct = Number(position.return_pct || 0);
  const hardDefenseBreak = [defenseLine, stopLine].some((item) => item?.state === "broken");
  const defenseNear = [defenseLine, stopLine].some((item) => item?.state === "warning");
  const trailingReview = trailingLine?.price && trailingLine.state === "broken";
  const defenseLabel = positionDefenseLabel(defenseLine, stopLine, defense);
  const defenseState = hardDefenseBreak ? "broken" : defenseNear ? "warning" : defense >= 60 ? "warning" : "normal";

  if (hardDefenseBreak || defense >= 90) {
    return {
      label: "위험축소",
      tone: "위험",
      defenseLabel,
      defenseState,
      message: `방어선 ${guardrailBrief(defenseLine)} · 위험선 ${guardrailBrief(stopLine)}. 구조 이탈 여부를 먼저 확인합니다.`,
    };
  }
  if (trailingReview || profit >= 75) {
    return {
      label: "수익보호 우선",
      tone: "수익관리",
      defenseLabel,
      defenseState,
      message: `수익보호선 ${guardrailBrief(trailingLine)}를 우선 봅니다. 수익 구간에서는 이익 보호가 중심입니다.`,
    };
  }
  if (defense >= 75 || defenseNear) {
    return {
      label: "방어검토",
      tone: "주의",
      defenseLabel,
      defenseState,
      message: `방어선 ${guardrailBrief(defenseLine)}이 가까운 구간입니다. S1/60일선 재회복 여부를 봅니다.`,
    };
  }
  if (defense >= 60) {
    return {
      label: "방어선 확인",
      tone: "주의",
      defenseLabel,
      defenseState,
      message: `방어선 ${guardrailBrief(defenseLine)} 기준으로 구조를 점검합니다.`,
    };
  }
  if (returnPct >= 10 || profit >= 40) {
    return {
      label: "보유 유지",
      tone: "수익관리",
      defenseLabel,
      defenseState,
      message: `방어선 ${guardrailBrief(defenseLine)} 기준으로 여유를 확인하며 보유 점검합니다.`,
    };
  }
  return {
    label: "보유 점검",
    tone: "관찰",
    defenseLabel,
    defenseState,
    message: `방어선 ${guardrailBrief(defenseLine)} 기준으로 새 신호를 기다립니다.`,
  };
}

function positionComponentValue(score, key) {
  const component = (score?.components || []).find((item) => item.key === key);
  const value = Number(component?.value);
  return Number.isFinite(value) ? value : 0;
}

function positionDefenseLabel(defenseLine, stopLine, defenseScore) {
  if (defenseLine?.state === "broken" || stopLine?.state === "broken" || defenseScore >= 90) return "이탈 확인";
  if (defenseLine?.state === "warning" || stopLine?.state === "warning") return "근접";
  if (defenseScore >= 60) return "확인";
  if (defenseLine?.price) return "여유";
  return "대기";
}

function guardrailBrief(item) {
  if (!item || !item.price) return "대기";
  return `${item.name} ${guardrailDistanceText(item)}`;
}

function positionGuardrails(result = {}, compact = false, itemsOverride = null) {
  const position = result.position || result;
  if (!position || position.missing_average_entry) return "";
  const items = itemsOverride || positionGuardrailItems(result);
  return `
    <div class="${compact ? "position-guardrails compact" : "position-guardrails"}">
      ${items.map((item) => `
        <div class="position-guardrail" data-state="${escapeHtml(item.state)}">
          <span>${escapeHtml(item.title)}</span>
          <strong>${item.price ? `$${fmt(item.price)}` : "-"}</strong>
          <small>${escapeHtml(item.name)} · ${escapeHtml(guardrailDistanceText(item))}</small>
        </div>
      `).join("")}
    </div>
  `;
}

function positionGuardrailItems(result = {}) {
  const position = result.position || result;
  const currentPrice = currentPositionPrice(result);
  const candidates = [];
  const brokenSupport = brokenSupportGuardrail(result, currentPrice);
  const support = result.support_resistance?.nearest_support;
  if (brokenSupport) {
    candidates.push(brokenSupport);
  } else if (support?.price) {
    candidates.push(makeGuardrailItem("방어선", support.label || "S1", support.price, currentPrice, "defense"));
  }
  const ma60 = result.sma?.["60"];
  if (ma60) {
    candidates.push(makeGuardrailItem("방어선", "60일선", ma60, currentPrice, "defense"));
  }
  const ma120 = result.sma?.["120"];
  if (ma120) {
    candidates.push(makeGuardrailItem("방어선", "120일선", ma120, currentPrice, "defense"));
  }
  const defense = nearestGuardrail(candidates) || makeGuardrailItem("방어선", "없음", null, currentPrice, "wait");
  const stop = makeGuardrailItem("위험선", `설정 ${compactPercent(position.stop_loss_pct)}`, position.stop_price, currentPrice, "danger");
  const trailingActive = Number(position.return_pct) > 0 && position.trailing_stop_price;
  const trailing = trailingActive
    ? makeGuardrailItem("수익보호", "트레일", position.trailing_stop_price, currentPrice, "profit")
    : makeGuardrailItem("수익보호", "수익권 이후", null, currentPrice, "wait");
  return [defense, stop, trailing];
}

function brokenSupportGuardrail(result = {}, currentPrice = null) {
  const brokeSupport = (result.signals || []).some((signal) =>
    ["POSITION_SUPPORT_BREAKDOWN", "POSITION_STRUCTURE_EXIT_REVIEW"].includes(signal.type)
  );
  const resistance = result.support_resistance?.nearest_resistance;
  if (!brokeSupport || !resistance?.price) return null;
  const distancePct = Number(currentPrice) > 0 ? (Number(resistance.price) / Number(currentPrice) - 1) * 100 : null;
  if (distancePct === null || distancePct < 0 || distancePct > 6) return null;
  return makeGuardrailItem("방어선", "이탈선", resistance.price, currentPrice, "defense");
}

function makeGuardrailItem(title, name, price, currentPrice, type) {
  const numericPrice = Number(price);
  const numericCurrent = Number(currentPrice);
  const distancePct = Number.isFinite(numericPrice) && numericPrice > 0 && Number.isFinite(numericCurrent) && numericCurrent > 0
    ? (numericPrice / numericCurrent - 1) * 100
    : null;
  return {
    title,
    name,
    price: Number.isFinite(numericPrice) && numericPrice > 0 ? numericPrice : null,
    distancePct,
    state: guardrailState(distancePct, type),
  };
}

function nearestGuardrail(items) {
  const valid = items.filter((item) => item.price);
  const below = valid.filter((item) => item.distancePct !== null && item.distancePct < 0);
  const source = below.length ? below : valid;
  return source.sort((a, b) => Math.abs(a.distancePct ?? 999) - Math.abs(b.distancePct ?? 999))[0] || null;
}

function currentPositionPrice(result = {}) {
  const direct = Number(result.price);
  if (Number.isFinite(direct) && direct > 0) return direct;
  const position = result.position || result;
  const average = Number(position.average_entry_price);
  const returnPct = Number(position.return_pct);
  if (Number.isFinite(average) && average > 0 && Number.isFinite(returnPct)) {
    return average * (1 + returnPct / 100);
  }
  return null;
}

function guardrailState(distancePct, type) {
  if (type === "wait") return "wait";
  if (distancePct === null || distancePct === undefined || Number.isNaN(Number(distancePct))) return "wait";
  const distance = Number(distancePct);
  if (distance >= 0) return "broken";
  if (Math.abs(distance) <= 3) return "warning";
  if (type === "profit") return "profit";
  return "normal";
}

function guardrailDistanceText(item) {
  if (item.distancePct === null || item.distancePct === undefined || Number.isNaN(Number(item.distancePct))) {
    return "대기";
  }
  const distance = Number(item.distancePct);
  const value = `${Math.abs(distance).toFixed(1)}%`;
  return distance >= 0 ? `이탈 ${value}` : `여유 ${value}`;
}

function compactPercent(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "-";
  return `${Number(value) > 0 ? "+" : ""}${Number(value).toFixed(0)}%`;
}

function signalChips(signals, limit = 8) {
  if (!signals.length) {
    return '<span class="signal-chip">신호 없음</span>';
  }
  return signals.slice(0, limit).map((signal) => `
    <span class="signal-chip" data-delivery="${escapeHtml(signal.delivery)}">${escapeHtml(SIGNAL_LABELS[signal.type] || signal.type)} · ${escapeHtml(DELIVERY_LABELS[signal.delivery] || signal.delivery)}</span>
  `).join("");
}

function resultSignalScope(result) {
  if (result?.position) return "position";
  return "watch";
}

function dateKeyFromValue(value) {
  if (!value) return "";
  if (typeof value === "string") {
    const match = value.match(/^(\d{4}-\d{2}-\d{2})/);
    if (match) return match[1];
  }
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "" : localDateKey(date);
}

function signalTradeDate(item) {
  return dateKeyFromValue(item.tradeDate || item.lastBar || item.generatedAt) || localDateKey(new Date());
}

function signalScopeLabel(scope) {
  return SIGNAL_SCOPE_LABELS[scope] || "관심";
}

function signalSeenKey(item) {
  return [item.scope || "watch", item.symbol || "UNKNOWN", item.type || "UNKNOWN", signalTradeDate(item)].join(":");
}

function legacySignalSeenKey(item) {
  if (!item?.symbol || !item?.type) return "";
  return `${item.symbol}:${item.type}:${localDateKey(new Date())}`;
}

function signalSortPriority(item) {
  const scopePriority = item.scope === "position" ? 0 : item.scope === "market" ? 1 : 2;
  const deliveryPriority = SIGNAL_DELIVERY_PRIORITY[item.delivery] ?? 3;
  const intentPriority = SIGNAL_INTENT_PRIORITY[item.intent] ?? 4;
  const levelPriority = SIGNAL_LEVEL_PRIORITY[normalizeSignalLevel(item.level)] ?? 11;
  return [scopePriority, deliveryPriority, intentPriority, levelPriority, item.symbol || "", item.type || ""];
}

function compareSignalItems(left, right) {
  const a = signalSortPriority(left);
  const b = signalSortPriority(right);
  for (let index = 0; index < a.length; index += 1) {
    if (a[index] < b[index]) return -1;
    if (a[index] > b[index]) return 1;
  }
  return 0;
}

function createSignalLogEntry(item, id) {
  const createdAt = new Date().toISOString();
  const scope = item.scope || "watch";
  return {
    id,
    symbol: item.symbol,
    scope,
    scopeLabel: signalScopeLabel(scope),
    level: normalizeSignalLevel(item.level),
    type: item.type,
    category: item.category || "",
    intent: item.intent || "",
    message: item.message,
    delivery: item.delivery,
    tradeDate: signalTradeDate(item),
    lastBar: item.lastBar || "",
    time: new Date(createdAt).toLocaleString(),
    createdAt,
    unread: true,
  };
}

function persistSeenSignals() {
  const logIds = state.signalLog.map((entry) => entry.id).filter(Boolean);
  const ids = [...new Set([...state.seenSignals, ...logIds])].slice(-SIGNAL_MEMORY_LIMIT);
  state.seenSignals = new Set(ids);
  localStorage.setItem("seenSignals", JSON.stringify(ids));
}

function persistSignalLog() {
  state.signalLog = state.signalLog.slice(0, SIGNAL_LOG_LIMIT);
  localStorage.setItem("signalLog", JSON.stringify(state.signalLog));
  persistSeenSignals();
}

function collectSignalItems(payload) {
  const items = [];
  const generatedAt = payload.generated_at || new Date().toISOString();
  for (const result of payload.results || []) {
    if (result.error) continue;
    const scope = resultSignalScope(result);
    for (const signal of result.signals || []) {
      items.push({
        symbol: result.symbol,
        scope,
        type: signal.type,
        level: signal.level,
        category: signal.category,
        intent: signal.intent,
        message: signal.message,
        delivery: signal.delivery,
        lastBar: result.last_bar || generatedAt,
        generatedAt,
      });
    }
  }
  for (const signal of payload.market?.signals || []) {
    items.push({
      symbol: "MARKET",
      scope: "market",
      type: signal.type,
      level: signal.level,
      category: signal.category || "MARKET",
      intent: signal.intent,
      message: signal.message,
      delivery: signal.delivery,
      lastBar: payload.market?.vix?.latest_time || generatedAt,
      generatedAt,
    });
  }
  return items.sort(compareSignalItems);
}

function processSignals(payload) {
  const newEntries = [];
  let pushCount = 0;
  let memoryChanged = false;
  for (const item of collectSignalItems(payload)) {
    if (item.delivery === "off") continue;
    const id = signalSeenKey(item);
    const legacyId = legacySignalSeenKey(item);
    const alreadySeen = state.seenSignals.has(id) || (legacyId && state.seenSignals.has(legacyId));
    if (alreadySeen) {
      if (!state.seenSignals.has(id)) {
        state.seenSignals.add(id);
        memoryChanged = true;
      }
      continue;
    }
    state.seenSignals.add(id);
    memoryChanged = true;
    newEntries.push(createSignalLogEntry(item, id));
    if (item.delivery === "push") {
      pushCount += 1;
    }
    if (item.delivery === "push" && state.initialAnalysisComplete) {
      notify(`${item.symbol} ${SIGNAL_LABELS[item.type] || item.type}`, item.message);
    }
  }
  if (newEntries.length) {
    state.signalLog = [...newEntries, ...state.signalLog].slice(0, SIGNAL_LOG_LIMIT);
    persistSignalLog();
    renderLog();
  } else if (memoryChanged) {
    persistSeenSignals();
  }
  if (pushCount > 0 && state.initialAnalysisComplete) {
    toast(`새 즉시 알림 ${pushCount}개`);
  }
  state.initialAnalysisComplete = true;
}

function renderLog() {
  const host = $("signalLog");
  const entries = state.signalLog
    .map(normalizeSignalEntry)
    .sort((a, b) => (parseLogDate(b)?.getTime() || 0) - (parseLogDate(a)?.getTime() || 0));
  const ranged = entries.filter((entry) => signalLogInRange(entry, state.signalLogRange));
  const filtered = ranged.filter((entry) => signalLogMatches(entry, state.signalLogFilter));
  const unreadCount = entries.filter(isSignalLogUnread).length;
  renderSignalLogRangeFilters(entries);
  renderSignalLogFilters(ranged);
  if ($("signalLogMeta")) {
    $("signalLogMeta").textContent = entries.length ? `${filtered.length}/${ranged.length}개 · 미확인 ${unreadCount}` : "0개";
  }
  if (!entries.length) {
    host.innerHTML = emptyState("기록 없음");
    return;
  }
  if (!ranged.length) {
    host.innerHTML = emptyState("기간 내 신호 없음");
    return;
  }
  if (!filtered.length) {
    host.innerHTML = emptyState("해당 신호 없음");
    return;
  }
  host.innerHTML = groupedSignalLog(filtered).map((group) => `
    <section class="log-group">
      <div class="log-date">${escapeHtml(group.label)}</div>
      ${group.symbols.map(signalLogSymbolGroup).join("")}
    </section>
  `).join("");
}

function renderSignalLogRangeFilters(entries = []) {
  const host = $("signalLogRangeBar");
  if (!host) return;
  host.innerHTML = Object.entries(SIGNAL_LOG_RANGES).map(([key, label]) => {
    const count = entries.filter((entry) => signalLogInRange(entry, key)).length;
    return `
      <button class="filter-chip ${state.signalLogRange === key ? "active" : ""}" type="button" data-signal-log-range="${escapeHtml(key)}" aria-pressed="${state.signalLogRange === key ? "true" : "false"}">
        ${escapeHtml(label)} <span>${count}</span>
      </button>
    `;
  }).join("");
}

function renderSignalLogFilters(entries = []) {
  const host = $("signalLogFilterBar");
  if (!host) return;
  host.innerHTML = Object.entries(SIGNAL_LOG_FILTERS).map(([key, label]) => {
    const count = entries.filter((entry) => signalLogMatches(entry, key)).length;
    return `
      <button class="filter-chip ${state.signalLogFilter === key ? "active" : ""}" type="button" data-signal-log-filter="${escapeHtml(key)}" aria-pressed="${state.signalLogFilter === key ? "true" : "false"}">
        ${escapeHtml(label)} <span>${count}</span>
      </button>
    `;
  }).join("");
}

function signalLogSymbolGroup(group) {
  const latest = group.entries[0];
  const unreadCount = group.entries.filter(isSignalLogUnread).length;
  const newestLabel = SIGNAL_LABELS[latest.type] || latest.type;
  const latestScope = signalScopeLabel(latest.scope);
  return `
    <details class="log-symbol-group" data-intent="${escapeHtml(latest.intent)}" ${unreadCount ? "open" : ""}>
      <summary class="log-symbol-summary">
        <div class="log-summary-top">
          <div class="log-title">
            <strong>${escapeHtml(group.symbol)}</strong>
            <span>${escapeHtml(latestScope)} · ${escapeHtml(newestLabel)} · 최신 ${escapeHtml(displayLogTime(latest))}</span>
          </div>
          <div class="log-badges">
            ${unreadCount ? `<span class="unread-badge">미확인 ${unreadCount}</span>` : ""}
            <span class="log-count-badge">${group.entries.length}개</span>
          </div>
        </div>
        <p>${escapeHtml(latest.message)}</p>
      </summary>
      <div class="log-symbol-items">
        ${group.entries.map(signalLogItem).join("")}
      </div>
    </details>
  `;
}

function signalLogItem(entry) {
  const meta = [
    signalScopeLabel(entry.scope),
    GROUP_LABELS[entry.category] || entry.category || "기타",
    entry.tradeDate ? `기준 ${entry.tradeDate}` : "",
  ].filter(Boolean).join(" · ");
  return `
    <article class="log-item" data-intent="${escapeHtml(entry.intent)}" data-level="${escapeHtml(entry.level)}" data-unread="${isSignalLogUnread(entry) ? "true" : "false"}">
      <div class="log-top">
        <div class="log-title">
          <strong>${escapeHtml(entry.symbol)}</strong>
          <span>${escapeHtml(SIGNAL_LABELS[entry.type] || entry.type)}</span>
        </div>
        <div class="log-badges">
          ${isSignalLogUnread(entry) ? `<span class="unread-badge">미확인</span>` : ""}
          <span class="badge" data-level="${escapeHtml(entry.level)}">${escapeHtml(entry.level)}</span>
          <span class="delivery-badge" data-delivery="${escapeHtml(entry.delivery)}">${escapeHtml(DELIVERY_LABELS[entry.delivery] || entry.delivery)}</span>
        </div>
      </div>
      <p>${escapeHtml(entry.message)}</p>
      <div class="log-meta">
        <span>${escapeHtml(meta)}</span>
        <time>${escapeHtml(displayLogTime(entry))}</time>
      </div>
    </article>
  `;
}

function groupedSignalLog(entries) {
  const groups = [];
  for (const entry of entries) {
    const label = displayLogDate(entry);
    const current = groups[groups.length - 1];
    if (current?.label === label) {
      current.entries.push(entry);
    } else {
      groups.push({ label, entries: [entry] });
    }
  }
  for (const group of groups) {
    group.symbols = groupedSignalLogBySymbol(group.entries);
  }
  return groups;
}

function groupedSignalLogBySymbol(entries) {
  const groups = [];
  const bySymbol = new Map();
  for (const entry of entries) {
    const symbol = entry.symbol || "기타";
    if (!bySymbol.has(symbol)) {
      const group = { symbol, entries: [] };
      bySymbol.set(symbol, group);
      groups.push(group);
    }
    bySymbol.get(symbol).entries.push(entry);
  }
  return groups;
}

function normalizeSignalEntry(entry) {
  const normalized = { ...entry };
  normalized.category = entry.category || inferSignalCategory(entry);
  normalized.intent = entry.intent || inferSignalIntent(normalized);
  normalized.delivery = entry.delivery || "log";
  normalized.level = normalizeSignalLevel(entry.level || "대기");
  normalized.scope = entry.scope || inferSignalScope(normalized);
  normalized.scopeLabel = signalScopeLabel(normalized.scope);
  normalized.tradeDate = entry.tradeDate || dateKeyFromValue(entry.lastBar);
  normalized.unread = entry.unread === true;
  return normalized;
}

function isSignalLogUnread(entry) {
  return entry.unread === true;
}

function signalLogInRange(entry, range) {
  if (range === "all") return true;
  const date = parseLogDate(entry);
  if (!date) return false;
  const now = new Date();
  if (range === "today") {
    return localDateKey(date) === localDateKey(now);
  }
  if (range === "week") {
    const start = new Date(now);
    start.setHours(0, 0, 0, 0);
    start.setDate(start.getDate() - 6);
    return date >= start;
  }
  return true;
}

function signalLogMatches(entry, filter) {
  if (filter === "all") return true;
  if (filter === "push") return entry.delivery === "push";
  if (filter === "opportunity") return entry.intent === "opportunity" || ["공포관심", "관심", "반등후보", "기회후보", "돌파후보", "진입검토", "매수검토", "자리검토", "반등체크"].includes(entry.level);
  if (filter === "position") return entry.scope === "position" || entry.category === "POSITION";
  if (filter === "market") return entry.scope === "market" || entry.category === "MARKET" || entry.symbol === "MARKET";
  if (filter === "risk") return entry.intent === "risk" || ["주의", "방어검토", "판매검토", "위험", "오류", "시장확인", "추격주의"].includes(entry.level);
  return true;
}

function inferSignalScope(entry) {
  if (entry.symbol === "MARKET" || entry.category === "MARKET") return "market";
  if (entry.category === "POSITION") return "position";
  return "watch";
}

function inferSignalCategory(entry) {
  const type = entry.type || "";
  if (entry.symbol === "MARKET" || /^(MARKET|VIX|SPY|QQQ)_/.test(type)) return "MARKET";
  if (/^(POSITION|PROFIT|TRAILING|STOP|LOSS|RISK)_/.test(type) || type.includes("_HELD")) return "POSITION";
  if (type.startsWith("RSI_")) return "RSI";
  if (type.includes("VOLUME")) return "VOLUME";
  if (type.startsWith("MA") || type.includes("CROSS")) return "MOVING_AVERAGE";
  if (type.includes("BREAKOUT") || type.includes("BREAKDOWN")) return "BREAKOUT";
  if (type.startsWith("GAP_")) return "GAP";
  if (type.startsWith("BOLLINGER") || type.startsWith("ICHIMOKU") || type.startsWith("SUPPORT")) return "CHART";
  if (type.startsWith("EARNINGS")) return "EARNINGS";
  return "";
}

function inferSignalIntent(entry) {
  const type = entry.type || "";
  const level = entry.level || "";
  if (["위험", "방어검토", "판매검토", "주의", "오류", "시장확인", "추격주의"].includes(level) || /STOP|LOSS|RISK|BREAKDOWN|BEARISH|DEAD|PANIC|FEAR/.test(type)) return "risk";
  if (["수익관리", "수익보호검토", "익절검토"].includes(level) || /PROFIT|TRAILING|BULLISH|HIGH_/.test(type)) return "profit";
  if (["공포관심", "관심", "반등후보", "기회후보", "돌파후보", "진입검토", "매수검토", "자리검토", "반등체크"].includes(level) || /RECOVERY|OVERSOLD|BREAKOUT/.test(type)) return "opportunity";
  return "review";
}

function normalizeSignalLevel(level) {
  return LEVEL_ALIASES[level] || level || "대기";
}

function displayLogDate(entry) {
  const date = parseLogDate(entry);
  if (!date) return "이전 기록";
  return date.toLocaleDateString("ko-KR", { month: "long", day: "numeric", weekday: "short" });
}

function displayLogTime(entry) {
  const date = parseLogDate(entry);
  if (!date) return entry.time || "";
  return date.toLocaleTimeString("ko-KR", { hour: "2-digit", minute: "2-digit" });
}

function parseLogDate(entry) {
  const raw = entry.createdAt || entry.time || "";
  const date = new Date(raw);
  return Number.isNaN(date.getTime()) ? null : date;
}

function localDateKey(date) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function indicatorPref(symbol) {
  const saved = state.indicatorPrefs[symbol] || {};
  return {
    bollinger: Boolean(saved.bollinger),
    ichimoku: Boolean(saved.ichimoku),
  };
}

function toggleIndicator(symbol, key) {
  if (!["bollinger", "ichimoku"].includes(key)) return;
  const previous = indicatorPref(symbol);
  const next = { ...previous, [key]: !previous[key] };
  state.indicatorPrefs[symbol] = next;
  localStorage.setItem("indicatorPrefs", JSON.stringify(state.indicatorPrefs));
  rerenderChartsForSymbol(symbol);
}

function isDrawingMode(symbol) {
  return Boolean(state.drawingModes[symbol]);
}

function toggleDrawingMode(symbol) {
  state.drawingModes[symbol] = !isDrawingMode(symbol);
  delete state.drawingDrafts[symbol];
  rerenderChartsForSymbol(symbol);
  toast(state.drawingModes[symbol] ? "선긋기 모드 켜짐" : "선긋기 모드 꺼짐");
}

function chartLines(symbol) {
  return Array.isArray(state.chartDrawings[symbol]) ? state.chartDrawings[symbol] : [];
}

function saveChartLines(symbol, lines) {
  state.chartDrawings[symbol] = lines.slice(-40);
  localStorage.setItem("chartDrawings", JSON.stringify(state.chartDrawings));
}

function undoChartLine(symbol) {
  const lines = chartLines(symbol).slice();
  if (!lines.length) {
    toast("삭제할 선이 없습니다.");
    return;
  }
  lines.pop();
  saveChartLines(symbol, lines);
  rerenderChartsForSymbol(symbol);
  toast("최근 선 삭제 완료");
}

function chartPref(symbol) {
  const defaults = state.config?.chart || {};
  const saved = state.chartPrefs[symbol] || {};
  return {
    timeframe: saved.timeframe || defaults.default_timeframe || "D",
    range: saved.range || defaults.default_range || "6M",
    customCount: saved.customCount || null,
    offset: saved.offset || 0,
  };
}

function setChartPref(symbol, patch) {
  const previous = chartPref(symbol);
  const next = { ...previous, ...patch };
  if (patch.range || patch.timeframe) {
    next.customCount = null;
    next.offset = 0;
  }
  state.chartPrefs[symbol] = next;
  localStorage.setItem("chartPrefs", JSON.stringify(state.chartPrefs));
  rerenderChartsForSymbol(symbol);
}

function rerenderChartsForSymbol(symbol) {
  document.querySelectorAll("canvas[data-symbol]").forEach((canvas) => {
    if (canvas.dataset.symbol === symbol) {
      const result = findResult(symbol, canvas.dataset.view || "position");
      if (result) {
        drawTradingChart(canvas, result);
      }
    }
  });
  const escapedSymbol = cssEscape(symbol);
  document.querySelectorAll(`button[data-symbol="${escapedSymbol}"][data-chart-kind]`).forEach((button) => {
    const pref = chartPref(symbol);
    const kind = button.dataset.chartKind;
    const value = button.dataset.value;
    button.classList.toggle("active", kind === "timeframe" ? pref.timeframe === value : pref.range === value && !pref.customCount);
  });
  document.querySelectorAll(`button[data-symbol="${escapedSymbol}"][data-indicator]`).forEach((button) => {
    const indicators = indicatorPref(symbol);
    const active = Boolean(indicators[button.dataset.indicator]);
    button.classList.toggle("active", active);
    button.setAttribute("aria-pressed", active ? "true" : "false");
  });
  document.querySelectorAll(`button[data-symbol="${escapedSymbol}"][data-drawing-action="toggle"]`).forEach((button) => {
    const active = isDrawingMode(symbol);
    button.classList.toggle("active", active);
    button.setAttribute("aria-pressed", active ? "true" : "false");
  });
}

function chartSourceBars(result, pref) {
  if (pref.timeframe === "W") {
    return aggregateWeeklyBars(result.bars || []);
  }
  return result.bars || [];
}

function visibleChartBars(sourceBars, pref) {
  if (!sourceBars.length) return [];
  const defaultCount = rangeCount(pref.timeframe, pref.range, sourceBars.length);
  const minCount = pref.timeframe === "W" ? 20 : 34;
  const count = clamp(pref.customCount || defaultCount, minCount, sourceBars.length);
  const maxOffset = Math.max(0, sourceBars.length - count);
  const offset = clamp(pref.offset || 0, 0, maxOffset);
  const end = sourceBars.length - offset;
  const start = Math.max(0, end - count);
  return sourceBars.slice(start, end);
}

function rangeCount(timeframe, range, length) {
  const daily = { "3M": 63, "6M": 126, "1Y": 252, ALL: length };
  const weekly = { "3M": 13, "6M": 26, "1Y": 52, ALL: length };
  return (timeframe === "W" ? weekly : daily)[range] || length;
}

function aggregateWeeklyBars(dailyBars) {
  const weeks = [];
  let current = null;
  for (const bar of dailyBars) {
    const key = weekKey(bar.time);
    if (!current || current.weekKey !== key) {
      current = {
        weekKey: key,
        time: key,
        open: bar.open,
        high: bar.high,
        low: bar.low,
        close: bar.close,
        volume: bar.volume || 0,
        signals: [...(bar.signals || [])],
      };
      weeks.push(current);
    } else {
      current.high = Math.max(current.high, bar.high);
      current.low = Math.min(current.low, bar.low);
      current.close = bar.close;
      current.volume += bar.volume || 0;
      current.signals = [...new Set([...current.signals, ...(bar.signals || [])])];
    }
  }
  attachClientIndicators(weeks);
  return weeks;
}

function weekKey(value) {
  const date = new Date(value);
  const day = (date.getUTCDay() + 6) % 7;
  date.setUTCDate(date.getUTCDate() - day);
  return date.toISOString().slice(0, 10);
}

function attachClientIndicators(bars) {
  const closes = bars.map((bar) => bar.close);
  const highs = bars.map((bar) => bar.high);
  const lows = bars.map((bar) => bar.low);
  const volumes = bars.map((bar) => bar.volume || 0);
  const rsiValues = rsiSeries(closes, 14);
  const volumeAverage = smaSeries(volumes, 20);
  const ma20 = smaSeries(closes, 20);
  const ma60 = smaSeries(closes, 60);
  const ma120 = smaSeries(closes, 120);
  const bollinger = bollingerSeries(closes, 20, 2);
  const ichimoku = ichimokuSeries(highs, lows);
  bars.forEach((bar, index) => {
    bar.rsi14 = rsiValues[index];
    bar.volume_sma = volumeAverage[index];
    bar.sma20 = ma20[index];
    bar.sma60 = ma60[index];
    bar.sma120 = ma120[index];
    bar.bb_middle = bollinger.middle[index];
    bar.bb_upper = bollinger.upper[index];
    bar.bb_lower = bollinger.lower[index];
    bar.ichimoku_tenkan = ichimoku.tenkan[index];
    bar.ichimoku_kijun = ichimoku.kijun[index];
    bar.ichimoku_span_a = ichimoku.spanA[index];
    bar.ichimoku_span_b = ichimoku.spanB[index];
  });
}

function smaSeries(values, period) {
  const output = [];
  let rolling = 0;
  values.forEach((value, index) => {
    rolling += value;
    if (index >= period) rolling -= values[index - period];
    output.push(index >= period - 1 ? rolling / period : null);
  });
  return output;
}

function rollingDeviationSeries(values, period) {
  return values.map((_, index) => {
    if (index < period - 1) return null;
    const window = values.slice(index - period + 1, index + 1);
    const average = window.reduce((sum, value) => sum + value, 0) / period;
    const variance = window.reduce((sum, value) => sum + (value - average) ** 2, 0) / period;
    return Math.sqrt(variance);
  });
}

function bollingerSeries(values, period, deviations) {
  const middle = smaSeries(values, period);
  const standardDeviation = rollingDeviationSeries(values, period);
  return {
    middle,
    upper: middle.map((value, index) => value === null ? null : value + standardDeviation[index] * deviations),
    lower: middle.map((value, index) => value === null ? null : value - standardDeviation[index] * deviations),
  };
}

function midpointSeries(highs, lows, period) {
  return highs.map((_, index) => {
    if (index < period - 1) return null;
    const highWindow = highs.slice(index - period + 1, index + 1);
    const lowWindow = lows.slice(index - period + 1, index + 1);
    return (Math.max(...highWindow) + Math.min(...lowWindow)) / 2;
  });
}

function ichimokuSeries(highs, lows) {
  const tenkan = midpointSeries(highs, lows, 9);
  const kijun = midpointSeries(highs, lows, 26);
  const spanB = midpointSeries(highs, lows, 52);
  const spanA = tenkan.map((value, index) => value === null || kijun[index] === null ? null : (value + kijun[index]) / 2);
  return { tenkan, kijun, spanA, spanB };
}

function rsiSeries(values, period) {
  const output = Array(values.length).fill(null);
  if (values.length <= period) return output;
  let gain = 0;
  let loss = 0;
  for (let index = 1; index <= period; index += 1) {
    const delta = values[index] - values[index - 1];
    gain += Math.max(delta, 0);
    loss += Math.max(-delta, 0);
  }
  let avgGain = gain / period;
  let avgLoss = loss / period;
  output[period] = rsiValue(avgGain, avgLoss);
  for (let index = period + 1; index < values.length; index += 1) {
    const delta = values[index] - values[index - 1];
    avgGain = (avgGain * (period - 1) + Math.max(delta, 0)) / period;
    avgLoss = (avgLoss * (period - 1) + Math.max(-delta, 0)) / period;
    output[index] = rsiValue(avgGain, avgLoss);
  }
  return output;
}

function rsiValue(avgGain, avgLoss) {
  if (avgLoss === 0) return 100;
  const rs = avgGain / avgLoss;
  return 100 - 100 / (1 + rs);
}

function drawTradingChart(canvas, result) {
  const context = canvas.getContext("2d");
  const pref = chartPref(result.symbol);
  const indicators = indicatorPref(result.symbol);
  const sourceBars = chartSourceBars(result, pref);
  const bars = visibleChartBars(sourceBars, pref);
  const width = canvas.width;
  const height = canvas.height;
  context.clearRect(0, 0, width, height);
  canvas.classList.toggle("drawing-canvas", isDrawingMode(result.symbol));
  canvas._chartLayout = null;
  if (bars.length < 20) return;

  const padLeft = 42;
  const padRight = 18;
  const priceTop = 18;
  const priceHeight = Math.round(height * 0.48);
  const volumeTop = priceTop + priceHeight + 22;
  const volumeHeight = Math.max(46, Math.round(height * 0.12));
  const rsiTop = volumeTop + volumeHeight + 32;
  const rsiHeight = Math.max(76, height - rsiTop - 38);
  const plotWidth = width - padLeft - padRight;
  const candleWidth = Math.max(3, Math.min(10, plotWidth / bars.length * 0.58));
  const priceValues = [];
  const overlayKeys = [
    ...(indicators.bollinger ? ["bb_upper", "bb_middle", "bb_lower"] : []),
    ...(indicators.ichimoku ? ["ichimoku_tenkan", "ichimoku_kijun", "ichimoku_span_a", "ichimoku_span_b"] : []),
  ];
  for (const bar of bars) {
    priceValues.push(bar.high, bar.low);
    for (const key of ["sma20", "sma60", "sma120", ...overlayKeys]) {
      if (typeof bar[key] === "number") priceValues.push(bar[key]);
    }
  }
  if (result.position?.average_entry_price) {
    priceValues.push(result.position.average_entry_price);
  }
  if (result.position?.stop_price) {
    priceValues.push(result.position.stop_price);
  }
  if (result.position?.trailing_stop_price) {
    priceValues.push(result.position.trailing_stop_price);
  }
  for (const level of autoChartLevels(result)) {
    if (Math.abs(Number(level.distance_pct || 0)) <= 18) {
      priceValues.push(level.price);
    }
  }
  for (const line of chartLines(result.symbol)) {
    if (typeof line.start?.price === "number") priceValues.push(line.start.price);
    if (typeof line.end?.price === "number") priceValues.push(line.end.price);
  }
  const draft = state.drawingDrafts[result.symbol];
  if (draft) {
    if (typeof draft.start?.price === "number") priceValues.push(draft.start.price);
    if (typeof draft.end?.price === "number") priceValues.push(draft.end.price);
  }
  const minPrice = Math.min(...priceValues);
  const maxPrice = Math.max(...priceValues);
  const maxVolume = Math.max(...bars.map((bar) => bar.volume || 0));
  const xFor = (index) => padLeft + (index / Math.max(bars.length - 1, 1)) * plotWidth;
  const yForPrice = (value) => priceTop + priceHeight - ((value - minPrice) / Math.max(maxPrice - minPrice, 0.01)) * priceHeight;
  const yForRsi = (value) => rsiTop + rsiHeight - (value / 100) * rsiHeight;
  canvas._chartLayout = { bars, minPrice, maxPrice, padLeft, padRight, priceTop, priceHeight, plotWidth, width, height };

  drawGrid(context, padLeft, padRight, width, priceTop, priceHeight, 4);
  drawGrid(context, padLeft, padRight, width, rsiTop, rsiHeight, 2);
  drawYAxisLabel(context, `$${maxPrice.toFixed(0)}`, 8, priceTop + 4);
  drawYAxisLabel(context, `$${minPrice.toFixed(0)}`, 8, priceTop + priceHeight);

  if (indicators.ichimoku) {
    drawCloud(context, bars, "ichimoku_span_a", "ichimoku_span_b", xFor, yForPrice);
  }
  if (indicators.bollinger) {
    drawBand(context, bars, "bb_upper", "bb_lower", xFor, yForPrice, "rgba(110, 168, 255, 0.08)");
  }

  bars.forEach((bar, index) => {
    const x = xFor(index);
    const openY = yForPrice(bar.open);
    const closeY = yForPrice(bar.close);
    const highY = yForPrice(bar.high);
    const lowY = yForPrice(bar.low);
    const up = bar.close >= bar.open;
    context.strokeStyle = up ? "#19d6a4" : "#ff6b6b";
    context.fillStyle = up ? "rgba(25, 214, 164, 0.72)" : "rgba(255, 107, 107, 0.76)";
    context.lineWidth = 1.2;
    context.beginPath();
    context.moveTo(x, highY);
    context.lineTo(x, lowY);
    context.stroke();
    const bodyTop = Math.min(openY, closeY);
    const bodyHeight = Math.max(Math.abs(closeY - openY), 2);
    context.fillRect(x - candleWidth / 2, bodyTop, candleWidth, bodyHeight);

    const volumeHeightPx = ((bar.volume || 0) / Math.max(maxVolume, 1)) * volumeHeight;
    context.fillStyle = up ? "rgba(25, 214, 164, 0.35)" : "rgba(255, 107, 107, 0.35)";
    context.fillRect(x - candleWidth / 2, volumeTop + volumeHeight - volumeHeightPx, candleWidth, volumeHeightPx);
  });

  if (indicators.bollinger) {
    drawLine(context, bars, "bb_upper", xFor, yForPrice, "rgba(110, 168, 255, 0.86)", 1);
    drawLine(context, bars, "bb_middle", xFor, yForPrice, "rgba(110, 168, 255, 0.42)", 1);
    drawLine(context, bars, "bb_lower", xFor, yForPrice, "rgba(110, 168, 255, 0.86)", 1);
  }
  drawLine(context, bars, "sma20", xFor, yForPrice, "#6ea8ff", 1.4);
  drawLine(context, bars, "sma60", xFor, yForPrice, "#ffcc66", 1.4);
  drawLine(context, bars, "sma120", xFor, yForPrice, "#b38cff", 1.2);
  if (indicators.ichimoku) {
    drawLine(context, bars, "ichimoku_tenkan", xFor, yForPrice, "#ff6b6b", 1.05);
    drawLine(context, bars, "ichimoku_kijun", xFor, yForPrice, "#c9d1d9", 1.05);
    drawLine(context, bars, "ichimoku_span_a", xFor, yForPrice, "rgba(25, 214, 164, 0.82)", 1);
    drawLine(context, bars, "ichimoku_span_b", xFor, yForPrice, "rgba(255, 204, 102, 0.72)", 1);
  }
  if (result.position?.average_entry_price) {
    drawHorizontal(context, yForPrice(result.position.average_entry_price), padLeft, width - padRight, "#ffffff", [6, 6], "평단");
  }
  if (result.position?.stop_price) {
    drawHorizontal(context, yForPrice(result.position.stop_price), padLeft, width - padRight, "rgba(255, 107, 107, 0.88)", [8, 5], "위험선");
  }
  if (result.position?.trailing_stop_price) {
    drawHorizontal(context, yForPrice(result.position.trailing_stop_price), padLeft, width - padRight, "rgba(255, 204, 102, 0.88)", [4, 5], "트레일");
  }
  drawAutoLevels(context, result, yForPrice, padLeft, width - padRight, priceTop, priceHeight);
  drawChartDrawings(context, result.symbol, bars, yForPrice, padLeft, plotWidth);

  drawHorizontal(context, yForRsi(70), padLeft, width - padRight, "rgba(255, 204, 102, 0.5)", [4, 4]);
  drawHorizontal(context, yForRsi(30), padLeft, width - padRight, "rgba(25, 214, 164, 0.5)", [4, 4]);
  drawLine(context, bars, "rsi14", xFor, yForRsi, "#19d6a4", 1.8);
  drawYAxisLabel(context, "RSI", 8, rsiTop + 14);

  const latest = bars[bars.length - 1];
  if (latest.signals?.length) {
    const x = xFor(bars.length - 1);
    const y = yForPrice(latest.close) - 14;
    context.fillStyle = "#ffcc66";
    context.beginPath();
    context.moveTo(x, y);
    context.lineTo(x - 7, y - 13);
    context.lineTo(x + 7, y - 13);
    context.closePath();
    context.fill();
  }

  context.fillStyle = "rgba(243, 246, 248, 0.58)";
  context.font = "12px Arial";
  context.fillText(`${pref.timeframe === "W" ? "Weekly" : "Daily"} · ${bars.length}/${sourceBars.length}`, padLeft, height - 14);
  canvas.dataset.visibleCount = String(bars.length);
}

function autoChartLevels(result) {
  const levels = result.support_resistance || {};
  return [...(levels.supports || []), ...(levels.resistances || [])].filter((level) => typeof level.price === "number");
}

function drawAutoLevels(context, result, yForPrice, x1, x2, priceTop, priceHeight) {
  const levels = autoChartLevels(result).slice(0, 6);
  if (!levels.length) return;
  context.save();
  context.font = "11px Arial";
  context.textBaseline = "middle";
  levels.forEach((level) => {
    const y = yForPrice(level.price);
    if (y < priceTop - 8 || y > priceTop + priceHeight + 8) return;
    const isSupport = level.kind === "support";
    const color = isSupport ? "rgba(25, 214, 164, 0.72)" : "rgba(255, 107, 107, 0.72)";
    context.strokeStyle = color;
    context.fillStyle = color;
    context.lineWidth = Math.min(1.8, 0.8 + Number(level.strength || 1) * 0.18);
    context.setLineDash([7, 5]);
    context.beginPath();
    context.moveTo(x1, y);
    context.lineTo(x2, y);
    context.stroke();
    context.setLineDash([]);
    const label = `${level.label || (isSupport ? "S" : "R")} $${fmt(level.price)}`;
    const textWidth = context.measureText(label).width;
    const labelX = Math.max(x1 + 4, x2 - textWidth - 6);
    context.fillText(label, labelX, y - (isSupport ? 7 : -7));
  });
  context.restore();
}

function drawBand(context, bars, upperKey, lowerKey, xFor, yFor, fillStyle) {
  const upper = [];
  const lower = [];
  bars.forEach((bar, index) => {
    if (typeof bar[upperKey] === "number" && typeof bar[lowerKey] === "number") {
      upper.push({ x: xFor(index), y: yFor(bar[upperKey]) });
      lower.unshift({ x: xFor(index), y: yFor(bar[lowerKey]) });
    }
  });
  if (upper.length < 2 || lower.length < 2) return;
  context.save();
  context.fillStyle = fillStyle;
  context.beginPath();
  context.moveTo(upper[0].x, upper[0].y);
  upper.slice(1).forEach((point) => context.lineTo(point.x, point.y));
  lower.forEach((point) => context.lineTo(point.x, point.y));
  context.closePath();
  context.fill();
  context.restore();
}

function drawCloud(context, bars, spanAKey, spanBKey, xFor, yFor) {
  const segments = [];
  let current = [];
  bars.forEach((bar, index) => {
    if (typeof bar[spanAKey] === "number" && typeof bar[spanBKey] === "number") {
      current.push({
        x: xFor(index),
        a: yFor(bar[spanAKey]),
        b: yFor(bar[spanBKey]),
        positive: bar[spanAKey] >= bar[spanBKey],
      });
      return;
    }
    if (current.length) {
      segments.push(current);
      current = [];
    }
  });
  if (current.length) segments.push(current);

  context.save();
  segments.forEach((segment) => {
    if (segment.length < 2) return;
    const positiveCount = segment.filter((point) => point.positive).length;
    context.fillStyle = positiveCount >= segment.length / 2 ? "rgba(25, 214, 164, 0.09)" : "rgba(255, 107, 107, 0.08)";
    context.beginPath();
    context.moveTo(segment[0].x, segment[0].a);
    segment.slice(1).forEach((point) => context.lineTo(point.x, point.a));
    [...segment].reverse().forEach((point) => context.lineTo(point.x, point.b));
    context.closePath();
    context.fill();
  });
  context.restore();
}

function drawChartDrawings(context, symbol, bars, yForPrice, padLeft, plotWidth) {
  const drawStoredLine = (line, dashed = false) => {
    if (typeof line.start?.price !== "number" || typeof line.end?.price !== "number") return;
    const startX = xForTimeValue(line.start.time, bars, padLeft, plotWidth);
    const endX = xForTimeValue(line.end.time, bars, padLeft, plotWidth);
    if (startX === null || endX === null) return;
    context.save();
    context.strokeStyle = dashed ? "rgba(243, 246, 248, 0.82)" : "#19d6a4";
    context.lineWidth = dashed ? 1.2 : 1.6;
    context.setLineDash(dashed ? [5, 5] : []);
    context.beginPath();
    context.moveTo(startX, yForPrice(line.start.price));
    context.lineTo(endX, yForPrice(line.end.price));
    context.stroke();
    context.restore();
  };
  chartLines(symbol).forEach((line) => drawStoredLine(line));
  const draft = state.drawingDrafts[symbol];
  if (draft) drawStoredLine(draft, true);
}

function xForTimeValue(time, bars, padLeft, plotWidth) {
  if (!bars.length) return null;
  const target = Date.parse(time);
  const first = Date.parse(bars[0].time);
  const last = Date.parse(bars[bars.length - 1].time);
  if (Number.isFinite(target) && Number.isFinite(first) && Number.isFinite(last) && first !== last) {
    return padLeft + clamp((target - first) / (last - first), 0, 1) * plotWidth;
  }
  const index = bars.findIndex((bar) => bar.time === time);
  if (index < 0) return null;
  return padLeft + (index / Math.max(bars.length - 1, 1)) * plotWidth;
}

function attachChartInteractions(canvas, result) {
  if (canvas.dataset.bound === "true") return;
  canvas.dataset.bound = "true";

  canvas.addEventListener("wheel", (event) => {
    if (!state.config?.chart?.zoom_enabled) return;
    event.preventDefault();
    const pref = chartPref(result.symbol);
    const sourceBars = chartSourceBars(result, pref);
    if (sourceBars.length < 2) return;
    const minCount = pref.timeframe === "W" ? 20 : 34;
    const currentCount = clamp(pref.customCount || rangeCount(pref.timeframe, pref.range, sourceBars.length), minCount, sourceBars.length);
    const nextCount = Math.round(currentCount * (event.deltaY < 0 ? 0.82 : 1.22));
    saveChartPref(result.symbol, {
      ...pref,
      customCount: clamp(nextCount, minCount, sourceBars.length),
    });
    rerenderChartsForSymbol(result.symbol);
  }, { passive: false });

  canvas.addEventListener("pointerdown", (event) => {
    if (isDrawingMode(result.symbol)) {
      event.preventDefault();
      const point = chartPointFromEvent(canvas, event);
      if (!point) return;
      try {
        canvas.setPointerCapture(event.pointerId);
      } catch {
        // Some synthetic/browser pointer events do not allow capture.
      }
      state.drawingDrafts[result.symbol] = { start: point, end: point, pointerId: event.pointerId };
      drawTradingChart(canvas, result);
      return;
    }
    if (!state.config?.chart?.zoom_enabled) return;
    try {
      canvas.setPointerCapture(event.pointerId);
    } catch {
      // Some synthetic/browser pointer events do not allow capture.
    }
    const pref = chartPref(result.symbol);
    const sourceBars = chartSourceBars(result, pref);
    const currentCount = Number(canvas.dataset.visibleCount || rangeCount(pref.timeframe, pref.range, sourceBars.length));
    const gesture = state.chartDrag[result.symbol] || { pointers: {} };
    gesture.pointers[event.pointerId] = { x: event.clientX, y: event.clientY };
    gesture.startX = event.clientX;
    gesture.startOffset = pref.offset || 0;
    gesture.startCount = currentCount;
    gesture.startDistance = twoPointerDistance(gesture.pointers);
    state.chartDrag[result.symbol] = gesture;
  });

  canvas.addEventListener("pointermove", (event) => {
    const draft = state.drawingDrafts[result.symbol];
    if (draft?.pointerId === event.pointerId) {
      event.preventDefault();
      const point = chartPointFromEvent(canvas, event);
      if (point) {
        draft.end = point;
        drawTradingChart(canvas, result);
      }
      return;
    }

    const drag = state.chartDrag[result.symbol];
    if (!drag?.pointers?.[event.pointerId]) return;
    drag.pointers[event.pointerId] = { x: event.clientX, y: event.clientY };
    const pref = chartPref(result.symbol);
    const sourceBars = chartSourceBars(result, pref);
    const visibleCount = Number(canvas.dataset.visibleCount || rangeCount(pref.timeframe, pref.range, sourceBars.length));
    const maxOffset = Math.max(0, sourceBars.length - visibleCount);

    const distance = twoPointerDistance(drag.pointers);
    if (distance && drag.startDistance) {
      const minCount = pref.timeframe === "W" ? 20 : 34;
      const nextCount = clamp(Math.round(drag.startCount * (drag.startDistance / distance)), minCount, sourceBars.length);
      saveChartPref(result.symbol, {
        ...pref,
        customCount: nextCount,
        offset: clamp(pref.offset || 0, 0, Math.max(0, sourceBars.length - nextCount)),
      });
      drawTradingChart(canvas, result);
      return;
    }

    const deltaBars = Math.round((event.clientX - drag.startX) / 8);
    saveChartPref(result.symbol, { ...pref, offset: clamp(drag.startOffset + deltaBars, 0, maxOffset) });
    drawTradingChart(canvas, result);
  });

  canvas.addEventListener("pointerup", (event) => {
    const draft = state.drawingDrafts[result.symbol];
    if (draft?.pointerId === event.pointerId) {
      event.preventDefault();
      const point = chartPointFromEvent(canvas, event) || draft.end;
      draft.end = point;
      if (Math.hypot((draft.end.x || 0) - (draft.start.x || 0), (draft.end.y || 0) - (draft.start.y || 0)) > 8) {
        const lines = chartLines(result.symbol);
        saveChartLines(result.symbol, [
          ...lines,
          {
            start: { time: draft.start.time, price: draft.start.price },
            end: { time: draft.end.time, price: draft.end.price },
            created_at: new Date().toISOString(),
          },
        ]);
      }
      delete state.drawingDrafts[result.symbol];
      drawTradingChart(canvas, result);
      return;
    }

    const drag = state.chartDrag[result.symbol];
    if (!drag?.pointers?.[event.pointerId]) return;
    delete drag.pointers[event.pointerId];
    const remaining = Object.values(drag.pointers);
    if (!remaining.length) {
      delete state.chartDrag[result.symbol];
      return;
    }
    drag.startX = remaining[0].x;
    drag.startOffset = chartPref(result.symbol).offset || 0;
    drag.startDistance = twoPointerDistance(drag.pointers);
    drag.startCount = Number(canvas.dataset.visibleCount || drag.startCount);
  });

  canvas.addEventListener("pointercancel", () => {
    delete state.drawingDrafts[result.symbol];
    delete state.chartDrag[result.symbol];
    drawTradingChart(canvas, result);
  });
}

function chartPointFromEvent(canvas, event) {
  const layout = canvas._chartLayout;
  if (!layout?.bars?.length) return null;
  const rect = canvas.getBoundingClientRect();
  const x = ((event.clientX - rect.left) / rect.width) * layout.width;
  const y = ((event.clientY - rect.top) / rect.height) * layout.height;
  if (y < layout.priceTop || y > layout.priceTop + layout.priceHeight) return null;
  const ratio = clamp((x - layout.padLeft) / layout.plotWidth, 0, 1);
  const index = clamp(Math.round(ratio * (layout.bars.length - 1)), 0, layout.bars.length - 1);
  const priceRatio = clamp((layout.priceTop + layout.priceHeight - y) / layout.priceHeight, 0, 1);
  const price = layout.minPrice + priceRatio * (layout.maxPrice - layout.minPrice);
  return {
    time: layout.bars[index].time,
    price: Number(price.toFixed(4)),
    x,
    y,
  };
}

function twoPointerDistance(pointers) {
  const values = Object.values(pointers || {});
  if (values.length < 2) return null;
  return Math.hypot(values[0].x - values[1].x, values[0].y - values[1].y);
}

function saveChartPref(symbol, pref) {
  state.chartPrefs[symbol] = pref;
  localStorage.setItem("chartPrefs", JSON.stringify(state.chartPrefs));
}

function drawGrid(context, padLeft, padRight, width, top, height, lines) {
  context.strokeStyle = "rgba(255, 255, 255, 0.08)";
  context.lineWidth = 1;
  for (let i = 0; i <= lines; i += 1) {
    const y = top + (height / lines) * i;
    context.beginPath();
    context.moveTo(padLeft, y);
    context.lineTo(width - padRight, y);
    context.stroke();
  }
}

function drawLine(context, bars, key, xFor, yFor, color, lineWidth) {
  context.strokeStyle = color;
  context.lineWidth = lineWidth;
  context.beginPath();
  let started = false;
  bars.forEach((bar, index) => {
    const value = bar[key];
    if (typeof value !== "number") return;
    const x = xFor(index);
    const y = yFor(value);
    if (!started) {
      context.moveTo(x, y);
      started = true;
    } else {
      context.lineTo(x, y);
    }
  });
  context.stroke();
}

function drawHorizontal(context, y, x1, x2, color, dash, label = "") {
  context.save();
  context.strokeStyle = color;
  context.lineWidth = 1;
  context.setLineDash(dash);
  context.beginPath();
  context.moveTo(x1, y);
  context.lineTo(x2, y);
  context.stroke();
  if (label) {
    context.setLineDash([]);
    context.fillStyle = color;
    context.font = "11px Arial";
    context.fillText(label, x1 + 5, y - 6);
  }
  context.restore();
}

function drawYAxisLabel(context, text, x, y) {
  context.fillStyle = "rgba(243, 246, 248, 0.56)";
  context.font = "11px Arial";
  context.fillText(text, x, y);
}

function notify(title, body) {
  if (
    !("Notification" in window)
    || Notification.permission !== "granted"
    || !notificationsAppEnabled()
  ) return;
  new Notification(title, { body });
}

function notificationsAppEnabled() {
  const stored = localStorage.getItem(NOTIFICATIONS_ENABLED_STORAGE_KEY);
  return stored === null ? true : stored === "true";
}

function notificationPermissionState() {
  if (typeof window === "undefined" || !("Notification" in window)) return "unsupported";
  return Notification.permission || "default";
}

function notificationStatusView(stateValue = notificationPermissionState()) {
  if (stateValue === "granted") {
    if (!notificationsAppEnabled()) {
      return {
        state: "muted",
        button: "알림 꺼짐",
        message: "PulseEdge 알림이 일시 중지되어 있습니다.",
        toast: "PulseEdge 알림이 꺼져 있습니다.",
      };
    }
    return {
      state: "granted",
      button: "알림 켜짐",
      message: "즉시 신호는 브라우저 알림으로 받습니다.",
      toast: "브라우저 알림이 켜져 있습니다.",
    };
  }
  if (stateValue === "denied") {
    return {
      state: "denied",
      button: "알림 차단됨",
      message: "브라우저 설정에서 PulseEdge 알림을 허용해야 합니다.",
      toast: "브라우저에서 알림이 차단되어 있습니다.",
    };
  }
  if (stateValue === "unsupported") {
    return {
      state: "unsupported",
      button: "알림 불가",
      message: "이 브라우저는 알림을 지원하지 않습니다.",
      toast: "이 브라우저는 알림을 지원하지 않습니다.",
    };
  }
  return {
    state: "default",
    button: "알림 켜기",
    message: "권한 허용 후 새 즉시 신호만 알림으로 받습니다.",
    toast: "",
  };
}

function renderNotificationStatus() {
  const button = $("notifyButton");
  if (!button) return;
  const status = $("notificationStatus");
  const view = notificationStatusView();
  button.textContent = view.button;
  button.dataset.notificationState = view.state;
  button.disabled = view.state === "unsupported";
  button.setAttribute("aria-label", `${view.button}. ${view.message}`);
  if (status) {
    status.textContent = view.message;
    status.dataset.notificationState = view.state;
  }
}

async function enableNotifications() {
  const before = notificationStatusView();
  if (before.state === "granted" || before.state === "muted") {
    const enabled = before.state !== "granted";
    localStorage.setItem(NOTIFICATIONS_ENABLED_STORAGE_KEY, String(enabled));
    renderNotificationStatus();
    toast(enabled ? "PulseEdge 알림을 켰습니다." : "PulseEdge 알림을 껐습니다.");
    return;
  }
  if (before.state === "unsupported" || before.state === "denied") {
    renderNotificationStatus();
    toast(before.toast);
    return;
  }
  const button = $("notifyButton");
  const originalText = button.textContent;
  try {
    button.disabled = true;
    button.textContent = "요청 중";
    const result = await Notification.requestPermission();
    if (result === "granted") {
      localStorage.setItem(NOTIFICATIONS_ENABLED_STORAGE_KEY, "true");
    }
    renderNotificationStatus();
    toast(result === "granted" ? "브라우저 알림 허용됨" : "브라우저 알림이 꺼져 있습니다.");
  } catch {
    renderNotificationStatus();
    toast("알림 권한 요청을 완료하지 못했습니다.");
  } finally {
    button.disabled = false;
    if (button.textContent === "요청 중") {
      button.textContent = originalText;
    }
    renderNotificationStatus();
  }
}

function clearLog() {
  state.signalLog = [];
  state.seenSignals = new Set();
  localStorage.removeItem("signalLog");
  localStorage.removeItem("seenSignals");
  renderLog();
}

function markLogRead() {
  if (!state.signalLog.some((entry) => entry.unread === true)) {
    toast("미확인 신호 없음");
    return;
  }
  state.signalLog = state.signalLog.map((entry) => ({ ...entry, unread: false }));
  localStorage.setItem("signalLog", JSON.stringify(state.signalLog));
  renderLog();
  toast("신호 확인 완료");
}

async function installApp() {
  if (state.deferredInstallPrompt) {
    const promptEvent = state.deferredInstallPrompt;
    state.deferredInstallPrompt = null;
    promptEvent.prompt();
    const choice = await promptEvent.userChoice.catch(() => null);
    renderInstallPanel();
    toast(choice?.outcome === "accepted" ? "설치 요청 완료" : "설치 취소");
    return;
  }
  toast(isIOS() ? "Safari 공유 버튼 > 홈 화면에 추가" : "브라우저 메뉴 > 설치 또는 홈 화면에 추가");
}

function registerServiceWorker() {
  if ("serviceWorker" in navigator) {
    navigator.serviceWorker.register("/service-worker.js").catch(() => {});
  }
}

window.addEventListener("beforeinstallprompt", (event) => {
  event.preventDefault();
  state.deferredInstallPrompt = event;
  renderInstallPanel();
});

window.addEventListener("appinstalled", () => {
  state.deferredInstallPrompt = null;
  renderInstallPanel();
  toast("PulseEdge 설치 완료");
});

function initRiskConsent() {
  const check = $("riskConsentCheck");
  const accept = $("riskConsentAcceptButton");
  check.addEventListener("change", () => {
    accept.disabled = !check.checked;
  });
  accept.addEventListener("click", acceptRiskConsent);
  showRiskConsent();
}

function riskConsentRecord() {
  try {
    return JSON.parse(localStorage.getItem(RISK_CONSENT_STORAGE_KEY) || "null");
  } catch {
    return null;
  }
}

function hasRiskConsent() {
  return riskConsentRecord()?.version === RISK_CONSENT_VERSION;
}

function showRiskConsent(options = {}) {
  const force = Boolean(options.force);
  const overlay = $("riskConsentOverlay");
  if (!force && hasRiskConsent()) {
    hideRiskConsent();
    renderRiskConsentStatus();
    return;
  }
  $("riskConsentCheck").checked = false;
  $("riskConsentAcceptButton").disabled = true;
  overlay.classList.add("active");
  overlay.setAttribute("aria-hidden", "false");
  document.body.classList.add("consent-open");
  renderRiskConsentStatus();
}

function hideRiskConsent() {
  const overlay = $("riskConsentOverlay");
  overlay.classList.remove("active");
  overlay.setAttribute("aria-hidden", "true");
  document.body.classList.remove("consent-open");
}

function acceptRiskConsent() {
  if (!$("riskConsentCheck").checked) return;
  localStorage.setItem(
    RISK_CONSENT_STORAGE_KEY,
    JSON.stringify({
      version: RISK_CONSENT_VERSION,
      acceptedAt: new Date().toISOString(),
    })
  );
  hideRiskConsent();
  renderRiskConsentStatus();
  toast("투자 유의 동의가 저장됐습니다.");
}

function renderRiskConsentStatus() {
  const status = $("riskConsentStatus");
  if (!status) return;
  const record = riskConsentRecord();
  if (record?.version === RISK_CONSENT_VERSION && record.acceptedAt) {
    status.textContent = `투자 유의 동의 완료 · ${new Date(record.acceptedAt).toLocaleDateString()}`;
    return;
  }
  status.textContent = "투자 유의 동의 필요";
}

function emptyState(message) {
  return `<div class="empty-state">${escapeHtml(message)}</div>`;
}

function toast(message) {
  const item = document.createElement("div");
  item.className = "toast";
  item.textContent = message;
  $("toastHost").appendChild(item);
  setTimeout(() => item.remove(), 4200);
}

function fmt(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "-";
  return Number(value).toLocaleString(undefined, { maximumFractionDigits: 2 });
}

function formatBarTime(value) {
  if (!value) return "-";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return String(value);
  return date.toLocaleDateString();
}

function formatRefreshTime(value) {
  if (!value) return "확인 전";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return String(value);
  return date.toLocaleString(undefined, {
    month: "numeric",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function dataStatusText(status) {
  if (!status || status.state === "unknown") return "확인 전";
  const refreshed = formatRefreshTime(status.fetched_at);
  if (status.stale) return `캐시 데이터 · ${refreshed} 갱신`;
  if (status.served_from_cache) return `정상 · 서버 캐시 · ${refreshed}`;
  return `정상 · 새로 조회 · ${refreshed}`;
}

function dataFreshnessSummaryText(summary) {
  if (!summary || summary.state === "unknown") return "";
  const status = summary.stale ? "캐시 데이터" : "정상 데이터";
  const basis = summary.last_bar ? `${formatBarTime(summary.last_bar)} 기준` : "기준일 확인 전";
  return `${status} · ${basis} · ${formatRefreshTime(summary.fetched_at)} 갱신`;
}

function signed(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "-";
  const numeric = Number(value);
  return `${numeric > 0 ? "+" : ""}${numeric.toFixed(2)}`;
}

function nullable(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "-";
  return Number(value).toFixed(2);
}

function valueOrEmpty(value) {
  if (value === null || value === undefined) return "";
  return escapeHtml(value);
}

function classForNumber(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "";
  return Number(value) >= 0 ? "positive" : "negative";
}

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value));
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

$("saveButton").addEventListener("click", saveConfig);
$("analyzeButton").addEventListener("click", analyze);
$("notifyButton").addEventListener("click", enableNotifications);
$("markLogReadButton")?.addEventListener("click", markLogRead);
$("clearLogButton").addEventListener("click", clearLog);

initTabs();
initInteractiveControls();
registerServiceWorker();
renderNotificationStatus();
document.addEventListener("visibilitychange", () => {
  if (!document.hidden) renderNotificationStatus();
});
window.addEventListener("focus", renderNotificationStatus);
initRiskConsent();

async function bootstrapApp() {
  await initAuth();
  await loadConfig();
  await analyze();
}

bootstrapApp().catch((error) => toast(error.message));
