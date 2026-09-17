# 字符串与请求加密破解配方

核心：**定位解密函数 → 确认算法 → 再批量**。不要假设方法名一定是 `.O(`。

真实 App 的密钥/域名样例在 `references/cases/`，禁止抄进当前报告。

## 1. 定位解密函数

```bash
grep -rnE 'Cipher\.getInstance|SecretKeySpec|javax\.crypto' jadx/sources | head
grep -rnE 'StringFog\.(decrypt|encrypt)|megatronking\.stringfog' jadx/sources | head
grep -rnE '\.(decode|decrypt|dec|d|O|a)\("[A-Za-z0-9+/]{8,}={0,2}"' jadx/sources | head
```

常见调用：单字母类.单字母方法 `("密文","密钥")`、`StringFog.decrypt`、Kotlin 静态方法、`new String(byte[])`。

确认本体后再：

```bash
python3 {skill_dir}/scripts/decrypt_strings.py jadx/sources --pattern '你确认的正则'
```

## 2. 配方

### A. Base64 + XOR（最常见）

```
plain = utf8( base64(cipher) XOR_cycle base64(key) )
```

jadx 输出里 `\n` 常是字面转义，先 `replace("\\n","\n")` 再 base64。

StringFog 默认变体算法相同，调用是 `StringFog.decrypt("c","k")`（或业务包代理类）。另有 `stringfog.aes` / `base64` / `custom`。

### B. AES 请求体

识别：`Interceptor.intercept()`、`"{\"data\":\""` 拼接、`AES/CBC/PKCS5Padding` 或 `Cipher.getInstance("AES")`（无 CBC → 常为 ECB）。

密钥/IV 多硬编码。体常包成 `{"data":"<base64>"}`。

### C. 其他

| 模式 | 识别 | 动作 |
|---|---|---|
| 纯 Base64 | 以 `=` 结尾的可见串 | 解码看是否 URL/JSON |
| AES-ECB | 无 IV，`Cipher.getInstance("AES")` | 找 key 字符串 |
| DES/3DES | `DES/` | 找 key/IV |
| 自定义替换表 | 非 base64 字符集 | 逆映射 |
| native | 解密只在 `.so` | 标需 Frida，勿假装完成 |

### D. manifest meta-data 二次加密

`<meta-data name="FOO" value="base64密文"/>` 的 key 可能是另一个 meta-data（`FOO_PW`）。

步骤：aapt 找成对 meta-data → grep 读取代码 → 看 `SecretKeySpec(pw.getBytes(),"AES")`。  
`Cipher.getInstance("AES")` 无 CBC/Padding → ECB。key 长度 16/24/32 → AES-128/192/256。

```bash
echo -n '<cipher_b64>' | base64 -d > c.bin
openssl enc -aes-192-ecb -d -K $(echo -n '<pw>' | xxd -p) -nopad -in c.bin
```

（算法确认后用当前 App 的值，不要用案例里的密文。）

### E. CDN/API 签名（验证算法即可）

动态域名框架常见 path+时间戳+token 的 MD5。

阿里云 authA 形态：

```
ts   = now/1000 + 有效秒数
hash = MD5( path + "-" + ts + "-0-0-" + token )
URL  += auth_key= ts-0-0-hash
```

**path 不含 query**（只到 `?` 前），把 query 算进去会 403 invalid md5hash。

authB 形态：`md5(token + yyyyMMddHHmm + path)` 进 URL 路径。

**授权边界**：logcat 捞**一条** `signUrl` 反验 md5 一致即够。未授权不要用新 ts 打生产、不要拉 m3u8/TS。

## 3. 网络层拦截器

找 `implements Interceptor`，记录：

- Header（Authorization、版本、平台、Data-Encode 等）
- Body 是否 AES 包裹
- 注入字段：timestamp、uuid、设备、root/vpn/sim

顺带还原环境检测（su 路径、Magisk 包名、`TYPE_VPN`、`Build.FINGERPRINT`）。

## 4. 解密结果过滤优先级

1. `http(s)` → API/CDN/政策页（域名常在混淆类 `static final String`）
2. `appId` / `appKey` / `token` / `secret`
3. `/api/` `/v1/` `/v2/`
4. 长字符串可能是材料，**不要**用过宽词（`app`/`dev`）当默认过滤

## 5. 脚本

```bash
python3 {skill_dir}/scripts/decrypt_strings.py <jadx_sources> [--pattern REGEX] [关键词]
python3 {skill_dir}/scripts/decrypt_strings.py --pair "密文" "密钥"
python3 {skill_dir}/scripts/scan_secrets.py <dir...>
```
