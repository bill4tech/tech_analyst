# 加固 / 壳识别

`extract_info.py` 的 `class_count == 0` **只是线索**（androguard 崩、multidex 解析失败也会是 0）。结合 so 名、包名、assets。

有 APKiD 更好：`apkid base.apk`。没有就靠下表。

## 厂商信号

| 信号 | 可能 |
|---|---|
| `libshell*.so` / `libDexHelper*.so` / `com.tencent.StubShell` / `libshella` | 腾讯乐固 |
| `libjiagu.so` / `libjiagu_a64.so` / `com.qihoo.util` | 360 加固 |
| `libsecexe.so` / `libsecmain.so` / `libSecShell.so` | 梆梆 |
| `libitsec.so` / `ijiami` / `libexec.so` + ijiami 资源 | 爱加密 |
| `libbaiduprotect.so` | 百度 |
| `libnesec.so` / 网易易盾 | 网易 |
| `libnllvm.so` / 娜迦 | 娜迦 |
| `libprotectClass.so` / 阿里聚安全 | 阿里 |
| `libvdog.so` / 几维 | 几维 |
| `assets/dexopt` + 极少 ClassDef | 通用加壳 |

## 流程

- 已确认加固：静态不要假装有业务 Java；报告「已加固，业务 DEX 不可用」
- 仍可分析：权限、组件、native 列表、明文 assets、壳本身
- 动态脱壳（Frida dump DEX 等）超出本 skill，提示用户即可
