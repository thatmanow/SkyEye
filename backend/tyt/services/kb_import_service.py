"""知识库文档导入：解析常见格式文本 -> 语义切分 -> 作为手动知识入库

支持格式（均利用运行环境已装库，无需额外依赖）：
  .txt/.md/.csv/.json/.text -> 直接解码（utf-8/gbk 容错）
  .docx                     -> python-docx
  .pdf                      -> pypdf
  .xlsx/.xls                -> openpyxl
  .html/.htm                -> beautifulsoup4

解析出的纯文本按段落/句子切分为若干片段，每段作为一条 kind=manual 知识入库，
与「手动录入」同等保留，不参与每日爬虫清理（每日一清只清 people_article/baostock_quote）。
"""
import hashlib
import logging
import re
from io import BytesIO
from pathlib import Path

from tyt.services import ai_service

logger = logging.getLogger(__name__)

SUPPORTED = {
    ".txt": "纯文本", ".md": "Markdown", ".markdown": "Markdown",
    ".csv": "CSV", ".json": "JSON", ".text": "纯文本",
    ".docx": "Word 文档", ".pdf": "PDF 文档",
    ".xlsx": "Excel 表格", ".xls": "Excel 表格",
    ".html": "HTML 网页", ".htm": "HTML 网页",
}
MAX_BYTES = 20 * 1024 * 1024
DEFAULT_CHUNK = 700
DEFAULT_OVERLAP = 80


def extract_text(filename: str, data: bytes) -> str:
    """按扩展名提取文档纯文本；不支持的格式抛 ValueError（提示支持列表）"""
    ext = Path(filename or "").suffix.lower()
    if ext not in SUPPORTED:
        raise ValueError(
            f"不支持的文件格式：{ext or '无扩展名'}，支持：{', '.join(sorted(SUPPORTED))}")
    if ext in (".txt", ".md", ".markdown", ".csv", ".json", ".text"):
        return _decode_text(data)
    if ext == ".docx":
        return _extract_docx(data)
    if ext == ".pdf":
        return _extract_pdf(data)
    if ext in (".xlsx", ".xls"):
        return _extract_xlsx(data)
    if ext in (".html", ".htm"):
        return _extract_html(data)
    raise ValueError(f"暂不支持的格式：{ext}")


def _decode_text(data: bytes) -> str:
    for enc in ("utf-8", "gbk", "utf-8-sig", "latin-1"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="ignore")


def _extract_docx(data: bytes) -> str:
    try:
        from docx import Document
    except ImportError:
        raise ValueError("服务端未安装 python-docx，无法解析 docx")
    doc = Document(BytesIO(data))
    parts = [p.text for p in doc.paragraphs if p.text and p.text.strip()]
    for table in doc.tables:
        for row in table.rows:
            cells = [c.text.strip() for c in row.cells if c.text and c.text.strip()]
            if cells:
                parts.append(" | ".join(cells))
    return "\n".join(parts)


def _extract_pdf(data: bytes) -> str:
    try:
        from pypdf import PdfReader
    except ImportError:
        raise ValueError("服务端未安装 pypdf，无法解析 PDF")
    try:
        reader = PdfReader(BytesIO(data))
    except Exception as e:
        raise ValueError(f"PDF 解析失败（可能已加密或损坏）：{e}")
    pages = []
    for page in reader.pages:
        t = page.extract_text() or ""
        if t.strip():
            pages.append(t)
    return "\n".join(pages)


def _extract_xlsx(data: bytes) -> str:
    try:
        from openpyxl import load_workbook
    except ImportError:
        raise ValueError("服务端未安装 openpyxl，无法解析 Excel")
    wb = load_workbook(BytesIO(data), read_only=True, data_only=True)
    rows = []
    for ws in wb.worksheets:
        for r in ws.iter_rows(values_only=True):
            cells = [str(c).strip() for c in r if c is not None and str(c).strip()]
            if cells:
                rows.append(" | ".join(cells))
    return "\n".join(rows)


