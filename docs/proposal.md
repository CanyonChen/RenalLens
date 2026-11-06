# DSC5002 Project Proposal
**DSC5002 项目提案**

**Course:** Exploratory Data Analysis and Visualization  
**课程：** 探索性数据分析与可视化

**Group number:** C61 65  
**小组编号：** C61 班第 65 组

**Members and student IDs:**  
**成员及学号：**

- Bai Yingdong 60209862
- Zhai Junsong 57855191
- Zhang Junjie 60754700
- Chen Canyang 60775208
- Peng Peiyan 60481323
- Li Jiaheng 60217585

## Title of the Project
**项目题目**

RenalLens: How Complete-Case Analysis and Imputation Shape Patterns in Chronic Kidney Disease Data 
RenalLens：缺失值处理对慢性肾病临床指标分布及相关性估计的影响

## Introduction
**引言**

Clinical datasets contain numerical measurements, categories and missing values.  
临床数据集既包含数值测量结果和类别信息，也存在缺失值。  
Removing incomplete records or filling missing entries can change the patients represented and the patterns visible.  
删除不完整记录或填补缺失项，可能会改变数据所反映的患者构成，以及从中观察到的规律。  
Extreme values may also reflect meaningful observations.  
极端值也可能反映有意义的观测结果。

We will examine how missing value handling affects sample composition, distributions and variable relationships in the public Chronic Kidney Disease (CKD) dataset.  
我们将使用公开的 Chronic Kidney Disease（慢性肾病，CKD）数据集，考察缺失值处理如何影响样本构成、变量分布及变量之间的关系。  
Transformations and scaling will provide additional visual comparisons.  
我们还将比较变量变换和缩放前后的图形。  
The project connects preprocessing decisions with descriptive statistics and visualization.  
本项目将通过描述性统计和可视化考察预处理决策的影响。

## Research Questions
**研究问题**

1. Which variables have the most missing values, and how does deleting incomplete records change the composition of the CKD and non-CKD groups?  
   哪些变量的缺失值最多？删除不完整记录后，CKD 组与非 CKD 组的样本构成如何变化？
2. How do complete-case analysis and simple imputation affect the distributions and associations of selected clinical measurements?  
   完整病例分析和简单填补会怎样影响所选临床指标的分布及其相互关联？
3. How do skewness, extreme observations and measurement scales influence the interpretation of individual-variable and multivariate plots?  
   分布偏度、极端观测值和测量尺度会怎样影响对单变量图和多变量图的解读？

## Dataset Description
**数据集说明**

