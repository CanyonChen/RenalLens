# RenalLens

**How Complete-Case Analysis and Imputation Shape Patterns in Chronic Kidney Disease Data**\
**缺失值处理对慢性肾病临床指标分布及相关性估计的影响**

RenalLens is a group project for **DSC5002 — Exploratory Data Analysis and Visualization** at City University of Hong Kong. We examine how missing-value handling changes the patients represented in a dataset, the distributions of clinical measurements, and the relationships visible in exploratory plots.

RenalLens 是香港城市大学 **DSC5002 — 探索性数据分析与可视化**课程的小组项目。我们研究缺失值处理如何改变数据所代表的患者构成、临床指标的分布，以及探索性图表中呈现的变量关系。

**Group / 小组：C61, Group 65**\
**Documents / 项目文档：[Bilingual proposal / 中英双语提案](docs/proposal.md) · [Proposal PDF / 提案 PDF](docs/DSC5002_CKD_Proposal.pdf)**

## Project status / 项目状态

**2026-11-07** · The completed CPU run covers 400 records, the three missing-data views, five clinical comparisons and two PCA fits. Requiring complete records reduced the pooled median creatinine from 1.30 to 1.10 mg/dL. Within the CKD group it rose from 2.25 to 4.10 mg/dL, with 43 of 250 patients retained. The standalone report includes eight downloadable figures and a creatinine–urea sensitivity analysis. [Clinical results](docs/clinical_report.html)

**2026-11-07** · 已在 CPU 上完成 400 条记录的全量分析。完整病例筛选后，总体肌酐中位数从 1.30 降到 1.10 mg/dL，CKD 组内从 2.25 升到 4.10 mg/dL，该组仅保留 43/250 人。医学报告包含五项临床分层比较、相关性敏感性分析和八张可下载的图。下载 HTML 后可离线打开。[医学分析与图表](docs/clinical_report.html)

**Published results / 本次结果。** [15 CSV tables / 结果表](docs/results/) · [Cohort report / 患者队列](docs/results/figures/cohort.html) · [PCA report / 尺度与 PCA](docs/results/figures/scales.html) · [8 SVG figures / 矢量图](docs/results/figures/clinical/) · [Preprocessing audit / 清洗审计](docs/results/preprocessing_audit.json)

| Research question / 研究问题 | Implemented evaluation / 已实现的测评 |
| --- | --- |
| Q1 · Missingness and representation / 缺失与样本构成 | Original missingness by feature and patient, group counts and shares by view, and within-group retention after deletion / 按指标和患者记录原始缺失，对比三种视角的组别计数、占比及删除后的组内保留率 |
| Q2 · Distributions and associations / 分布与关联 | Overall and group summaries of the five measurements, concentration at the observed median, paired sample sizes and Pearson/Spearman coefficients in each view / 五项指标的总体与分组统计、原始中位数处的取值集中程度，以及各视角下的成对样本量与两种相关系数 |
| Q3 · Extremes, skewness and scale / 极端值、偏度与尺度 | Traceable extreme observations, paired raw/log values, raw/z-score patient matrices and two fixed-cohort PCA fits / 可追溯的极端观测、配对的原值与对数、患者的原尺度与标准化矩阵，以及同队列的两组 PCA |

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

