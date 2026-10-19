"""尽调报告服务：数据装配 + PDF/Excel 生成

报告内容全部来自真实查询结果（MySQL/Neo4j 实时查询），每条数据带来源标注。
"""
import logging
from datetime import datetime
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy.orm import Session

from tyt.config import REPORT_DIR, RISK_TYPE_NAMES
from tyt.models import Company, ReportTask, RiskRecord
from tyt.services import company_service, risk_service, graph_service

logger = logging.getLogger(__name__)

# 中文字体：优先系统黑体，失败则降级（PDF 中文必需）
_FONT = None


def _register_font() -> str | None:
    global _FONT
    if _FONT is not None:
        return _FONT
    for name, path in [
        ("SimHei", "C:/Windows/Fonts/simhei.ttf"),
        ("MSYaHei", "C:/Windows/Fonts/msyh.ttc"),
        ("SimSun", "C:/Windows/Fonts/simsun.ttc"),
    ]:
        try:
            pdfmetrics.registerFont(TTFont(name, path))
            _FONT = name
            return name
        except Exception:
            continue
    _FONT = ""
    return None


def _ai_review(data: dict) -> str | None:
    """深度版专属：调用本地大模型生成综合研判段落（失败返回 None，不阻断报告生成）"""
    try:
        from tyt.services import ai_service
        c = data["company"]
        risks = data["risks"]
        dist = "、".join(
            f"{RISK_TYPE_NAMES.get(k, k)} {v} 条" for k, v in risks["counts"].items()
        ) or "无公开风险记录"
        top = [r["title"] for records in risks["by_type"].values() for r in records[:3]][:6]
        lines = [
            f"企业：{c['name']}（行业：{c.get('industry') or '未知'}，登记状态：{c.get('reg_status') or '未知'}）",
            f"注册资本：{c.get('reg_capital_wan') or '—'} 万元，成立日期：{c.get('founded_date') or '—'}",
            f"综合风险评分：{risks['risk_score']}/100；风险分布：{dist}",
        ]
        if top:
            lines.append("主要风险记录：" + "；".join(top))
        lines.append(
            f"股东 {len(data['shareholders'])} 名，对外投资 {len(data['investments'])} 家，"
            f"分支机构 {len(data.get('branches') or [])} 家，近年工商变更 {len(data.get('changes') or [])} 条"
        )
        prompt = (
            "你是企业尽调分析师。基于以下公开工商与风险数据，输出一段结构化尽调研判，"
            "按【风险态势】【重点关注】【尽调建议】三个要点分段，总共不超过200字，语言简练专业，"
            "不得编造数据中不存在的信息。\n\n" + "\n".join(lines)
        )
        review = ai_service.chat(prompt)
        return review.strip() if review and review.strip() else None
    except Exception as e:
        logger.warning("AI 综合研判生成失败，深度版报告跳过该段落: %s", e)
        return None


