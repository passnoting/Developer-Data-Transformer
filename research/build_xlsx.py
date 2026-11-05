# -*- coding: utf-8 -*-
"""Build the 2026Q4 market research workbook."""
import math
from pathlib import Path
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.table import Table, TableStyleInfo

ROOT = Path(__file__).resolve().parent
OUT = ROOT.parent / "report" / "data" / "market-research-2026Q4.xlsx"
OUT.parent.mkdir(parents=True, exist_ok=True)

INK = "1F2937"
ACCENT = "1F4FD8"
HEAD_FILL = PatternFill("solid", fgColor="EEF2F9")
ZEBRA = PatternFill("solid", fgColor="FAFBFD")
GOOD = PatternFill("solid", fgColor="E8F7EF")
WARN = PatternFill("solid", fgColor="FFF4E5")
BAD = PatternFill("solid", fgColor="FDECEC")
THIN = Side(style="thin", color="DDE3EA")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
H_FONT = Font(name="Arial", size=10, bold=True, color="334155")


def disp_len(s):
    """Rough display width: CJK chars count double."""
    n = 0
    for ch in str(s):
        n += 2 if ord(ch) > 127 else 1
    return n


def est_lines(s, width):
    return max(1, math.ceil(disp_len(s) / max(width - 1, 6)))


def sheet(wb, title, widths, headers, rows, wrap_cols=(), num_cols=(), note=None):
    ws = wb.create_sheet(title)
    ws.sheet_view.showGridLines = False
    r = 1
    if note:
        ws.cell(row=1, column=1, value=note).font = Font(name="Arial", size=9, italic=True, color="64748B")
        ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=len(headers))
        ws.row_dimensions[1].height = 30
        ws.cell(row=1, column=1).alignment = Alignment(wrap_text=True, vertical="center")
        r = 3
    hr = r
    hdr_lines = 1
    for i, h in enumerate(headers, 1):
        c = ws.cell(row=hr, column=i, value=h)
        c.font = H_FONT
        c.fill = HEAD_FILL
        c.border = BORDER
        c.alignment = Alignment(vertical="center", wrap_text=True, horizontal="center")
        hdr_lines = max(hdr_lines, est_lines(h, widths[i - 1]))
    ws.row_dimensions[hr].height = max(26, hdr_lines * 14 + 8)
    for j, row in enumerate(rows):
        rr = hr + 1 + j
        lines = 1
        for i, v in enumerate(row, 1):
            c = ws.cell(row=rr, column=i, value=v)
            c.font = Font(name="Arial", size=10, color=INK)
            c.border = BORDER
            c.alignment = Alignment(vertical="top", wrap_text=(i in wrap_cols))
            if j % 2 == 1:
                c.fill = ZEBRA
            if i in num_cols and isinstance(v, (int, float)):
                c.number_format = "#,##0"
            if i in wrap_cols and v is not None:
                lines = max(lines, est_lines(v, widths[i - 1]))
        ws.row_dimensions[rr].height = min(max(16, lines * 13.5 + 4), 150)
    last = hr + len(rows)
    if rows:
        ws.auto_filter.ref = f"A{hr}:{get_column_letter(len(headers))}{last}"
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.freeze_panes = ws.cell(row=hr + 1, column=1)
    return ws, hr, last


wb = Workbook()
wb.remove(wb.active)

# ---------------------------------------------------------------- 1 说明
ws = wb.create_sheet("说明")
ws.sheet_view.showGridLines = False
ws.column_dimensions["A"].width = 3
ws.column_dimensions["B"].width = 26
ws.column_dimensions["C"].width = 110

lines = [
    ("H1", "海外 SaaS 市场调研 · 数据附录 · 2026 Q4"),
    ("P", "配套报告：report/index.html    |    数据截止：2026-11-04    |    口径：全球英语市场（US/EU/CA/AU）"),
    ("BLANK", ""),
    ("H2", "这个工作簿里有什么"),
    ("LI", "评分模型 —— 5 个方向 × 5 个维度的加权打分，以及权重定义"),
    ("LI", "竞品总表 —— 88 个产品的定位、免费层、入门价、计量方式（跨方向重复的已标注）"),
    ("LI", "关键词库 —— 132 个英文关键词，含月搜索量、意图、难度、建议打法"),
    ("LI", "缺口清单 —— 10 个可开工的服务位，含需求证据、1.0 形态、定价与评分"),
    ("LI", "单位经济 —— $100 预算分配、5 个收款通道实收对比、转化漏斗三档"),
    ("LI", "数据源 —— 每条关键事实的 URL、日期与可信度等级"),
    ("BLANK", ""),
    ("H2", "怎么读"),
    ("P", "1. 先看「评分模型」的第二块（权重），确认你认同这个权衡：缺口 25% > 需求/付费/可行 各 20% > 冷启动 15%。"),
    ("P", "2. 再看「缺口清单」，只读「需求证据」和「现有产品为什么接不住」两列——分数是判断，证据才是事实。"),
    ("P", "3. 「关键词库」可以直接按「建议」列排序，优先做标了「最优 / 金句词」的词。"),
    ("BLANK", ""),
    ("H2", "可信度分级（重要）"),
    ("LI", "A · 已验证 —— 实际打开页面/接口读到原文（GitHub API、npm API、官网 pricing、官方文档）"),
    ("LI", "B · 二手可信 —— 有署名的报道/汇总，标注了转引链（Bloomberg、TechCrunch、FintechSpecs、行业复盘）"),
    ("LI", "C · 推断/估算 —— 基于 SERP 观察与常识区间的量级判断，仅用于相对比较，不可当作绝对值引用"),
    ("BLANK", ""),
    ("H2", "已知偏差"),
    ("P", "· G2 / Capterra / Trustpilot / Reddit 在采集环境全部 403，差评样本偏技术社区（HN、GitHub Issues）。"),
    ("P", "· 无 Ahrefs / Semrush 权限；仅 CSV 方向 30 个词有第三方工具实测值，其余为区间估计。"),
    ("P", "· 私有 SaaS 的 ARR 普遍不透明；收入证据以融资、定价页、用户数、收购/关停替代。"),
    ("P", "· 所有价格「查于 2026-11」，政策类事实以标注日期为准，可能已变动。"),
    ("BLANK", ""),
    ("H2", "一句话结论"),
    ("P", "以 CSV/Excel 清洗工具免费获客，以「定时 + 校验 + 审计 + 断链告警」的数据管道收费；避开 AI Agent 监控与 AI 代码测试。"),
]
r = 1
for kind, text in lines:
    c = ws.cell(row=r, column=2 if kind != "P" else 2, value=text)
    if kind == "H1":
        c.font = Font(name="Arial", size=18, bold=True, color=ACCENT)
        ws.row_dimensions[r].height = 30
    elif kind == "H2":
        c.font = Font(name="Arial", size=11, bold=True, color="0F172A")
        ws.row_dimensions[r].height = 24
    elif kind == "LI":
        c.font = Font(name="Arial", size=10, color="334155")
        ws.row_dimensions[r].height = 17
    elif kind == "P":
        c.font = Font(name="Arial", size=10, color="334155")
        c.alignment = Alignment(wrap_text=True, vertical="top")
        ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=3)
        ws.row_dimensions[r].height = 30
    r += 1

