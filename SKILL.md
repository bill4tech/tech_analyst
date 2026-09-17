---
name: apk-deep-reverse
description: "对单个 Android APK/APKS/XAPK 做深度逆向：静态反编译、字符串/请求加密破解、模拟器动态运行、root 提取登录后服务端密钥、还原后端接口并输出 HTML 报告。仅在用户明确要密钥/接口/动态运行/深度逆向时使用；纯技术对标、多 APK 对比、只要 SDK 清单，改走 apk-reverse-analysis；目标是网站/网页/H5/JS 加密，改走 web-deep-reverse。触发词：深度分析apk、挖密钥、拿appKey、模拟器跑apk、抓取接口、安全分析apk、还原后端、登录后配置。"
---

# APK 深度逆向（静态 + 动态）

对**单个** APK 做：拆包 → 静态事实 → 加密破解 →（授权后）动态取证 → HTML 报告。

核心价值在动态层：Zego appID、融云 appKey、OSS 等常在**登录后由服务端下发**，静态永远拿不到。但动态成本高，默认不要跑。

**用途**：技术对标、安全评估、CTF。不用于攻击他人系统。

**边界**：本 skill 只管 Android 客户端。网站/网页/H5/浏览器侧的 JS 加密、接口签名、流媒体抓取 → `web-deep-reverse`。但两者共享方法论（签名重放、CDN auth_key、m3u8 验证），App 逆向进行到「宿主机重放接口/抓直播流」时，可直接引用 web-deep-reverse 的 `references/api-replay.md` 与 `scripts/cdn_sign.py`。

`{skill_dir}` = 本 skill 根目录。脚本一律 `{skill_dir}/scripts/...`，不要用 cwd 相对路径。

---

## 分流与门闩（先读再动手）

### 走错 skill 就停

满足任一条 → 改用 `apk-reverse-analysis`，或只做 ①–③ 出浅层结论：

- 多个 APK 对比 / 「技术对标」/ 只要 SDK 清单
- 用户没说密钥、接口、动态、模拟器、登录后配置
- 只给了文件夹、没指定要深挖哪一个
- **目标是网站/网页/H5/JS 加密/流媒体网站** → `web-deep-reverse`

### 高成本动作先问

未获本轮明确授权，禁止：

- 安装到模拟器、UI 自动登录、`adb root` 拉 `/data/data`
- 对真实后端做签名重放、批量打接口、拉直播流

用户只说「看看用了什么 SDK」≠ 授权动态。

### 工具缺失就降级，禁止会话里下大包

检查：`aapt`/`aapt2`、`adb`、`emulator`、`java`、`jadx`、`python3` + `androguard`。

- 缺 jadx：静态停在 aapt + `extract_info.py`，报告写「未反编译」
- 缺模拟器 / 无匹配 ABI 的 AVD / `adb root` 失败：跳过 ⑥，报告「动态：未执行 + 原因」
- **不要**在会话里 curl 下载 jadx zip（约 116MB）

### 证据纪律

- 禁止把 `references/cases/` 里的密钥、token、域名抄进**当前** App 报告
- 没跑动态就标「动态：未执行」，不要编 MMKV/连接证据
- 不确定写「疑似」；密钥分级：硬编码 / 服务端下发 / 猜测

---

## 流程

```
① 输入/工作目录 → ② 静态提取 → ③ 技术栈/壳/框架
→ ④ jadx（能跑才跑）→ ⑤ 加密破解
→ ⑥ 动态（已授权 + 环境够）→ ⑦ 验证/重放（已授权）
→ ⑧ HTML 报告（动态未做也要诚实写）
```

① 机械；②③④⑤ 静态；⑥ 灵魂但可跳过；⑦ 需额外授权；⑧ 必交付。

案例（Fita / 斗球）只在对上相同模式时读 `references/cases/`，当配方锚点，不当填空题。

---

## ① 输入与工作目录

支持 `.apk` / `.xapk` / `.apks`。

```bash
python3 {skill_dir}/scripts/unpack_apk.py "<输入文件>" "<work_dir>"
```

产物约定（后续步骤都写这里，可恢复：目录里已有产物就跳过）：

```
work/<pkg_or_stem>/
  input/      # base.apk + splits
  static/     # extract_info.json、manifest、secrets
  jadx/       # jadx 输出
  decrypt/    # 批量解密结果
  runtime/    # guest/ vs authed/ 拉取的应用数据
  report/
```

- `.apks`/`.xapk`：必须记下 **base ABI**，选 AVD 时匹配
- 漏装 ABI split → 运行崩溃（见动态手册）

---

## ② 静态提取

```bash
python3 {skill_dir}/scripts/extract_info.py "<base.apk>" --json > static/extract_info.json
aapt dump badging base.apk | grep -E "package|launchable-activity|sdkVersion|native-code"
aapt dump xmltree base.apk AndroidManifest.xml > static/manifest_tree.txt
python3 {skill_dir}/scripts/scan_secrets.py static/jadx 之前也可先扫 apk 解压目录、assets、xml
```