We will use the public Chronic Kidney Disease dataset from the UCI Machine Learning Repository [[1]](#ref-1), [[2]](#ref-2).  
我们将使用 UCI 机器学习库中公开的 Chronic Kidney Disease 数据集 [[1]](#ref-1)、[[2]](#ref-2)。  
Each row represents one patient record.  
每一行代表一条患者记录。

| Dataset characteristic<br>数据集特征 | Description<br>说明 |
| --- | --- |
| Size<br>规模 | 400 patient records and 24 explanatory variables, plus one class label<br>400 条患者记录、24 个解释变量，另有 1 个类别标签 |
| Class composition<br>类别构成 | 250 CKD records and 150 non-CKD records<br>250 条 CKD 记录和 150 条非 CKD 记录 |
| Numerical measurements<br>数值测量指标 | Examples include age, blood pressure, blood glucose, blood urea, serum creatinine and hemoglobin<br>例如年龄、血压、血糖、血尿素、血清肌酐和血红蛋白 |
| Categorical and coded variables<br>类别变量和编码变量 | Examples include hypertension, diabetes, red blood cell assessment, and albumin and sugar grades<br>例如高血压、糖尿病、红细胞评估结果，以及白蛋白和糖的分级 |
| Data characteristics<br>数据特点 | Missing values, whitespace inconsistencies and different measurement scales<br>存在缺失值，空白字符的使用不一致，测量尺度各异 |

A preliminary audit of all 24 explanatory variables retained 158 complete records: 43 CKD and 115 non-CKD.  
对全部 24 个解释变量进行初步核查后，保留下来的完整记录有 158 条，其中 CKD 组 43 条，非 CKD 组 115 条。  
The CKD share therefore changed from 62.5% in the full dataset to 27.2% after complete-case deletion [[2]](#ref-2).  
因此，仅保留完整病例后，CKD 记录的占比从全数据集中的 62.5% 降至 27.2% [[2]](#ref-2)。  
These are sample proportions, not population disease prevalence.  
这些占比反映的是样本构成，不能据此推断总体患病率。  
This observed change motivates our investigation of sample representation.  
正是这一变化促使我们考察样本对不同患者群体的代表性。

Its manageable size and mix of variable types support transparent inspection.  
数据集规模适中，兼有多种类型的变量，便于逐项核查。  
The class label enables comparisons of how processing affects the two groups.  
借助类别标签，我们可以比较数据处理对两组患者的影响。

## EDA and Data Visualization Plan
**探索性数据分析与数据可视化计划**

### Data cleaning and missing value handling
**数据清洗与缺失值处理**

We will preserve the source data and audit variable types, documented units, missing markers, category spellings, numerical conversions and duplicate rows.  
我们将保留原始数据，核查变量类型、文档中注明的计量单位、缺失值标记、类别拼写、数值转换和重复行。  
Whitespace will be normalized before missingness is assessed.  
在检查缺失情况之前，我们会先统一空白字符的格式。  
Coded measurements will follow the data dictionary rather than automatically being treated as continuous variables.  
对于采用编码的测量指标，我们将依据数据字典确定处理方式，避免一律按连续变量处理。  
The diagnosis label will be excluded from explanatory-feature calculations.  
涉及解释变量的计算均不使用诊断标签。

We will compare three views: available observed values for each variable, the complete-case subset, and the full dataset with median imputation for numerical variables and mode imputation for categorical variables.  
我们将比较三种处理方式：逐个变量使用已有观测值，仅使用完整病例子集，以及在全数据集中用中位数填补数值变量、用众数填补类别变量。  
Imputation will not use the diagnosis label.  
填补缺失值时不使用诊断标签。  
Indicators will identify originally missing entries, and each plot will report its sample size.  
我们将用指示变量标记原本缺失的条目，并在每张图中注明实际样本量。  
Changes involving complete cases will be interpreted alongside the change in patient composition.  
解读完整病例分析得到的变化时，我们也会考虑患者构成的变化。

### Summary statistics and extreme observations
**汇总统计量与极端观测值**

The main analysis will focus on hemoglobin, serum creatinine, blood urea, blood glucose and blood pressure.  
主要分析将聚焦血红蛋白、血清肌酐、血尿素、血糖和血压。  
We will report available sample sizes, means, medians, standard deviations and interquartile ranges, with group summaries where useful.  
我们将报告各指标的有效样本量、均值、中位数、标准差和四分位距，并在适用时按组汇总。  
Extreme values will be flagged and inspected; removal will require a documented data-quality reason.  
我们会标记并核查极端值。若要删除某个极端值，必须记录具体的数据质量依据。  
For suitable positively skewed measurements, original and logarithmic views will be compared, with transformations and units clearly stated.  
对于适合取对数的右偏指标，我们将对比原始尺度和对数尺度下的图形，并注明变换方式和单位。

### Data visualization
**数据可视化**

We will use Python to prepare the data and create plots.  
我们将使用 Python 整理数据并绘图。  
Distribution comparisons will use consistent axes and histogram bins or empirical cumulative distribution curves.  
比较分布时，我们会统一坐标轴和直方图的分箱方式，或使用经验累积分布曲线。  
The planned visualizations connect directly to the research questions.  
下列图表分别对应前述研究问题。

| Visualization<br>图表类型 | Purpose<br>用途 |
| --- | --- |
| Missing-rate bars and a missingness matrix<br>缺失率条形图和缺失矩阵 | Locate missing values and identify entries that are missing together<br>定位缺失值，识别哪些条目会同时缺失 |
| Group-count and proportion bars<br>各组样本数和占比条形图 | Show sample loss and changes in CKD representation after deletion<br>展示删除不完整记录后减少了多少样本，以及 CKD 样本占比如何变化 |
| Aligned histograms and cumulative distribution curves<br>使用相同坐标尺度的直方图和累积分布曲线 | Compare observed, complete-case and imputed distributions<br>比较已有观测值、完整病例和填补后数据的分布 |
| Box plots and selected scatter plots<br>箱线图和针对所选变量绘制的散点图 | Examine group differences, extreme values and variable relationships<br>考察组间差异、极端值及变量之间的关系 |
| Correlation and patient-by-feature heatmaps<br>相关性热图和以患者为行、特征为列的热图 | Summarize associations and compare measurements with different units<br>汇总变量间的关联，并比较使用不同单位的测量指标 |

### Correlation analysis and scale effects
**相关性分析与尺度效应**

Pearson and Spearman correlations will describe complementary aspects of relationships among selected numerical variables.  
我们将使用 Pearson 和 Spearman 相关系数，从互补的角度描述所选数值变量之间的关系。  
We will report the sample size for each comparison and examine whether relationships persist across missing value strategies.  
我们会报告每次比较的样本量，并考察在不同缺失值处理策略下，这些关系是否仍然存在。  
Transformation and scaling comparisons will hold the patient set and other processing steps fixed wherever possible.  
比较不同变换和缩放方式时，我们将尽可能使用同一批患者，并保持其他处理步骤一致。  
Ordinary z-score standardization does not change Pearson correlations for fixed observations; its effects will be examined in patient-by-feature heatmaps and, optionally, PCA.  
对于同一组观测值，常规 z 分数标准化不会改变 Pearson 相关系数。我们将通过以患者为行、特征为列的热图考察标准化的影响，也可进一步采用主成分分析（PCA）。

## Other Methods (Optional)
**其他方法（可选）**

Principal component analysis (PCA) may supplement the main plots.  
主成分分析（PCA）可用于补充主要图表。  
Using the same median-imputed records and a fixed set of numerical features, we will compare PCA before and after standardization through score plots, explained variance and feature loadings.  
我们将使用同一批经中位数填补的记录和同一组数值特征，通过主成分得分图、解释方差和特征载荷，比较标准化前后的 PCA 结果。  
PCA will help illustrate scale effects, and visible groupings will be interpreted as exploratory patterns.  
PCA 有助于展示测量尺度的影响，图中可见的分组将作为探索性发现来解读。

## Expected Outcomes
**预期结果**

We will produce a data-quality summary, a record of preprocessing decisions and matched visual comparisons.  
我们将整理数据质量摘要、记录预处理决策，并制作可逐项对照的图表。  
The analysis will show how complete-case deletion changes sample representation, whether simple imputation creates concentrations or changes distributional spread, and which selected relationships remain stable.  
分析将展示仅保留完整病例会怎样改变样本的代表性、简单填补是否会让数据集中在某些取值或改变分布的离散程度，以及所考察的哪些变量关系仍然稳定。  
We will evaluate processing choices through sample retention, visual interpretability and the consistency of descriptive findings.  
我们将从样本保留情况、图表的可解释性和描述性分析结果的一致性三个方面评价不同的处理方式。  
Conclusions will concern associations and processing effects within this dataset.  
结论将限于本数据集中的变量关联和数据处理的影响。

## References
**参考文献**

<a id="ref-1"></a>

[1] Rubini, L., Soundarapandian, P., & Eswaran, P. (2015). Chronic Kidney Disease [Dataset]. UCI Machine Learning Repository. <https://doi.org/10.24432/C5G020>

<a id="ref-2"></a>

[2] UCI Machine Learning Repository. Chronic Kidney Disease official data CSV. <https://archive.ics.uci.edu/static/public/336/data.csv> (accessed 24 October 2026).

