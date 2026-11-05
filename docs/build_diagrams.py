# -*- coding: utf-8 -*-
"""
FlowTable 项目流程图生成器。

一张脚本 → 四种输出：
  *.png     直接看 / 贴进文档
  *.svg     矢量，可打印
  *.drawio  draw.io 可直接拖拽编辑
  *.mmd     GitHub / Notion 直接渲染

改图只改这里的 SPEC，别去手改产物。
用法：python docs/build_diagrams.py
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from pathlib import Path
from xml.sax.saxutils import escape as xml_escape

from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parent
SCALE = 2

FONT_BOLD = "C:/Windows/Fonts/msyhbd.ttc"
FONT_REG = "C:/Windows/Fonts/msyh.ttc"

PALETTE = {
    "client": ("#EEF4FF", "#C7D7FB", "#1E3A8A"),
    "edge":   ("#ECFDF5", "#A7F3D0", "#065F46"),
    "data":   ("#FFF7ED", "#FED7AA", "#9A3412"),
    "ext":    ("#F5F3FF", "#DDD6FE", "#5B21B6"),
    "money":  ("#FDF2F8", "#FBCFE8", "#9D174D"),
    "note":   ("#F8FAFC", "#E2E8F0", "#334155"),
}


@dataclass
class Node:
    id: str
    x: float
    y: float
    w: float
    h: float
    title: str
    subs: list[str] = field(default_factory=list)
    kind: str = "client"


@dataclass
class Edge:
    a: str
    b: str
    sa: str = "right"
    sb: str = "left"
    label: str = ""
    dashed: bool = False
    # 手工指定拐点，用来绕开中间的方块；不给就走默认的正交路由
    via: tuple[tuple[float, float], ...] = ()
    # 标签位置（默认放在最长线段中点）
    label_at: tuple[float, float] | None = None


@dataclass
class Diagram:
    slug: str
    title: str
    subtitle: str
    width: int
    height: int
    nodes: list[Node]
    edges: list[Edge]
    lanes: list[tuple[float, float, str]] = field(default_factory=list)
    legend: list[tuple[str, str]] = field(default_factory=list)


# --------------------------------------------------------------------------
# 布局
# --------------------------------------------------------------------------
def box(nid, x, y, w, h, title, subs=None, kind="client"):
    return Node(nid, x, y, w, h, title, subs or [], kind)


def d1() -> Diagram:
    nodes = [
        # ① 客户端
        box("web_tools", 24, 78, 232, 66, "免费工具页", ["Astro 静态 · /tools/*", "SEO 长尾入口，文件不上传"], "client"),
        box("web_app", 24, 160, 232, 66, "应用界面", ["管道列表 / 运行日志", "逐格 diff + 撤销"], "client"),
        box("engine_wasm", 24, 242, 232, 66, "浏览器清洗引擎", ["同一份 core，跑在 WASM", "5MB 内免费不限次"], "client"),
        box("chrome_ext", 24, 324, 232, 66, "Chrome 扩展（可选）", ["从当前页面抓表", "只做漏斗，不做收银台"], "note"),

        # ② Edge Worker
        box("api", 330, 78, 250, 66, "API 路由 /api/*", ["Bearer 鉴权 · CORS", "建管道 / 手动跑 / 查运行"], "edge"),
        box("cron", 330, 160, 250, 60, "Cron 调度器", ["每日 06:00 / 每小时（Pro）"], "edge"),
        box("runner", 330, 236, 250, 92, "管道执行器", ["fetch → transform → validate", "→ snapshot → alert", "失败/异常都留日志"], "edge"),
        box("alerts", 330, 344, 250, 60, "告警器", ["行数 ±20% / 运行失败"], "edge"),
        box("billing", 330, 420, 250, 60, "计费 webhook", ["Creem 验签 → 订阅状态"], "money"),

        # ③ 存储
        box("d1", 664, 78, 226, 92, "D1 元数据", ["workspace / pipeline / rules", "runs / subscriptions", "不存原始数据"], "data"),
        box("r2", 664, 186, 226, 66, "R2 快照", ["最新一次结果 + meta", "7 天自动过期"], "data"),
        box("hosted", 664, 268, 226, 66, "托管表页 /t/:token", ["只读页面 + CSV 下载"], "data"),

        # ④ 外部
        box("sources", 940, 78, 268, 92, "数据源 API", ["任意 REST / JSON（分页 / 鉴权）", "Shopify · Stripe 预置"], "ext"),
        box("creem", 940, 186, 268, 60, "Creem（MoR）", ["3.9% + $0.40 · 代缴 VAT"], "money"),
        box("dest", 940, 268, 268, 66, "客户的表", ["Google Sheets / Excel", "IMPORTDATA 或直接下 CSV"], "ext"),
        box("resend", 940, 344, 268, 60, "Resend", ["告警与周报邮件"], "ext"),
    ]
    edges = [
        Edge("web_tools", "api"),
        Edge("web_app", "api", via=((292, 193), (292, 111)), label="建管道"),
        Edge("api", "d1"),
        Edge("cron", "runner", "bottom", "top"),
        Edge("runner", "sources", via=((620, 282), (620, 260), (914, 260), (914, 124)),
             label="拉数", label_at=(760, 260)),
        Edge("runner", "d1", via=((620, 282), (620, 111))),
        Edge("runner", "r2", via=((620, 282), (620, 219))),
        Edge("runner", "hosted", via=((620, 282), (620, 301))),
        Edge("alerts", "resend"),
        Edge("hosted", "dest", label="IMPORTDATA"),
        Edge("creem", "billing", "left", "right", via=((906, 216), (906, 450)), dashed=True),
    ]
    return Diagram(
        "01-architecture",
        "系统架构：一条管道怎么跑完",
        "前端（Astro / 浏览器 WASM）· 后端（Cloudflare Worker + Cron）· 存储（D1 / R2）· 外部（数据源 / 收款 / 邮件）",
        1240, 520, nodes, edges,
        lanes=[(16, 248, "① 客户端"), (322, 266, "② Edge Worker"), (656, 242, "③ 存储"), (932, 284, "④ 外部服务")],
        legend=[("client", "前端"), ("edge", "后端"), ("data", "存储"), ("ext", "外部"), ("money", "计费")],
    )


def d2() -> Diagram:
    nodes = [
        box("search", 20, 90, 190, 64, "搜索长尾词", ["clean csv online", "fix csv encoding"], "note"),
        box("landing", 246, 90, 190, 64, "工具落地页", ["一个词 = 一个页面", "无注册即可用"], "client"),
        box("tool", 472, 90, 190, 64, "免费清洗", ["浏览器内，不上传", "逐格 diff 建立信任"], "client"),
        box("paywall", 698, 90, 190, 64, "付费触发点", ["第 3 次上传 / 想保存规则", "想每天自动跑"], "money"),
        box("signup", 924, 90, 200, 64, "注册（邮箱）", ["Free 1 条管道", "手动跑"], "client"),

        box("build", 924, 250, 200, 64, "建管道", ["选源 → 选规则 → 选目标", "TTFV 目标 < 10 分钟"], "client"),
        box("firstrun", 698, 250, 190, 64, "首次运行", ["真实数据跑通", "看到 before/after"], "edge"),
        box("daily", 472, 250, 190, 64, "每日自动刷新", ["托管表 + CSV", "行数历史"], "edge"),
        box("alert", 246, 250, 190, 64, "行数异常告警", ["±20% 或归零", "邮件先于老板"], "edge"),
        box("upgrade", 20, 250, 190, 64, "升级 Pro", ["$19 → $49", "按管道数计价"], "money"),

        box("outreach", 20, 400, 190, 64, "社区外联", ["40 条不带链接的私信"], "note"),
        box("concierge", 246, 400, 190, 64, "手工交付", ["$49 一次性清表", "72 小时收到第一笔钱"], "money"),
        box("convert", 472, 400, 190, 64, "转订阅", ["规则固化 → $19/月", "从服务变成产品"], "money"),
    ]
    edges = [
        Edge("search", "landing"),
        Edge("landing", "tool"),
        Edge("tool", "paywall"),
        Edge("paywall", "signup"),
        Edge("signup", "build", "bottom", "top"),
        Edge("build", "firstrun", "left", "right"),
        Edge("firstrun", "daily", "left", "right"),
        Edge("daily", "alert", "left", "right"),
        Edge("alert", "upgrade", "left", "right"),
        Edge("outreach", "concierge"),
        Edge("concierge", "convert"),
        Edge("concierge", "build", "top", "bottom", dashed=True, label="同一批人"),
    ]
    return Diagram(
        "02-user-journey",
        "用户旅程与变现：从一次搜索到一笔订阅",
        "上排 = 自助路径（SEO → 免费工具 → 付费墙）· 中排 = 激活与留存 · 下排 = 手工交付这条更快的现金流",
        1150, 500, nodes, edges,
        lanes=[(12, 1130, "")],
        legend=[("client", "用户动作"), ("edge", "系统动作"), ("money", "收钱点"), ("note", "获客")],
    )


def d3() -> Diagram:
    nodes = [
        box("local", 20, 96, 200, 70, "本地开发", ["pnpm dev / dev:api", "node 直接跑 TS 测试"], "client"),
        box("push", 250, 96, 180, 70, "git push", ["feature 分支"], "note"),
        box("preview", 460, 96, 210, 70, "Cloudflare Pages 构建", ["预览 URL（每个 PR 一个）", "静态产物 apps/web/dist"], "edge"),
        box("review", 700, 96, 180, 70, "冒烟检查", ["工具页能跑", "/api/health 通"], "note"),
        box("prod", 910, 96, 210, 70, "合并 main → 生产", ["Pages 自动部署", "域名 + 缓存刷新"], "edge"),

        box("wdeploy", 910, 236, 210, 70, "Worker 部署", ["wrangler deploy", "绑定 D1 / R2"], "edge"),
        box("migrate", 700, 236, 180, 70, "D1 迁移", ["schema.sql 幂等", "先备份再执行"], "data"),
        box("cron_on", 460, 236, 210, 70, "Cron 生效", ["每日 06:00 跑全量", "每小时跑 Pro"], "edge"),
        box("watch", 250, 236, 180, 70, "监控与告警", ["运行失败 / 行数异常", "自检 job"], "data"),
        box("rollback", 20, 236, 200, 70, "回滚", ["Pages：回退部署", "Worker：wrangler rollback"], "money"),

        box("deliver", 20, 376, 200, 70, "交付给客户", ["托管表 + CSV", "邮件告警"], "ext"),
        box("support", 250, 376, 180, 70, "支持与迭代", ["邮件支持", "按流失原因改产品"], "note"),
    ]
    edges = [
        Edge("local", "push"),
        Edge("push", "preview"),
        Edge("preview", "review"),
        Edge("review", "prod"),
        Edge("prod", "wdeploy", "bottom", "top"),
        Edge("wdeploy", "migrate", "left", "right"),
        Edge("migrate", "cron_on", "left", "right"),
        Edge("cron_on", "watch", "left", "right"),
        Edge("watch", "rollback", "left", "right", dashed=True),
        Edge("watch", "deliver", "bottom", "top", label="健康"),
        Edge("deliver", "support", "right", "left"),
    ]
    return Diagram(
        "03-release",
        "发布与运维：从一次 commit 到客户看到新数据",
        "静态站走 Pages，后端走 Workers；迁移幂等、先备份；任何一步失败都有明确回滚动作",
        1150, 480, nodes, edges,
        lanes=[(12, 1130, "")],
        legend=[("client", "本地"), ("edge", "CI / 运行时"), ("data", "数据"), ("note", "检查点")],
    )


DIAGRAMS = [d1(), d2(), d3()]


# --------------------------------------------------------------------------
# 几何
# --------------------------------------------------------------------------
def anchor(n: Node, side: str) -> tuple[float, float]:
    return {
        "left": (n.x, n.y + n.h / 2),
        "right": (n.x + n.w, n.y + n.h / 2),
        "top": (n.x + n.w / 2, n.y),
        "bottom": (n.x + n.w / 2, n.y + n.h),
    }[side]


def route(a: Node, b: Node, sa: str, sb: str, via: tuple[tuple[float, float], ...] = ()) -> list[tuple[float, float]]:
    p1 = anchor(a, sa)
    p2 = anchor(b, sb)
    if via:
        return [p1, *via, p2]
    if sa in ("left", "right") and sb in ("left", "right"):
        mid = (p1[0] + p2[0]) / 2
        return [p1, (mid, p1[1]), (mid, p2[1]), p2]
    if sa in ("top", "bottom") and sb in ("top", "bottom"):
        mid = (p1[1] + p2[1]) / 2
        return [p1, (p1[0], mid), (p2[0], mid), p2]
    if sa in ("left", "right"):
        return [p1, (p2[0], p1[1]), p2]
    return [p1, (p1[0], p2[1]), p2]


def label_point(pts: list[tuple[float, float]], at: tuple[float, float] | None) -> tuple[float, float]:
    if at:
        return at
    best, best_len = (pts[0], pts[1]), -1.0
    for i in range(len(pts) - 1):
        seg = math.dist(pts[i], pts[i + 1])
        if seg > best_len:
            best_len, best = seg, (pts[i], pts[i + 1])
    return ((best[0][0] + best[1][0]) / 2, (best[0][1] + best[1][1]) / 2)


def arrow_head(p_prev, p_tip, size=7):
    ang = math.atan2(p_tip[1] - p_prev[1], p_tip[0] - p_prev[0])
    a = (p_tip[0] - size * math.cos(ang - math.pi / 7), p_tip[1] - size * math.sin(ang - math.pi / 7))
    b = (p_tip[0] - size * math.cos(ang + math.pi / 7), p_tip[1] - size * math.sin(ang + math.pi / 7))
    return [p_tip, a, b]


# --------------------------------------------------------------------------
# PNG
# --------------------------------------------------------------------------
def render_png(d: Diagram) -> Path:
    W, H = d.width * SCALE, d.height * SCALE
    img = Image.new("RGB", (W, H), "#FFFFFF")
    dr = ImageDraw.Draw(img)

    f_title = ImageFont.truetype(FONT_BOLD, 13 * SCALE)
    f_title_s = ImageFont.truetype(FONT_BOLD, 11 * SCALE)
    f_sub = ImageFont.truetype(FONT_REG, 10 * SCALE)
    f_lane = ImageFont.truetype(FONT_BOLD, 10 * SCALE)
    f_head = ImageFont.truetype(FONT_BOLD, 19 * SCALE)
    f_desc = ImageFont.truetype(FONT_REG, 11 * SCALE)

    def S(v):
        return int(round(v * SCALE))

    by_id = {n.id: n for n in d.nodes}

    # 标题
    dr.text((S(20), S(18)), d.title, font=f_head, fill="#0F172A")
    dr.text((S(20), S(46)), d.subtitle, font=f_desc, fill="#64748B")

    # 车道
    for x, w, label in d.lanes:
        if not label:
            continue
        dr.rounded_rectangle([S(x), S(70), S(x + w), S(d.height - 16)], radius=S(12),
                             fill="#FBFCFE", outline="#EDF1F6", width=S(1))
        dr.text((S(x + 12), S(76)), label, font=f_lane, fill="#7C8798")

    # 先画线：让方块盖住穿过的部分，视觉上就"绕过去"了
    paths = {}
    for e in d.edges:
        pts = route(by_id[e.a], by_id[e.b], e.sa, e.sb, e.via)
        paths[id(e)] = pts
        for i in range(len(pts) - 1):
            x1, y1 = pts[i]
            x2, y2 = pts[i + 1]
            if e.dashed:
                dist = math.hypot(x2 - x1, y2 - y1)
                if dist == 0:
                    continue
                steps = max(1, int(dist / 8))
                for k in range(steps):
                    if k % 2:
                        continue
                    t0, t1 = k / steps, (k + 0.9) / steps
                    dr.line([S(x1 + (x2 - x1) * t0), S(y1 + (y2 - y1) * t0),
                             S(x1 + (x2 - x1) * t1), S(y1 + (y2 - y1) * t1)],
                            fill="#94A3B8", width=S(1.4))
            else:
                dr.line([S(x1), S(y1), S(x2), S(y2)], fill="#94A3B8", width=S(1.4))

    # 节点
    for n in d.nodes:
        fill, stroke, ink = PALETTE[n.kind]
        dr.rounded_rectangle([S(n.x), S(n.y), S(n.x + n.w), S(n.y + n.h)], radius=S(10),
                             fill=fill, outline=stroke, width=S(1.6))
        font = f_title if dr.textlength(n.title, font=f_title) / SCALE <= n.w - 20 else f_title_s
        dr.text((S(n.x + 12), S(n.y + 11)), n.title, font=font, fill=ink)
        for i, line in enumerate(n.subs[:3]):
            dr.text((S(n.x + 12), S(n.y + 32 + i * 14)), line, font=f_sub, fill="#5A6675")

    # 箭头画在方块之上
    for e in d.edges:
        pts = paths[id(e)]
        dr.polygon([(S(p[0]), S(p[1])) for p in arrow_head(pts[-2], pts[-1])], fill="#94A3B8")

    # 标签
    for e in d.edges:
        if not e.label:
            continue
        mx, my = label_point(paths[id(e)], e.label_at)
        lw = dr.textlength(e.label, font=f_sub) / SCALE
        bx, by = mx - lw / 2 - 4, my - 8
        dr.rectangle([S(bx), S(by), S(bx + lw + 8), S(by + 15)], fill="#FFFFFF")
        dr.text((S(bx + 4), S(by + 1)), e.label, font=f_sub, fill="#64748B")

    # 图例
    if d.legend:
        lx, ly = 22, d.height - 30
        for kind, name in d.legend:
            fill, stroke, _ = PALETTE[kind]
            dr.rounded_rectangle([S(lx), S(ly), S(lx + 12), S(ly + 12)], radius=S(3),
                                 fill=fill, outline=stroke, width=S(1))
            dr.text((S(lx + 17), S(ly - 1)), name, font=f_sub, fill="#64748B")
            lx += 17 + dr.textlength(name, font=f_sub) / SCALE + 16

    path = OUT / f"{d.slug}.png"
    img.save(path, optimize=True)
    return path


# --------------------------------------------------------------------------
# SVG
# --------------------------------------------------------------------------
def render_svg(d: Diagram) -> Path:
    by_id = {n.id: n for n in d.nodes}
    head = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{d.width}" height="{d.height}" '
        f'viewBox="0 0 {d.width} {d.height}" font-family="-apple-system,Segoe UI,Microsoft YaHei,sans-serif">',
        f'<rect width="{d.width}" height="{d.height}" fill="#fff"/>',
        f'<text x="20" y="30" font-size="19" font-weight="700" fill="#0F172A">{xml_escape(d.title)}</text>',
        f'<text x="20" y="52" font-size="11" fill="#64748B">{xml_escape(d.subtitle)}</text>',
    ]
    for x, w, label in d.lanes:
        if not label:
            continue
        head.append(
            f'<rect x="{x}" y="70" width="{w}" height="{d.height - 86}" rx="12" fill="#FBFCFE" stroke="#EDF1F6"/>'
        )
        head.append(f'<text x="{x + 12}" y="82" font-size="10" font-weight="700" fill="#7C8798">{xml_escape(label)}</text>')

    lines, arrows, boxes, labels = [], [], [], []
    for e in d.edges:
        pts = route(by_id[e.a], by_id[e.b], e.sa, e.sb, e.via)
        dash = ' stroke-dasharray="5 4"' if e.dashed else ""
        poly = " ".join(f"{p[0]:.1f},{p[1]:.1f}" for p in pts)
        lines.append(f'<polyline points="{poly}" fill="none" stroke="#94A3B8" stroke-width="1.4"{dash}/>')
        tri = arrow_head(pts[-2], pts[-1])
        arrows.append('<polygon points="' + " ".join(f"{p[0]:.1f},{p[1]:.1f}" for p in tri) + '" fill="#94A3B8"/>')
        if e.label:
            mx, my = label_point(pts, e.label_at)
            labels.append(
                f'<text x="{mx:.1f}" y="{my + 3:.1f}" font-size="10" fill="#64748B" text-anchor="middle" '
                f'paint-order="stroke" stroke="#fff" stroke-width="4">{xml_escape(e.label)}</text>'
            )

    for n in d.nodes:
        fill, stroke, ink = PALETTE[n.kind]
        boxes.append(
            f'<rect x="{n.x}" y="{n.y}" width="{n.w}" height="{n.h}" rx="10" fill="{fill}" stroke="{stroke}" stroke-width="1.6"/>'
        )
        boxes.append(
            f'<text x="{n.x + 12}" y="{n.y + 24}" font-size="13" font-weight="700" fill="{ink}">{xml_escape(n.title)}</text>'
        )
        for i, line in enumerate(n.subs[:3]):
            boxes.append(
                f'<text x="{n.x + 12}" y="{n.y + 43 + i * 14}" font-size="10" fill="#5A6675">{xml_escape(line)}</text>'
            )

    legend = []
    lx = 22
    for kind, name in d.legend:
        fill, stroke, _ = PALETTE[kind]
        legend.append(f'<rect x="{lx}" y="{d.height - 30}" width="12" height="12" rx="3" fill="{fill}" stroke="{stroke}"/>')
        legend.append(f'<text x="{lx + 17}" y="{d.height - 20}" font-size="10" fill="#64748B">{xml_escape(name)}</text>')
        lx += 17 + len(name) * 10 + 16

    parts = head + lines + boxes + arrows + labels + legend + ["</svg>"]
    path = OUT / f"{d.slug}.svg"
    path.write_text("\n".join(parts), encoding="utf-8")
    return path


# --------------------------------------------------------------------------
# drawio
# --------------------------------------------------------------------------
def render_drawio(d: Diagram) -> Path:
    cells = []
    for n in d.nodes:
        fill, stroke, ink = PALETTE[n.kind]
        label = "<b>" + n.title + "</b>" + ("<br>" + "<br>".join(n.subs) if n.subs else "")
        style = (
            f"rounded=1;whiteSpace=wrap;html=1;arcSize=12;fillColor={fill};"
            f"strokeColor={stroke};fontColor={ink};align=left;verticalAlign=top;"
            f"spacingLeft=8;spacingTop=4;fontSize=11;"
        )
        cells.append(
            f'<mxCell id="{n.id}" value="{xml_escape(label)}" style="{style}" vertex="1" parent="1">'
            f'<mxGeometry x="{n.x}" y="{n.y}" width="{n.w}" height="{n.h}" as="geometry"/></mxCell>'
        )
    for i, e in enumerate(d.edges):
        style = "edgeStyle=orthogonalEdgeStyle;rounded=1;html=1;strokeColor=#94A3B8;endArrow=block;endSize=6;"
        if e.dashed:
            style += "dashed=1;"
        label = xml_escape(e.label) if e.label else ""
        cells.append(
            f'<mxCell id="e{i}" value="{label}" style="{style}" edge="1" parent="1" '
            f'source="{e.a}" target="{e.b}"><mxGeometry relative="1" as="geometry"/></mxCell>'
        )
    xml = (
        '<mxfile host="flowtable" version="24.0.0">'
        f'<diagram id="{d.slug}" name="{xml_escape(d.title)}">'
        '<mxGraphModel dx="1200" dy="800" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" '
        'arrows="1" fold="1" page="1" pageScale="1" math="0" shadow="0">'
        "<root><mxCell id=\"0\"/><mxCell id=\"1\" parent=\"0\"/>"
        + "".join(cells)
        + "</root></mxGraphModel></diagram></mxfile>"
    )
    path = OUT / f"{d.slug}.drawio"
    path.write_text(xml, encoding="utf-8")
    return path


# --------------------------------------------------------------------------
# mermaid（手写：自动生成的布局不如人脑排的）
# --------------------------------------------------------------------------
MERMAID = {
"01-architecture": """flowchart LR
  subgraph C["① 客户端"]
    direction TB
    A1["免费工具页<br/><small>Astro 静态 · SEO</small>"]
    A2["应用界面<br/><small>管道 / 日志 / diff</small>"]
    A3["浏览器清洗引擎<br/><small>WASM · 不上传</small>"]
    A4["Chrome 扩展（可选）<br/><small>只做漏斗</small>"]
  end
  subgraph E["② Edge Worker"]
    direction TB
    B1["API /api/*<br/><small>Bearer 鉴权</small>"]
    B2["Cron 调度"]
    B3["管道执行器<br/><small>fetch → transform → validate</small>"]
    B4["告警器<br/><small>行数 ±20%</small>"]
    B5["计费 webhook<br/><small>Creem 验签</small>"]
  end
  subgraph D["③ 存储"]
    direction TB
    C1[("D1<br/><small>元数据 / 规则 / 运行记录</small>")]
    C2[("R2<br/><small>快照 · 7 天</small>")]
    C3["托管表页<br/><small>/t/:token</small>"]
  end
  subgraph X["④ 外部"]
    direction TB
    X1["数据源 API<br/><small>REST / Shopify / Stripe</small>"]
    X2["Creem<br/><small>MoR · 代缴税</small>"]
    X3["客户的表<br/><small>Sheets / Excel</small>"]
    X4["Resend<br/><small>邮件</small>"]
  end
  A1 --> B1
  A2 -->|建管道| B1
  B1 --> C1
  B2 --> B3
  B3 -->|拉数| X1
  B3 --> C1
  B3 --> C2
  B3 --> C3
  B4 --> X4
  X2 -.->|webhook| B5
  C3 -->|IMPORTDATA| X3
