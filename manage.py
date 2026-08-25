"""Onboarding asistanı komut satırı aracı.

Örnekler:
    python cli.py index --clear
    python cli.py status
    python cli.py ask "Yemek masraf limiti ne kadar?" --no-llm
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.config import ensure_directories  # noqa: E402
from core.rag_pipeline import OnboardingRAG  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Microsoft Stajyer Onboarding Asistanı")
    subparsers = parser.add_subparsers(dest="command", required=True)

    index_parser = subparsers.add_parser("index", help="PDF klasörünü indeksle")
    index_parser.add_argument("--clear", action="store_true", help="Mevcut indeksi sil")

    subparsers.add_parser("status", help="Sistem durumunu göster")

    ask_parser = subparsers.add_parser("ask", help="Dokümanlara soru sor")
    ask_parser.add_argument("question", help="Sorulacak soru")
    ask_parser.add_argument("--no-llm", action="store_true", help="Sadece kaynaklı fallback kullan")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    ensure_directories()
    rag = OnboardingRAG()

    if args.command == "index":
        print(json.dumps(rag.index_documents(clear_existing=args.clear), ensure_ascii=False, indent=2))
        return 0
    if args.command == "status":
        print(json.dumps(rag.status(), ensure_ascii=False, indent=2))
        return 0
    if args.command == "ask":
        response = rag.ask(args.question, allow_llm=not args.no_llm)
        print(response.answer)
        if response.sources:
            print("\nKaynaklar:")
            for source in response.sources:
                page = f"s. {source.page}" if source.page else ""
                print(f"- {source.source} {page}")
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
