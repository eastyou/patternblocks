# patternblocks · 图案积木裁剪片

[![CI](https://github.com/eastyou/patternblocks/actions/workflows/ci.yml/badge.svg)](https://github.com/eastyou/patternblocks/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)


用纯标准库生成 **A4 可打印的图案积木（pattern blocks）裁剪页** 与 **拼图挑战卡**：等边三角形、菱形、梯形、正六边形、正方形，全部使用统一边长，三角形族面积比严格为 1:2:3:6。

适合课堂教具、几何面积教学、学生作品集与家庭打印。

## 特性

- 五种积木统一边长（默认 30 mm，可在 15～60 mm 之间调整），三角形、菱形、梯形、正六边形可以无缝拼合。
- 面积由鞋带公式精确计算：`三角形:菱形:梯形:正六边形 = 1:2:3:6`（容差 1e-6）。
- 自动按行排版分页，包围盒互不重叠、不超出 A4 可用区域，并预留 2% 打印安全余量。
- 输出为单个 HTML：封面含面积对照表与图例，其后是裁剪页、10 道拼图挑战卡与答案页。
- 零第三方依赖，Python 3.9+，全部函数带类型注解。

## 安装

```bash
pip install -e .
```

也可以不安装，直接在仓库根目录运行：

```bash
python -m patternblocks -o blocks.html
```

## 使用

```bash
# 默认：五种形状各 6 片，边长 30 mm
patternblocks

# 自定义边长、数量与输出文件
patternblocks --side 45 --each 8 -o classroom.html

# 只打印三角形和菱形，不生成挑战卡
patternblocks --shapes 三角形,菱形 --no-challenges

# 修改标题
patternblocks --title "三年级几何教具"
```

| 参数 | 说明 | 默认值 |
| --- | --- | --- |
| `-o, --output` | 输出 HTML 路径 | `patternblocks.html` |
| `--side` | 统一边长（mm），范围 15～60 | `30` |
| `--each` | 每种形状数量，范围 1～12 | `6` |
| `--shapes` | 逗号分隔的形状名，中英文均可 | 全部五种 |
| `--no-challenges` | 不生成挑战卡与答案页 | 关闭 |
| `--title` | 文档标题 | `图案积木裁剪片` |

退出码：`0` 成功，`1` 写文件失败，`2` 参数错误（中文提示输出到 stderr）。

打印建议：A4、缩放 100%（1:1），沿实线轮廓剪下。

## 面积关系

统一边长 `s`：

| 形状 | 面积 | 相当于几个三角形 |
| --- | --- | --- |
| 等边三角形 | `√3/4 · s²` | 1 |
| 菱形（60°/120°） | `√3/2 · s²` | 2 |
| 梯形（下底 2s、上底 s） | `3√3/4 · s²` | 3 |
| 正六边形 | `3√3/2 · s²` | 6 |
| 正方形 | `s²` | `4/√3 ≈ 2.31` |

正方形虽然边长相同，但面积不落在 1:2:3:6 的整数倍体系中，因此单独说明。

## 项目结构

```
patternblocks/
├── patternblocks/
│   ├── __init__.py      # 包导出与版本号
│   ├── __main__.py      # python -m patternblocks
│   ├── model.py         # 顶点、面积、校验与分页排版
│   ├── render.py        # HTML/SVG 渲染
│   └── cli.py           # 命令行入口
├── tests/               # unittest 测试（模型 / 渲染 / CLI）
├── examples/            # 生成好的示例页面
├── pyproject.toml
└── .github/workflows/ci.yml
```

## 测试

```bash
python -m unittest discover -s tests -v
```

## 许可证

MIT License，Copyright (c) 2026 eastyou。
