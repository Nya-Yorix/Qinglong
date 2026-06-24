#!/usr/bin/env python3
# # 当前脚本来自于 http://script.nnioj.com/ 脚本库下载！
# # 当前脚本来自于 http://script.nnioj.com/ 脚本库下载！
# # 当前脚本来自于 http://script.nnioj.com/ 脚本库下载！
# # 脚本库中的所有脚本文件均来自热心网友上传和互联网收集。
# # 脚本库仅提供文件上传和下载服务，不提供脚本文件的审核。
# # 您在使用脚本库下载的脚本时自行检查判断风险。
# # 所涉及到的 账号安全、数据泄露、设备故障、软件违规封禁、财产损失等问题及法律风险，与脚本库无关！均由开发者、上传者、使用者自行承担。

# -*- coding: utf-8 -*-
# ============================================================
# 🎀 脚本名称: 中国移动云盘·每日云朵助手
# 📦 功能描述: 任务一键完成｜薅云朵｜抽奖｜备份礼品
# 🔐 环境变量: YDYP_CK
#   格式: Basic xxx#手机号 （多账号用 @ 分割，或换行）
# ⏰ 定时: 0 0 8,16,20 * * *
# 📅 更新: 2026-05-08 v2.0
# 🎀 aiaiからレムへのプレゼント 💕
# ============================================================
"""
🌟 中国移动云盘 — 每日云朵助手 v2.0 🌟

每天帮你做的事：
  ① 自动登录 🔑
  ② 遍历所有待完成任务 → 一键领取 📋
  ③ "戳一下" × 10 次 👆
  ④ 🎰 自动抽奖（每次2云朵！）
  ⑤ 🎁 备份礼品领取
  ⑥ 📰 关注签到
  ⑦ 📊 输出日报告

🎯 使用方式：
  青龙面板 → 环境变量 YDYP_CK = "Basic xxx#138xxxx"
  多账号用 @ 隔开

💡 接口状态：
  ✅ 任务系统 (sign_in_3) — 25个任务，每月几千云朵
  ✅ 邮箱任务 (newsign_139mail) — 16个任务
  ✅ 戳一下 (id=319) — 每天10次随机
  ✅ 抽奖系统 — 每次2云朵，有剩余次数就能抽！
  ✅ 备份礼品 — 完成备份后领取
"""

import os
import re
import sys
import json
import time
import random
from datetime import datetime
from typing import Optional, List, Tuple

import requests

# ─── 配置 ────────────────────────────────────────────────
UA = (
    "Mozilla/5.0 (Linux; Android 14; 24031PN0DC) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Mobile Safari/537.36 "
    "MCloudApp/12.0.0"
)
API_BASE = "https://caiyun.feixin.10086.cn"
SSO_URL = "https://orches.yun.139.com/orchestration/auth-rebuild/token/v1.0/querySpecToken"
# ──────────────────────────────────────────────────────────


