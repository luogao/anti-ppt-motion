# anti-ppt-motion

让画面参与解释的 Agent Skill：主体变化、视觉证据、口播锚点和按时间码返修。

An instruction-only skill for narrated motion videos. It helps agents make
objects, evidence and relationships carry the explanation instead of relying
on successive text slides. Fixed shots, text and pauses remain valid choices.

**Status:** v0.1 work in progress. The controlled experiment and human blind
review are tracked in [eval/results.md](eval/results.md). No improvement claim
is made before results exist. First target: Codex + Remotion; other hosts have
not been validated.

## 安装与使用

在你自己的项目里放入这份 Skill（不要在正在进行 A/B 的两组共享配置里安装）：

```sh
git clone https://github.com/luogao/anti-ppt-motion .agents/skills/anti-ppt-motion
```

对 Agent 明确说明：

> 使用 `.agents/skills/anti-ppt-motion/SKILL.md`。根据这段口播和素材，做一段
> Motion 视频。先确定观众要理解什么，让对象变化、证据或关系参与表达；
> 实际检查产物，再指出最需要修改的时间段。

入口：[SKILL.md](SKILL.md)。需要时读取动作方法、反例或观看与返修参考。
Skill 本身没有 npm 依赖、不带私有组件，也不需要云端渲染服务。制作和渲染
仍由用户已有工具负责。可使用我们的 [Remotion 最小起点](examples/starter)。

## 首版内容

- 四种动作方法：状态变化、路径与因果、积累与释放、差异揭示。
- 画面问题到具体修正的对应；避免把“永远在动”变成审美规则。
- 三个公开教学简报：[队列](examples/queue.md)、[比较](examples/comparison.md)、
  [产品流程](examples/product-flow.md)。
- [固定条件比较协议](eval/protocol.md)和全量结果记录。

对照 A/B 中，两组共享同一份据官方文档整理的 Remotion 技术基线；这不是
完整官方 Skills 包。B 的唯一额外输入是这份 Skill 包。首稿与相同预算后的
终稿分开保存。我们不会故意要求 A 制作 PPT，也不会只展示最好的一对。

## 验证边界

格式校验、渲染成功和浏览器播放不能证明观众理解有所改善。静帧检查不能
替代完整动态观看。原始模型输出具有随机性：重渲已有源文件与重新生成
作品，是两种不同的复现。

测试材料里的数据和界面均标为教学模拟，不是任何真实产品的效率承诺。
介绍视频的结构见 [eval/episode.md](eval/episode.md)。

## 开发检查

```sh
python3 -m unittest discover -s tests
cd examples/starter
npm ci --ignore-scripts
npm run check
```

## License

[MIT](LICENSE) covers this repository's original instructions and code.
Third-party tools, packages and their licenses remain separate. No private
Motion Kit code, company assets or commercial music is included.
