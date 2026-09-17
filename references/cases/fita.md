# 案例锚点：Fita（仅当模式对上时读）

禁止把本文件中的域名、密钥、appID 填进**其他** App 的报告。

## 模式

- 业务包类数很少，第三方（融云、Zego、Adjust）占绝大多数 → SDK 拼装型
- 字符串：混淆类双参 `V1.b.O(cipher, key)` = Base64 + 循环 XOR
- 请求：OkHttp Interceptor，body `{"data": AES_CBC_PKCS5}`，key/IV 硬编码
- 登录后 MMKV 明文 JSON 下发 zego_config / rong_cloud_config / oss_config
- 游客态 app_id=0、AppKey 空；登录后再拉一次做 diff

## 识别锚点（可搜，不要当标准答案）

- 包前缀 `io.rong` 量级数千 + `im.zego` + `libZegoExpressEngine.so`
- `com.adjust` + `libsigner.so` 符号 `Java_com_adjust_sdk_sig_NativeLibHelper_nSign`
- 字符串 `control.kochava.com`
- 注入字段：timestamp / uuid / is_root / is_vpn_conn / sim

## 曾验证过的事实（仅复盘本包时可用）

- 业务域藏在混淆类 `static final String`（XOR 解开）
- AES-CBC 16 字节 ASCII key + IV
- MMKV `app_info` 登录后才有真实 Zego appID、融云 AppKey、OSS bucket
