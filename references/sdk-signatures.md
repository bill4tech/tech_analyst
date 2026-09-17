# SDK / 包名前缀签名表

用 `package_prefixes`（类名前缀计数）对照此表。数字只表示「深度集成时量级」，看相对占比，不要用某次案例的绝对数当标准。

跨平台命中后读 `frameworks.md`。壳/加固 so 读 `packers.md`。

## 跨平台框架

| 包名/文件信号 | 结论 |
|---|---|
| `index.android.bundle` in assets、`com.facebook.react` | React Native |
| `flutter_assets`、`io.flutter` | Flutter |
| `libunity.so`、`com.unity3d` | Unity 游戏 |
| `cordova` in assets、`org.apache.cordova` | Cordova |
| `mono`、`Xamarin` | Xamarin |
| 无以上 + 大量 `kotlin` 类 | Kotlin 原生 |

## IM 即时通讯

| 前缀 | SDK | 备注 |
|---|---|---|
| `io.rong.imlib` / `io.rong.imkit` | 融云 RongCloud | 深度集成时类数可达数千；appKey 常由服务端下发；libRongIMLib.so 是铁证 |
| `cn.jiguang.im` | 极光 IM | |
| `com.tencent.imsdk` | 腾讯 IM | |
| `com.netease.nimlib` / `com.netease.nim` | 网易云信 NIM | 注意与网易云音乐等其他网易系区分；manifest 的 `com.netease.nim.appKey` 明文常见 |
| `com.jmessage` / `cn.jmessage` | 极光 JMessage | |

**多 IM 共存提示**：大厂模板 App 可同时集成融云 + 网易云信（斗球体育实证：io.rong 749 类 + com.netease 1139 类），运行时由服务端下发的 `imType` 切换，别因一个占主导漏掉另一个。

## 音视频 / 直播

| 前缀 | SDK | 备注 |
|---|---|---|
| `im.zego.zegoexpress` / `com.zego.zegoavkit2` | 即构 Zego | libZegoExpressEngine.so；appID 常由服务端下发 |
| `com.tencent.liteav` / `com.tencent.trtc` | 腾讯 TRTC/短视频 | libliteavsdk.so |
| `org.webrtc` | WebRTC | |
| `cn.rongcloud.rtc` | 融云 RTC | |
| `com.agora` | Agora 声网 | |
| `tv.danmaku.ijk.media` / libijkffmpeg+ijkplayer+ijksdl | ijkplayer | 直播播放常用；可能同时有 libtxplayer/txffmpeg（TXPlayer） |
| librtmp-jni.so | RTMP 推拉流 | 直播/连麦 |

## 验证码 / 风控 / 活体

| 前缀 | SDK | 备注 |
|---|---|---|
| `com.geetest` / assets 里 gt4.js / libgtc4core.so | 极验 GeeTest（含 4 代） | 登录/发码硬前置；captchaId 常运行时下发存 SharedPreferences |
| libLivenessModule.so | 活体检测 | 直播/社交 App 主播认证、实名场景 |
| `com.getkeepsafe` | 开源 relinker（so 重链接） | 非风控，勿误判 |

## 归因 / 统计

| 前缀 | SDK | 备注 |
|---|---|---|
| `com.adjust.sdk` | Adjust | libsigner.so 的符号 `Java_com_adjust_sdk_sig_NativeLibHelper_nSign` 是铁证 |
| `com.kochava` / `control.kochava.com` 字符串 | Kochava | |
| `com.appsflyer` | AppsFlyer | |
| `com.google.firebase.analytics` | Firebase Analytics | |
| `com.umeng` | 友盟 | 可能带 libumeng-spy.so（间谍式数据采集）；友盟分享 UI 常被误认成主业务 |
| `cn.thinkingdata` / `cn.data` | 数数科技 | |
| `com.mixpanel` | Mixpanel | |
| `com.tencent.bugly` | Bugly 崩溃 | |
| `io.openinstall` / manifest `com.openinstall.APP_KEY` | openinstall | 国内渠道归因（App 内可复现场景还原） |