# ---------------------------------------------------------------- 2 评分模型
dims = [
    ("需求强度", 0.20, "有多少人在主动找解决方案", [7, 8, 9, 6, 8]),
    ("供给缺口", 0.25, "现有产品哪里没做好 / 有没有人腾出位置", [7, 4, 7, 5, 9]),
    ("付费意愿", 0.20, "他们已经在为类似的东西付多少钱", [7, 7, 7, 8, 6]),
    ("单人可交付", 0.20, "一个人 6 周能否做出可信的 1.0", [8, 6, 8, 4, 6]),
    ("$100 冷启动", 0.15, "不花钱能不能被目标客户看见", [8, 5, 8, 4, 7]),
]
dirs = ["API 数据转换", "AI Agent 监控", "CSV / Excel 处理", "AI 代码测试", "小企业自动化"]
rows = []
for name, w, desc, scores in dims:
    rows.append([name, w, desc] + scores)
tot = ["加权总分", 1.0, "Σ(维度分 × 权重)"]
for i in range(5):
    tot.append(round(sum(d[1] * d[3][i] for d in dims), 2))
rows.append(tot)
rows.append(["排名", None, "按加权总分降序"] + [f"{i+1}" for i in sorted(range(5), key=lambda k: -tot[3 + k])])
ws, hr, last = sheet(
    wb, "评分模型",
    [16, 9, 40, 16, 16, 17, 16, 16],
    ["维度", "权重", "这个维度在问什么", *dirs],
    rows,
    wrap_cols=(3,), num_cols=(),
    note="评分 0–10，是判断值不是测量值。换一个评分者名次可能变化 1–2 位，但 Agent 与 Code 明显靠后这个结论是稳的。",
)
for rr in range(hr + 1, hr + 6):
    wc = ws.cell(row=rr, column=2)
    wc.number_format = "0%"
    wc.alignment = Alignment(horizontal="center")
ws.cell(row=hr + 6, column=2).number_format = "0%"
ws.cell(row=hr + 6, column=2).alignment = Alignment(horizontal="center")
for c in range(2, 9):
    ws.cell(row=hr + 7, column=c).alignment = Alignment(horizontal="center")
for c in range(4, 9):
    cell = ws.cell(row=hr + 6, column=c)
    cell.font = Font(name="Arial", size=10, bold=True)
    cell.fill = GOOD
    cell.number_format = "0.00"
    cell.alignment = Alignment(horizontal="center")
for c in range(1, 9):
    ws.cell(row=hr + 7, column=c).font = Font(name="Arial", size=10, bold=True, color="64748B")

