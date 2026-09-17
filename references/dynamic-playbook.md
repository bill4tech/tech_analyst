# 动态分析手册

未获用户明确授权：禁止安装、自动登录、root 拉数据、打生产接口。

环境不够就降级，报告写原因。不要编证据。

## 降级树（从上到下选第一条能做的）

1. **root 读应用数据** — 登录前后 diff，性价比最高
2. **MITM 抓登录后配置** — 模拟器 tcpdump 常废；host 抓网卡 / HTTP Toolkit / 卸钉扎
3. **Frida hook** — 静态找不到解密函数、或密钥只在内存
4. **签名重放** — 仅当用户授权，且用一条 logcat 样例反验
5. **失败** — Header 标「动态：未执行」

## 模拟器前置

```
android_preflight / android_list_avds
```

- AVD **ABI 必须匹配** base（`aapt dump badging` 的 `native-code` 或 split 文件名）
- 首选 google_apis（`adb root` 可用），API 34+
- 无匹配 AVD / 非 rootable 镜像 → 跳过本阶段

```bash
adb wait-for-device
# 直到 getprop sys.boot_completed == 1
adb root
adb install-multiple -r base.apk split_*.apk    # 全部 split，漏 ABI 会崩
```

启动：

```bash
adb logcat -c
adb shell am start -n <包名>/<启动 Activity>    # Activity 来自 manifest
```

UI：`android_ui_describe` → `resolve` → `tap`。不要猜坐标。  
出海 App 的 Quick Login / Guest 常无验证码，是最省力路径。  
`dumpsys activity top` 确认主界面 resume。

权限弹窗可 `pm grant` 预授权。直播类冷启动常见：隐私协议 → 开屏广告「跳过」→ 引导页 → 主界面。

SystemUI ANR（「System UI isn't responding」）常是假象：`adb root` 后 `pidof com.android.systemui | xargs kill`，不要 force-stop 目标 App。

## 路径 1：root 拉数据

登录后等 5–10 秒让配置回包。

```bash
{skill_dir}/scripts/pull_app_data.sh <包名> runtime/guest     # 先游客
# …登录…
{skill_dir}/scripts/pull_app_data.sh <包名> runtime/authed
python3 {skill_dir}/scripts/compare_runtime.py runtime/guest runtime/authed
```

常见落点：`shared_prefs/`、`files/mmkv/`、`databases/`、`app_webview/`。  
MMKV 经常是明文 JSON，`strings` 即可。游客配置常是 app_id=0 / key 空。

TYDomain 系：`shared_prefs/domain_cache_*.xml`（当前域 + signType + token）。静态解密域名池后，用这份对照运行时选中域。token 跨 App 相同 → 同团队强证据（值来自**当前**拉取，不要填案例 token）。

## 路径 2：流量

模拟器内 tcpdump 经常抓不到虚拟网卡流量。优先：

- 宿主机抓 emulator 网卡
- HTTP Toolkit / mitmproxy + 用户 CA
- 若有钉扎：先在 jadx 确认 `CertificatePinner` / network security config，再考虑 objection 卸钉（需授权）

`/proc/<pid>/net/tcp6` 只能证明连过谁：IPv4 倒序字节；`::ffff:` 是 IPv4-mapped。`ipinfo.io` 查 ASN。不要把它当成抓包。

## 路径 3：Frida（可选）

本机无 frida 就跳过。有价值的 hook：

- `javax.crypto.Cipher.doFinal`
- OkHttp `Interceptor.intercept` / `RealCall`
- MMKV `decodeString`
- 已定位的自研 `decrypt`

把明文打到 log，再与路径 1 交叉验证。

## 路径 4：签名重放

见 `decrypt-recipes.md` 配方 E。验证算法用一条样例；新请求打生产需要单独授权。

## 证据最小集（做了动态才写进报告）

1. 密钥表：名称 → 值 → 来源文件/日志
2. 游客 vs 登录 diff
3. 主界面 Activity、关键 logcat 域名、（可选）进程连接 IP
