"""문서 → 텍스트. txt·md·csv·json·html·pdf(pypdf, BSD). 그 외는 거부한다(바이너리 오입력 방지)."""
import html
import io
import json
import re

TEXT_MIMES = ("text/plain", "text/markdown", "text/csv", "application/json", "text/html")
EXT = {".txt": "text/plain", ".md": "text/markdown", ".markdown": "text/markdown", ".csv": "text/csv",
       ".json": "application/json", ".html": "text/html", ".htm": "text/html", ".pdf": "application/pdf"}


class ExtractError(ValueError):
    pass


def mime_of(filename: str, declared: str | None) -> str:
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return EXT.get(ext) or (declared or "application/octet-stream").split(";")[0].strip()


def text_of(data: bytes, mime: str) -> str:
    if mime == "application/pdf":
        from pypdf import PdfReader
        from pypdf.errors import PdfReadError
        try:
            reader = PdfReader(io.BytesIO(data))
            return "\n\n".join((p.extract_text() or "") for p in reader.pages)
        except (PdfReadError, ValueError, KeyError) as exc:
            raise ExtractError(f"PDF 해석 실패 / unreadable PDF: {type(exc).__name__}") from None
    if mime not in TEXT_MIMES:
        raise ExtractError(f"지원하지 않는 형식 / unsupported type: {mime}")
    text = data.decode("utf-8", "replace")
    if mime == "text/html":
        text = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", text)
        text = html.unescape(re.sub(r"<[^>]+>", " ", text))
    if mime == "application/json":
        try:
            text = json.dumps(json.loads(text), ensure_ascii=False, indent=1)
        except ValueError:
            pass
    return text


def chunks(text: str, size: int = 800, overlap: int = 120) -> list[str]:
    """문단 경계를 우선하는 고정 길이 청크(겹침 포함). 빈 줄·공백만 있는 조각은 버린다."""
    text = re.sub(r"[ \t]+", " ", text.replace("\r\n", "\n")).strip()
    paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    out, buf = [], ""
    for p in paras:
        while len(p) > size:  # 아주 긴 문단은 자른다
            head, p = p[:size], p[size - overlap:]
            if buf:
                out.append(buf)
                buf = ""
            out.append(head)
        if len(buf) + len(p) + 2 <= size:
            buf = f"{buf}\n\n{p}" if buf else p
        else:
            if buf:
                out.append(buf)
            buf = (buf[-overlap:] + "\n\n" + p) if buf and overlap else p
    if buf:
        out.append(buf)
    return [c for c in out if c.strip()]