# ---------------------------------------------------------------- 3 竞品总表
C = [
    # 方向, 产品, 定位, 免费层, 入门价(USD/月), 计量, 目标客户, 来源
    ("API", "Zapier", "9000+ 应用的无代码自动化", "100 tasks / 2 步 / 无 webhook", "$19.99（年付，750 tasks）", "task（成功 action）", "SMB 业务团队", "zapier.com/pricing.md (2026-11-04)"),
    ("API", "Make", "可视化场景编排", "1,000 credits / 2 scenario", "$9（10k credits）", "credit（每个 module）", "运营 / SMB", "make.com/pricing (2026-10 核对)"),
    ("API", "n8n", "可自托管的工作流", "自托管免费", "€20（2.5k 执行）", "execution（整条流程）", "技术团队", "n8n.io/pricing (2026-11)"),
    ("API", "Pipedream", "事件驱动开发者平台", "仅开发环境", "$99（Startup，10k credits）", "credit", "开发者", "pipedream.com/pricing (2026-11)"),
    ("API", "Retool Workflows", "内部工具 + 定时任务", "有", "按席位", "seat + 运行", "内部工具团队", "retool.com/pricing (动态渲染)"),
    ("API", "Workato", "企业自动化 + iPaaS", "无", "报价制", "task / recipe", "中大企业", "workato.com (报价制)"),
    ("API", "Boomi", "iPaaS + 主数据管理", "无", "报价制", "连接数 / 消息量", "企业", "boomi.com (报价制)"),
    ("API", "MuleSoft", "Anypoint API 集成平台", "无（Community 已停）", "报价制", "订阅 / vCore", "大型企业", "mulesoft.com (报价制)"),
    ("API", "Celigo", "NetSuite 生态集成", "无", "报价制", "flow / 端点", "中端 ERP 客户", "celigo.com (报价制)"),
    ("API", "Fivetran", "托管 ELT 标杆", "500k MAR", "年合约 $12,000 起", "monthly active rows", "中大型数据团队", "fivetran.com/pricing (2026-11)"),
    ("API", "Airbyte", "开源 ELT + 云托管", "自托管免费 / 14 天试用", "$20（5 credits）", "credit（≈1GB）", "中小数据团队", "airbyte.com/pricing (2026-11)"),
    ("API", "Estuary", "流式 CDC + 实时转换", "无公开", "unknown", "GB / 连接", "数据工程", "estuary.dev (未渲染)"),
    ("API", "Meltano", "开源 ELT（Singer 生态）", "开源免费", "Cloud 报价制", "项目 / 合约", "数据工程", "meltano.com (2026-11)"),
    ("API", "dbt", "SQL 转换层（T in ELT）", "dbt Core 免费", "按 developer seat", "seat", "分析工程", "getdbt.com/pricing (2026-11)"),
    ("API", "Parabola", "非技术运营的表格化数据流", "1 用户 / 1,000 credits", "已转报价制", "credit", "运营 / 财务", "parabola.io/pricing (2026-11)"),
    ("API", "Firecrawl", "网页 → 结构化数据", "500 搜索 / 1,000 页", "$16（Hobby）", "credit", "开发者 / AI 团队", "firecrawl.dev/pricing (2026-11)"),
    ("API", "Flatfile", "面向终端用户的文件导入", "有", "按导入量", "row / import", "SaaS 产品团队", "flatfile.com (2026-11)"),
    ("API/CSV", "OneSchema", "导入器 + AI 字段映射", "2,000 credits", "$20", "credits（$0.012）", "SaaS 产品团队", "oneschema.co/pricing (2026-11)"),
    ("API", "Unstructured", "文档 → 结构化数据", "有", "按页", "页", "AI 团队", "unstructured.io (2026-11)"),
    ("API", "LlamaParse", "复杂文档解析（LlamaIndex）", "有", "按页", "页", "AI 团队", "llamaindex.ai (2026-11)"),

    ("Agent", "Langfuse", "通用 trace + eval + prompt", "50k units / 2 席", "$29", "trace + observation + score", "SMB → 企业", "langfuse.com/pricing (2026-11)"),
    ("Agent", "LangSmith", "LangChain 原生可观测性", "5k traces / 1 席", "$39 / 席", "seat + LSU（$1.00）", "已用 LangChain 的团队", "langchain.com/pricing (2026-11)"),
    ("Agent", "Arize Phoenix", "开源 trace / eval", "无限", "$0（自建）", "span", "有 DevOps 的团队", "github.com/Arize-ai/phoenix (2026-11)"),
    ("Agent", "Arize AX", "企业 eval + 合规", "25k spans", "$50", "span + GB", "企业", "arize.com/pricing (2026-11)"),
    ("Agent", "W&B Weave", "W&B 生态内的 LLM 追踪", "unknown", "unknown", "unknown", "ML 团队", "wandb.ai (2026-11)"),
    ("Agent", "Helicone", "网关式日志，最轻", "10k req", "$79", "request + GB", "轻量团队", "helicone.ai/pricing (2026-11)"),
    ("Agent", "Braintrust", "eval-first 平台", "$10 credits + 1GB", "$249", "GB processed + score", "AI 原生团队", "braintrust.dev/pricing (2026-11)"),
    ("Agent", "AgentOps", "agent 专用，pip 一行接入", "有（额度未公开）", "unknown", "event / span", "agent 开发者", "agentops.ai (2026-11)"),
    ("Agent", "Traceloop", "OTel 平台，企业向", "50k spans / 5 席", "仅 Enterprise", "span", "企业", "traceloop.com/pricing (2026-11)"),
    ("Agent", "OpenLLMetry", "埋点 SDK（非平台）", "免费", "$0", "无（自选后端）", "开发者", "github.com/traceloop/openllmetry"),
    ("Agent", "PromptLayer", "prompt 版本 + 日志", "2.5k req", "$49", "request（$0.003）", "团队", "promptlayer.com/pricing (2026-11)"),
    ("Agent", "Honeycomb", "通用 APM + LLM 语义", "有", "unknown", "event / GB", "企业", "honeycomb.io (2026-11)"),
    ("Agent", "Datadog LLM Obs.", "全栈 APM 延伸", "40k LLM spans", "$160", "仅 LLM span", "大企业", "datadoghq.com/pricing (2026-11)"),
    ("Agent", "New Relic", "全栈按量计费", "100GB / 月", "$0.40/GB 超量", "GB + seat", "企业", "newrelic.com/info/pricing (2026-11)"),
    ("Agent", "Fiddler", "企业 AI 控制面 / 合规", "仅 guardrails", "$0.002 / trace", "trace", "企业", "fiddler.ai/pricing (2026-11)"),
    ("Agent", "Humanloop", "prompt / eval 平台", "—", "已关停（2025-08，被 Anthropic 收购）", "—", "—", "humanloop.com/docs/v5/changelog/2025/08"),
    ("Agent", "Galileo", "eval / 护栏", "—", "被 Cisco/Splunk 收购（2026-05）", "—", "—", "行业报道 (2026-05)"),
    ("Agent", "Vellum", "prompt / eval 平台", "—", "已关停（2026-11-02）", "—", "—", "vellum.ai (2026-11)"),

    ("CSV", "Julius AI", "上传 CSV 对话式分析 / 建模", "有额度", "unknown（官网 403）", "消息 / 额度", "CSV 分析师", "julius.ai (2026-11)"),
    ("CSV", "Rows", "在线表格 + AI + 连接器", "5 AI tasks / 1MB", "已关停（2026-05-31）", "—", "—", "rows.com/blog/post/rows-is-joining-superhuman"),
    ("CSV", "Quadratic", "AI + Python/SQL 表格", "有限 AI", "$18 / 用户", "AI credits", "分析师", "quadratichq.com/pricing (2026-11)"),
    ("CSV", "Numerous.ai", "=AI() 批量清洗 / 分类", "7 天试用", "$10", "字符 + 公式次数", "运营", "numerous.ai (2026-11)"),
    ("CSV", "Formula Bot", "文本生公式 + 数据分析", "10 消息 / 25 actions", "$20", "AI Actions", "个人", "betteranalyst.com (2026-11)"),
    ("CSV", "SheetAI", "Sheets AI 函数（可 BYOK）", "BYOK 免费不限", "$12", "~500 runs/月", "个人", "sheetai.app/pricing (2026-11)"),
    ("CSV", "Bricks", "CSV → 仪表盘 / 报告", "20 条 AI 消息", "$25 / 用户", "AI messages", "小团队", "thebricks.com/pricing (2026-11)"),
    ("CSV", "OpenRefine", "本地开源清洗 / 聚类", "全免费", "$0", "—", "数据工作者", "openrefine.org"),
    ("CSV", "Easy Data Transform", "桌面可视化 ETL", "全功能试用", "$99 一次性", "授权", "个人", "easydatatransform.com"),
    ("CSV", "CSVbox", "嵌入式 CSV 导入 + 校验", "100 导入 / 5 行", "$16（年付）", "导入数 + 行数", "SaaS 团队", "csvbox.io/pricing (2026-11)"),
    ("CSV", "Dromo", "嵌入式导入 + AI 映射", "sandbox", "$599", "250 导入（$3/个）", "SaaS 团队", "dromo.io/pricing (2026-11)"),
    ("CSV", "Coefficient", "Sheets ↔ CRM/DB 定时刷新", "3 源 / 5k 行 / 50 刷新", "$49（$99/用户）", "刷新次数 + 席位", "财务 / RevOps", "coefficient.io/pricing (2026-11)"),
    ("CSV", "Airtable", "表格数据库 + 自动化", "1k 记录", "按 seat", "记录 / 自动化 runs", "团队", "airtable.com/pricing (2026-11)"),
    ("CSV", "Gumloop", "AI 工作流 + 表格节点", "试用", "$37", "credits", "运营", "gumloop.com/pricing (2026-11)"),
    ("CSV/SMB", "Zapier Tables", "自动化数据表", "100 tasks", "unknown", "tasks", "团队", "zapier.com/tables (2026-11)"),
    ("CSV", "ConvertCSV", "CSV↔JSON/SQL/XML，纯前端", "全免费", "$0（API 另计）", "—", "流量站", "convertcsv.com（月访问约 81 万）"),
    ("CSV", "TableConvert", "30+ 格式互转 + 编辑器", "免费（带广告）", "$12", "credits", "流量站", "tableconvert.com/pricing（月访问约 45 万）"),
    ("CSV", "CloudConvert", "通用格式转换（含 CSV/XLSX）", "10 credits / 日", "按 credits 包", "credits", "流量站", "cloudconvert.com/pricing (2026-11)"),

    ("Code", "Qodo (Codium)", "从 PR 审查到测试生成", "14 天试用", "$0.012 / credit", "credit（池化）", "中大型团队", "qodo.ai/pricing (2026-11)"),
    ("Code", "Diffblue Cover", "Java 自动写单测", "试用", "报价制", "项目", "银行 / 保险 Java", "diffblue.com (2026-11)"),
    ("Code", "Early AI", "给存量代码生成单测", "unknown", "unknown", "—", "中小团队", "early.ai (2026-11)"),
    ("Code", "Tusk", "PR 自动补测试", "unknown", "unknown", "—", "小团队", "usetusk.ai (2026-11)"),
    ("Code", "CodeRabbit", "PR 审查 + 生成测试", "有免费档", "unknown", "仓库 / 席位", "全规模", "coderabbit.ai (2026-11)"),
    ("Code", "Sentry Seer", "从线上错误反推修与测", "随 Sentry 免费档", "unknown", "事件量", "Sentry 用户", "sentry.io (2026-11)"),
    ("Code", "GitHub Copilot", "IDE 内生成测试", "有免费档", "$10 / 席", "席位", "全部", "github.com/features/copilot (2026-11)"),
    ("Code", "QA Wolf", "托管式 E2E，保证覆盖率", "试用 runs", "$1 / run（Web）$2（Mobile）", "按结果 run", "中型 SaaS", "qawolf.com/pricing (2026-11)"),
    ("Code", "Momentic", "AI 原生 E2E", "2,000 credits", "$125", "credit + 并发", "产品团队", "momentic.ai/pricing (2026-11)"),
    ("Code", "Octomind", "AI 生成 + 托管 E2E", "—", "已关停（2026-04 宣布，6 月关闭）", "—", "—", "monito.dev/compare/octomind (存档)"),
    ("Code", "Testsigma", "低代码 + Agentic 测试", "无", "无公开价", "并行 / 分钟", "企业", "testsigma.com (2026-11)"),
    ("Code", "Applitools", "视觉 AI + Autonomous", "试用", "$667（年付）", "checkpoint", "企业", "applitools.com/pricing (2026-11)"),
    ("Code", "mabl", "低代码企业 E2E", "无", "无公开价", "并行", "企业", "mabl.com (2026-11)"),
    ("Code", "Testim (Tricentis)", "AI E2E", "试用", "报价制", "seat", "企业", "tricentis.com (2026-11)"),
    ("Code", "Meticulous", "AI E2E（视觉 diff）", "有", "unknown", "—", "前端团队", "meticulous.ai (2026-11)"),
    ("Code", "Codecov", "覆盖率", "公开仓库无限 + 250 私有上传", "按席位", "仓库 / 上传", "工程团队", "codecov.io (2026-11)"),
    ("Code", "Coveralls", "覆盖率", "OSS 永久免费", "$10（1 私有仓）", "私有仓库数", "小团队", "coveralls.io/pricing (2026-11)"),
    ("Code", "SonarQube", "代码质量 / 静态分析", "Community 免费", "报价制", "LOC", "工程团队", "sonarsource.com (2026-11)"),
    ("Code", "Stryker", "变异测试", "完全免费", "$0", "—", "开源", "stryker-mutator.io"),

    ("SMB", "Relay.app", "人机协同审批自动化", "—", "已关停（2026-09）", "—", "—", "relay.app"),
    ("SMB", "Bardeen", "网页抓取 / 线索（已转型）", "unknown", "unknown", "—", "销售", "bardeen.ai (2026-11)"),
    ("SMB", "Activepieces", "开源、可自托管", "1,000 credits", "$20（10k credits）", "credit（仅 AI 计费）", "小团队", "activepieces.com/pricing (2026-11)"),
    ("SMB", "Windmill", "面向开发者的执行平台", "自托管无限执行", "$120（Enterprise）", "seat + worker", "开发者", "windmill.dev/pricing (2026-11)"),
    ("SMB", "Lindy", "Slack 里的 AI 队友", "$50 credits（7 天）", "$49.99 / 人", "credit", "SMB", "lindy.ai/pricing (2026-11)"),
    ("SMB", "Relevance AI", "AI Workforce", "无自助", "仅 Enterprise", "自定义", "企业", "relevanceai.com/pricing (2026-11)"),
    ("SMB", "Dify", "开源 LLM 应用平台", "社区版免费", "$590 / 工作区 / 年", "message credit", "团队", "dify.ai/pricing (2026-11)"),
    ("SMB", "Coze", "Bot 平台（字节）", "有免费额度", "unknown", "—", "个人", "coze.com (2026-11)"),
    ("SMB", "Durable", "30 秒建站 + AI agent", "300 credits", "$25（1k credits）", "credit", "本地商家", "durable.com/pricing (2026-11)"),
    ("SMB", "Jobber", "家政派单 / 收款", "unknown", "unknown（Cloudflare 拦截）", "seat", "家政服务", "getjobber.com"),
    ("SMB", "Housecall Pro", "家政派单 / 收款", "unknown", "unknown（Cloudflare 拦截）", "seat", "家政服务", "housecallpro.com"),
    ("SMB", "Podium", "评价 + 短信 + AI 接待", "无", "销售制（10 万+ 客户）", "消息 / 席位", "本地商家", "podium.com"),
    ("SMB", "SimpleTexting", "短信营销", "unknown", "unknown", "短信条数", "SMB", "simpletexting.com"),
    ("SMB", "Zapier（同 API）", "见 API 行", "100 tasks", "$19.99", "task", "SMB", "同上"),
    ("SMB", "Make（同 API）", "见 API 行", "1,000 credits", "$9", "credit", "SMB", "同上"),
    ("SMB", "n8n（同 API）", "见 API 行", "自托管免费", "€20", "execution", "技术团队", "同上"),
]
ws, hr, last = sheet(
    wb, "竞品总表",
    [9, 20, 30, 26, 24, 22, 18, 38],
    ["方向", "产品", "一句话定位", "免费层", "入门价", "计量方式", "目标客户", "来源 / 查证日"],
    C, wrap_cols=(3, 4, 5, 6, 7, 8),
    note=f"共 {len(C)} 行（含 3 行跨方向重复，去重后约 {len(C)-3} 个产品）。价格查于 2026-11，动态渲染或报价制的标注 unknown / 报价制，未编造。",
)

