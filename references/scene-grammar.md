# 把多拍内容编排成场景

先写“事实怎么被看见”，再写“画面长什么样”。下面是衔接方法，不是三套可重复换字的版式。按内容选一种或组合，不要求全用。

| 编排 | 主体怎样承接 | 取景为什么改变 | 检查重点 |
|---|---|---|---|
| 跟随到原因 | 同一对象从入口经过路径，在瓶颈处受阻 | 跟随对象，让阻挡发生在眼前 | 受阻原因可见；对象没有在转场中消失 |
| 局部到全貌 | 先看一个具体样本，再揭示它所在的整体关系 | 扩大视野让此前看不见的上下游进入画面 | 被揭示的空间与原主体有关，不是缩小一张卡片腾位置 |
| 在原地改写机制 | 保留对象和空间，只改变限制条件或处理方式 | 把变化处拉到注意中心，再看结果传回整体 | 结果由机制变化引起，不能切到一个无关的“成功”页面 |
| 同基准显出差异 | 保留共同标尺、对象和观察位置 | 重构相邻空间或叠合对照，让差异直接被看见 | 标尺、数据、时间条件相同，视点不制造假优势 |

## 用可执行的节拍记录代替风格词

差的记录：“快节奏、有空间感、高级一点；第二段换个标题。”

可制作的记录：“先在近景看同一物体完成一次操作；沿它的路径后退，露出上游正在累积的对象，操作节奏保持原速；改变瓶颈处的机制，跟随原来的对象走通，最后扩大视野确认积累正在减少。”

其中的物体、操作和关系应来自当前内容。不要照搬这个故事到没有瓶颈的论题。证据是录屏时，保留真实界面与操作，使用取景和标注引导观看，不补造功能。

一条最小节拍记录可以是：

> 时间／口播词 → 观众新理解 → 可见事件 → 主体保留什么身份 → 如何接到下一拍

## 一个世界，多种取景

同一个世界里，对象位置与相互关系持续存在。镜头靠近操作点、跟随正在移动的主体，或扩大视野揭示上下游；这样运动本身增加了信息。不要先堆出几张完整海报，再让相机在海报之间滑动。

Remotion 中可把世界画在同一个绝对定位容器中，镜头控制该容器的偏移与缩放。下面只示范坐标关系；主体、轨迹、关键帧和停留时间必须根据实际口播设计：

```tsx
const frame = useCurrentFrame();
const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;
// x/y are world coordinates at the center of the viewport.
const x = interpolate(frame, cameraFrames, cameraX, clamp);
const y = interpolate(frame, cameraFrames, cameraY, clamp);
const zoom = interpolate(frame, cameraFrames, cameraZoom, clamp);
return <AbsoluteFill style={{overflow: 'hidden'}}>
  <div style={{position:'absolute', left:0, top:0,
    transformOrigin:'0 0',
    transform:`translate(${width/2-x*zoom}px, ${height/2-y*zoom}px) scale(${zoom})`}}>
    {/* Persistent objects and relationships in world coordinates. */}
  </div>
</AbsoluteFill>;
```

使用镜头并不自动消除 PPT 感。每个镜头动作都要能回答“这次多看见了什么，为什么现在要看”。主体占屏大小、文字可读性和结果停留必须实际检查，不能为了制造对比而把另一版压暗、裁小或加速。
