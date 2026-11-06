# anti-ppt-motion

面向口播解释视频的场景式 Motion Skill：连续空间、明确的景别变化，以及可复用的镜头代码。

本开发分支已完成新版的一对实际输出：未加载版展示完整图表，加载版从局部拉远到全貌。
所有者反馈“对比不是很强烈”，本轮不进入宣传片制作；尚无独立真人盲评。
旧版对照未显示令人信服的增益，失败记录保留；定向制作的参考片不作为实验结果。
[第一轮公开记录](https://github.com/luogao/anti-ppt-motion/releases/tag/experiment-v0.1)。

## Skill 实际包含什么

- [SKILL.md](SKILL.md)：调用后默认采用连续场景与近景到全貌的画面语言，用户明确要求优先。
- [镜头配方](references/shot-recipes.md)：局部事实、关系揭示、共同尺度比较和机制变化。
- [scene-world.tsx](assets/scene-world.tsx)：可复制到 Remotion 项目的 `CameraGroup`、`WorldBlock` 和正交投影。
- 场景承接、问题定位与按时间码返修参考。

这是方法加代码资源的包，当前验证工作流为 Codex 显式加载 + Remotion。
它不是只有提示词的实验，也没有更换两组的渲染引擎。空间代码仅依赖已有 React / Remotion；
不带字体、音乐、私有 Motion Kit、预渲染成片或当前测试题的完整场景。

## 使用

取得本次开发版（`main` 仍保留首轮版本）：

```sh
git clone --branch feat/resource-backed-skill --single-branch \
  https://github.com/luogao/anti-ppt-motion .agents/skills/anti-ppt-motion
```

将此目录放入项目的 `.agents/skills/anti-ppt-motion`，然后明确要求 Agent 使用其中的 `SKILL.md`，
提供自己的口播和素材。使用 Remotion 时，Agent 可按配方把 `assets/scene-world.tsx` 复制到项目源码并导入。
关键帧、对象、时间、数据和镜头表需要按实际内容生成；不是原样套用一个已经完成的视频。

Skill 的默认风格适合想要场景与运镜的 Motion 内容。用户要求静态图表、固定机位或严格还原时应遵从用户，
不把某一种视觉风格说成通用审美标准。必须保留事实、尺度、单位、可读性和结果阅读时间。

## 本轮对照怎么做

[协议](eval/resource-pilot.md)：两组共享 T2 数据题、同一配音、起点、依赖、模型和预算。
只给 B 组额外加载 Skill 包，并挂载它自带的源代码资源。两组各一次首稿、一次相同预算复核；
生成的 Scene 不经作者修改。所有版本与失败保留；后台系统上下文仍有无法完全验证相同的边界。

v0.4 两组的首稿与复核稿共 4 个版本均通过类型检查与渲染；最终两版解码音频一致。
加载版实际调用镜头资源，在约 1.43–3.03 秒从 2.1 倍近景拉到 1 倍全图；未加载版维持全图。
加载版仍为二维图表，本轮没有测出三维效果或理解提升。[本轮结果与限制](eval/resource-result-v04.md)。

资源和镜头约束的改动是产品迭代，不与旧版结果混算。此轮是选定案例的后续试跑，尚无独立真人盲评，
不能据此承诺所有题材、宿主或模型都更好。30 秒与 10 秒是视频中的教学数据，不是 Skill 制作速度。

```sh
npm ci --ignore-scripts --prefix examples/starter
python3 -m unittest discover -s tests
node tests/scene_world_check.cjs
python3 eval/run_resource_pilot.py --assets /path/to/cleared-assets \
  --output /path/to/new-output --browser /path/to/chromium \
  --browser-lock /path/to/shared-browser-wrapper
```

沿用首轮已获授权、已校验的素材清单。媒体与运行输出保留在 Git 之外。
实验脚本需要 Python、Codex CLI、Node、FFmpeg、Chromium 和共享浏览器锁；已测版本见历史协议。
历史 `eval/run.py` / `eval/run_scene_pilot.py` 的结果需对应其冻结源版本读取；新版使用上面的资源试跑入口。
[本期推广视频的证据与结构](eval/promotion-video.md)。

## License

[MIT](LICENSE) 适用于原创说明与源代码，包括空间与镜头模块。第三方软件和用户素材的许可分别处理。
未包含密钥、账号或配音模型标识、公司素材和商业音乐。