# ---------------------------------------------------------------- 4 关键词库
K = []
def add(d, items):
    for it in items:
        K.append((d, *it))

add("API 转换", [
    ("convert json to csv api", 300, "交易", "低", "最优 · 直接对应付费意图"),
    ("json to csv converter api", 400, "交易", "低", "最优"),
    ("api response to excel", 250, "交易", "低", "最优"),
    ("rest api to csv", 500, "交易", "低", "最优"),
    ("json to excel api", 350, "交易", "低", "可打"),
    ("transform api response to table", 90, "交易", "低", "金句词 · 意图=付费"),
    ("scheduled api to csv export", 70, "交易", "低", "金句词 · 意图=付费"),
    ("webhook payload transform", 150, "信息", "低", "可打"),
    ("transform webhook json to csv", 30, "交易", "低", "可打"),
    ("json schema mapping tool", 200, "商业", "低", "可打"),
    ("json mapping ui", 100, "商业", "低", "可打"),
    ("field mapping automation", 150, "商业", "中", "需差异化"),
    ("nested json to csv", 900, "信息", "低", "工具页引流"),
    ("flatten json to table", 300, "信息", "低", "工具页引流"),
    ("json to csv with nested objects", 200, "信息", "低", "工具页引流"),
    ("api pagination to csv", 50, "信息", "低", "内容钩子"),
    ("csv export from rest api", 250, "交易", "低", "可打"),
    ("api to google sheets", 2400, "交易", "中", "强需求 · 需差异化落地页"),
    ("webhook to google sheets", 1300, "交易", "中", "可打 · 转化路径短"),
    ("api to spreadsheet automation", 300, "交易", "中", "可打"),
    ("no code api connector", 350, "商业", "中", "需差异化"),
    ("api data transformation tool", 250, "商业", "中", "需差异化"),
    ("etl alternative for startups", 200, "商业", "中", "对比页"),
    ("api integration platform for small business", 400, "商业", "高", "别正面打"),
    ("zapier alternative cheaper", 1900, "商业", "高", "别正面打"),
    ("json schema change breaking pipeline", 50, "信息", "低", "内容钩子 · 直接对应痛点"),
])
add("Agent 监控", [
    ("langsmith alternative", 300, "商业", "低", "最优 · SERP 弱"),
    ("langfuse alternative", 150, "商业", "低", "最优"),
    ("langfuse self hosted", 400, "商业", "低", "可打（流量流向文档）"),
    ("langfuse pricing", 350, "商业", "中", "对比页"),
    ("langfuse vs langsmith", 900, "对比", "高", "别打 · 已被对比站占满"),
    ("llm observability", 1300, "信息", "高", "别打"),
    ("llm observability tools", 450, "商业", "中", "需差异化"),
    ("ai agent observability", 500, "信息", "中", "可打"),
    ("agent observability open source", 90, "商业", "低", "最优"),
    ("openai agent monitoring", 250, "商业", "中", "可打"),
    ("llm trace debugging", 70, "商业", "低", "可打"),
    ("trace llm calls", 100, "信息", "低", "内容"),
    ("llm cost tracking", 350, "商业", "中", "工具页"),
    ("prompt version control", 600, "商业", "中", "已被覆盖"),
    ("prompt management tool", 500, "商业", "中", "需差异化"),
    ("llm evaluation tool", 800, "商业", "高", "别打"),
    ("rag evaluation", 700, "信息", "中", "内容"),
    ("llm as judge", 1600, "信息", "高", "别打"),
    ("ai agent testing", 400, "商业", "中", "可打"),
    ("ai agent regression testing", 50, "商业", "低", "最优 · 缺口词"),
    ("how to debug ai agent", 90, "信息", "低", "内容引流"),
    ("opentelemetry llm", 200, "信息", "低", "内容"),
])
add("CSV / Excel", [
    ("csv to json", 40000, "工具", "高", "大站占满 · 别打"),
    ("csv to excel", 30000, "工具", "高", "大站占满"),
    ("json to csv", 20000, "工具", "高", "大站占满"),
    ("remove duplicates in excel", 18000, "how-to", "中", "可打"),
    ("excel to json", 8000, "工具", "中", "可打"),
    ("csv to sql", 5000, "工具", "中", "可打"),
    ("merge csv files", 2500, "工具", "低", "可打"),
    ("split csv file", 1500, "工具", "低", "可打"),
    ("excel formula generator", 1000, "工具", "低", "陷阱 · KD 低但已被套利饱和"),
    ("excel formula generator free", 1500, "工具", "低", "陷阱"),
    ("clean csv online", 1000, "工具", "低", "最优"),
    ("csv validator", 800, "工具", "低", "最优"),
    ("csv to google sheets", 700, "工具", "低", "可打"),
    ("remove blank rows csv", 600, "工具", "低", "可打"),
    ("split column by delimiter online", 400, "工具", "低", "可打"),
    ("remove empty columns excel", 350, "how-to", "低", "可打"),
    ("fix csv encoding utf-8", 300, "故障", "低", "最优 · SERP 是论坛帖"),
    ("excel formula from text description", 150, "商业", "低", "可打"),
    ("excel formula checker", 250, "商业", "低", "最优 · 对应 Excel 体检"),
    ("convert csv to json with headers", 250, "工具", "低", "可打"),
    ("remove duplicates from csv keep first", 200, "精确", "低", "最优"),
    ("csv delimiter changer", 200, "工具", "低", "最优"),
    ("dedupe csv online", 120, "工具", "低", "最优"),
    ("validate csv before import", 90, "商业", "低", "金句词 · 意图=付费"),
    ("merge excel sheets into one", 900, "how-to", "中", "可打"),
    ("text to formula", 320, "工具", "低", "可打"),
    ("excel ai assistant", 110, "商业", "低", "可打"),
    ("ai excel formula", 50, "商业", "低", "可打"),
    ("csv to json python", 2000, "开发", "中", "内容（开发者，不付费）"),
    ("formula bot", 880, "品牌", "低", "竞品词 · 可做对比页"),
])
add("代码测试", [
    ("unit test generator", 2000, "商业", "中", "Qodo/Copilot 占位"),
    ("pytest coverage report", 1500, "信息", "高", "别打"),
    ("ai unit test generator", 1200, "商业", "中", "需差异化"),
    ("ai test generation", 900, "商业", "高", "资本密集区"),
    ("ai qa automation", 800, "商业", "高", "别打"),
    ("mutation testing tool", 700, "商业", "中", "Stryker 占位"),
    ("cypress test generator", 600, "商业", "中", "通用词"),
    ("flaky test detection", 500, "信息+商业", "中", "最优 · 对应缺口 (c)"),
    ("jest test generator", 400, "交易", "低", "可打"),
    ("github copilot unit tests", 400, "信息", "中", "内容"),
    ("mutation testing vs code coverage", 400, "信息", "中", "内容"),
    ("playwright flaky test", 350, "信息", "低", "可打 · 痛点词"),
    ("java unit test generator", 350, "交易", "中", "可打"),
    ("test impact analysis", 300, "商业", "中", "可打 · 对应缺口 (a)"),
    ("playwright test generator ai", 300, "商业", "低", "对应托管模式（别做）"),
    ("octomind alternative", 300, "商业", "低", "最优 · 关停红利 6–12 个月"),
    ("selenium test generator ai", 250, "商业", "中", "通用词"),
    ("qa wolf alternative", 200, "商业", "低", "可打 · 对比页"),
    ("generate pytest from function", 150, "交易", "低", "可打"),
    ("ai generated tests useless", 150, "信息", "低", "情绪词 · 引到可信度检测"),
    ("increase code coverage automatically", 100, "商业", "低", "可打"),
    ("diffblue alternative", 100, "商业", "低", "对比页"),
    ("tests assert nothing", 50, "信息", "低", "内容"),
    ("code coverage badge", 1000, "信息", "高", "别打"),
])
add("小企业自动化", [
    ("workflow automation", 22000, "信息", "高", "别打"),
    ("ai automation", 20000, "信息", "高", "别打"),
    ("automation software", 18000, "商业", "高", "别打"),
    ("zapier alternative", 12000, "商业", "高", "别打"),
    ("business process automation", 9000, "商业", "高", "别打"),
    ("zapier pricing", 9000, "商业", "中", "对比页"),
    ("no code automation", 8000, "信息", "中", "内容"),
    ("make vs zapier", 6500, "商业", "中", "对比页"),
    ("n8n vs zapier", 4000, "商业", "中", "对比页"),
    ("make.com pricing", 3000, "商业", "低", "对比页"),
    ("automated appointment reminders", 2000, "商业", "中", "垂直内容"),
    ("missed call text back", 1600, "商业", "低", "可打 · 垂直服务"),
    ("smb automation", 1200, "商业", "低", "可打"),
    ("zapier vs make vs n8n", 1200, "商业", "低", "对比页"),
    ("shopify to quickbooks automation", 900, "商业", "低", "可打"),
    ("n8n vs zapier pricing", 800, "交易", "低", "对比页"),
    ("google review request automation", 700, "商业", "低", "可打"),
    ("zapier task limit", 500, "信息", "低", "内容"),
    ("zapier too expensive", 400, "商业", "低", "可打 · 对比页"),
    ("automation monitoring tool", 400, "商业", "低", "最优 · ★ 无工具型落地页"),
    ("law firm intake automation", 350, "商业", "低", "垂直"),
    ("zapier for real estate agents", 300, "商业", "低", "垂直"),
    ("zapier monitoring", 300, "交易", "低", "最优 · ★ 最优词"),
    ("automate invoice reminders for small business", 250, "商业", "低", "最优"),
    ("hvac dispatch automation", 250, "商业", "低", "最优 · 垂直"),
    ("zapier error alerts", 200, "交易", "低", "最优 · ★ 最优词"),
    ("dental practice automation", 200, "商业", "低", "垂直"),
    ("quickbooks late payment reminder", 200, "商业", "低", "垂直"),
    ("housecall pro zapier", 150, "交易", "低", "垂直"),
    ("jobber automation", 120, "交易", "低", "垂直"),
])
ws, hr, last = sheet(
    wb, "关键词库",
    [14, 42, 12, 14, 8, 34],
    ["方向", "关键词", "月搜索量", "意图", "难度", "建议 / 说明"],
    K, wrap_cols=(6,), num_cols=(3,),
    note=f"共 {len(K)} 个词。除 CSV 方向的 30 个有第三方工具实测值外，其余为区间估计（0 预算无 Ahrefs 权限）。用途：相对排序 + 内容日历，不要当绝对流量预测。",
)
# colour-code suggestions
for row in range(hr + 1, last + 1):
    v = ws.cell(row=row, column=6).value or ""
    if v.startswith("最优") or v.startswith("金句词"):
        ws.cell(row=row, column=6).fill = GOOD
    elif v.startswith("别打") or v.startswith("陷阱") or v.startswith("大站"):
        ws.cell(row=row, column=6).fill = BAD

