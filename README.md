# Yorix の 青龙面板

| APP          | 环境变量                    | 值                                                           |
| :----------- | :-------------------------- | :----------------------------------------------------------- |
| 中国移动云盘 | `YDYP_CK`                   | `Basic <实际Token>#<手机号>`                                 |
| 天翼云盘     | `TY_USERNAME` `TY_PASSWORD` | **两个独立变量**： `TY_USERNAME` = `手机号` `TY_PASSWORD` = `密码` |
| 百度网盘     | `BAIDU_COOKIE`              | Cookie 字符串 `key1=value1; key2=value2; ...`                |
| 必应积分     | `bing_ck_1` `bing_token_1`  | `ck`填写[Cookie](https://rewards.bing.com/api/getuserinfo?type=1&X-Requested-With=XMLHttpRequest) `token`填写[刷新令牌](https://login.live.com/oauth20_authorize.srf?client_id=0000000040170455&scope=service::prod.rewardsplatform.microsoft.com::MBI_SSL&response_type=code&redirect_uri=https://login.live.com/oauth20_desktop.srf) [令牌获取脚本](https://www.tampermonkey.net/script_installation.php#url=https://g.geeck.eu.org/https://github.com/Popukok/Some_scripts/raw/refs/heads/main/Bing/bing_refreshToken.user.js) *支持多账号*               |
| 酷狗音乐     | `kgck`                      | 格式：`token#userid` 抓完包直接搜索`token`就能找到变量|
| 夸克网盘     | `COOKIE_QUARK`              | 格式：`user=UserName;url=https://...` 示例：`user=Yorix;url=https://...` |
| 什么值得买   | `SMZDM_COOKIE`              | Cookie 字符串 `key1=value1; key2=value2; ...`                |
| 肖恩AI       | -------------               |修改代码                                                      |
## Other

| APP      | Github                                           |
| -------- | ------------------------------------------------ |
| 库街区   | https://github.com/mxyooR/Kuro-autosignin        |
| 阿里云盘❌ | https://github.com/Stonewuu/aliyundrive_autosign |