`extract_info.py` 只吐事实：包名/版本/SDK/权限/组件/类数/`package_prefixes`/框架标记/native/assets。

androguard 失败时用 aapt 保底，**不要**把解析失败直接写成「已加固」。壳判断见 ③。

便宜高收益（不必模拟器）：

- `assets/`、`res/raw/`、`google-services.json`、`network_security_config.xml`
- 导出组件 / deeplink / intent-filter
- so 的 `strings` 与导出符号
- 证书钉扎：`CertificatePinner`、pin-set、TrustKit

---

## ③ 技术栈 / 壳 / 框架

读 `package_prefixes`，对照 `references/sdk-signatures.md`。  
顺序：跨平台框架 → 壳 → IM/音视频/统计 → 工具库 → 产品形态。

**壳**：`class_count == 0` 只是线索。对照 `references/packers.md` 的 so/包名。已加固则静态业务代码到此为止，报告写清；动态脱壳超出范围，提示即可。

**RN / Flutter / Unity**：不要按「业务 Java 包很少」判无业务。读 `references/frameworks.md` 再继续。

自研占比 ≈ 业务前缀类数 ÷ 总类数。多 IM 共存时（融云+云信）别漏，运行时可能由 `imType` 切换。

---

## ④ jadx

本机已有 `jadx` 才跑：

```bash
jadx -j 6 --no-debug-info -d jadx/ base.apk    # 2 万类约数分钟，可后台
```

失败或未安装 → 跳过 ⑤ 的源码向破解，仍可扫 apk 内明文/xml/so。  
业务代码在 `jadx/sources/<业务包>/`；混淆目录用 grep，不要通读。

---

## ⑤ 加密破解

决策，不要一上来套 `.O("c","k")`：

1. 明文 / 资源 / manifest meta-data 已有
2. 开源字符串加密（StringFog 等）
3. 自研 XOR/AES，jadx 里看得到 `Cipher`/`Base64`
4. native 加密 → 标「需 Frida」，不要假装解完

配方与识别锚点：`references/decrypt-recipes.md`。  
对上 StringFog / 双参 Base64+XOR / AES 请求体 / meta-data 二次加密时，再打开对应小节。

```bash
python3 {skill_dir}/scripts/decrypt_strings.py jadx/sources --json > decrypt/strings.json
python3 {skill_dir}/scripts/scan_secrets.py jadx/sources assets/ > static/secrets.txt
```

先定位解密函数再批量；`--pattern` 在确认调用签名后传入。  
jadx 源码里 `"\n"` 常是字面反斜杠+n，解密前要还原，否则 base64 失败。

---

## ⑥ 动态运行（已授权才进入）

读 `references/dynamic-playbook.md`，按降级树选一条，不要默认 root+MMKV：

1. 能 root → 拉 prefs / MMKV / db（先游客，再登录，diff）
2. 能 MITM / 卸钉扎 → 抓登录后配置接口
3. 有 Frida → hook `Cipher.doFinal` / OkHttp / MMKV
4. 模拟器播不了且用户授权 → ⑦ 签名重放
5. 全失败 → 报告「动态未完成 + 原因」

```bash
{skill_dir}/scripts/pull_app_data.sh <包名> runtime/guest     # 登录前
# UI 登录后再拉
{skill_dir}/scripts/pull_app_data.sh <包名> runtime/authed
python3 {skill_dir}/scripts/compare_runtime.py runtime/guest runtime/authed
```

未登录常返回空壳（app_id=0、key 空）。别在游客态下结论「没有密钥」。

---

## ⑦ 验证与签名重放（额外授权）

默认验证：logcat 关键词、`/proc/<pid>/net/*` 证明连过谁（模拟器 tcpdump 常废）。  
host 侧抓 emulator 网卡 / HTTP Toolkit 优于只读 tcp 表。

**签名重放**：用 logcat **一条**样例反验算法即可。未授权不要对新 ts 批量打生产、不要 curl 拉流。算法见配方 E。path 不含 query。  
构造签名 URL / 验证 m3u8→TS 全链路时，直接用 `web-deep-reverse` 的工具：`{web_skill}/scripts/cdn_sign.py`（auth_key 生成）与 `{web_skill}/references/api-replay.md`（重放纪律 + 流媒体三层验证）。`{web_skill}` = `~/.agents/skills/web-deep-reverse`。

---

## ⑧ HTML 报告

读 `references/html-report.md`，CSS 用 `{skill_dir}/assets/report.css` 内联进单文件。  
命名 `<YYYYMMDD>-<HHmm>-deep-reverse.html`，写当前工作目录（或 `work/.../report/`），`open` 并告知路径。

必须含：基本信息、技术方案、第三方、安全体系、业务、权限、**动态章节（含未执行原因）**、复盘。  
Header 标明证据级别：静态 only / 静态+运行时文件 / 静态+抓包 / 含重放。

---

## 伦理

- 仅安全研究、对标、CTF
- 提取的密钥只用于验证分析，不用于攻击或薅羊毛
- 报告脚注：「仅用于技术研究与学习目的」
