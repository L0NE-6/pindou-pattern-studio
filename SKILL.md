---
name: pindou-pattern-studio
description: |
  将人物、宠物、动漫角色或生活照片转换为可制作的 MARD 拼豆图纸。
  当用户说“转拼豆”“出图纸”“做25x25/30x30拼豆”“生成色号和用量”时使用。
  输出网格 CSV、带坐标的色号图、真实拼豆预览和用量清单。
metadata:
  category: lifestyle-creative
  tags: perler-beads,mard,pixel-art,image-to-pattern
---

# 拼豆图纸工坊

## 目标

把用户提供的图片转换为可以实际照着摆放的拼豆图纸。优先保留脸部、眼神、
发型轮廓、服装主色和关键配饰，不把图片当成普通低分辨率缩略图处理。

## 输入

- 图片文件
- 目标尺寸：默认 `30x30`
- 可选风格：人物、宠物、物品、图标
- 可选要求：必须保留的颜色、必须删除的背景、贴边黑轮廓

## 执行流程

1. 运行：

   ```bash
   python scripts/auto_pattern.py input.png --size 30 --name my-pattern
   ```

2. 查看 `output/my-pattern_preview.png`。如果脸部、眼睛或主轮廓失真，编辑
   `my-pattern_grid.csv`。只使用 `pattern_core.py` 中已有的 MARD 色号。

3. 对关键区域手工修版：

   - 外轮廓和贴边格必须使用 `H8`
   - 眼睛使用 `H8`、`H2`、`C13`、`C24` 和主发色的明暗层次
   - 人物脸部保留 `E16`，腮红使用 `E15`
   - 左右发色保持同一主色，暗部使用相邻深色
   - 避免孤立豆和只有一个像素宽的悬空结构

4. 重新渲染并校验：

   ```bash
   python scripts/render_pattern.py my-pattern_grid.csv --name my-pattern
   ```

5. 检查 `my-pattern_summary.json` 的 `outline_errors`。必须为空数组。

## 输出

- `<name>_chart.png`：带行列坐标和色号用量表的制作图
- `<name>_preview.png`：带拼豆圆片和中心孔的效果预览
- `<name>_grid.csv`：可继续编辑的色号网格
- `<name>_summary.json`：尺寸、颜色、豆数和轮廓校验

## 设计约束

- 不要用无关图片代替用户提供的原图。
- 不要把背景误当成主体。
- 尺寸越小，越应主动简化细节，但不能省略辨识度最高的特征。
- 修改后必须重新渲染并确认没有未知色号、越界或贴边非黑轮廓。
- 示例图纸位于 `examples/`，可作为人物类修版参考。

## 完成标准

同时满足以下条件才算完成：

1. 预览图主体可辨认；
2. 脸部和眼睛没有糊成色块；
3. 外轮廓闭合且贴边格为 `H8`；
4. 色号图、预览图、CSV 和用量清单全部生成；
5. `outline_errors` 为空。
