# RenalLens

**How Complete-Case Analysis and Imputation Shape Patterns in Chronic Kidney Disease Data**\
**缺失值处理对慢性肾病临床指标分布及相关性估计的影响**

RenalLens is a group project for **DSC5002 — Exploratory Data Analysis and Visualization** at City University of Hong Kong. We examine how missing-value handling changes the patients represented in a dataset, the distributions of clinical measurements, and the relationships visible in exploratory plots.

RenalLens 是香港城市大学 **DSC5002 — 探索性数据分析与可视化**课程的小组项目。我们研究缺失值处理如何改变数据所代表的患者构成、临床指标的分布，以及探索性图表中呈现的变量关系。

**Group / 小组：C61, Group 65**\
**Documents / 项目文档：[Bilingual proposal / 中英双语提案](docs/proposal.md) · [Proposal PDF / 提案 PDF](docs/DSC5002_CKD_Proposal.pdf)**

## Project status / 项目状态

The repository contains the proposal, a shared Python development environment, and a Windows setup script. The four analysis files (`data_preprocess.py`, `pipeline.sh`, `test.py`, and `train.py`) are currently empty placeholders; data cleaning, analysis, plotting, and an end-to-end pipeline are still to be implemented. The workflow below describes the agreed project plan. The `train.py` filename is a placeholder and does not imply that a predictive model has been implemented or is required.

仓库目前包含项目提案、统一的 Python 开发环境和 Windows 配置脚本。四个分析文件（`data_preprocess.py`、`pipeline.sh`、`test.py`、`train.py`）仍为空占位文件；数据清洗、分析、绘图和完整流水线有待实现。下文的分析流程描述项目计划。`train.py` 只是预留文件名，不代表已实现预测模型，也不表示项目必须开展模型训练。

## Research questions / 研究问题

1. **Missingness and representation.** Which variables have the most missing values, and how does complete-case deletion change the composition of the CKD and non-CKD groups?\
   **缺失情况与样本代表性。** 哪些变量缺失最多？删除不完整记录后，CKD 组与非 CKD 组的样本构成如何变化？
2. **Distributions and associations.** How do complete-case analysis and simple imputation affect selected clinical measurements and their relationships?\
   **分布与变量关联。** 完整病例分析和简单填补会怎样影响所选临床指标的分布及相互关系？
3. **Interpretation of plots.** How do skewness, extreme observations, transformations, and measurement scales affect individual-variable and multivariate plots?\
   **图表解读。** 偏度、极端观测值、变量变换和测量尺度会怎样影响单变量及多变量图表的解读？

## Dataset / 数据集