# ---------------------------------------------------------------- 5 缺口清单
G = [
    (1, "自动化断链监控（Zapier / Make / n8n 静默失败告警）", "Zapier 官方文档承认 Safely halted 不告警；Make Ignore 让失败项消失；zapier monitoring KD≈10", "原生 Alerts + Observability API 仅 Enterprise；第三方只有零星咨询师与包月代管", "计数比对 + 心跳 + 邮件告警，不依赖平台 API", "$19–49/月", 8, 9, 9),
    (2, "脏 CSV/Excel 的中价位清洗管道（定时+校验+审计）", "clean csv online 1,000/KD22；validate csv before import KD5；AI 编数据的恐惧普遍", "CSVbox $16 只做一次性导入；OneSchema $200、Dromo $599 要工程接入", "规则化清洗 + 每格 diff + 每日定时 + 审计日志", "$19–49/月", 9, 8, 9),
    (3, "schema 变更的人话级评审与自动适配", "Airbyte 2026 年三个 issue 全是 schema change 导致静默丢数；Zapier 承认换步骤顺序即断映射", "现有产品把 JSON diff 丢给工程师，非技术用户无法判断影响", "变更 → 影响面 → 一句人话建议 → 一键适配", "$19–49/月（或含在 #2）", 7, 9, 8),
    (4, "API/JSON → 定时刷新的干净表格（非开发者版）", "api to google sheets 2,400；scheduled api to csv export 意图极强；npm json-2-csv 640 万/月", "Zapier 按 task 计费且免费层无 webhook；Airbyte 要先有 warehouse；Pipedream 要写代码", "5 个源 + 任意 REST 入口 → Sheets/CSV，按表计价", "$19–49/月", 8, 8, 8),
    (5, "Excel 模型体检（错公式/断链/硬编码/循环引用）", "会计与 FP&A 痛点极强；审计咨询 $100–300/小时；excel formula checker 250/KD12", "几乎没有产品化，只有人类审计与零散小工具", "上传 .xlsx → 12 项体检报告（可交付给老板/客户）", "$99–499 一次性", 7, 9, 7),
    (6, "垂直行业成品自动化包（HVAC/牙科/法律/房产）", "missed call text back 1,600；hvac dispatch automation 250/KD14；服务商自认垂直空缺", "通用模板饱和；Podium 等垂类工具贵且绑定；小商家要人帮装", "2–3 条成品流程 + 安装 + 月度托管", "$500–1,500 安装 + $200–500/月", 8, 7, 7),
    (7, "Flaky test 根因诊断", "HN 原句「每周花几小时返工」；flaky test detection 500；现有工具只识别不归因", "Codecov / Datadog CI 只做识别/隔离/重跑，根因要人肉查", "JUnit XML + 重跑 → 根因报告（CLI / VS Code）", "$19–49/月", 6, 8, 8),
    (8, "AI Agent 失败根因报告（不是 trace 面板）", "HN「几十万次运行根本没法追踪」「静默退化无告警」；LangSmith ARR 估算 $1,200–1,600 万", "Langfuse 等开源把存储+面板做成免费；巨头收购后重心转企业合规", "每日失败摘要邮件，归到 5–8 个固定原因", "$29–99/月", 8, 7, 6),
    (9, "Prompt / Agent 回归门禁（改了会不会退化）", "ai agent regression testing KD 极低；离线 dataset 与线上 trace 两套模型从未打通", "Braintrust / LangSmith 做评测但闭环靠手工；promptfoo 被 OpenAI 收，只覆盖 CI 侧", "PR 里跑变更影响面 diff，不达标就挡", "$29–99/月", 7, 7, 6),
    (10, "按变更风险排序的测试补齐", "Stack Overflow 2025：66% 花更多时间修「几乎对」的代码；覆盖率已成表演", "所有人都在优化覆盖率，没人优化故障概率", "静态分析 + 只跑受影响测试 + 风险排序", "$29–99/月", 6, 7, 6),
]
rows = [[g[0], g[1], g[2], g[3], g[4], g[5], g[6], g[7], g[8], round(0.35 * g[6] + 0.40 * g[7] + 0.25 * g[8], 2)] for g in G]
ws_g, hr_g, last_g = sheet(
    wb, "缺口清单",
    [6, 40, 52, 52, 40, 24, 8, 8, 8, 9],
    ["#", "服务位", "需求证据", "现有产品为什么接不住", "1.0 形态", "定价", "需求", "缺口", "可行", "综合"],
    rows, wrap_cols=(2, 3, 4, 5, 6),
    note="综合 = 0.35×需求 + 0.40×缺口 + 0.25×单人可行。分数是判断，请重点看证据列。",
)
for rr in range(hr_g + 1, last_g + 1):
    c = ws_g.cell(row=rr, column=10)
    c.number_format = "0.00"
    c.alignment = Alignment(horizontal="center")
    c.font = Font(name="Arial", size=10, bold=True)
    ws_g.cell(row=rr, column=1).alignment = Alignment(horizontal="center")

