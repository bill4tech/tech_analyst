# 案例锚点：斗球体育（仅当模式对上时读）

禁止把本文件中的 token、AppKey、域名填进**其他** App 的报告。

## 模式

- StringFog 代理类 `*.StringFog.decrypt("c","k")`，默认 Base64+XOR
- manifest `RONG_CLOUD_APP_KEY` + `RONG_CLOUD__APP_KEY_PW`：密文 + 另一项当 AES 密钥
- `Cipher.getInstance("AES")` 无 CBC → AES-ECB，PW 的 UTF-8 字节作 key（长度 24 → AES-192）
- `com.bfw.tydomain`：分级域名池 + CDN 签名；运行时 `domain_cache_*.xml`
- 多 IM：融云 + 网易云信，服务端 `imType` 切换
- 直播拉流：阿里云 authA，path **不含** query；模拟器播不了则宿主机重放（需授权）

## 识别锚点

- `com.github.megatronking.stringfog`
- `DomainBean` / `DomainCacheManager` / `CDNSignature` / `AliyunCdnAuth`
- 华为云 OBS `app_<env>.json`、npm 镜像做资源热更新
- 极验 / 活体 so（主播认证）

## 同源判定

域池 token 若与另一 App **当前拉取值**相同 → 同团队。不要用本案例记住的 token 去「证明」无关包。
