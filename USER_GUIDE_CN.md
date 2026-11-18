# 补充代码 S1 —— 使用说明

本代码包依据早期研究记录整理，并结合论文中补充的方法进行了修正或重构。**它不是原来执行程序的原封不动备份，也不包含示例数据或研究原始数据。**

## 内容说明

- `run_statistics.py`：读取用户自行准备的 CSV 或 Excel 文件，分析各粒度的七项景观指标，计算 MK 趋势（含 Hamed–Rao 修正）、UF/UB 与 Pettitt。
- `run_retention.py`：读取用户自行准备的景观类型矢量面积、栅格面积和廊道断裂标志表，计算 Ei、V 和信息保持边界。
- `run_recommendation.py`：根据六项核心指标的 Pettitt 结果和细粒度步长容差，得到推荐粒度候选值；仍需结合 MK 和廊道证据确认。
- `arcgis10_2_rasterization.py`：ArcGIS 10.2 的**模板程序**，需在安装了 ArcGIS/arcpy 的计算机中配置自己的数据路径、字段、范围和参数后测试。不要在普通 Python 3 环境直接运行。
- `ARCGIS_METHOD_PSEUDOCODE.md`：GIS 数据准备、RMA/RCC 栅格化、廊道评价和指标导出流程说明。
- `METHODS_AUDIT.md`：代码实现来源、方法限制和验证状态。
- `SUBMISSION_NOTE.md`：补充代码及数据可用性声明的建议文本。

本代码包**不提供示例数据或演示数据**。运行程序所需的输入文件需要使用者根据自己的研究数据自行整理。自动化测试使用测试代码内部构造的数据，不依赖单独的数据文件目录。

## 安装

在普通 Python 3 环境打开命令行：

```bash
python -m pip install -r requirements.txt
```

## 统计分析输入数据

`run_statistics.py` 读取 CSV 或 Excel。每个研究区域、每个粒度一行，支持以下字段：

`LID, SIZE, NP, PD, ENN_MN, PLADJ, COHESION, MESH, AI`

- `SIZE`：粒度，单位为米，必须为正数；同一 `LID` 下不能重复。
- `LID`：研究区域标识。只有一个区域时可以不提供。
- 早期表头别名 `ENNN`、`ESH` 会分别自动转换为 `ENN_MN`、`MESH`。
- 指标值必须为数值且不能包含无穷值或缺失值。七项指标均可读取，其中六项（不含 MESH）用于基准决策。

使用自己准备的 CSV：

```bash
python run_statistics.py "D:/your_data/metrics.csv" --output-dir "D:/your_result/stat_results"
```

使用 Excel 指定工作表和研究区域：

```bash
python run_statistics.py "D:/your_data/metrics.xlsx" --sheet HAIKOU --area HAIKOU --output-dir "D:/your_result/stat_results"
```

输出包括 `statistical_summary.csv` 和 `uf_ub_sequences.csv`。输出文件包含输入数据的衍生成果，涉及受限数据时，未经授权不要上传或公开。

如果尚未安装 `pymannkendall`，可使用 `--skip-trend` 对数据读取和部分处理流程进行有限测试；此时原始 MK 和 Hamed–Rao MK 结果会标记为 `NOT_RUN`，**不能用于正式科研统计报告**：

```bash
python run_statistics.py "D:/your_data/metrics.csv" --skip-trend --output-dir "D:/your_result/smoke_test"
```

## 信息保持评价输入数据

`run_retention.py` 需要使用者自行准备 CSV，每个粒度、每种景观类型一行，字段为：

`SIZE,class,reference_area,raster_area,corridor_discontinuous`

- `reference_area`：该类型的矢量参考面积，需为正数，同一类型在不同粒度下保持一致。
- `raster_area`：该类型的栅格面积，即像元数量乘以像元面积；面积单位需与参考面积一致。
- `corridor_discontinuous`：依据固定参考河流路径判定的布尔值；同一粒度下各景观类型行应填写相同的判定值。
- 不同粒度必须包含相同的景观类型集合；地图边界、范围及边缘像元处理方式应保持一致。

运行命令：

```bash
python run_retention.py "D:/your_data/area_corridor.csv" --output "D:/your_result/retention_summary.csv"
```

四项**操作性失效标准**为：任一 `|Ei| >= 20%`、任一 `Ei <= -90%`、区域 `V >= 10%`，或代表性廊道发生断裂。程序报告首次满足任一失效标准的粒度，遵循论文的**边界阈值**约定；它不等同于最后一个无误差粒度。信息保持评价步长为市级 20 m、区级 10 m、镇级 5 m；这与突变点分析的细粒度步长不同。

`landscape_methods.py` 中的 `corridor_is_continuous` 是沿给定参考廊道掩膜进行布尔连通性判断的**示意性实现**。它不会从 GIS 河流源数据自动提取河道路径，也不保证与论文中的人工空间核查完全等价。实际使用前应记录并核实河流路径选择、4 邻域或 8 邻域、掩膜缓冲、桥梁修正和边缘处理方式。

## 推荐粒度候选值

先使用自己的指标数据运行 `run_statistics.py`，再将生成的 `statistical_summary.csv` 作为推荐程序输入：

```bash
python run_recommendation.py "D:/your_result/stat_results/statistical_summary.csv" --area HAIKOU --retention-limit 90 --step 5 --agreement 4 --tolerance-steps 1
```

请根据实际区域、信息保持边界和研究尺度修改参数。程序使用六项核心指标 `NP, PD, ENN_MN, PLADJ, COHESION, AI`，默认要求至少四项指标的 Pettitt 突变点达到统计支持（p < 0.05），并允许一个细粒度步长的位置容差；`MESH` 作为补充指标。输出是候选值，不是无需复核的最终结论。仍需结合 MK 候选区间、面积误差、廊道证据和敏感性分析综合判断。

## ArcGIS 10.2 栅格化

在 **ArcGIS 10.2 对应的 Python 环境**中运行 `arcgis10_2_rasterization.py`，按实际数据配置输入面要素、整数型 `CLASS_ID` 字段、投影坐标、固定范围、输出目录和各尺度粒度序列。模板使用 ArcPy `PolygonToRaster_conversion`：

- RMA 使用 `MAXIMUM_AREA`（最大面积规则）；
- RCC 使用 `CELL_CENTER`（像元中心规则）。

栅格原点偏移包括 `original`、`X + 0.25g`、`Y + 0.25g` 和 `XY + 0.5g`，其中 `g` 为当前像元大小。该模板尚未在本环境中执行，因为缺少 ArcPy 和受限几何数据。它也不负责计算景观指标；相关指标需使用研究中一致的 FRAGSTATS 或其他等效工具及参数导出。具体流程见 `ARCGIS_METHOD_PSEUDOCODE.md`。

## 测试与投稿前核查

运行单元测试：

```bash
python -m pytest tests -q
```

当前代码整理环境未安装所需统计库，因此端到端 MK/Hamed–Rao 结果尚未完成验证；ArcGIS 模板也未实际执行。由于未提供原始经验指标序列，当前代码尚未核对其是否能精确得到论文报告的 150/50/25 m 结果。

投稿前请使用有权访问的真实数据，在研究所用的软件和参数环境中重新运行并核对结果。真实调查数据、河流矢量、逐粒度指标序列及其衍生成果均应按数据管理要求保存，不要未经授权放入公开代码仓库。
