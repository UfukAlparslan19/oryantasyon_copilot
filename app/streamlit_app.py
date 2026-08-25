"""Oryantasyon Copilot Streamlit arayüzü."""
from __future__ import annotations

import sys
import os
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.config import ensure_directories, settings  # noqa: E402
from core.rag_pipeline import OnboardingRAG  # noqa: E402
from core.analytics import AnalyticsLogger
from core.pdf_viewer import PDFViewer

st.set_page_config(
    page_title="Oryantasyon Copilot",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Koyu Renk, Premium Dark Glassmorphism CSS
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');
    
    :root { 
        --brand: #2b88d8; 
        --brand-glow: rgba(43, 136, 216, 0.5);
        --ink: #e2e8f0; 
        --muted: #94a3b8; 
        --surface: rgba(15, 23, 42, 0.6);
        --glass-border: rgba(255, 255, 255, 0.08);
    }
    
    /* Global App Background */
    .stApp {
        background: radial-gradient(circle at 15% 50%, #1e1b4b, #0f172a 40%, #020617 100%);
        font-family: 'Inter', sans-serif;
        color: var(--ink);
    }
    
    /* Hide some default Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {background-color: transparent !important;}

    .block-container { max-width: 1000px; padding-top: 1rem; }
    
    /* Hero Section (Welcome) */
    .hero { 
        padding: 3rem 4rem; 
        border-radius: 24px; 
        background: var(--surface); 
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid var(--glass-border); 
        box-shadow: 0 10px 40px rgba(0, 0, 0, 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.1);
        margin-bottom: 2.5rem; 
        text-align: center;
        animation: fadeIn 1s ease-out;
    }
    .hero h1 { 
        margin: 0 0 .5rem 0; 
        font-size: 3.2rem; 
        font-weight: 600;
        background: linear-gradient(to right, #38bdf8, #818cf8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: 0 2px 20px rgba(56, 189, 248, 0.2);
    }
    .hero p { color: #cbd5e1; font-size: 1.2rem; margin: 0; font-weight: 300; }
    
    /* Glass Cards for sources */
    .source-card { 
        background: rgba(30, 41, 59, 0.7); 
        backdrop-filter: blur(8px);
        border-left: 4px solid var(--brand); 
        border-radius: 12px;
        padding: 1rem 1.2rem; 
        margin: .8rem 0; 
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        transition: all 0.3s ease;
        border-top: 1px solid var(--glass-border);
        border-right: 1px solid var(--glass-border);
        border-bottom: 1px solid var(--glass-border);
    }
    .source-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.4), 0 0 15px var(--brand-glow);
        border-color: rgba(43, 136, 216, 0.3);
    }
    .source-card b { color: #f8fafc; font-weight: 500; font-size: 1.05rem; }
    .small-muted { color: var(--muted); font-size: .9rem; line-height: 1.4; display: block; margin-top: 4px; }
    
    /* Privacy Badge */
    .privacy { 
        color: #34d399; 
        background: rgba(6, 78, 59, 0.4); 
        backdrop-filter: blur(4px);
        border: 1px solid rgba(52, 211, 153, 0.2); 
        padding: .85rem 1rem; 
        border-radius: 12px; 
        font-size: .95rem; 
        display: flex;
        align-items: center;
        gap: 8px;
        margin-top: 10px;
    }
    
    /* Custom Chat bubbles */
    .stChatMessage {
        background-color: rgba(15, 23, 42, 0.6) !important;
        backdrop-filter: blur(12px);
        border-radius: 20px !important;
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
        box-shadow: 0 8px 24px rgba(0,0,0,0.2);
        padding: 1.5rem !important;
        margin-bottom: 1.5rem !important;
    }
    
    /* Animations */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_resource(show_spinner=False)
def get_pipeline() -> OnboardingRAG:
    ensure_directories()
    return OnboardingRAG(settings)

@st.cache_resource(show_spinner=False)
def get_analytics() -> AnalyticsLogger:
    ensure_directories()
    return AnalyticsLogger(settings.data_dir / "analytics.db")

@st.cache_resource(show_spinner=False)
def get_pdf_viewer() -> PDFViewer:
    ensure_directories()
    return PDFViewer(settings.pdf_dir)

pipeline = get_pipeline()
analytics = get_analytics()
pdf_viewer = get_pdf_viewer()

with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/4/44/Microsoft_logo.svg", width=120)
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Yeni Analitik Paneli
    st.title("📊 İK Analitik Paneli")
    stats = analytics.get_stats()
    col1, col2 = st.columns(2)
    col1.metric("Toplam Soru", stats["total_queries"])
    col2.metric("YZ Yanıtlı", stats["llm_answered"])
    
    st.divider()
    
    st.title("⚙️ Sistem Kontrolü")
    status = pipeline.status()
    st.caption(f"**İndekslenmiş Parça:** {status['indexed_chunks']}")
    st.caption(f"**Embedding:** {status['embedding_backend']}")
    st.caption(f"**LLM Model:** {status['ollama_model']}")

    st.divider()
    st.subheader("📄 Yeni Belge Yükle")
    st.write("Sisteme yeni bir PDF politikası veya rehber ekleyin.")
    uploaded_file = st.file_uploader("PDF Seç", type=["pdf"], label_visibility="collapsed")
    if uploaded_file is not None:
        if st.button("Belgeyi İndeksle", type="primary", use_container_width=True):
            with st.spinner("Belge kaydediliyor ve vektör uzayına ekleniyor..."):
                save_path = settings.pdf_dir / uploaded_file.name
                with open(save_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                # Sadece yeni dosyayı ekle (mevcutları silme)
                result = pipeline.index_documents(clear_existing=False)
            
            if "messages" not in st.session_state:
                st.session_state.messages = []
                
            st.session_state.messages.append({
                "role": "assistant",
                "content": f"📁 **{uploaded_file.name}** başarıyla sisteme yüklendi ve öğrenildi! Artık bu belgedeki konular hakkında sorular sorabilirsiniz."
            })
            st.rerun()
            
    st.divider()
    if st.button("Tüm İndeksi Sıfırla (Temizle)", use_container_width=True):
        with st.spinner("İndeks sıfırlanıyor..."):
            pipeline.index_documents(clear_existing=True)
        st.success("İndeks temizlendi ve baştan oluşturuldu.")
        st.rerun()

    st.divider()
    use_llm = st.toggle(
        "Ollama LLM Aktif",
        value=True,
        help="Kapalıysa yalnızca PDF'lerden özet (extractive) yanıt döndürür.",
    )
    st.markdown(
        '<div class="privacy">🔒 <b>Gizlilik:</b> PDF verileri yerel ortamda kalır. '
        'İnternete sızdırılmaz.</div>',
        unsafe_allow_html=True,
    )

if "messages" not in st.session_state:
    st.session_state.messages = []

# Welcome Screen (Sadece mesaj yoksa göster)
if not st.session_state.messages:
    st.markdown(
        """
        <div class="hero">
          <h1>Oryantasyon Copilot ✨</h1>
          <p>Şirket içi uzman yapay zekanız. Kurum politikaları, İK kuralları ve destek süreçlerini anında öğrenin.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    st.markdown("### 💡 Hazır Sorular")
    cols = st.columns(3)
    if cols[0].button("🍽️ Yemek masraf limiti ne kadar?", use_container_width=True):
        st.session_state.temp_prompt = "Yemek masraf limiti ne kadar?"
        st.rerun()
    if cols[1].button("💻 Donanım arızasında ne yapmalıyım?", use_container_width=True):
        st.session_state.temp_prompt = "Donanım arızasında ne yapmalıyım?"
        st.rerun()
    if cols[2].button("🔐 Cihazım çalınırsa kime haber vermeliyim?", use_container_width=True):
        st.session_state.temp_prompt = "Cihazım çalınırsa kime haber vermeliyim?"
        st.rerun()

# Handle predefined prompt clicks
prompt = st.chat_input("Oryantasyon hakkında merak ettiklerinizi sorun...")

if "temp_prompt" in st.session_state and st.session_state.temp_prompt:
    prompt = st.session_state.temp_prompt
    st.session_state.temp_prompt = None

for message in st.session_state.messages:
    avatar = "✨" if message["role"] == "assistant" else "👤"
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])
        if message.get("sources"):
            with st.expander("📄 Kaynak Belgeleri İncele", expanded=False):
                for source in message["sources"]:
                    page = f"s. {source['page']}" if source.get("page") else ""
                    st.markdown(
                        f'<div class="source-card"><b>{source["source"]} {page}</b>'
                        f'<br><span class="small-muted">{source["text"]}</span></div>',
                        unsafe_allow_html=True,
                    )
                    # Resim daha önce oluşturulmuşsa göster
                    if source.get("image_rendered"):
                        st.image(source["image_rendered"], use_container_width=True)

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)
        
    with st.chat_message("assistant", avatar="✨"):
        # Hafıza (Memory) içeriğini modele gönderiyoruz (son eklenen kullanıcı sorusu hariç)
        chat_history = st.session_state.messages[:-1]
        
        response = pipeline.ask(prompt, allow_llm=use_llm, chat_history=chat_history)
        
        # Analitiğe kaydet
        analytics.log_query(prompt, response.used_llm, len(response.sources))
        
        # Streaming Daktilo Efekti
        if response.used_llm:
            full_response = st.write_stream(response.answer)
        else:
            full_response = response.answer
            st.markdown(full_response)
        
        source_payload = []
        if response.fallback_reason:
            st.caption(f"⚠️ Bilgi: {response.fallback_reason}. Yalnızca PDF parçaları gösteriliyor.")
            
        if response.sources:
            with st.expander("📄 Kaynak Belgeleri İncele", expanded=True):
                for source in response.sources:
                    page = f"s. {source.page}" if source.page else ""
                    st.markdown(
                        f'<div class="source-card"><b>{source.source} {page}</b>'
                        f'<br><span class="small-muted">{source.text}</span></div>',
                        unsafe_allow_html=True,
                    )
                    
                    img_data = None
                    if source.page:
                        img = pdf_viewer.get_page_image(source.source, source.page)
                        if img:
                            st.image(img, caption=f"{source.source} - Sayfa {source.page}", use_container_width=True)
                            # Resmi session_state'de sakla ki sayfa yenilenince kaybolmasın
                            img_data = img

                    source_payload.append(
                        {
                            "source": source.source, 
                            "page": source.page, 
                            "text": source.text,
                            "image_rendered": img_data
                        }
                    )
                    
    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": full_response,
            "sources": source_payload,
        }
    )
