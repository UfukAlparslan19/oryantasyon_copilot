"""Ollama yerel LLM istemcisi ve kontrollü cevap üretimi."""
from __future__ import annotations

import re
import json
from typing import Any

import requests

from .config import Settings, settings
from .models import AssistantAnswer, SearchResult


SYSTEM_PROMPT = """Sen Microsoft Stajyer Onboarding Asistanısın.

Yalnızca verilen şirket dokümanı parçalarındaki bilgilere dayanarak yanıt ver.
Dokümanlarda bulunmayan bir bilgiyi tahmin etme veya uydurma. Yanıtın Türkçe,
net ve eyleme dönük olsun. Gerekiyorsa adımları numaralandır. Her önemli
iddianın sonunda [Kaynak: dosya adı, s. X] biçiminde kaynak göster.
Dokümanlarda yeterli bilgi yoksa şu ifadeyi kullan: 'Bu bilgi onboarding
dokümanlarında bulunmuyor; mentorunuza veya ilgili ekip kanalına danışın.'
"""


class OllamaClient:
    """Ollama /api/chat uç noktasına bağlanan küçük istemci."""

    def __init__(self, app_settings: Settings = settings) -> None:
        self.settings = app_settings
        self.base_url = self.settings.ollama_base_url.rstrip("/")

    def is_available(self) -> bool:
        try:
            response = requests.get(
                f"{self.base_url}/api/tags", timeout=min(self.settings.request_timeout, 3)
            )
            return response.ok
        except requests.RequestException:
            return False

    def generate(self, question: str, context: str, chat_history: list[dict[str, str]] = None) -> Any:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        
        if chat_history:
            # Hafıza (Memory): Sadece son 4 etkileşimi (2 soru, 2 cevap) al
            for msg in chat_history[-4:]:
                if msg["role"] in ["user", "assistant"]:
                    messages.append({"role": msg["role"], "content": msg["content"]})
                    
        messages.append({
            "role": "user",
            "content": (
                f"DOKÜMAN PARÇALARI:\n{context}\n\n"
                f"SORU:\n{question}\n\nYalnızca bu parçalara dayanarak yanıtla."
            ),
        })
        
        payload: dict[str, Any] = {
            "model": self.settings.ollama_model,
            "stream": True,  # Streaming (Daktilo Efekti) Aktif
            "options": {"temperature": 0.1, "num_ctx": 4096},
            "messages": messages,
        }
        try:
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                stream=True,
                timeout=self.settings.request_timeout,
            )
            response.raise_for_status()
            
            def stream_generator():
                for line in response.iter_lines():
                    if line:
                        data = json.loads(line)
                        chunk = data.get("message", {}).get("content", "")
                        if chunk:
                            yield chunk
                            
            return stream_generator()
        except requests.RequestException as exc:
            raise RuntimeError(
                f"Ollama bağlantısı kurulamadı ({self.base_url})."
            ) from exc


def format_context(results: list[SearchResult]) -> str:
    """Retrieved parçaları modele ve fallback cevaba gönderilecek biçime getirir."""
    blocks: list[str] = []
    for index, result in enumerate(results, start=1):
        page = f"s. {result.page}" if result.page else "sayfa bilgisi yok"
        blocks.append(
            f"[{index}] Kaynak: {result.source}, {page}\n"
            f"İçerik: {result.text}"
        )
    return "\n\n".join(blocks)


def _sentence_match_score(question: str, sentence: str) -> float:
    question_terms = set(re.findall(r"[\wçğıöşüÇĞİÖŞÜ]+", question.lower()))
    sentence_terms = set(re.findall(r"[\wçğıöşüÇĞİÖŞÜ]+", sentence.lower()))
    if not question_terms or not sentence_terms:
        return 0.0
    return len(question_terms & sentence_terms) / len(question_terms)


def _clean_sentence(sentence: str) -> str:
    sentence = sentence.strip()
    if "Bu belge yalnızca" in sentence:
        return ""
    if sentence.startswith("Demo Kurum"):
        return ""
    return sentence


def fallback_sources(question: str, results: list[SearchResult]) -> list[SearchResult]:
    """Fallback cevabında yalnızca ilgili ve tekil kaynakları döndürür."""
    scored: list[tuple[float, float, SearchResult]] = []
    for result in results:
        sentences = [_clean_sentence(item) for item in re.split(r"(?<=[.!?])\s+", result.text)]
        sentences = [item for item in sentences if item]
        score = max((_sentence_match_score(question, item) for item in sentences), default=0.0)
        scored.append((score, result.relevance, result))
    scored.sort(key=lambda item: (item[0], item[1]), reverse=True)
    relevant = [item[2] for item in scored if item[0] > 0]
    candidates = relevant or [item[2] for item in scored[:1]]
    unique: list[SearchResult] = []
    seen: set[str] = set()
    for result in candidates:
        if result.chunk_id not in seen:
            unique.append(result)
            seen.add(result.chunk_id)
        if len(unique) == 3:
            break
    return unique


def fallback_answer(question: str, results: list[SearchResult]) -> str:
    """Ollama kurulmamışsa retrieved bağlamdan şeffaf, extractive yanıt üretir."""
    if not results:
        return (
            "Bu bilgi onboarding dokümanlarında bulunmuyor; mentorunuza veya "
            "ilgili ekip kanalına danışın."
        )

    candidates: list[tuple[float, str, SearchResult]] = []
    for result in fallback_sources(question, results):
        for sentence in re.split(r"(?<=[.!?])\s+", result.text):
            sentence = _clean_sentence(sentence)
            if sentence:
                candidates.append((_sentence_match_score(question, sentence), sentence, result))
    candidates.sort(key=lambda item: (item[0], item[2].relevance), reverse=True)
    selected = [item for item in candidates[:3] if item[0] > 0]
    if not selected:
        selected = [(0.0, results[0].text, results[0])]

    lines = ["Yerel LLM kullanılmadığı için dokümanlardan çıkarılan bilgi:"]
    for _, sentence, result in selected:
        page = f", s. {result.page}" if result.page else ""
        lines.append(f"- {sentence} [Kaynak: {result.source}{page}]")
    return "\n".join(lines)


def answer_question(
    question: str,
    results: list[SearchResult],
    client: OllamaClient | None = None,
    *,
    allow_llm: bool = True,
    chat_history: list[dict[str, str]] = None,
) -> AssistantAnswer:
    """Soruyu cevaplar; model erişimini ve fallback nedenini açıkça bildirir."""
    if not results:
        return AssistantAnswer(
            answer=fallback_answer(question, results), sources=[], used_llm=False
        )

    client = client or OllamaClient()
    context = format_context(results)
    if allow_llm:
        try:
            if client.is_available():
                return AssistantAnswer(
                    answer=client.generate(question, context, chat_history=chat_history),
                    sources=results,
                    used_llm=True,
                )
            reason = "Ollama çalışmıyor veya erişilebilir değil"
        except RuntimeError as exc:
            reason = str(exc)
    else:
        reason = "Yerel LLM kullanımı ayarlardan kapatıldı"

    return AssistantAnswer(
        answer=fallback_answer(question, results),
        sources=fallback_sources(question, results),
        used_llm=False,
        fallback_reason=reason,
    )
