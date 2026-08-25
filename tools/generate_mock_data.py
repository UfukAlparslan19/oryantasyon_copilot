"""Demo onboarding PDF'lerini üretir."""
from __future__ import annotations

import os
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT / "data" / "pdfs"

# Windows ve Linux uyumlu fontlar
FONT_CANDIDATES = [
    "C:/Windows/Fonts/arial.ttf",
    "C:/Windows/Fonts/segoeui.ttf",
    "C:/Windows/Fonts/calibri.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
]
BOLD_CANDIDATES = [
    "C:/Windows/Fonts/arialbd.ttf",
    "C:/Windows/Fonts/segoeuib.ttf",
    "C:/Windows/Fonts/calibrib.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]

def choose_font(candidates: list[str]) -> str:
    for candidate in candidates:
        if Path(candidate).exists():
            return candidate
    return None

MOCK_DOCUMENTS = [
    {
        "filename": "Microsoft_Global_Yemek_ve_Harcama_Politikasi_2024.pdf",
        "title": "Microsoft Yemek ve Masraf Politikası",
        "content": [
            "# Microsoft Yemek ve Harcama Politikası",
            "Bu doküman tüm Microsoft stajyerleri ve tam zamanlı çalışanları için geçerlidir.",
            "## 1. Günlük Yemek Limiti",
            "Günlük yemek masrafı limiti 450 TL olarak güncellenmiştir. Bu limiti aşan harcamalar kişisel bütçeden karşılanır.",
            "## 2. Masraf Girişi",
            "Harcamalarınızı MS Expense portalı üzerinden fiş/fatura görseli ekleyerek yapmalısınız. Onay süreci 3 iş günü sürer."
        ]
    },
    {
        "filename": "IT_Donanim_ve_Aksesuar_Rehberi_v3.pdf",
        "title": "BT Donanım ve Arıza Rehberi",
        "content": [
            "# BT Donanım ve Arıza Rehberi",
            "Microsoft bünyesinde kullandığınız cihazların yönetimi IT departmanına aittir.",
            "## 1. Donanım Arızası",
            "Cihazınız bozulursa, IT_Support@microsoft.local adresine bir bilet açmanız gerekmektedir. Yeni cihaz tahsisi maksimum 2 gün sürer.",
            "## 2. Ekipman Talebi",
            "Klavye, mouse veya ikinci monitör taleplerinizi yöneticinizin onayı ile portal üzerinden yapabilirsiniz."
        ]
    },
    {
        "filename": "Guvenlik_ve_Veri_Koruma_Yonergesi.pdf",
        "title": "Güvenlik ve Veri Koruma Yönergesi",
        "content": [
            "# Güvenlik ve Veri Koruma Yönergesi",
            "Veri gizliliği Microsoft'un en önemli önceliğidir.",
            "## 1. Cihaz Çalınması veya Kaybolması",
            "Cihazınız çalınırsa veya kaybolursa **DERHAL** (en geç 1 saat içinde) Güvenlik Operasyonları (SecOps) ekibine 444-SEC numarasından haber vermelisiniz.",
            "## 2. Şifre Politikası",
            "Şifreler 90 günde bir değiştirilmeli ve en az 14 karakter olmalıdır."
        ]
    },
    {
        "filename": "Stajyer_Ilk_Gun_Oryantasyon_Plani.pdf",
        "title": "Stajyer İlk Gün Oryantasyon Planı",
        "content": [
            "# Stajyer İlk Gün Oryantasyon Planı",
            "Aramıza hoş geldiniz! İlk gününüzde tamamlamanız gereken adımlar şunlardır:",
            "## Sabah (09:00 - 12:00)",
            "Lobiye kayıt, yaka kartının alınması ve cihaz teslimi. Ardından mentor ile ilk tanışma toplantısı.",
            "## Öğleden Sonra (13:30 - 17:00)",
            "Gerekli yazılımların (Visual Studio, Teams vb.) kurulması ve MS Learn üzerinden zorunlu siber güvenlik eğitiminin tamamlanması."
        ]
    },
    {
        "filename": "Uzaktan_Calisma_ve_Esnek_Mesai_Sartlari.pdf",
        "title": "Uzaktan Çalışma ve Esnek Mesai",
        "content": [
            "# Uzaktan Çalışma ve Esnek Mesai Şartları",
            "Microsoft hibrid çalışma modelini benimser.",
            "## 1. Ofise Katılım",
            "Haftanın en az 3 günü ofisten çalışma beklenmektedir. Kalan günler uzaktan çalışılabilir.",
            "## 2. Çekirdek Saatler",
            "Ekiplerin ortak senkronizasyonu için saat 10:00 ile 15:00 arası çekirdek mesai saatleridir. Toplantılar genellikle bu saatlere planlanır."
        ]
    },
    {
        "filename": "Performans_Degerlendirme_ve_Geri_Bildirim.pdf",
        "title": "Performans Değerlendirme Sistemi",
        "content": [
            "# Performans Değerlendirme Sistemi",
            "## 1. Hedef Belirleme",
            "Stajınızın ilk haftasında mentorunuz ile birlikte 3 aylık hedeflerinizi (OKR) belirlemeniz beklenir.",
            "## 2. Connect Görüşmeleri",
            "Yöneticiniz ile her ay düzenli 1:1 (birebir) Connect görüşmeleri yaparak gidişatı değerlendirebilirsiniz."
        ]
    },
    {
        "filename": "Izin_ve_Tatil_Haklari_2024.pdf",
        "title": "İzin ve Tatil Hakları",
        "content": [
            "# İzin ve Tatil Hakları 2024",
            "## Yıllık İzin",
            "Stajyerler program süresince toplam 5 gün mazeret izni kullanma hakkına sahiptir. İzinler Workday sistemi üzerinden yöneticinin onayına sunulur.",
            "## Resmi Tatiller",
            "Resmi ve dini bayramlar Microsoft takviminde tatil olarak kabul edilir."
        ]
    },
    {
        "filename": "Ofis_ici_Kurallar_ve_Rehber.pdf",
        "title": "Ofis İçi Kurallar ve Tesis Kullanımı",
        "content": [
            "# Ofis İçi Kurallar",
            "## 1. Toplantı Odaları",
            "Toplantı odaları Outlook üzerinden rezerve edilmelidir. 15 dakika boyunca kullanılmayan odaların rezervasyonu iptal olur.",
            "## 2. Kafeterya ve İçecekler",
            "Kat mutfaklarındaki atıştırmalıklar ve içecekler tüm çalışanlar için ücretsizdir."
        ]
    },
    {
        "filename": "Yazilim_Gelistirme_Standartlari.pdf",
        "title": "Yazılım Geliştirme Standartları",
        "content": [
            "# Yazılım Geliştirme Standartları",
            "## Kod İnceleme (Code Review)",
            "Main branch'e yapılan tüm Pull Request (PR) süreçlerinde en az 2 Senior geliştiricinin onayı zorunludur.",
            "## Güvenlik Taraması",
            "Credential Leak (Kimlik bilgisi sızıntısı) önlemek için tüm commitler otomatik CredScan aracından geçer."
        ]
    },
    {
        "filename": "Kariyer_Gelisim_ve_MS_Learn.pdf",
        "title": "Kariyer Gelişim Eğitimleri",
        "content": [
            "# Kariyer Gelişim ve Eğitim",
            "## MS Learn Portalı",
            "Çalışanlar, MS Learn üzerinden istedikleri sertifika sınavlarına ücretsiz olarak katılabilir.",
            "## Mentorluk Programı",
            "Dileyen her stajyer, kendi takımı dışından bir lider ile mentorluk süreci başlatabilir."
        ]
    }
]

def markdown_to_story(lines: list[str]) -> list[object]:
    styles = getSampleStyleSheet()
    body = ParagraphStyle(
        "BodyTR", parent=styles["BodyText"], fontName="DemoSans", fontSize=11,
        leading=16, spaceAfter=8, textColor="#333333",
    )
    h1 = ParagraphStyle(
        "H1TR", parent=body, fontName="DemoSansBold", fontSize=22,
        leading=26, spaceAfter=16, textColor="#0078d4",
    )
    h2 = ParagraphStyle(
        "H2TR", parent=body, fontName="DemoSansBold", fontSize=14,
        leading=18, spaceBefore=10, spaceAfter=8, textColor="#111111",
    )
    story: list[object] = []
    for line in lines:
        line = line.strip()
        if not line:
            story.append(Spacer(1, 3 * mm))
            continue
        if line.startswith("# "):
            story.append(Paragraph(line[2:], h1))
        elif line.startswith("## "):
            story.append(Paragraph(line[3:], h2))
        else:
            story.append(Paragraph(line, body))
    return story

def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    font_path = choose_font(FONT_CANDIDATES)
    bold_path = choose_font(BOLD_CANDIDATES)
    
    if font_path and bold_path:
        pdfmetrics.registerFont(TTFont("DemoSans", font_path))
        pdfmetrics.registerFont(TTFont("DemoSansBold", bold_path))
    else:
        # Fallback to standard Helvetica if Windows fonts not found
        import reportlab.rl_config
        reportlab.rl_config.warnOnMissingFontGlyphs = 0
        from reportlab.pdfbase import _fontdata
        pdfmetrics.registerFont(TTFont("DemoSans", _fontdata.standardFonts[0]))
        pdfmetrics.registerFont(TTFont("DemoSansBold", _fontdata.standardFonts[0]))
        print("Uyarı: Türkçe font bulunamadı, varsayılan font kullanılıyor.")
        
    for doc_info in MOCK_DOCUMENTS:
        output = OUTPUT_DIR / doc_info["filename"]
        document = SimpleDocTemplate(
            str(output), pagesize=A4, rightMargin=20 * mm, leftMargin=20 * mm,
            topMargin=20 * mm, bottomMargin=20 * mm, title=doc_info["title"],
            author="Oryantasyon Copilot Sistemi",
        )
        document.build(markdown_to_story(doc_info["content"]))
        print(f"Oluşturuldu: {output.name}")

if __name__ == "__main__":
    main()
