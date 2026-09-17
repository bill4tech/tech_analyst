# 跨平台框架分支

`framework_markers` 或包前缀命中后，**不要**用「Java 业务类很少」判定无业务逻辑。

## React Native

信号：`assets/index.android.bundle`、`com.facebook.react`、Hermes `libhermes.so`。

- 业务在 JS bundle，不在 `jadx/sources/<业务包>`
- 文本 bundle 可直接搜 URL/key；Hermes 字节码需额外反编译（本 skill 不强制，报告写「Hermes bundle，未反编译」）
- 原生侧仍可能有 IM/音视频 SDK 与登录后配置，动态层照旧有价值

## Flutter

信号：`assets/flutter_assets`、`io.flutter`、`libapp.so` / `libflutter.so`。

- Dart 在 AOT snapshot（`libapp.so`），jadx 几乎看不到业务
- 可 `strings libapp.so` 扫 URL；完整还原超出范围
- 插件仍可能带 Java 层密钥读取 + 登录后 MMKV，动态层仍值得做

## Unity / Cocos / Xamarin

- Unity：`libunity.so`、`assets/bin/Data` — 逻辑在 IL2CPP/Mono
- Cordova：`assets/www`
- Xamarin：`assemblies` / `libmonodroid`

报告标明框架，静态 Java 分析降级为 SDK/壳/权限；需要的话动态照降级树做。