def _extract_html(data: bytes) -> str:
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        raise ValueError("服务端未安装 beautifulsoup4，无法解析 HTML")
    html = _decode_text(data)
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style"]):
        tag.decompose()
    return soup.get_text(separator="\n")


def _clean_text(text: str) -> str:
    text = text.replace("　", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def chunk_text(text: str, chunk_size: int = DEFAULT_CHUNK,
               overlap: int = DEFAULT_OVERLAP) -> list[str]:
    """按段落优先、超长段落按句切分；保持片段语义完整"""
    text = _clean_text(text)
    if not text:
        return []
    paras = [p.strip() for p in re.split(r"\n+", text) if p.strip()]
    chunks: list[str] = []
    buf = ""
    for p in paras:
        if len(buf) + len(p) + 1 <= chunk_size:
            buf = (buf + "\n" + p).strip() if buf else p
            continue
        if buf:
            chunks.append(buf)
            buf = ""
        if len(p) > chunk_size:
            chunks.extend(_split_sentences(p, chunk_size, overlap))
        else:
            buf = p
    if buf:
        chunks.append(buf)
    return [c for c in chunks if c.strip()]


def _split_sentences(text: str, chunk_size: int, overlap: int) -> list[str]:
    sentences = re.split(r"(?<=[。！？!?；;\n])", text)
    sentences = [s.strip() for s in sentences if s and s.strip()]
    chunks, buf = [], ""
    for s in sentences:
        if len(buf) + len(s) + 1 <= chunk_size:
            buf = (buf + s).strip() if buf else s
        else:
            if buf:
                chunks.append(buf)
            if len(s) > chunk_size:
                step = max(1, chunk_size - overlap)
                for i in range(0, len(s), step):
                    chunks.append(s[i:i + chunk_size])
                buf = ""
            else:
                buf = s
    if buf:
        chunks.append(buf)
    return chunks


def _auto_title(hint: str | None, text: str, filename: str) -> str:
    if hint and hint.strip():
        return hint.strip()[:120]
    for line in text.splitlines():
        line = line.strip()
        if 2 <= len(line) <= 120 and not line.startswith(("#", "*", "-", "|", "=", "、")):
            return line
    return Path(filename).stem[:120] or "导入文档"


def import_document(filename: str, data: bytes, title_hint: str | None = None,
                    chunk_size: int = DEFAULT_CHUNK, overlap: int = DEFAULT_OVERLAP) -> dict:
    """解析文档 -> 切分 -> 逐片段以 manual 知识入库；返回统计（imported/title/chunks 等）"""
    raw = extract_text(filename, data)
    text = _clean_text(raw)
    if not text:
        return {"imported": 0, "title": None, "total_chars": 0, "chunks": 0,
                "filename": Path(filename).name, "message": "未能提取到有效文本"}
    title = _auto_title(title_hint, text, filename)
    chunks = chunk_text(text, chunk_size, overlap)
    imported = 0
    doc_ids: list[str] = []
    name = Path(filename).name
    for i, c in enumerate(chunks):
        chunk_title = title if i == 0 else f"{title}（第{i + 1}段）"
        meta = {
            "kind": "manual",
            "title": chunk_title[:120],
            "source": f"文档导入 · {name}",
            "doc_name": name,
            "chunk": i + 1,
            "chunk_total": len(chunks),
        }
        h = hashlib.md5(f"{filename}:{i}:{c}".encode("utf-8")).hexdigest()[:16]
        doc_id = f"manual:doc:{h}"
        if ai_service.upsert_knowledge(doc_id, c, meta):
            imported += 1
            doc_ids.append(doc_id)
    logger.info("文档导入知识库：%s 切分 %d 段，成功入库 %d 条", name, len(chunks), imported)
    return {
        "imported": imported,
        "title": title,
        "total_chars": len(text),
        "chunks": len(chunks),
        "filename": name,
        "doc_ids": doc_ids,
    }
