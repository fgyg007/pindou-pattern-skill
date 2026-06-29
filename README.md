# 拼豆图纸生成器 / Perler-Bead Pattern Maker

一个 [Claude Code](https://claude.com/claude-code) **Skill**：把一张**图片**或一张**现成图纸**，变成干净可用的拼豆图纸，并自动产出三样东西——

- 🧩 **可编辑的网页工具**（像素网格，能在浏览器里改色、微调）
- 🖨️ **1:1 可打印 PDF**（按 100% 打印后，正好对得上你手里的拼豆板）
- 📋 **用料清单**（每种颜色各需要多少颗豆）

> 核心是**物理精确**：PDF 按实际尺寸打印后，每个格子中心间距 = 一颗豆的间距，把真板子盖上去就能直接拼。

支持「咕卡像素图」「Hama / 拼豆 / Perler / Fuse bead」这类需求。

---

## 一、安装

> 前提：你已经装好 Claude Code。

把仓库直接克隆到 Claude Code 的用户级 skills 目录即可：

```bash
git clone https://github.com/fgyg007/pindou-pattern.git ~/.claude/skills/pindou-pattern
```

然后 **重启 Claude Code（或开个新会话）**，让它加载这个新 skill。

装完装一下脚本依赖（只需要两个包）：

```bash
pip install -r ~/.claude/skills/pindou-pattern/requirements.txt
```

> 想让 PDF 上显示中文颜色名，系统里最好有 Noto Sans CJK 字体；没有也不影响，色号和数量照样打印。

---

## 二、怎么用

装好后，**直接用大白话跟 Claude 说就行**，它会自动调用这个 skill。例如：

- 「把这张图做成拼豆图纸」（然后把图片发给它）
- 「这张图纸帮我清理一下，重新生成干净的版本」
- 「我要一张 52×52 的图纸，能 1:1 打印贴着板子拼」
- 「算一下这个图案每种颜色要多少颗豆」

也可以显式调用：`/pindou-pattern`。

Claude 会**先看图、设参数、生成预览，再根据效果反复调整**，最后把网页工具、PDF 和用料清单一起给你。

### 什么图效果好？

- ✅ **单个清晰主体**（卡通、贴纸、emoji、logo、像素画）转出来很漂亮。
- ⚠️ **复杂照片 / 多主体场景**在 52×52 的分辨率下很难做干净——这是分辨率的硬限制，没有方法能绕过。这种情况建议只聚焦一个主体，或者把图纸做大一点。

---

## 三、打印对不上板子？

90% 的原因是**打印缩放**，不是图纸本身。

- PDF 里自带一条 **100mm 校准线**。
- 打印时一定选 **「实际尺寸 / 100%」**，不要选「适应页面 / Fit to page」。
- 打完用尺子量一下那条校准线是不是 100mm，对了就能贴板子拼。

标准板参数：`52 点 / 宽 140mm → 间距 2.745mm`。

---

## 四、手动跑脚本（可选）

平时让 Claude 自动跑就行。想自己跑也可以，进 `scripts/` 目录：

```bash
# 图片 → 图纸（先出预览，再迭代）
python scripts/image_to_pattern.py 输入.png --out grid.json --preview prev.png --cells 52 --bg transparent

# 现成图纸 → 清理后的网格
python scripts/parse_sheet.py 图纸.png --rows 52 --cols 52 --bounds X0 Y0 X1 Y1 --out grid.json --preview prev.png

# 1:1 可打印 PDF
python scripts/make_pdf.py grid.json --out 拼豆图纸_52x52.pdf --dots 52 --span 140

# 可编辑网页工具
python scripts/build_tool.py grid.json --out 拼豆工具.html
```

完整工作流见 [`SKILL.md`](SKILL.md)，调色板与取值说明见 [`references/workflow.md`](references/workflow.md)。

---

## License

[MIT](LICENSE) — 随便用、随便改、随便分发。