def assemble_report_data(db: Session, company_id: int) -> dict | None:
    """装配报告数据：工商 + 风险 + 股权 + 人员 + 投资 + 图谱摘要"""
    company = company_service.company_detail(db, company_id)
    if not company:
        return None
    risks = risk_service.get_company_risks(db, company_id)
    data = {
        "company": company,
        "risks": risks,
        "shareholders": company_service.get_shareholders(db, company_id),
        "personnel": company_service.get_personnel(db, company_id),
        "investments": company_service.get_investments(db, company_id),
        "branches": company_service.get_branches(db, company_id),
        "changes": company_service.get_changes(db, company_id, limit=20),
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    try:
        data["graph"] = graph_service.company_graph(company_id)
        data["controller"] = graph_service.actual_controller(company_id)
    except Exception as e:
        logger.warning("graph data unavailable in report: %s", e)
        data["graph"], data["controller"] = {"nodes": [], "edges": []}, {"controllers": []}
    return data


def generate_pdf(data: dict, out_path: Path, template: str = "standard") -> Path:
    font = _register_font()
    if font:
        styles = getSampleStyleSheet()
        h1 = ParagraphStyle("H1", parent=styles["Heading1"], fontName=font, fontSize=18)
        h2 = ParagraphStyle("H2", parent=styles["Heading2"], fontName=font, fontSize=13)
        normal = ParagraphStyle("N", parent=styles["Normal"], fontName=font, fontSize=10, leading=16)
    else:
        styles = getSampleStyleSheet()
        h1, h2, normal = styles["Heading1"], styles["Heading2"], styles["Normal"]

    doc = SimpleDocTemplate(
        str(out_path), pagesize=A4,
        leftMargin=16 * mm, rightMargin=16 * mm, topMargin=16 * mm, bottomMargin=16 * mm,
        title=f"天眼通尽调报告 - {data['company']['name']}",
    )
    story = []
    c = data["company"]

    story.append(Paragraph(
        "天眼通 · 企业尽调报告" + ("（深度版）" if template == "deep" else ""), h1))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        f"报告对象：{c['name']}　|　生成时间：{data['generated_at']}　|　"
        f"数据来源：{c.get('source') or '公开工商数据'}　|　采集时间：{c.get('collected_at') or '—'}",
        normal))
    story.append(Spacer(1, 10))

    story.append(Paragraph("一、工商基础信息", h2))
    rows = [
        ["统一社会信用代码", c.get("credit_code") or "—"],
        ["法定代表人", c.get("legal_person") or "—"],
        ["登记状态", c.get("reg_status") or "—"],
        ["注册资本（万元）", str(c.get("reg_capital_wan") or "—")],
        ["成立日期", c.get("founded_date") or "—"],
        ["企业类型", c.get("company_type") or "—"],
        ["所属行业", c.get("industry") or "—"],
        ["注册地址", c.get("address") or "—"],
        ["登记机关", c.get("reg_authority") or "—"],
        ["经营范围", (c.get("business_scope") or "—")[:200]],
    ]
    t = Table(rows, colWidths=[40 * mm, 130 * mm])
    t.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#eef2f7")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("FONTNAME", (0, 0), (-1, -1), font or "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
    ]))
    story.append(t)
    story.append(Spacer(1, 10))

    story.append(Paragraph("二、风险概览", h2))
    risk_rows = [["风险类型", "数量"]]
    for tkey, cnt in data["risks"]["counts"].items():
        risk_rows.append([RISK_TYPE_NAMES.get(tkey, tkey), str(cnt)])
    if len(risk_rows) == 1:
        risk_rows.append(["暂无公开风险记录", "0"])
    risk_rows.append(["综合风险评分", f"{data['risks']['risk_score']} / 100"])
    t = Table(risk_rows, colWidths=[60 * mm, 40 * mm])
    t.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eef2f7")),
        ("FONTNAME", (0, 0), (-1, -1), font or "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
    ]))
    story.append(t)

    risk_records = data["risks"].get("by_type", {})
    for tkey, records in risk_records.items():
        shown = records if template == "deep" else records[:8]
        story.append(Spacer(1, 6))
        story.append(Paragraph(f"{RISK_TYPE_NAMES.get(tkey, tkey)}明细（{len(records)}条）", normal))
        for r in shown:
            story.append(Paragraph(
                f"· {r['title']}（{r.get('occur_date') or '日期未知'}；来源：{r.get('source') or '公开渠道'}）", normal))

    story.append(Spacer(1, 10))
    story.append(Paragraph("三、股权结构", h2))
    sh_rows = [["股东", "类型", "持股比例", "认缴出资（万元）"]]
    for s in data["shareholders"]:
        sh_rows.append([s["holder_name"], "自然人" if s["holder_type"] == "person" else "机构",
                        f"{s['share_ratio']}%" if s.get("share_ratio") else "—",
                        str(s.get("subscribed_capital_wan") or "—")])
    t = Table(sh_rows, colWidths=[70 * mm, 22 * mm, 30 * mm, 40 * mm])
    t.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eef2f7")),
        ("FONTNAME", (0, 0), (-1, -1), font or "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
    ]))
    story.append(t)

    story.append(Spacer(1, 10))
    story.append(Paragraph("四、主要人员", h2))
    for p in data["personnel"]:
        story.append(Paragraph(f"· {p['name']}　{p['position'] or ''}", normal))

    story.append(Spacer(1, 10))
    story.append(Paragraph("五、对外投资（前 10）", h2))
    for i in data["investments"][:10]:
        story.append(Paragraph(
            f"· {i['investee_name']}　持股 {i['share_ratio'] or '—'}%　"
            f"投资 {i['invested_amount_wan'] or '—'} 万元", normal))

    ctrl = data.get("controller", {}).get("controllers") or []
    sec = 6
    if ctrl:
        story.append(Spacer(1, 10))
        story.append(Paragraph("六、股权穿透（疑似实际控制人）", h2))
        for cc in ctrl[:3]:
            story.append(Paragraph(
                f"· {cc['person']}　综合有效持股约 {cc['effective'] * 100:.2f}%", normal))
        sec = 7

    if template == "deep":
        cn = "零一二三四五六七八九十"
        changes = data.get("changes") or []
        story.append(Spacer(1, 10))
        story.append(Paragraph(f"{cn[sec]}、工商变更记录（近 {len(changes)} 条）", h2))
        if changes:
            for ch in changes[:20]:
                story.append(Paragraph(
                    f"· {ch.get('change_date') or '日期未知'}　{ch['change_type']}："
                    f"{ch.get('before_value') or '—'} → {ch.get('after_value') or '—'}", normal))
        else:
            story.append(Paragraph("暂无公开变更记录", normal))

        branches = data.get("branches") or []
        story.append(Spacer(1, 10))
        story.append(Paragraph(f"{cn[sec + 1]}、分支机构（{len(branches)} 家）", h2))
        if branches:
            for b in branches:
                story.append(Paragraph(
                    f"· {b['branch_name']}　{b.get('branch_status') or '—'}　"
                    f"负责人：{b.get('branch_person') or '—'}　{(b.get('province') or '') + (b.get('city') or '')}", normal))
        else:
            story.append(Paragraph("暂无分支机构记录", normal))

        review = _ai_review(data)
        story.append(Spacer(1, 10))
        story.append(Paragraph(f"{cn[sec + 2]}、AI 综合研判（本地大模型生成）", h2))
        if review:
            for para in review.splitlines():
                para = para.strip()
                if para:
                    story.append(Paragraph(para, normal))
        else:
            story.append(Paragraph("本节内容生成失败或暂不可用，请以上述公开数据为准。", normal))

    story.append(Spacer(1, 14))
    story.append(Paragraph(
        "合规声明：本报告数据均来自公开合法渠道（来源已逐条标注），仅供商业参考，"
        "不构成任何投资或交易建议；如与官方登记信息不一致，以官方公示为准。", normal))

    doc.build(story)
    return out_path


