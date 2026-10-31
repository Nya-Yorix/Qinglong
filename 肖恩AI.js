// supxh.xin 每日签到 (肖恩AI 免费API) - JS 版 (Node.js 18+, 零依赖, 多账号)
// 运行: node 01-AI.js
//
// 多账号: 环境变量 SUPXH_ACCOUNTS, 格式: 邮箱1&密码1#邮箱2&密码2
//   (# 分隔多个账号, & 分隔账号与密码, 密码里不能含 #)
//   例: a@qq.com#pass123&b@qq.com#pass456
// 兼容旧变量: 未设置 SUPXH_ACCOUNTS 时回退到 SUPXH_EMAIL / SUPXH_PASS 单账号
"use strict";
const fs = require("fs");
const path = require("path");

const BASE = "https://go.toter.me";
const LOG = path.join(process.cwd(), "supxh_signin.log");

// 解析 SUPXH_ACCOUNTS: "user1&passwd#user2&passwd"
function parseAccounts(raw) {
  const list = [];
  for (const seg of String(raw || "").split("&")) {
    const s = seg.trim();
    if (!s) continue;
    const amp = s.indexOf("#");
    if (amp <= 0) continue;
    const user = s.slice(0, amp).trim();
    const pass = s.slice(amp + 1).trim();
    if (user && pass) list.push({ user, pass });
  }
  return list;
}

function getAccounts() {
  const raw = process.env.SUPXH_ACCOUNTS;
  if (raw && raw.trim()) return parseAccounts(raw);
  // 兼容旧的单账号变量
  if (process.env.SUPXH_EMAIL && process.env.SUPXH_PASS) {
    return [{ user: process.env.SUPXH_EMAIL.trim(), pass: process.env.SUPXH_PASS }];
  }
  return [];
}

// apiKey 只显示前十位, 其余用星号代替
function maskKey(key) {
  const k = String(key || "");
  if (!k) return "(无apiKey)";
  if (k.length <= 10) return k;
  return k.slice(0, 10) + "*".repeat(k.length - 10);
}

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

function errMsg(e) {
  return e && e.message ? e.message : String(e);
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

// 单账号完整流程: 登录 -> 签到 -> 查询 /api/auth/me
async function runAccount(acc, idx) {
  const tag = `账号${idx}(${acc.user})`;
  const jar = {};
  const ret = { name: acc.user, ok: false, already: false, bonus: 0, remaining: "未知", key: maskKey(""), msg: "" };

  // 1. 登录 (cookie 写入 jar)
  try {
    const r = await fetch(BASE + "/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username: acc.user, password: acc.pass }),
      signal: AbortSignal.timeout(20000),
    });
    grabCookie(r, jar);
    if (r.status >= 400) { ret.msg = `登录失败 (HTTP ${r.status})`; log(`[${tag}] ` + ret.msg); return ret; }
  } catch (e) { ret.msg = "登录失败: " + errMsg(e); log(`[${tag}] ` + ret.msg); return ret; }

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
  } catch (e) { ret.msg = "签到请求失败: " + errMsg(e); log(`[${tag}] ` + ret.msg); return ret; }

  const suc = deepGet(res, "success") === true;
  const msg = String(deepGet(res, "message") || "");
  const bonus = deepGet(res, "bonus");
  log(`[${tag}] signin -> success=${suc} message=${msg} bonus=${bonus === undefined ? "" : bonus}`);

  // 3. 查询用户信息 (用户名 / 剩余额度 / apiKey)
  try {
    const r3 = await fetch(BASE + "/api/auth/me", {
      headers: { "Accept": "application/json", Cookie: cookieHeader(jar) },
      signal: AbortSignal.timeout(20000),
    });
    const me = await r3.json();
    log("固定额度=" + (deepGet(me, "permanentQuota") || "") + " 今日签到额度=" + (deepGet(me, "dailyQuota") || ""));
    ret.name = deepGet(me, "username") || ret.name;
    if (bonus !== undefined && bonus !== null && bonus !== "") ret.bonus = bonus;
    else ret.bonus = deepGet(me, "dailyQuota") ?? 0;
    ret.remaining = deepGet(me, "quota") ?? deepGet(me, "permanentQuota") ?? "未知";
    ret.key = maskKey(deepGet(me, "apiKey"));
    if (!suc && deepGet(me, "hasSignedInToday") === true) ret.already = true;
  } catch (e) { log(`[${tag}] 查询用户信息失败: ` + errMsg(e)); }

  // 签到接口返回 success=false 但提示已签到时, 视为已完成
  if (suc || ret.already || /已签到/.test(msg)) {
    ret.ok = true;
    ret.already = ret.already || !suc;
  } else {
    ret.msg = msg || "签到失败 (响应无 success=true)";
  }
  return ret;
}

// 汇总行格式: [Username] 签到成功 +xxxx 额度 剩余xxxx apiKey前十位+星号
function summaryLine(r) {
  if (!r.ok) return `[${r.name}] 签到失败: ${r.msg}`;
  const state = r.already ? "今日已签到" : "签到成功";
  return `[${r.name}] ${state} +${r.bonus} 剩余额度 ${r.remaining} API：${r.key}`;
}

async function main() {
  const accounts = getAccounts();
  if (accounts.length === 0) {
    log("未配置账号! 请设置环境变量 SUPXH_ACCOUNTS, 格式: 邮箱1#密码1&邮箱2#密码2");
    return 1;
  }
  log(`========== 开始签到, 共 ${accounts.length} 个账号 ==========`);
  const results = [];
  for (let i = 0; i < accounts.length; i++) {
    const acc = accounts[i];
    log(`---- 账号${i + 1}: ${acc.user} ----`);
    try {
      results.push(await runAccount(acc, i + 1));
    } catch (e) {
      log(`账号${i + 1} 运行异常: ` + errMsg(e));
      results.push({ name: acc.user, ok: false, already: false, bonus: 0, remaining: "未知", key: maskKey(""), msg: "运行异常: " + errMsg(e) });
    }
  }
  log("========== 签到汇总 ==========");
  for (const r of results) log(summaryLine(r));
  return results.every((r) => r.ok) ? 0 : 1;
}

main().then((code) => process.exit(code));