class Cloud139Client:
    """☁️ 移动云盘 API 客户端"""

    def __init__(self, auth_token: str, phone: str):
        self.auth = auth_token
        self.phone = phone
        self.masked = phone[:3] + "****" + phone[-4:]
        self._session = requests.Session()
        self._session.headers.update({
            "User-Agent": UA,
            "Content-Type": "application/json",
            "Accept": "*/*",
        })
        self._jwt_headers: dict = {}
        self._jwt_cookies: dict = {}
        self._logs: List[str] = []
        # 统计
        self._tasks_done = 0
        self._cloud_earned = 0
        self._draw_count = 0
        self._poke_count = 0

    # ── 日志 ──
    def _log(self, msg: str, emoji: str = "💬") -> str:
        ts = datetime.now().strftime("%H:%M:%S")
        line = f"  {emoji} [{ts}] {msg}"
        print(line)
        self._logs.append(line)
        return line

    def _ok(self, msg: str) -> str:
        return self._log(msg, "✅")

    def _info(self, msg: str) -> str:
        return self._log(msg, "💬")

    def _warn(self, msg: str) -> str:
        return self._log(msg, "⚠️")

    def _fail(self, msg: str) -> str:
        return self._log(msg, "❌")

    @staticmethod
    def _sleep(a: float = 0.8, b: float = 1.5):
        time.sleep(random.uniform(a, b))

    # ── 认证 ──
    def _get_sso_token(self) -> Optional[str]:
        try:
            resp = self._session.post(
                SSO_URL,
                headers={"Authorization": self.auth},
                json={"account": self.phone, "toSourceId": "001005"},
                timeout=10,
            ).json()
            if resp.get("success"):
                self._ok("SSO 令牌 🪪")
                return resp["data"]["token"]
            self._fail(f"SSO 失败: {resp.get('message', '?')}")
        except requests.RequestException as e:
            self._fail(f"SSO 网络异常: {e}")
        return None

    def login(self) -> bool:
        sso = self._get_sso_token()
        if not sso:
            return False
        try:
            resp = self._session.post(
                f"{API_BASE}/portal/auth/tyrzLogin.action",
                params={"ssoToken": sso},
                timeout=10,
            ).json()
            if resp.get("code") == 0:
                jt = resp["result"]["token"]
                self._jwt_headers = {
                    "User-Agent": UA,
                    "Accept": "*/*",
                    "Host": "caiyun.feixin.10086.cn",
                    "Content-Type": "application/json",
                    "Referer": f"{API_BASE}/",
                    "jwtToken": jt,
                }
                self._jwt_cookies = {"jwtToken": jt}
                self._ok(f"JWT 令牌 🗝️")
                return True
            self._fail(f"JWT 失败: {resp.get('msg', '?')}")
        except requests.RequestException as e:
            self._fail(f"JWT 网络异常: {e}")
        return False

    # ── API 请求 ──
    def _get(self, path: str, **kw) -> Optional[dict]:
        headers = {**self._jwt_headers, **kw.pop("headers", {})}
        cookies = {**self._jwt_cookies, **kw.pop("cookies", {})}
        kw.setdefault("timeout", 10)
        try:
            r = self._session.get(API_BASE + path, headers=headers, cookies=cookies, **kw)
            return r.json() if r.status_code == 200 else None
        except Exception:
            return None

    def _post(self, path: str, body: dict = None, **kw) -> Optional[dict]:
        headers = {**self._jwt_headers, **kw.pop("headers", {})}
        cookies = {**self._jwt_cookies, **kw.pop("cookies", {})}
        kw.setdefault("timeout", 10)
        try:
            r = self._session.post(API_BASE + path, headers=headers, cookies=cookies, json=body or {}, **kw)
            return r.json() if r.status_code == 200 else None
        except Exception:
            return None

    def _click(self, task_id: int) -> bool:
        self._sleep(0.3, 0.8)
        r = self._get(f"/market/signin/task/click?key=***&id={task_id}")
        return bool(r and r.get("code") == 0)

    # ── 任务模块 ──
    def _do_clickable_tasks(self, marketname: str, label: str) -> int:
        """遍历指定市场任务，执行WAIT+click类型的任务"""
        r = self._get(f"/market/signin/task/taskList?marketname={marketname}")
        if not r or r.get("msg") != "success":
            self._warn(f"获取{label}任务列表失败")
            return 0
        tasks = r.get("result", {})
        total = sum(len(v) for v in tasks.values())
        self._info(f"📋 {label}: {total} 个任务")

        count = 0
        for group, tl in tasks.items():
            for t in tl:
                if t.get("state") != "WAIT":
                    continue
                steps = t.get("stepTypeSet", [])
                if not ("click" in steps or "sendcloud" in steps):
                    continue
                name = t.get("name", "?")
                if self._click(t["id"]):
                    self._ok(f"✨ 完成 [{t['id']}] {name[:30]}")
                    count += 1
                    self._cloud_earned += self._extract_reward(t)
                else:
                    self._warn(f"😅 失败 [{t['id']}] {name[:30]}")
        return count

    @staticmethod
    def _extract_reward(task: dict) -> int:
        desc = task.get("description", "") or task.get("rewardStr", "")
        nums = re.findall(r"(\d+)", desc)
        return max((int(n) for n in nums if int(n) < 10000), default=0) if nums else 0

    def _do_poke(self, count: int = 10) -> int:
        """👆 戳一下"""
        ok = 0
        for i in range(count):
            if self._click(319):
                ok += 1
            if i < count - 1:
                self._sleep(0.2, 0.4)
        return ok

    def _do_draw(self) -> int:
        """🎰 自动抽奖 — 每次2云朵"""
        # 查看剩余次数
        r = self._get("/market/playoffic/drawInfo")
        if not r or r.get("msg") != "success":
            self._warn("抽奖信息获取失败")
            return 0
        info = r.get("result", {})
        remaining = info.get("surplusNumber", 0)
        if remaining <= 0:
            self._info("🎰 今日抽奖次数已用完 ✨")
            return 0
        self._info(f"🎰 还有 {remaining} 次抽奖机会，开始抽～")

        drawn = 0
        for i in range(remaining):
            r = self._get("/market/playoffic/draw")
            if r and r.get("code") == 0:
                prize = r.get("result", {}).get("prizeName", "?")
                if "云朵" in prize:
                    self._cloud_earned += 2
                drawn += 1
                self._sleep(0.3, 0.6)
            else:
                self._warn(f"🎰 第{i+1}抽失败")
                break
        self._ok(f"🎰 抽奖 {drawn}/{remaining} 次 ✨")
        return drawn

    def _do_backup_gift(self):
        """🎁 备份礼品领取"""
        r = self._get("/market/backupgift/info")
        if not r or r.get("msg") != "success":
            return
        info = r.get("result", {})
        state = info.get("state", -1)
        cur = info.get("curMonth", 0)
        self._info(f"🎁 备份礼品: 本月可领 {cur} 云朵 | 状态: {state}")
        if state == 1:  # 已达成条件
            r = self._get("/market/backupgift/receive")
            if r and r.get("code") == 0:
                self._ok(f"🎁 备份礼品领取成功！+{cur} 云朵 ☁️")
                self._cloud_earned += cur
            else:
                msg = r.get("result", "?") if r else "?"
                self._warn(f"🎁 备份礼品领取: {msg}")
        else:
            self._info("🎁 备份礼品需要先完成月月备份任务哦～")

    def _do_push_task(self):
        """🔔 推送任务检查"""
        r = self._get("/market/msgPushOn/task/status")
        if not r or r.get("msg") != "success":
            return
        info = r.get("result", {})
        s1 = info.get("firstTaskStatus", "?")
        s2 = info.get("secondTaskStatus", "?")
        pt = info.get("pushTaskStatus", "?")
        self._info(f"🔔 推送任务状态: 首任务={s1} 次任务={s2} 推送={pt}")

        r = self._post("/market/msgPushOn/task/obtain")
        if r and r.get("code") == 0:
            oc = r.get("result", {}).get("obtainCode", -1)
            if oc == 1:
                self._ok("🔔 推送任务领取成功 ✅")
            else:
                self._info(f"🔔 推送任务: 领取码 {oc}")
        else:
            self._warn("🔔 推送任务领取失败")

    # ── 主流程 ──
    def run(self) -> str:
        """🚀 执行每日任务"""
        print()
        self._print_banner("🌟 中国移动云盘 · 每日云朵助手 v2.0 🌟")
        self._info(f"📱 账号: {self.masked}")

        if not self.login():
            return "❌ 登录失败，请检查 CK 是否过期"

        # ① 主任务系统
        self._print_section("📋 云盘任务")
        td1 = self._do_clickable_tasks("sign_in_3", "云盘任务")
        self._tasks_done += td1

        # ② 139邮箱任务
        self._print_section("📧 139邮箱任务")
        td2 = self._do_clickable_tasks("newsign_139mail", "139邮箱任务")
        self._tasks_done += td2

        # ③ 戳一下
        self._print_section("👆 戳一下")
        self._poke_count = self._do_poke(10)
        self._ok(f"👆 戳了 {self._poke_count}/10 次 ✨")

        # ④ 抽奖
        self._print_section("🎰 抽奖")
        self._draw_count = self._do_draw()

        # ⑤ 备份礼品
        self._print_section("🎁 备份礼品")
        self._do_backup_gift()

        # ⑥ 推送任务
        self._print_section("🔔 推送任务")
        self._do_push_task()

        # ⑦ 日报告
        summary = self._summary()
        return summary

    def _summary(self) -> str:
        """📝 生成日报告"""
        lines = [
            "",
            f"  {'🌸' * 22}",
            f"  🌸 ☁️ 移动云盘 · 日报告",
            f"  🌸 📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            f"  🌸 📱 {self.masked}",
            f"  🌸 {'🌸' * 22}",
            "",
            f"    ✨ 完成任务: {self._tasks_done} 个",
            f"    ☁️ 今日云朵: +{self._cloud_earned}",
            f"    👆 戳了一下: {self._poke_count}/10",
            f"    🎰 抽奖次数: {self._draw_count}",
            "",
            f"  💖 aiaiからレムへのプレゼント 💕",
            f"  {'🌸' * 22}",
        ]
        result = "\n".join(lines)
        print(result)
        self._logs.append(result)
        return result

    def _print_banner(self, text: str):
        pad = "🌟"
        print(f"  {pad * 22}")
        print(f"  {pad}  {text}")
        print(f"  {pad * 22}")

    def _print_section(self, title: str):
        print()
        print(f"  ── {title} ──")