def generate_xlsx(data: dict, out_path: Path, template: str = "standard") -> Path:
    wb = Workbook()
    header_fill = PatternFill("solid", fgColor="1F3864")
    header_font = Font(color="FFFFFF", bold=True)

    ws = wb.active
    ws.title = "工商信息"
    ws.append(["字段", "值"])
    c = data["company"]
    for k, v in [
        ("企业名称", c["name"]), ("统一社会信用代码", c.get("credit_code")),
        ("法定代表人", c.get("legal_person")), ("登记状态", c.get("reg_status")),
        ("注册资本（万元）", c.get("reg_capital_wan")), ("成立日期", c.get("founded_date")),
        ("企业类型", c.get("company_type")), ("行业", c.get("industry")),
        ("注册地址", c.get("address")), ("登记机关", c.get("reg_authority")),
        ("经营范围", c.get("business_scope")),
        ("数据来源", c.get("source")), ("采集时间", c.get("collected_at")),
        ("报告生成时间", data["generated_at"]),
    ]:
        ws.append([k, v])
    for cell in ws[1]:
        cell.fill, cell.font = header_fill, header_font
    ws.column_dimensions["A"].width = 22
    ws.column_dimensions["B"].width = 70

    ws2 = wb.create_sheet("风险记录")
    ws2.append(["风险类型", "细分类型", "标题", "金额（万元）", "法院", "案号", "发生日期", "来源", "来源链接"])
    for tkey, records in data["risks"].get("by_type", {}).items():
        for r in records:
            ws2.append([RISK_TYPE_NAMES.get(tkey, tkey), r.get("risk_subtype"),
                        r["title"], r.get("amount_wan"), r.get("court"),
                        r.get("case_no"), r.get("occur_date"),
                        r.get("source"), r.get("source_url")])
    for cell in ws2[1]:
        cell.fill, cell.font = header_fill, header_font

    ws3 = wb.create_sheet("股东")
    ws3.append(["股东", "类型", "持股比例(%)", "认缴出资（万元）", "来源"])
    for s in data["shareholders"]:
        ws3.append([s["holder_name"], "自然人" if s["holder_type"] == "person" else "机构",
                    s.get("share_ratio"), s.get("subscribed_capital_wan"), s.get("source")])
    for cell in ws3[1]:
        cell.fill, cell.font = header_fill, header_font

    ws4 = wb.create_sheet("对外投资")
    ws4.append(["被投企业", "持股比例(%)", "投资金额（万元）", "状态", "来源"])
    for i in data["investments"]:
        ws4.append([i["investee_name"], i.get("share_ratio"), i.get("invested_amount_wan"),
                    i.get("investee_reg_status"), i.get("source")])
    for cell in ws4[1]:
        cell.fill, cell.font = header_fill, header_font

    ws5 = wb.create_sheet("主要人员")
    ws5.append(["姓名", "职位", "是否法定代表人"])
    for p in data["personnel"]:
        ws5.append([p["name"], p.get("position"), "是" if p.get("is_legal_person") else "否"])
    for cell in ws5[1]:
        cell.fill, cell.font = header_fill, header_font

    if template == "deep":
        ws6 = wb.create_sheet("变更记录")
        ws6.append(["变更日期", "变更类型", "变更前", "变更后", "来源"])
        for ch in data.get("changes") or []:
            ws6.append([ch.get("change_date"), ch.get("change_type"),
                        ch.get("before_value"), ch.get("after_value"), ch.get("source")])
        for cell in ws6[1]:
            cell.fill, cell.font = header_fill, header_font

        ws7 = wb.create_sheet("分支机构")
        ws7.append(["分支机构", "状态", "负责人", "省份", "城市"])
        for b in data.get("branches") or []:
            ws7.append([b.get("branch_name"), b.get("branch_status"),
                        b.get("branch_person"), b.get("province"), b.get("city")])
        for cell in ws7[1]:
            cell.fill, cell.font = header_fill, header_font

    wb.save(out_path)
    return out_path


def build_report_files(task_id: int, company_id: int, template: str = "standard") -> tuple[Path, Path]:
    """同步生成 PDF + Excel（Celery 任务与同步模式共用）"""
    from tyt.db.mysql import SessionLocal
    db = SessionLocal()
    try:
        data = assemble_report_data(db, company_id)
        if not data:
            raise RuntimeError(f"company {company_id} not found")
        out_dir = Path(REPORT_DIR)
        out_dir.mkdir(parents=True, exist_ok=True)
        pdf_path = out_dir / f"report_{task_id}_{company_id}.pdf"
        xlsx_path = out_dir / f"report_{task_id}_{company_id}.xlsx"
        generate_pdf(data, pdf_path, template)
        generate_xlsx(data, xlsx_path, template)
        return pdf_path, xlsx_path
    finally:
        db.close()