# ---------------------------------------------------------------- 6 单位经济
ws = wb.create_sheet("单位经济")
ws.sheet_view.showGridLines = False
ws.column_dimensions["A"].width = 3
for col, w in zip("BCDE", [34, 18, 22, 40]):
    ws.column_dimensions[col].width = w

def block(title, row, headers, data, note=""):
    c = ws.cell(row=row, column=2, value=title)
    c.font = Font(name="Arial", size=12, bold=True, color=ACCENT)
    r = row + 1
    for i, h in enumerate(headers):
        cc = ws.cell(row=r, column=2 + i, value=h)
        cc.font = H_FONT
        cc.fill = HEAD_FILL
        cc.border = BORDER
        cc.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    ws.row_dimensions[r].height = 30
    for j, d in enumerate(data):
        for i, v in enumerate(d):
            cc = ws.cell(row=r + 1 + j, column=2 + i, value=v)
            cc.font = Font(name="Arial", size=10)
            cc.border = BORDER
            cc.alignment = Alignment(vertical="top", wrap_text=True)
        if j % 2 == 1:
            for i in range(len(headers)):
                ws.cell(row=r + 1 + j, column=2 + i).fill = ZEBRA
    if note:
        nc = ws.cell(row=r + len(data) + 2, column=2, value=note)
        nc.font = Font(name="Arial", size=9, italic=True, color="64748B")
        return r + len(data) + 3
    return r + len(data) + 2

