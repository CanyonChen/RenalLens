"""Generate the project entry point and evidence links from published CSV tables."""
import csv
import re
from pathlib import Path

from site_support import NAV_STYLE, navigation, update_navigation

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"


def build():
    with (DOCS / "reanalysis/tables/eligibility_rules.csv").open(encoding="utf-8", newline="") as stream:
        rules = list(csv.DictReader(stream))
    def row(rule, group):
        return next(r for r in rules if r["rule"] == rule and r["group"] == group)
    def count(rule, group):
        r = row(rule, group)
        return f'{r["n_retained"]} / {r["n_original_group"]}'
    labels = {"all24": "全部 24 项", "core5": "5 个核心指标", "renal_pair": "肌酐与尿素", "glucose": "随机血糖"}
    body = ""
    for rule, label in labels.items():
        r = row(rule, "ckd")
        body += f'<tr><th scope="row">{label}</th><td>{count(rule,"all")}</td><td>{count(rule,"ckd")}</td><td>{count(rule,"notckd")}</td><td>{r["n_glucose_high"]} / {r["n_glucose_measured"]}（{float(r["glucose_high_share"]):.1%}）</td></tr>'
    block = f'''<!-- eligibility-comparison --><section id="eligibility">
<h2>完整，究竟要求哪些字段？</h2>
<p>删除规则由当前研究问题需要的字段决定。保留原始读数，只改变参与分析的患者集合，就得到以下对照。表中高血糖指随机血糖 ≥200 mg/dL，分母为所保留 CKD 患者中血糖实测的人数。</p>
<div class="table-wrap" style="overflow-x:auto"><table><caption>字段要求与可观察人群</caption><thead><tr><th scope="col">完整要求</th><th scope="col">全体保留</th><th scope="col">CKD 保留</th><th scope="col">非 CKD 保留</th><th scope="col">CKD 高血糖 / 血糖实测</th></tr></thead><tbody>{body}</tbody></table></div>
<p>第 43 号病历仅缺红细胞评估 rbc；其五项核心指标均有实测值。24 项规则会删除这条记录，5 项规则保留其 204 mg/dL 的随机血糖。完整病例结果同时依赖字段要求与缺失结构。</p>
<p><a href="tables/eligibility_rules.csv">下载规则对照 CSV</a> · <a href="../results/figures/cohort.html?patient=43&amp;feature=bgr&amp;view=complete_case">交互追踪病例 43</a></p></section><!-- /eligibility-comparison -->'''
    report = DOCS / "reanalysis/missing_data.html"
    content = report.read_text(encoding="utf-8")
    content = re.sub(r'\s*<!-- eligibility-comparison -->.*?<!-- /eligibility-comparison -->\s*', '\n', content, flags=re.S)
    content = content.replace('<section id="selection">', block + '\n<section id="selection">', 1)
    report.write_text(content, encoding="utf-8")
    css = '''body{margin:0;background:#faf9f6;color:#27242a;font:17px/1.8 Arial,"Microsoft YaHei",sans-serif}*{box-sizing:border-box}main{max-width:1080px;margin:auto;padding:12px 24px 60px}header{padding:36px 0 28px;border-bottom:2px solid #941344}h1{font-size:clamp(30px,5vw,48px);line-height:1.25;max-width:850px}h2{font-size:26px;margin:32px 0 10px}h3{font-size:21px;margin:0 0 10px}p{max-width:900px}a{color:#156368;text-underline-offset:4px}.by,.note{font-size:14px;color:#5f5c64}.lead{font-size:21px}.route{padding:24px 0;border-bottom:1px solid #d5cfce}.route p{margin:8px 0}.metric{color:#941344;font-weight:bold}table{border-collapse:collapse;width:100%;font-size:15px}th,td{text-align:left;border-bottom:1px solid #d5cfce;padding:12px 10px;white-space:nowrap}.table-wrap{overflow-x:auto}footer{margin-top:40px;border-top:1px solid #d5cfce;padding-top:20px}'''
    page = f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>RenalLens · 缺失记录怎样改变可见的人群</title><style>{css}{NAV_STYLE}</style></head><body><main>{navigation("", "index.html")}
<header><p class="by">City University of Hong Kong · DSC5002 · C61, Group 65</p><h1>缺失记录，怎样改变我们看到的患者？</h1><p class="lead">RenalLens 用 UCI 的 400 条肾病记录，追踪删除、填补与测量尺度怎样改变人群、分布和关联。</p><p>第 43 号病历有 <span class="metric">204 mg/dL</span> 的随机血糖，只缺一项红细胞评估。为何它会从分析中消失？</p></header>
<section><h2>从一个病例，走到整个人群</h2>
<article class="route"><h3><a href="results/figures/cohort.html?patient=43&amp;feature=bgr&amp;view=complete_case">01　追踪患者与缺失值</a></h3><p>切换 24 项、5 项与当前字段规则；比较分组保留率、四分位数和相关性。点选患者后，可以带着同一行号进入 PCA。</p><p><span class="metric">{count("all24","all")} → {count("core5","all")}</span>：改用五项核心指标，更多已有读数留在分析中。</p></article>
<article class="route"><h3><a href="results/figures/scales.html?patient=43&amp;feature=bgr">02　比较尺度与 PCA</a></h3><p>固定同一批患者，对照原单位与 z 标准化后的投影、带符号方向系数及原值／对数的配对分位位置。</p></article>
<article class="route"><h3><a href="reanalysis/missing_data.html">03　核对方法与结果</a></h3><p>查看样本组成、分组肌酐变化、填补验证、敏感性分析与 CSV。总体肌酐中位数由 1.30 降至 1.10 mg/dL，CKD 组内却由 2.25 升至 4.10 mg/dL。</p></article></section>
<section><h2>汇报与研究资料</h2><p><a href="presentation/deck.html">8 页项目演示</a> · <a href="presentation/RenalLens_Presentation.pdf">演示 PDF</a> · <a href="presentation/Presenter_notes.md">演讲稿</a></p><p><a href="poster/RenalLens_Poster.pdf">海报 PDF</a> · <a href="report/RenalLens_Report.pdf">一页报告</a> · <a href="proposal.md">研究提案</a></p><p class="note">补充专题：<a href="reanalysis/index.html">CKD 临床病例分析</a> · <a href="presentation/case-study.html">原病例演示</a>。原始行号按 CSV 表头后的第一行记为 1。</p></section>
<footer><p class="note">所有交互数据嵌入 HTML，下载离线包后从 index.html 打开。图中的组别沿用 UCI 提供的诊断标签。</p></footer></main></body></html>'''
    (DOCS / "index.html").write_text(page, encoding="utf-8")
    for relative in ("reanalysis/missing_data.html", "reanalysis/index.html", "clinical_report.html"):
        update_navigation(DOCS / relative, DOCS)
    print("Built project homepage, eligibility comparison and shared navigation.")


if __name__ == "__main__":
    build()
