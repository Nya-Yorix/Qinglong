# Yorix の 青龙面板

| APP          | 环境变量                    | 值                                                           |
| :----------- | :-------------------------- | :----------------------------------------------------------- |
| 中国移动云盘 | `YDYP_CK`                   | `Basic <实际Token>#<手机号>`                                 |
| 天翼云盘     | `TY_USERNAME` `TY_PASSWORD` | **两个独立变量**： `TY_USERNAME` = `手机号` `TY_PASSWORD` = `密码` |
| 小黑盒       |`json文件`  | (仅签到无奖励) 首次运行会生成 `heiboxconfig.json` 配置文件，用手机进行抓包复制 cookie 的数据填入小黑盒的 cookie ， `heybox_id`，`heybox_id` 可以在请求链接获取，`imei` 请求连接里面获得(imei可以不填，但有可能会**封号**)|
| 百度网盘     | `BAIDU_COOKIE`              | Cookie 字符串 `key1=value1; key2=value2; ...`                |
| 夸克网盘     | `COOKIE_QUARK`              | 格式：`user=UserName;url=https://...` 示例：`user=Yorix;url=https://drive-m.quark.cn/1/clouddrive/file/count?pr=uc&fr=pc&pdir_count=...` |
| 什么值得买   | `SMZDM_COOKIE`              | Cookie 字符串 `key1=value1; key2=value2; ...`                |
## Other

| APP      | Github                                           |
| -------- | ------------------------------------------------ |
| 库街区   | https://github.com/mxyooR/Kuro-autosignin        |
| 阿里云盘❌ | https://github.com/Stonewuu/aliyundrive_autosign |