r = 1
ws.cell(row=r, column=2, value="单位经济：一个 $19/月 的产品，钱是怎么没的").font = Font(name="Arial", size=16, bold=True)
r += 2

r = block("① $100 预算分配", r,
          ["项目", "金额", "是否必须", "说明"],
          [("域名（.com，Cloudflare 成本价）", "$10.44", "必须", "唯一必须花的钱"),
           ("Chrome 扩展注册（可选）", "$5.00", "可选", "只在做「从页面抓表」时花"),
           ("Reddit 小广告测文案（4 天 × $5）", "$20.00", "建议", "不是为了获客，是测哪句话有人点"),
           ("买一个竞品高级版看 onboarding", "$25.00", "建议", "比读 10 篇评测有用"),
           ("机动", "$39.56", "备用", "留给「你付费我就试」的时刻"),
           ("合计", "$100.00", "", "其中约 $36 是不必花的")])

r = block("② 月收入 $1,000 时，各通道实收（10 笔 $100，跨境卡订阅）", r,
          ["通道", "费率", "实收", "备注"],
          [("Stripe（直连）", "2.9%+$0.30，国际卡 +1.5%", "≈$953", "需海外实体与账户；自己报 VAT/销售税"),
           ("Creem", "3.9%+$0.40", "≈$950", "MoR 代缴税；支付宝提现，$50 起付"),
           ("Paddle", "5%+$0.50", "≈$945", "MoR；需站点审核"),
           ("Lemon Squeezy", "5%+$0.50", "≈$945", "已是 Stripe 公司"),
           ("Polar", "5%+$0.50（+1.5% 国际卡）", "≈$930", "MoR；开发者工具友好")])

r = block("③ 单客户经济（$19/月）", r,
          ["项", "数值", "口径", "说明"],
          [("月费", "$19.00", "挂牌价", ""),
           ("MoR 抽成后实收", "$17.55", "5%+$0.50", "Creem 更低：$18.16"),
           ("年净收入", "$210.60", "实收 × 12", "不含流失"),
           ("月流失 8% 时的 LTV", "≈$219", "实收 / 流失率", "只够覆盖极低的 CAC"),
           ("年付 $190（≈2 个月免费）时的 LTV", "≈$180", "一次性", "但现金流与留存显著更好")])

r = block("④ 转化漏斗三档（要 10 个付费用户需要多少流量）", r,
          ["情形", "免费→付费", "需要注册数", "需要访客数"],
          [("乐观", "4%", "250", "8,300（按 3% 注册率）"),
           ("基准", "2%", "500", "16,700"),
           ("悲观", "1%", "1,000", "33,300")],
          )

r = block("⑤ 第一笔收入的四条路径（按速度排序）", r,
          ["路径", "到账时间", "单价", "现实产出（30 天）"],
          [("手工交付 + 服务化订单", "24–72 小时", "$49–99/单", "3–6 单"),
           ("社区答疑转化", "3–7 天", "$19–49/月", "1–3 个付费"),
           ("Product Hunt / Show HN", "当天，量小", "$19/月", "0–2 个付费"),
           ("SEO 工具页", "3–12 个月", "$19/月", "30 天内≈0")])

