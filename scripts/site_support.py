"""Navigation shared by the published pages and embedded offline explorers."""

from pathlib import Path

NAV_STYLE = """.project-nav{display:flex;flex-wrap:wrap;gap:8px 20px;padding:16px 0;
border-bottom:1px solid #cfdbd7;font:14px/1.6 Arial,'Microsoft YaHei',sans-serif}
.project-nav a{color:#156368;text-decoration:underline;text-underline-offset:3px}
.project-nav a[aria-current=page]{font-weight:700;color:#941344}
@media print{.project-nav{display:none}}"""


def navigation(prefix, active=""):
    pages = [("index.html", "项目首页"), ("results/figures/cohort.html", "患者与缺失值交互"),
             ("results/figures/scales.html", "尺度与 PCA 交互"),
             ("reanalysis/missing_data.html", "分析与数据"), ("presentation/deck.html", "项目演示")]
    links = []
    for target, label in pages:
        attrs = ' aria-current="page"' if target == active else ""
        if "cohort.html" in target:
            attrs += ' id="cohort-link" data-carry-patient="true"'
        if "scales.html" in target:
            attrs += ' id="pca-link" data-carry-patient="true"'
        links.append(f'<a href="{prefix}{target}"{attrs}>{label}</a>')
    return '<nav class="project-nav" aria-label="项目导航">' + "".join(links) + '</nav>'


def update_navigation(file, docs):
    """Add or refresh generated navigation without changing the report body."""
    import os
    import re
    relative = file.relative_to(docs).as_posix()
    prefix = os.path.relpath(docs, file.parent).replace("\\", "/") + "/"
    page = file.read_text(encoding="utf-8")
    page = re.sub(r'<!-- project-navigation -->.*?<!-- /project-navigation -->', '', page, flags=re.S)
    block = '<!-- project-navigation --><style>' + NAV_STYLE + '</style>' + navigation(prefix, relative) + '<!-- /project-navigation -->'
    if '<main' in page:
        page = re.sub(r'(<main[^>]*>)', lambda m: m.group(1) + block, page, count=1)
    file.write_text(page, encoding="utf-8")
