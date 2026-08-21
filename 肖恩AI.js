// supxh.xin 每日签到 (肖恩AI 免费API) - JS 版 (Node.js, 零依赖)
// 运行: node signin_supxh.js
// 账号密码可用环境变量 SUPXH_EMAIL / SUPXH_PASS 覆盖
"use strict";
const fs = require("fs");
const path = require("path");

const EMAIL = process.env.SUPXH_EMAIL || "这里填邮箱";
const PASS = process.env.SUPXH_PASS || "这里填密码";
const BASE = "https://free.supxh.xin";
const LOG = path.join(process.cwd(), "supxh_signin.log");

function stamp() {
  const d = new Date();
  const p = (n) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}:${p(d.getSeconds())}`;
}
// 递归查找嵌套 JSON 中的键 (响应可能嵌套在 data 下)
function deepGet(o, key) {
  if (o && typeof o === "object") {
    if (key in o) return o[key];
    for (const k of Object.keys(o)) {
      const r = deepGet(o[k], key);
      if (r !== undefined) return r;
    }
  }
  return undefined;
}

function log(msg) {
  const line = `[${stamp()}] ${msg}`;
  console.log(line);
  try { fs.appendFileSync(LOG, line + "\n", "utf8"); } catch (e) {}
}

// ---- 简易 cookie jar ----
function grabCookie(res, jar) {
  let list = [];
  try { list = res.headers.getSetCookie(); } catch (e) {}
  if (list.length === 0) {
    const raw = res.headers.get("set-cookie");
    if (raw) list = [raw];
  }
  for (const c of list) {
    const part = c.split(";")[0];
    const eq = part.indexOf("=");
    if (eq > 0) jar[part.slice(0, eq).trim()] = part.slice(eq + 1).trim();
  }
}
function cookieHeader(jar) {
  return Object.entries(jar).map(([k, v]) => k + "=" + v).join("; ");
}

async function main() {
  const jar = {};

  // 1. 登录 (cookie 写入 jar)
  try {
    const r = await fetch(BASE + "/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username: EMAIL, password: PASS }),
      signal: AbortSignal.timeout(20000),
    });
    grabCookie(r, jar);
    if (r.status >= 400) { log("login failed (HTTP " + r.status + ")"); return 1; }
  } catch (e) { log("login failed: " + e); return 1; }

  // 2. 签到
  let res;
  try {
    const r2 = await fetch(BASE + "/api/user/signin", {
      method: "POST",
      headers: { "Content-Type": "application/json", "Accept": "application/json", Cookie: cookieHeader(jar) },
      body: "{}",
      signal: AbortSignal.timeout(20000),
    });
    res = await r2.json();
  } catch (e) { log("signin failed: " + e); return 1; }

  const msg = deepGet(res, "message") || "";
  const bonus = deepGet(res, "bonus") || "";
  const suc = deepGet(res, "success") || "";
  log(`signin -> success=${suc} message=${msg} bonus=${bonus}`);
  log("签到结果: " + msg + (bonus ? " (获得 " + bonus + " 额度)" : ""));

  // 3. 查当日额度 (可选)
  try {
    const r3 = await fetch(BASE + "/api/auth/me", {
      headers: { "Accept": "application/json", Cookie: cookieHeader(jar) },
      signal: AbortSignal.timeout(20000),
    });
    const me = await r3.json();
    log("固定额度=" + (deepGet(me, "permanentQuota") || "") + " 今日签到额度=" + (deepGet(me, "dailyQuota") || ""));
  } catch (e) { log("查额度失败: " + e); }
  return 0;
}

main().then((code) => process.exit(code));