The full run confirmed the preliminary counts in the proposal. Requiring all 24 explanatory variables retained **158 complete records (43 CKD and 115 non-CKD)**. CKD accounted for **62.5% of the original sample and 27.2% of complete cases**. These percentages describe the study sample. [Clinical results](docs/clinical_report.html#selection)

全量运行复核了提案中的样本数。要求全部 24 项特征齐全后，保留 **158 条记录（CKD 43 条，非 CKD 115 条）**，CKD 样本占比从 **62.5% 降至 27.2%**。这些比例的分母是本研究样本。[患者去留与缺失矩阵](docs/clinical_report.html#selection)

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
3. **Trace representation and distributions.** Report counts, means, medians, standard deviations and interquartile ranges. Link each patient's missing entries to their retention status and compare the five measurements across the three views.\
   **追踪样本构成与分布。** 报告样本量、均值、中位数、标准差和四分位距。从每位患者原本缺少的项目追溯其去留，在三种视角下对照五项指标的分布。
4. **Inspect associations and transformations.** Compare each pair's Pearson and Spearman estimates with its underlying patients. Examine eligible measurements before and after the log transformation using the same observations.\
   **核对关联与变换。** 将两种相关系数与参与计算的患者点对照，对适用指标用相同观测比较原值与自然对数。
5. **Fit both PCA models.** Use the same median-imputed records and the same five features. Fit centered PCA in original units, then fit PCA after z-score standardization. Export scores, explained variance and loadings for both. Diagnosis is used to label the projections.\
   **比较两组 PCA。** 固定中位数填补后的患者与五项指标，分别做原始单位下的中心化 PCA、z 标准化后的 PCA。两组均输出得分、解释方差和载荷，诊断标签仅用于标识投影中的患者。

### Clinical interpretation / 医学分析

A pooled change masks an opposite change within CKD. The pooled median hemoglobin rose from 12.65 to 14.25 after deletion, while the CKD median fell from 10.90 (204 measured) to 9.80 (43 complete). The available records do not establish why a test was missing. [Clinical results](docs/clinical_report.html)

删行后，全体血红蛋白中位数由 12.65 升至 14.25，但 CKD 组内由 10.90（204 人实测）降至 9.80（43 人完整）。应结合各组保留率解读合并结果。检查为何缺失，还需要就诊流程与病历资料。[医学结果报告](docs/clinical_report.html)

Within each recorded diagnosis group, the following comparisons use the clinical context as **originally recorded**. An unrecorded history or albumin grade has its own row in all three views. Each cell reports the stratum size, the measured and imputed counts, and the median with the 25th and 75th percentiles. These are unadjusted, cross-sectional descriptions.

在 CKD、非 CKD 两组内分别比较下表。三种缺失策略均按**原始记录**划分病史或白蛋白等级，原本缺失的分层信息单列为“未记录”。每格给出层内人数、实测与填补人数，以及中位数和第 25、75 百分位数。先比较实测分布，再看删除或填补改变了多少患者和读数；小样本层应随结果报告分母。

| Clinical question / 医学问题 | How to interpret the comparison / 读表依据 |
| --- | --- |
| Kidney function / 肾功能：`sc × al`、`bu × al` | Compare serum creatinine and blood urea across the original albumin grades. / 在同一诊断组内看各白蛋白等级的肌酐和血尿素分布是否同向变化，再对照两者的实测散点。肌酐受肌肉量影响，脱水也可升高血尿素。`bu` 采用原字段的血尿素定义，`al` 仅有 0–5 编码。[UCI 变量字典](https://archive.ics.uci.edu/dataset/336/chronic+kidney+disease) · [NIDDK 肌酐解读](https://www.niddk.nih.gov/research-funding/research-programs/kidney-clinical-research-epidemiology/laboratory/factors-affecting-egfr-accuracy/clinical-measurements) · [NHS 血尿素解读](https://www.southtees.nhs.uk/services/pathology/tests/Urea/) |
| Anemia / 贫血：`hemo × ane` | Compare hemoglobin across recorded anemia groups. / 按贫血记录比较血红蛋白。CKD 相关的促红细胞生成素减少是一种可能机制，缺铁、炎症或失血也可能参与。数据缺少铁代谢指标，字典仅给血红蛋白单位 `gms`，因此沿用原始贫血标记，个体病因待其他证据确认。[NIDDK 肾病与贫血](https://www.niddk.nih.gov/health-information/kidney-disease/anemia) |
| Diabetes / 糖尿病：`bgr × dm` | Compare random blood glucose across recorded diabetes groups. / 看糖尿病记录为“有”“无”“未记录”的患者，其随机血糖分布有多大重叠。进餐时间会影响单次读数，按随机血糖作诊断还涉及典型症状等条件。数据未提供进餐时间、典型症状或 HbA1c。[NIDDK 糖尿病检验](https://www.niddk.nih.gov/health-information/professionals/clinical-tools-patient-management/diabetes/diabetes-prediabetes) |
| Hypertension / 高血压：`bp × htn` | Compare the recorded pressure across hypertension groups. / 按高血压记录对比血压。UCI 只给一个 `bp` 值和 mmHg 单位，未标明收缩压、舒张压或复测方式。可以描述组间读数差异，判断血压控制情况还需明确测量类型、条件和重复读数。[UCI 变量字典](https://archive.ics.uci.edu/dataset/336/chronic+kidney+disease) · [WHO 高血压说明](https://www.who.int/news-room/fact-sheets/detail/hypertension) |

KDIGO defines CKD by kidney abnormalities present for at least three months and classifies it by cause, GFR and albuminuria. UCI has one row per patient and supplies a diagnosis label. Serial results, sex and a quantitative urine albumin-to-creatinine ratio (uACR) are unavailable. We keep the supplied labels and describe PCA as variation across the five readings.

KDIGO 的 CKD 定义要求肾脏结构或功能异常持续至少三个月，临床分类结合病因、肾小球滤过率（GFR）和白蛋白尿。这里缺少纵向复测、性别和定量尿白蛋白/肌酐比（uACR），无法据此重建标准成人肌酐 eGFR 或 KDIGO 分期。报告沿用原始 CKD 标签，PCA 仅描述这五项读数在样本中怎样共同变化。[KDIGO 2024 指南，§1.1.3](https://kdigo.org/wp-content/uploads/2024/03/KDIGO-2024-CKD-Guideline.pdf) · [NIDDK 成人 eGFR 公式](https://www.niddk.nih.gov/research-funding/research-programs/kidney-clinical-research-epidemiology/laboratory/glomerular-filtration-rate-equations/adults)

### Interactive visual comparisons / 交互可视化方案

Both reports use the source `row_id`. Each view makes a processing decision visible and lets the reader check it against the underlying observations.

两份离线报告共用原始 `row_id`。可按下面的顺序演示，每一步都能从图中找到对应的样本或统计量。

| Question / 问题 | Interaction / 如何阅读 |
| --- | --- |
| Which patients are retained? / 谁被保留？ | Each patient occupies a fixed cell within their diagnosis group. Select a measurement and switch views to see deletion or imputation at the same location. Select a patient to inspect their missing fields. / 每位患者在所属诊断组中有固定格位。选定指标并切换处理方式，可看见哪些行被删除、哪些读数被填补。点一格即可核查该患者缺了哪些项。 |
| Where does the imputed mass go? / 填补值集中到了哪里？ | Compare quartiles on one measurement axis and inspect how many values at the full-cohort median were observed or filled. The sample size belongs to the selected view and group. / 同一数轴上对照三种视角的分位数，区分全队列中位数处的实测值与填补值，结合当前视角及分组的有效人数解读。 |
| Which associations change? / 哪对指标的关系发生变化？ | Compare the three estimates for each of ten pairs on a fixed correlation scale. Select a pair and a strategy to inspect the actual points and their imputation status. / 在固定的相关系数轴上比较十对指标各自的三种估计。选择一对及其处理视角，查看构成该系数的患者点及填补情况。 |
| What changes with units? / 尺度改变了什么？ | Select one patient in the two PCA projections to inspect their raw and standardized readings. Inspect PC1 or PC2 to see which features shape that axis. A paired raw/log view exposes the upper tail of eligible measurements. / 两幅 PCA 图同时定位所选患者，对照其原值、z 分数与填补标记。切换 PC1 或 PC2 查看各指标在该方向的权重，原值与对数的配对视图用于查看右尾如何变化。 |

The two PCA fits estimate their own axes. Interpret each using its explained variance and feature weights. A patient's two plotted positions refer to the same source record. For one axis, squared eigenvector coefficients sum to one, while the exported loading is the coefficient multiplied by the square root of the eigenvalue.

两组 PCA 各自估计主轴，同一患者的两个位置应结合各图的解释方差和特征权重分别解读。每个主轴的方向系数平方之和为 1，可用于展示该轴的构成。CSV 中的载荷另按方向系数乘特征值的平方根计算。

For a walkthrough, select serum creatinine (`sc`). Pick a source row flagged by the 1.5 × IQR rule to locate that patient in the cohort display. Enter the same row ID in the PCA report to highlight both projections and its column in the five-measurement strip. The readings show which values were measured and which were filled.

演示时可以选血清肌酐（`sc`）。若有按 1.5 × IQR 规则标记的极端实测值，从复核列表定位其患者格，再在 PCA 页选同一行号。两幅投影和五项读数色带会同时定位该患者，读数旁标有实测或填补来源。

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
│   ├── data_preprocess.py     # Clean and audit the three views / 清洗、核查并构建三种视角
│   ├── pipeline.sh            # Run the stages in order / 顺序执行各阶段
│   ├── setup.ps1              # Windows environment setup / Windows 环境配置
│   ├── test.py                # Compare missing-value strategies / 测评缺失值处理策略
│   ├── train.py               # Scale transformations and PCA / 尺度变换与 PCA
│   └── views/                 # Offline HTML report templates / 离线报告模板
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

### 5. Run the descriptive evaluation / 运行描述性测评

From the repository root, the following commands work in PowerShell and Bash. They produce numerical tables by default. The preprocessing step gives every source row a stable `row_id` for matching patients across views.

在仓库根目录依次执行以下命令，适用于 PowerShell 和 Bash。默认生成数值表。预处理为每条原始记录分配稳定的 `row_id`，可据此对齐不同视角中的同一患者。

```sh
uv run --locked python scripts/data_preprocess.py
uv run --locked python scripts/test.py
uv run --locked python scripts/train.py
```

In Bash, `bash scripts/pipeline.sh` runs the same three stages, including both PCA fits. Run `bash scripts/pipeline.sh --plots` for the two interactive reports, eight clinical SVG figures and sensitivity table. In PowerShell, add `--plots` to the last two commands above and then run the figure command below. Open the resulting HTML files offline. Supply `--download-date YYYY-MM-DD` when the actual download date is known.

在 Bash 中，`bash scripts/pipeline.sh --plots` 会重新生成两份交互报告、八张医学 SVG 图和敏感性结果表。在 PowerShell 中，给上面后两条命令分别加上 `--plots`，随后运行下列命令，可同时把图嵌入经医学解读的单文件报告。报告正文对应当前 UCI 原表的 SHA-256。已知下载日期时，可向预处理脚本传入 `--download-date YYYY-MM-DD`。

```sh
uv run --locked python scripts/clinical_figures.py --report outputs/clinical_report.html
```

| Where to look / 输出位置 | What to inspect / 阅读方式 |
| --- | --- |
| `data/processed/` | `preprocessing_audit.json` records the source checksum, cleaning decisions and fill values. The three views are `observed.csv`, `complete_case.csv` and `imputed.csv`. In `missing_mask.csv`, 1 identifies an originally missing cell / 审计文件记录来源校验值、清洗决策及各列填充值。三张视角表共用原始行号，缺失矩阵中 1 表示原本缺失 |
| `outputs/group_composition.csv`, `outputs/missing_rates.csv` | Compare each group's share within a view and the fraction retained from its original group / 区分某组占当前视角的比例与该组自身的保留率 |
| `outputs/distribution_summary.csv`, `outputs/extreme_observations.csv`, `outputs/correlations.csv` | Read spread and concentration alongside the sample composition. Each correlation uses observations available for that pair / 结合样本构成解读离散与集中程度。每对相关系数使用该对指标共同有效的记录 |
| `outputs/clinical_strata.csv` | Five clinical comparisons within each recorded diagnosis group. Read them side by side in `cohort.html` with `--plots`. / 分诊断组查看五项医学比较，启用 `--plots` 后可在队列报告中并排核对分层人数、实测与填补数及分位数 |
| `outputs/log_comparison.csv`, `outputs/patient_features_*.csv`, `outputs/scale_parameters.csv` | Inspect log eligibility and paired skewness, then compare patient measurements on raw and standardized scales / 查看对数变换适用条件及配对样本的偏度，再对照同一批患者的原尺度与标准化结果 |
| `outputs/pca_scores.csv`, `outputs/pca_variance.csv`, `outputs/pca_loadings.csv` | Scores, explained variance and feature loadings for the two default PCA fits / 两组 PCA 默认输出的得分、解释方差及特征载荷 |
| `outputs/renal_sensitivity.csv`, `outputs/figures/clinical/*.svg` | Observed creatinine–urea pairs by diagnosis and after omitting one maximum creatinine reading, plus eight reusable figures / 分诊断组及暂不计肌酐最高一条记录的成对实测结果，以及八幅可用于报告的矢量图 |
| `outputs/figures/cohort.html`, `outputs/figures/scales.html` | With `--plots`, the first report traces patients, distributions and associations. The second explores measurement scales and PCA. Each file contains its own data and controls / 启用 `--plots` 后，第一份报告展示患者去留、分布和关联，第二份展示尺度与 PCA。两者均内嵌所需数据和控件 |

The summary tables use sample standard deviations. Extreme-value flags use Tukey's 1.5 × IQR fences across all patients in each view and retain the source row ID. The log comparison includes a measurement when it has at least three observed values, all positive, with positive sample skewness. Standardization uses the imputed cohort's mean and population standard deviation for each feature.

描述统计采用样本标准差。极端值按各视角全体患者的 1.5 × IQR 箱线图规则标记，表中保留原始行号供复核。一项指标至少有三个有效观测、全部为正且样本偏度大于零时，才比较同批患者的原值与自然对数。标准化使用填补后全队列中各变量的均值与总体标准差。

For a separate run, choose a new `--output-dir` and `--processed-dir`. Optional files from earlier runs stay in their original directory. Use `uv run --locked jupyter lab` for interactive inspection.

若需分开保存多次运行，为各次运行设置独立的 `--output-dir` 和 `--processed-dir`。此前生成的可选结果保存在原目录中。交互式查看可使用 `uv run --locked jupyter lab`。

## Environment and dependency management / 环境与依赖管理

| File / 文件 | Role / 作用 |
| --- | --- |
| `.python-version` | Selects the exact default Python version: `3.13.15` / 指定默认 Python 精确版本 `3.13.15` |
| `pyproject.toml` | Declares dependencies, the Python requirement, the `dev` group, and the required uv version / 声明依赖、Python 版本要求、`dev` 开发依赖组和 uv 版本要求 |
| `uv.lock` | Records resolved direct and transitive dependencies, with platform markers and package hashes / 记录解析后的直接与间接依赖、平台条件和软件包哈希 |
| `requirements.txt` | Generated export of all dependency groups from `uv.lock`, with exact versions and hashes / 从 `uv.lock` 导出的全部依赖组，包含精确版本与哈希 |
| `.venv/` | Local environment created by uv; excluded from Git / uv 创建的本地环境，不提交到 Git |

The analysis environment includes **NumPy, pandas, SciPy, Matplotlib, seaborn, and scikit-learn**. The default `dev` group adds **JupyterLab and ipykernel**. The analysis uses pandas for imputation and scikit-learn for scaling and PCA. This repository is configured as a non-packaged analysis project (`package = false`).

分析环境包含 **NumPy、pandas、SciPy、Matplotlib、seaborn 和 scikit-learn**，默认安装的 `dev` 组包含 **JupyterLab 和 ipykernel**。分析使用 pandas 填补缺失值，使用 scikit-learn 完成标准化与 PCA。仓库按分析项目管理，无需将自身安装为 Python 包（`package = false`）。

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