# ---------------------------------------------------------------- 7 数据源
S = [
    ("Chrome 商店内支付 2020-09-21 停止新建、2021-02-01 起不再收款", "Chrome 官方弃用页", "https://developer.chrome.com/docs/webstore/cws-payments-deprecation", "2020-09", "A"),
    ("扩展审核多数 <24h，90%+ 3 天内", "Chrome 官方审核说明", "https://developer.chrome.com/docs/webstore/review-process", "2026-11", "A"),
    ("91.5% 的扩展用户数 <1,000", "Crawlora 全量抓取统计", "https://crawlora.net/blog/chrome-extension-graveyard-2026", "2026", "B"),
    ("付费功能须填真实物理地址；MV3 禁远程代码", "Chrome 商店政策", "https://developer.chrome.com/docs/webstore/program-policies", "2026-11", "A"),
    ("Shopify 应用首 $1M 终身 0%，超出 15%", "Shopify changelog", "https://shopify.dev/changelog/posts/update-to-shopifys-app-developer-revenue-share", "2025-04", "A"),
    ("Creem 3.9%+$0.40，支付宝单笔 ≤5 万 CNY，$50 起付", "Creem 官方文档", "https://docs.creem.io/merchant-of-record/finance/payouts", "2026-11", "A"),
    ("Polar 5%（Free）/ 4%+$25（Pro）", "Polar 官方费率", "https://polar.sh/docs/merchant-of-record/fees", "2026-11", "A"),
    ("Paddle / LS 5%+$0.50；$1M ARR 有效费率 5.5%–6.2%", "FintechSpecs 对比", "https://fintechspecs.com/blog/merchant-of-record-fees-compared/", "2026-10", "B"),
    ("新页面一年内进前 10 仅 1.74%（英文 6.11%）；前 10 页面 73% 超 3 年", "Ahrefs 100 万 URL 研究", "https://ahrefs.com/blog/how-long-does-it-take-to-rank-in-google-and-how-old-are-top-ranking-pages/", "2025-05", "A"),
    ("Show HN 中位 2 分；50 分=前 6%；半衰期 24h", "188,085 帖全量分析", "https://danfking.github.io/blog/2026/04/23/show-hn-by-the-numbers/", "2026-04", "B"),
    ("PH featured #6 第 30 天：9 客户 / $531", "VisitTrack 复盘", "https://visitrack.app/blog/how-to-measure-product-hunt-launch", "2026-10", "C"),
    ("Sheets 插件 OAuth 验证卡审 8 周", "Google 开发者论坛", "https://discuss.google.dev/t/oauth-verification-for-workspace-add-on-stuck-for-8-weeks-client-critical/318451", "2026-01", "B"),
    ("Rows 被 Superhuman 收购，2026-05-31 关停；220 万用户、83 亿次导入", "Rows 官方博客", "https://rows.com/blog/post/rows-is-joining-superhuman", "2026-02", "A"),
    ("Langfuse 36,991 stars / MIT", "GitHub API", "https://api.github.com/repos/langfuse/langfuse", "2026-11-04", "A"),
    ("Langfuse 被 ClickHouse 收购", "Langfuse 博客", "https://langfuse.com/blog/joining-clickhouse", "2026-01", "A"),
    ("Arize 被 Dynatrace 以 $9.15 亿收购", "Dynatrace 新闻稿 / 行业报道", "https://www.dynatrace.com/news/", "2026-08", "B"),
    ("Octomind 2026-04 宣布关停，6 月公司关闭", "Monito 存档说明", "https://www.monito.dev/compare/octomind", "2026-05", "B"),
    ("80% 用 AI；信任从 40%→29%；66% 花更多时间修「几乎对」的代码", "Stack Overflow 2025 调查", "https://stackoverflow.blog/2025/12/29/developers-remain-willing-but-reluctant-to-use-ai-the-2025-developer-survey-results-are-here/", "2025-12", "A"),
    ("Zapier 各档价格、超额 2.5×、封顶 3×", "Zapier 官方 pricing.md", "https://zapier.com/pricing.md", "2026-11-04", "A"),
    ("Zapier Safely halted 不告警；Make Ignore 让失败项消失", "引 Zapier/Make 官方文档", "https://yehonatandev.com/blog/zapier-make-silent-failure-monitoring", "2026-09", "B"),
    ("Airbyte schema 变更导致静默失败 / 丢数", "GitHub Issues #78427 / #77627", "https://github.com/airbytehq/airbyte/issues/78427", "2026-04/05", "A"),
    ("npm 月下载：csv-parse 8,400 万 / papaparse 7,060 万 / xlsx 4,900 万 / json-2-csv 640 万", "npm API", "https://api.npmjs.org/downloads/point/last-month/csv-parse", "2026-11-03", "A"),
    ("n8n $25 亿估值（2025-10）；2026-05 SAP 投资后 $52 亿", "Bloomberg / SAP 公告", "https://www.bloomberg.com/news/articles/2025-10-09/ai-agent-startup-n8n-nets-2-5-billion-valuation-with-backing-from-nvidia", "2025-10", "B"),
    ("Zapier ARR ~$3.1 亿；$50 亿估值", "Sacra / Latka 估算", "https://sacra.com/c/zapier/", "2023–24", "C"),
    ("Relay.app 2026-09 关停", "Relay 官网公告", "https://relay.app/", "2026-09", "B"),
    ("MIT NANDA：95% 的 GenAI pilot 无可量化 P&L 影响", "MIT NANDA 报告（二手转引）", "https://nanda.media.mit.edu/", "2025", "B"),
    ("Numerous.ai ARR ≈ $55 万（5 人）", "GetLatka 估算", "https://getlatka.com/companies/numerous.ai", "2025-07", "C"),
    ("Formula Bot ARR $50 万–$100 万", "Startup Founder Stories / 播客", "https://startupfounderstories.com/stories/david-bressler-formulabot-20k", "2025", "C"),
    ("Zapier 单流程 $300–800、时薪 $40–90", "Upwork 成本指南（转引）", "https://joinpond.ai/blog/zapier-expert", "2026-10", "B"),
    ("Fivetran 年合约 list 价 $12,000 起", "Fivetran 定价 / 第三方汇总", "https://www.fivetran.com/pricing", "2026-11", "B"),
]
ws, hr, last = sheet(
    wb, "数据源",
    [46, 26, 62, 12, 6],
    ["事实", "来源", "URL", "日期", "等级"],
    S, wrap_cols=(1, 2, 3),
    note="A=已打开页面/接口读到原文；B=有署名的报道或官方文档转引；C=第三方估算。无法核验的已在正文标注 unknown。",
)
for row in range(hr + 1, last + 1):
    v = ws.cell(row=row, column=5).value
    ws.cell(row=row, column=5).fill = {"A": GOOD, "B": WARN, "C": BAD}.get(v, ZEBRA)
    ws.cell(row=row, column=5).alignment = Alignment(horizontal="center")

wb.save(OUT)
print("saved:", OUT)
print("size:", f"{OUT.stat().st_size:,}")
print("sheets:", wb.sheetnames)