# ─── 入口 ──────────────────────────────────────────────────

def parse_env(env_value: str) -> List[Tuple[str, str]]:
    accounts = []
    for line in re.split(r"[\n@]", env_value.strip()):
        line = line.strip()
        if "#" in line:
            parts = line.split("#", 1)
            accounts.append((parts[0].strip(), parts[1].strip()))
    return accounts


def main():
    """🐣 主函数"""
    print(f"  🌟 中国移动云盘 · 每日云朵助手 v2.0 🌟")
    print(f"  🌟 启动: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    env_ck = os.environ.get("YDYP_CK", "").strip()
    accounts = parse_env(env_ck) if env_ck else []

    if not accounts and len(sys.argv) >= 3:
        accounts.append((sys.argv[1], sys.argv[2]))

    if not accounts:
        print("  😅 未检测到账号信息")
        print()
        print("  📖 请设置环境变量 YDYP_CK")
        print("    格式: Basic xxx#手机号")
        print("    多账号: Basic a#138xxxx@Basic b#139xxxx")
        print()
        print("  💡 或命令行: python3 139cloud.py 'Basic xxx' 手机号")
        sys.exit(1)

    print(f"  👥 共 {len(accounts)} 个账号")
    print()

    for i, (auth, phone) in enumerate(accounts, 1):
        print(f"\n  {'─' * 48}")
        print(f"  📍 账号 {i}/{len(accounts)}")
        print(f"  {'─' * 48}")

        client = Cloud139Client(auth, phone)
        try:
            client.run()
        except Exception as e:
            masked = phone[:3] + "****" + phone[-4:]
            print(f"  ❌ [{masked}] 异常: {e}")
            import traceback
            traceback.print_exc()
        print()

    print(f"\n  {'🎉' * 22}")
    print(f"  🎉 全部搞定 | {len(accounts)} 个账号")
    print(f"  {'🎉' * 22}")


if __name__ == "__main__":
    main()
