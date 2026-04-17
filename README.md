# 基于暗通道先验的多算法图像去雾系统

基于 PySide6 的桌面端图像去雾系统，提供 6 种去雾算法、实时参数调节、质量评估指标计算等功能。

## 环境要求

- Python 3.10+
- 依赖见 `requirements.txt`

```
pip install -r requirements.txt
```

## 启动

```
python main.py
```

## 功能概览

### 支持的去雾算法

| 算法 | 说明 | 可调参数 |
|------|------|---------|
| 暗通道去雾 | 经典 DCP (Dark Channel Prior) | 窗口大小、去雾强度、透射率下界 |
| 引导滤波 DCP | 引导滤波优化透射率 | 窗口大小、滤波半径、正则化、去雾强度、透射率下界 |
| Retinex 去雾 | MSR / SSR 模式可选 | 模式、sigma_1/2/3 |
| CLAHE 去雾 | 限制对比度自适应直方图均衡化 | 对比度限制、网格大小 |
| 改进型改进 DCP | 带天空区域检测的增强 DCP | 窗口大小、滤波半径、正则化、去雾强度、透射率下界、天空阈值、亮度阈值 |
| 暗通道改进 | 自适应模板 + 改进大气光估计 + 天空区域透射率修正 | 去雾强度、透射率下界、滤波半径、正则化 |

### 质量评估指标

-  PSNR / SSIM / MSE / 处理耗时
-  对比度 σ / 色调还原 d / 有效细节 I / 结构信息 S / 综合指标 q
  - 综合指标公式: `q = S × I_valid × d × σ / 10`

### 界面交互

- **手动应用**: 调整参数后需点击"应用"按钮才触发处理，不会因滑块变化而自动处理
- **操作历史**: 支持多步撤销，带时间戳记录
- **图像对比**: 原图与结果并排显示，支持拖拽打开图像
- **快捷键**: Ctrl+O 打开 / Ctrl+S 保存 / Ctrl+R 重置

## 项目结构

```
v5/
├── main.py                  # 程序入口
├── requirements.txt         # 依赖列表
│
├── core/                    # 算法核心层
│   ├── registry.py          #   算法注册表（数据驱动，新增算法无需改 UI）
│   ├── dark_channel.py      #   暗通道去雾 (DCP)
│   ├── guided_filter.py     #   引导滤波
│   ├── retinex.py           #   Retinex 去雾
│   ├── clahe_dehaze.py      #   CLAHE 去雾
│   ├── improved_dcp.py      #   改进型改进 DCP
│   ├── paper_improved.py    #   暗通道改进算法
│   ├── metrics.py           #   PSNR / SSIM / MSE 计算
│   ├── evaluation.py        #   论文 5 项评价指标
│   ├── worker.py            #   后台线程管理
│   └── utils.py             #   工具函数
│
└── ui/                      # UI 层
    ├── app_controller.py    #   应用控制器（业务逻辑）
    ├── main_window.py       #   主窗口（纯布局）
    ├── theme.py             #   暗色主题样式
    └── widgets/
        ├── param_panel.py   #     参数面板（药丸按钮 + 滑块）
        ├── metrics_panel.py #     质量评估面板（两列网格）
        ├── history_panel.py #     操作历史面板（带时间戳）
        ├── image_viewer.py  #     图像对比视图
        └── histogram_widget.py #  直方图组件
```

## 架构设计

```
┌─────────────────────────────────────────────────┐
│  MainWindow (纯 UI 布局，零业务逻辑)              │
│  ┌──────────┐  ┌──────────┐  ┌──────────────┐  │
│  │ CompareView│  │ParamPanel│  │ MetricsPanel │  │
│  │  (图像显示) │  │(参数调节) │  │ (质量评估)    │  │
│  └──────────┘  └──────────┘  └──────────────┘  │
│  ┌──────────────────────────────────────────┐   │
│  │ HistoryPanel / LogPanel                   │   │
│  └──────────────────────────────────────────┘   │
└─────────────────┬───────────────────────────────┘
                  │ 信号/回调
┌─────────────────▼───────────────────────────────┐
│  AppController (业务逻辑层)                       │
│  图像状态 / 参数收集 / 线程调度 / 指标计算         │
└─────────────────┬───────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────┐
│  WorkerManager → PreviewWorker (QThread)         │
│  后台执行算法，序号机制过滤过期结果                │
└─────────────────┬───────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────┐
│  AlgorithmRegistry (注册表，数据驱动)              │
│  算法文件末尾 register() → UI 自动生成控件        │
└─────────────────────────────────────────────────┘
```

## PyInstaller打包发布

```bash
pip install pyinstaller
```

```bash
pyinstaller --name "图像去雾系统" ^
            --onefile ^
            --windowed ^
            --add-data "images;images" ^
            --noconfirm ^
            main.py
```

参数说明：

| 参数 | 作用 |
|------|------|
| `--name` | 生成的 exe 文件名 |
| `--onefile` | 打包为单个 exe 文件 |
| `--windowed` | 不弹出命令行黑窗口（GUI 程序必须加） |
| `--add-data "images;images"` | 打包 images 文件夹（Windows 用 `;` 分隔） |
| `--noconfirm` | 覆盖已有输出目录，无需手动确认 |

> **macOS / Linux** 用户请将 `;` 改为 `:`，即 `--add-data "images:images"`，并去掉 `^` 换行符改用 `\`。

#### 3. 获取产物

```
dist/图像去雾系统.exe    ← 双击即可运行
```

> 打包后 exe 文件约 150~250 MB（含 Python 解释器 + PySide6 + NumPy + OpenCV）。