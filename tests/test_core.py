from pathlib import Path

from core.chunker import build_chunks, split_text
from core.llm import answer_question, fallback_answer
from core.models import SearchResult
from core.pdf_loader import load_pdf


ROOT = Path(__file__).resolve().parents[1]


def test_split_text_keeps_content_and_overlap():
    text = " ".join(f"kelime{i}" for i in range(80))
    chunks = split_text(text, chunk_size=100, overlap=20)
    assert len(chunks) > 1
    assert chunks[0].startswith("kelime0")
    assert "kelime79" in chunks[-1]
    assert set(chunks[0].split()) & set(chunks[1].split())


def test_build_chunks_contains_source_metadata():
    chunks = build_chunks(
        Path("ornek.pdf"), [(2, "Yemek masrafı üst limiti 250 TL'dir.")], chunk_size=120, overlap=10
    )
    assert len(chunks) == 1
    assert chunks[0].source == "ornek.pdf"
    assert chunks[0].page == 2
    assert chunks[0].as_metadata()["page"] == 2


def test_demo_pdfs_are_readable():
    pdfs = sorted((ROOT / "data" / "pdfs").glob("*.pdf"))
    assert len(pdfs) == 3
    pages = load_pdf(pdfs[0])
    assert pages
    assert any("yemek" in text.lower() for _, text in pages)


def test_fallback_answer_is_source_cited():
    source = SearchResult(
        chunk_id="x",
        text="Donanım arızasında IT Destek Portalı üzerinden kayıt açılmalıdır.",
        source="02_donanım_ve_it_destek.pdf",
        page=1,
        distance=0.1,
    )
    answer = fallback_answer("Donanım arızasında ne yapmalıyım?", [source])
    assert "IT Destek Portalı" in answer
    assert "02_donanım_ve_it_destek.pdf" in answer
    assert "s. 1" in answer


def test_answer_question_without_llm_is_transparent():
    source = SearchResult(
        chunk_id="x",
        text="Günlük yemek desteği üst limiti 250 TL'dir.",
        source="01_masraf_ve_yemek_politikasi.pdf",
        page=1,
        distance=0.1,
    )
    result = answer_question("Yemek limiti nedir?", [source], allow_llm=False)
    assert result.used_llm is False
    assert result.fallback_reason == "Yerel LLM kullanımı ayarlardan kapatıldı"
    assert "250 TL" in result.answer