We use the public [Chronic Kidney Disease dataset from the UCI Machine Learning Repository](https://archive.ics.uci.edu/dataset/336/chronic+kidney+disease), DOI: [10.24432/C5G020](https://doi.org/10.24432/C5G020). Each row represents one patient record. The [official CSV](https://archive.ics.uci.edu/static/public/336/data.csv) is the input specified in the proposal.

我们使用 UCI 机器学习库公开的 [Chronic Kidney Disease 数据集](https://archive.ics.uci.edu/dataset/336/chronic+kidney+disease)，DOI：[10.24432/C5G020](https://doi.org/10.24432/C5G020)。每行代表一条患者记录，提案指定的输入为 [UCI 官方 CSV](https://archive.ics.uci.edu/static/public/336/data.csv)。

| Item / 项目 | Description / 说明 |
| --- | --- |
| Size / 规模 | 400 patient records; 24 explanatory variables and one class label / 400 条患者记录，24 个解释变量和 1 个类别标签 |
| Groups / 分组 | 250 CKD and 150 non-CKD records / CKD 组 250 条，非 CKD 组 150 条 |
| Main measurements / 主要指标 | Hemoglobin (`hemo`), serum creatinine (`sc`), blood urea (`bu`), blood glucose (`bgr`), and blood pressure (`bp`) / 血红蛋白、血清肌酐、血尿素、血糖和血压 |
| Data-quality issues / 数据质量问题 | Missing entries, inconsistent whitespace, coded categories, and different measurement scales / 缺失项、空白字符不一致、类别编码和测量尺度差异 |
| Data license / 数据许可 | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/), as stated by UCI / 依 UCI 页面标注，采用 CC BY 4.0 许可 |

The proposal's preliminary audit reports **158 complete records: 43 CKD and 115 non-CKD**, after requiring all 24 explanatory variables to be present. The CKD share changes from **62.5% to 27.2%**. These are sample proportions, not estimates of population disease prevalence. See the [proposal](docs/proposal.md) for the scope of this preliminary observation.

提案中的初步核查表明：要求全部 24 个解释变量均有观测值后，保留 **158 条完整记录，其中 CKD 组 43 条、非 CKD 组 115 条**，CKD 样本占比从 **62.5% 降至 27.2%**。这些数值描述样本构成，不能用于估计总体患病率。该初步观察的具体范围见[提案](docs/proposal.md)。

## Planned analysis / 分析计划

### Three data views / 三种数据视角

| View / 视角 | Definition / 定义 | Comparison / 比较内容 |
| --- | --- | --- |
| Available observations / 已有观测值 | Use observed values for each variable, or observed pairs for a pairwise comparison / 单变量使用其非缺失观测值，成对比较使用两变量均非缺失的记录 | Baseline distributions and associations, with the sample size reported for each plot or pair / 作为分布和关联的基准，并注明每张图或每对变量的样本量 |
| Complete cases / 完整病例 | Retain records with all 24 explanatory variables observed / 仅保留 24 个解释变量全部有观测值的记录 | Sample loss, group composition, and changes in distributions and associations / 样本损失、组别构成，以及分布和关联的变化 |
| Simple imputation / 简单填补 | Fill numerical variables with their medians and categorical variables with their modes / 数值变量用中位数填补，类别变量用众数填补 | Changes in concentration, spread, and relationships while retaining all records / 保留全部记录后，观察取值集中程度、离散程度和变量关系的变化 |

### Workflow and interpretation / 流程与解读原则

1. **Audit and clean.** Preserve the downloaded file; inspect types, documented units, missing markers, whitespace, category spellings, numerical conversions, and duplicate records. Follow the data dictionary for coded measurements.\
   **核查与清洗。** 保留下载的原始文件，检查类型、文档单位、缺失值标记、空白字符、类别拼写、数值转换和重复记录；按照数据字典处理编码型指标。
2. **Compare missing-value strategies.** Build the three views above and keep indicators for originally missing entries. Exclude the diagnosis label from imputation and explanatory-feature calculations.\
   **比较缺失值策略。** 构建上述三种视角，保留原始缺失位置的指示变量。填补及解释变量计算不使用诊断标签。
3. **Summarize and visualize.** Report counts, means, medians, standard deviations, and interquartile ranges. Use missingness plots, group-count bars, aligned histograms or empirical cumulative distribution curves, box plots, and selected scatter plots.\
   **汇总与绘图。** 报告样本量、均值、中位数、标准差和四分位距；绘制缺失情况图、组别计数图、对齐的直方图或经验累积分布曲线、箱线图和所选散点图。
4. **Inspect associations and scale effects.** Compare Pearson and Spearman correlations, patient-by-feature heatmaps, and suitable logarithmic transformations. Keep the patient set and other processing steps fixed for scale comparisons.\
   **检查关联与尺度效应。** 比较 Pearson 与 Spearman 相关系数、患者与特征热图及适用的对数变换。比较尺度时，保持患者集合及其他处理步骤一致。
5. **Optionally explore PCA.** Compare unstandardized and standardized numerical features using the same median-imputed records; inspect scores, explained variance, and loadings.\
   **可选 PCA 分析。** 在同一批中位数填补后的记录上，对比数值特征标准化前后的主成分得分、解释方差和载荷。

Extreme observations will be inspected, with removal requiring a documented data-quality reason. Ordinary z-score standardization does not change Pearson correlations for a fixed set of observations. Conclusions will describe associations and processing effects within this dataset.

极端观测值需要逐项核查，删除时应记录具体的数据质量依据。对固定的一组观测值，常规 z 分数标准化不会改变 Pearson 相关系数。最终结论将限于本数据集中的变量关联和数据处理效应。

**Planned deliverables:** a data-quality summary, a record of preprocessing decisions, matched visual comparisons, and a course report connecting findings to the research questions.\
**计划产出：** 数据质量摘要、预处理决策记录、可逐项对照的图表，以及围绕研究问题组织的课程报告。

## Repository layout / 仓库结构

```text
RenalLens/
├── docs/
│   ├── proposal.md
│   └── DSC5002_CKD_Proposal.pdf
├── scripts/
│   ├── data_preprocess.py     # Placeholder / 占位文件
│   ├── pipeline.sh            # Placeholder / 占位文件
│   ├── setup.ps1              # Windows environment setup / Windows 环境配置
│   ├── test.py                # Placeholder / 占位文件
│   └── train.py               # Placeholder / 占位文件
├── .gitignore
├── .python-version
├── LICENSE
├── README.md
├── pyproject.toml
├── requirements.txt
├── setup.bat                  # Windows double-click entry / Windows 双击入口
└── uv.lock
```

Local working directories are created as needed: `data/raw/` for original downloads, `data/interim/` and `data/processed/` for derived data, and `outputs/` for generated results. These directories are ignored by Git. Put figures and reports selected for submission in `docs/`, where they can be versioned.

按需创建本地工作目录：`data/raw/` 存放原始下载文件，`data/interim/` 与 `data/processed/` 存放派生数据，`outputs/` 存放生成结果。这些目录由 Git 忽略；确定用于提交的图表与报告放入 `docs/`，以便纳入版本管理。

## Quick start / 快速开始

The team uses **Python 3.13.15** and **uv 0.13.7**. The commands below use the repository's lockfile and include the shared Jupyter development tools. The first setup requires an internet connection. See the [official uv installation instructions](https://docs.astral.sh/uv/getting-started/installation/) for details.

全组统一使用 **Python 3.13.15** 和 **uv 0.13.7**。以下命令按仓库锁文件安装环境，并包含共用的 Jupyter 开发工具。首次配置需要联网，安装方式可参考 [uv 官方文档](https://docs.astral.sh/uv/getting-started/installation/)。

### One-click setup on Windows / Windows 一键配置

After cloning or downloading this repository, **double-click [setup.bat](setup.bat)**. You can also run the following command from the repository root:

克隆或下载仓库后，**双击根目录的 [setup.bat](setup.bat)**。也可以在仓库根目录执行：

```powershell
.\setup.bat
```

The script installs the pinned uv version for the current user if necessary, creates or synchronizes `.venv/` from `uv.lock`, checks dependency compatibility, and imports the eight project libraries. uv downloads the required Python version automatically when it is unavailable locally, so a new member does not need to install Python first. The uv version is read from `pyproject.toml`; Python is selected using `.python-version`.

脚本会在需要时为当前用户安装指定版本的 uv，按 `uv.lock` 创建或同步 `.venv/`，检查依赖兼容性，并导入项目使用的八个库。本机缺少指定 Python 时，uv 会自动下载，因此新组员无需预先安装 Python。uv 版本读取自 `pyproject.toml`，Python 版本读取自 `.python-version`。

The first setup requires internet access. Wait for **`Environment OK`** and **`Setup complete`**, then restart VS Code or open a new standalone terminal to use `uv`. Select `.venv\Scripts\python.exe` in VS Code. Rerun the same script after pulling dependency changes; it reuses installed tools and packages when their versions match. Its source is [scripts/setup.ps1](scripts/setup.ps1). The script uses the [official uv installer](https://docs.astral.sh/uv/reference/installer/) and [automatic Python downloads](https://docs.astral.sh/uv/concepts/python-versions/).

首次配置需要联网。看到 **`Environment OK`** 和 **`Setup complete`** 后，重启 VS Code 或打开一个新的独立终端以使用 `uv`，并在 VS Code 中选择 `.venv\Scripts\python.exe`。拉取依赖变更后，可以再次运行同一脚本；版本一致的工具与软件包会被复用。脚本源码见 [scripts/setup.ps1](scripts/setup.ps1)，其安装流程采用 [uv 官方安装器](https://docs.astral.sh/uv/reference/installer/)及[自动下载 Python](https://docs.astral.sh/uv/concepts/python-versions/)机制。

For macOS/Linux or manual Windows setup, follow the steps below. After one-click setup, continue at **step 4** to download the dataset.

macOS/Linux 或希望手动配置的 Windows 用户可按下列步骤操作。完成一键配置的用户可直接从**第 4 步**下载数据开始。

### 1. Install uv / 安装 uv

**Windows — PowerShell**

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/0.13.7/install.ps1 | iex"
```

**macOS / Linux**

```bash
curl -LsSf https://astral.sh/uv/0.13.7/install.sh | sh
```

Reopen the terminal after installation, then check the version.\
安装后重新打开终端，再检查版本。

```sh
uv --version
```

### 2. Clone and synchronize / 克隆并同步环境

```sh
git clone https://github.com/CanyonChen/RenalLens.git
cd RenalLens
uv python install 3.13.15
uv sync --locked
uv run --locked python --version
```

If the repository is already on your computer, run the uv commands from its root directory. `uv sync --locked` creates `.venv/` and installs the locked dependencies. It fails if `pyproject.toml` and `uv.lock` disagree, allowing the team to detect configuration drift. See [uv locking and syncing](https://docs.astral.sh/uv/concepts/projects/sync/).

如果已经有本地仓库，在仓库根目录执行 uv 命令即可。`uv sync --locked` 会创建 `.venv/` 并安装锁定的依赖；当 `pyproject.toml` 与 `uv.lock` 不一致时会报错，便于全组及时发现配置不同步。具体行为见 [uv 锁定与同步文档](https://docs.astral.sh/uv/concepts/projects/sync/)。

### 3. Verify the environment / 验证环境

```sh
uv run --locked python -c "import numpy, pandas, scipy, matplotlib, seaborn, sklearn, ipykernel, jupyterlab; print('Environment OK')"
uv pip check
```

Use `uv run --locked` to run commands in the project environment; manual activation is unnecessary. In VS Code, select the interpreter under `.venv/`: `.venv\Scripts\python.exe` on Windows or `.venv/bin/python` on macOS/Linux. Select the same environment as the notebook kernel.

使用 `uv run --locked` 在项目环境内运行命令，无需手动激活。VS Code 中请选择 `.venv/` 内的解释器：Windows 为 `.venv\Scripts\python.exe`，macOS/Linux 为 `.venv/bin/python`。Notebook 内核也选择同一环境。

### 4. Download the dataset / 下载数据集

Download the official CSV once and retain it unchanged. This command works in PowerShell and macOS/Linux shells.\
下载一次官方 CSV 后，保留原始文件不变。下列命令适用于 PowerShell 和 macOS/Linux 终端。

```sh
uv run --locked python -c "from pathlib import Path; from urllib.request import urlretrieve; p = Path('data/raw/ckd.csv'); p.parent.mkdir(parents=True, exist_ok=True); urlretrieve('https://archive.ics.uci.edu/static/public/336/data.csv', p); print(p)"
```

Check that the file has 400 rows and 25 columns, including the label:\
检查文件是否包含 400 行、25 列，其中 1 列为类别标签：

```sh
uv run --locked python -c "import pandas as pd; df = pd.read_csv('data/raw/ckd.csv'); print(df.shape)"
```

Record the download date, source URL, and file checksum when documenting an analysis. Perform cleaning on a copy and write derived data to the corresponding local data directory.\
记录分析过程时，应注明下载日期、来源 URL 和文件校验值。清洗基于副本开展，派生数据写入对应的本地数据目录。

### 5. Start exploratory work / 开始探索性分析

```sh
uv run --locked jupyter lab
```

The Jupyter environment is ready for development. Add runnable analysis commands here as the scripts are implemented; the current placeholder scripts do not produce analysis results.

Jupyter 环境可用于开发。后续实现脚本时，请同步在这里补充可运行的分析命令；目前的占位脚本尚不产出分析结果。

## Environment and dependency management / 环境与依赖管理

| File / 文件 | Role / 作用 |
| --- | --- |
| `.python-version` | Selects the exact default Python version: `3.13.15` / 指定默认 Python 精确版本 `3.13.15` |
| `pyproject.toml` | Declares dependencies, the Python requirement, the `dev` group, and the required uv version / 声明依赖、Python 版本要求、`dev` 开发依赖组和 uv 版本要求 |
| `uv.lock` | Records resolved direct and transitive dependencies, with platform markers and package hashes / 记录解析后的直接与间接依赖、平台条件和软件包哈希 |
| `requirements.txt` | Generated export of all dependency groups from `uv.lock`, with exact versions and hashes / 从 `uv.lock` 导出的全部依赖组，包含精确版本与哈希 |
| `.venv/` | Local environment created by uv; excluded from Git / uv 创建的本地环境，不提交到 Git |

The analysis dependencies are **NumPy, pandas, SciPy, Matplotlib, seaborn, and scikit-learn**. The default `dev` group adds **JupyterLab and ipykernel**. `scikit-learn` supports imputation, scaling, and optional PCA. This repository is configured as a non-packaged analysis project (`package = false`).

分析依赖包括 **NumPy、pandas、SciPy、Matplotlib、seaborn 和 scikit-learn**；默认安装的 `dev` 组包含 **JupyterLab 和 ipykernel**。`scikit-learn` 用于填补、缩放和可选的 PCA。仓库按分析项目管理，无需将自身安装为 Python 包（`package = false`）。

### Routine synchronization / 日常同步

After pulling updates, run:\
拉取更新后执行：

```sh
git pull --ff-only
uv sync --locked
```

Commit `pyproject.toml`, `uv.lock`, `.python-version`, and `requirements.txt` when they change. Share the lockfile through Git; each member creates their own `.venv/`. Platform-specific packages may differ across operating systems, while the shared dependency versions follow the same lockfile.

环境配置发生变化时，提交 `pyproject.toml`、`uv.lock`、`.python-version` 和 `requirements.txt`。通过 Git 共享锁文件，每位组员在本机创建 `.venv/`。不同操作系统的平台专用依赖可能不同，共用依赖版本以同一份锁文件为准。

### Change dependencies / 修改依赖

Use `uv add PACKAGE_NAME` for an analysis dependency, `uv add --group dev PACKAGE_NAME` for a development tool, or `uv remove PACKAGE_NAME` to remove a dependency. Replace `PACKAGE_NAME` with the actual package name. These commands update the project metadata and lockfile. Regenerate the compatibility export afterward:

添加分析依赖使用 `uv add PACKAGE_NAME`，添加开发工具使用 `uv add --group dev PACKAGE_NAME`，移除依赖使用 `uv remove PACKAGE_NAME`，将 `PACKAGE_NAME` 替换为实际包名。这些命令会更新项目配置和锁文件，随后重新生成兼容导出文件：

```sh
uv export --locked --all-groups --no-emit-project --format requirements.txt --output-file requirements.txt
```

`requirements.txt` is generated; do not edit it manually or replace it with `pip freeze`. The export command is described in [uv's export documentation](https://docs.astral.sh/uv/concepts/projects/export/). Use the uv project workflow above for normal team development.

`requirements.txt` 是生成文件，请勿手动维护或用 `pip freeze` 覆盖。导出机制见 [uv 官方文档](https://docs.astral.sh/uv/concepts/projects/export/)。全组日常开发使用上述 uv 项目工作流。

For an agreed dependency upgrade, update the relevant package explicitly, verify the environment and analysis, then regenerate `requirements.txt`. For example:\
需要升级依赖时，由小组确认后显式更新对应软件包，验证环境与分析，再重新导出 `requirements.txt`。例如：

```sh
uv lock --upgrade-package pandas
uv sync --locked
uv export --locked --all-groups --no-emit-project --format requirements.txt --output-file requirements.txt
```

If Python or uv itself is upgraded, update the corresponding version pins and quick-start instructions together, then regenerate and verify the lockfile and export.\
升级 Python 或 uv 本身时，应同步修改版本约束和快速开始说明，再重新生成并验证锁文件及导出文件。

## Team workflow / 小组协作

- Develop on a task branch and use a pull request to review changes. Keep commits focused on a single analysis or environment change.\
  在任务分支上开发，通过 Pull Request 审阅改动；每次提交围绕一项分析或环境变更展开。
- Record preprocessing decisions, sample counts, units, and the missing-value strategy alongside each result. Use consistent axes and histogram bins for comparisons.\
  随结果记录预处理决策、样本量、单位和缺失值策略；对比图使用一致的坐标范围与直方图分箱。
- Set and report a fixed random seed when a method uses randomness. Keep notebook execution order reproducible and remove temporary debug output before review.\
  方法涉及随机过程时，固定并记录随机种子；保证 Notebook 执行顺序可复现，审阅前清理临时调试输出。
- Keep raw data, local caches, and generated working outputs out of commits. Version the code, notebooks, decisions, and selected final figures or reports.\
  原始数据、本地缓存和临时生成结果不提交；代码、Notebook、决策记录及选定的最终图表与报告纳入版本管理。

## Team / 小组成员

| Member / 成员 | Student ID / 学号 |
| --- | --- |
| Bai Yingdong | 60209862 |
| Zhai Junsong | 57855191 |
| Zhang Junjie | 60754700 |
| Chen Canyang | 60775208 |
| Peng Peiyan | 60481323 |
| Li Jiaheng | 60217585 |

## License and citation / 许可与引用

Original project code and documentation are released under the [MIT License](LICENSE), copyright © 2026 RenalLens contributors. The UCI dataset retains its separate [CC BY 4.0 license](https://archive.ics.uci.edu/dataset/336/chronic+kidney+disease); cite its creators when using or redistributing it. Third-party packages retain their respective licenses.

本项目原创代码与文档采用 [MIT 许可证](LICENSE)，版权归 2026 RenalLens contributors 所有。UCI 数据集保留其独立的 [CC BY 4.0 许可](https://archive.ics.uci.edu/dataset/336/chronic+kidney+disease)，使用或再分发时需注明数据创建者。第三方软件包适用各自的许可证。

> Rubini, L., Soundarapandian, P., & Eswaran, P. (2015). *Chronic Kidney Disease* [Dataset]. UCI Machine Learning Repository. https://doi.org/10.24432/C5G020.