## 国内大厂 / 基础设施

| 前缀 | SDK |
|---|---|
| `com.tencent.mmkv` | 腾讯 MMKV（KV 存储，libmmkv.so） |
| `com.tencent.pag` / `libpag` | 腾讯 PAG 动画 |
| `com.aliyun` / `com.alibaba.sdk.android.oss` | 阿里云 OSS |
| `com.huawei.hms` | 华为 HMS |
| `com.hihonor` | 荣耀 |
| `com.samsung` | 三星 |
| `com.bytedance` | 字节系 |

## 动态域名 / CDN 容灾（TYDomain 系，重点）

| 前缀 | SDK | 备注 |
|---|---|---|
| `com.bfw.tydomain` | TYDomain 动态域名框架 | 域名池 + 多 CDN 签名 + Ping 测速容灾；域名常从华为云 OBS `app_<env>.json` 下发 |
| `com.bw.tmapmanager` | 同系 CDN 管理（TmapDomainsManager） | 与 tydomain 配套出现 |
| `com.bfw.*` 其他 | bfw 系 SDK | **域池 token 跨 App 复用是同团队铁证**（值必须来自当前包，见 cases 仅作模式说明） |

CDN 签名类锚点：`AliyunCdnAuth`（authA/authB）、`TencentCdnAuth`、`HuaWeiCdnAuth`、`CDNSignFactory` —— 见 decrypt-recipes.md 配方 E。

## 工具库

| 前缀 | 用途 |
|---|---|
| `com.github.megatronking.stringfog` | **StringFog 字符串加密框架**（Base64+XOR 默认变体，另有 AES/base64/custom）；业务类常见 `xxx.StringFog` 代理类 |
| `com.hjq` | 安卓工具集（shape 布局/权限/窗口） |
| `xyz.doikki.videoplayer` | DoDoPlayer 视频播放器（封装 ExoPlayer/IJK） |
| `com.opensource.svgaplayer` | SVGA 动画（直播礼物常用） |
| `com.drake.net` | DrKNet 网络库 |
| `razerdp.basepopup` | BasePopup 弹窗 |
| `com.bumptech.glide` | Glide 图片加载 |
| `com.squareup.okhttp3` / `okhttp3` | OkHttp |
| `com.squareup.retrofit2` | Retrofit |
| `com.google.gson` | Gson |
| `com.google.protobuf` | Protobuf |
| `com.google.zxing` | 二维码扫描 |
| `com.google.android.exoplayer2` / `androidx.media3` | ExoPlayer/Media3 |
| `com.github.danikula` | AndroidVideoCache 视频缓存 |
| `com.airbnb.lottie` | Lottie 动画 |
| `com.hpplay` | 乐播投屏（直播/视频 App 大屏投屏，类数可能上千） |

## 产品形态快速推理

- AI 聊天：包名含 chat/ai/companion + 大量 SSE/WebSocket + 角色类
- 社交/直播：IM SDK + 音视频 SDK + SVGA 礼物 + 金币/钱包类
- **体育直播/博彩**：赛事/比分类（match/score/odds）+ 直播播放器（ijk/LiteAV）+ 竞猜/让球/大小球类 + 主播/礼物类 + 极验验证码 + 动态域名（域名常被投诉轮换）+ 活体检测
- 工具：权限少 + 功能集中 + 类数小
- 游戏：Unity/Cocos + 大量 so
- 出海 App 常见组合：融云/Zego + Adjust/Kochava 双归因 + Firebase + Google Billing + 阿里云 OSS

## 加密相关识别

- 包名含 `encrypt` / `crypto` / `sign` / `encode` 的类 → 加密实现
- `libsigner.so` 存在：先看符号，若是 Adjust 的 NativeLibHelper 则是归因签名库，不是自研加密
- `com.facebook.crypto` → 或 Facebook Conceal