""",
"02-user-journey": """flowchart LR
  subgraph ACQ["获客"]
    direction LR
    S["搜索长尾词"] --> L["工具落地页"] --> T["免费清洗"] --> P["付费触发点"] --> R["注册"]
  end
  subgraph ACT["激活与留存"]
    direction RL
    B["建管道"] --> F["首次运行"] --> DA["每日自动刷新"] --> AL["行数异常告警"] --> U["升级 Pro"]
  end
  subgraph SVC["服务化收款（更快）"]
    direction LR
    O["社区外联"] --> CC["手工交付 $49"] --> CV["转订阅 $19/月"]
  end
  R --> B
  CC -.->|同一批人| B
""",
"03-release": """flowchart LR
  subgraph DEV["本地"]
    A["pnpm dev"] --> B["git push"]
  end
  subgraph CI["Cloudflare Pages"]
    C["预览构建<br/><small>每个 PR 一个 URL</small>"] --> D["冒烟检查"]
  end
  subgraph PROD["生产"]
    E["合并 main → Pages"] --> F["wrangler deploy<br/>Worker"]
    F --> G["D1 迁移<br/><small>幂等 · 先备份</small>"]
    G --> H["Cron 生效"]
  end
  subgraph OPS["运维"]
    I["监控 / 自检"] --> J["回滚<br/><small>Pages 回退 / wrangler rollback</small>"]
    K["交付客户<br/><small>托管表 + CSV + 告警</small>"]
  end
  B --> C
  D --> E
  H --> I
  I -->|健康| K
""",
}


def render_mermaid(d: Diagram) -> Path:
    path = OUT / f"{d.slug}.mmd"
    path.write_text(MERMAID[d.slug].strip() + "\n", encoding="utf-8")
    return path


# --------------------------------------------------------------------------
def main() -> None:
    made = []
    for d in DIAGRAMS:
        made += [render_png(d), render_svg(d), render_drawio(d), render_mermaid(d)]
    for p in made:
        print(f"{p.name:28s} {p.stat().st_size:>8,} bytes")


if __name__ == "__main__":
    main()
