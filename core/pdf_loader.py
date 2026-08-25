"""PDF metin çıkarma yardımcıları."""
from __future__ import annotations

from pathlib import Path
from typing import Iterator

from pypdf import PdfReader


def _clean_extracted_text(text: str) -> str:
    """Üretim sırasında eklenen tekrar eden altbilgiyi metin indeksinden çıkarır."""
    kept: list[str] = []
    for line in text.splitlines():
        normalized = " ".join(line.split())
        if "Microsoft Stajyer Onboarding Asistanı" in normalized and "Demo doküman" in normalized:
            continue
        if normalized.lower().startswith("sayfa ") and normalized[6:].strip().isdigit():
            continue
        kept.append(line)
    return "\n".join(kept).strip()


class PDFLoadError(RuntimeError):
    """PDF okunamadığında yükseltilen hata."""


def iter_pdf_pages(pdf_path: Path) -> Iterator[tuple[int, str]]:
    """PDF içindeki metinleri 1-tabanlı sayfa numarasıyla döndürür."""
    try:
        reader = PdfReader(str(pdf_path))
    except Exception as exc:  # pragma: no cover - pypdf'in özel hata tipleri sürüme bağlıdır
        raise PDFLoadError(f"PDF açılamadı: {pdf_path.name}") from exc

    for page_number, page in enumerate(reader.pages, start=1):
        try:
            text = _clean_extracted_text(page.extract_text() or "")
        except Exception as exc:  # pragma: no cover
            raise PDFLoadError(
                f"PDF sayfası okunamadı: {pdf_path.name} / sayfa {page_number}"
            ) from exc
        if text:
            yield page_number, text


def load_pdf(pdf_path: Path) -> list[tuple[int, str]]:
    """Tek bir PDF'in boş olmayan sayfalarını listeler."""
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF bulunamadı: {pdf_path}")
    if pdf_path.suffix.lower() != ".pdf":
        raise ValueError(f"Beklenen dosya uzantısı .pdf, alınan: {pdf_path.suffix}")
    return list(iter_pdf_pages(pdf_path))
