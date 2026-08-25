# Staj Sunumu için Demo Akışı

## 1. Problem cümlesi

“Yeni başlayan stajyerler, şirket içinde hangi belgenin nerede olduğunu bilmediği için mentorlarına tekrar tekrar aynı operasyonel soruları soruyor. Bu proje, kurum içi onboarding belgelerinde doğal dille arama yapan ve cevabın kaynağını gösteren yerel bir asistan sunuyor.”

## 2. Gizlilik cümlesi

“İK ve şirket içi yönergeler gizli olabilir. Bu nedenle PDF’ler yerel okunuyor, embedding’ler yerel üretiliyor ve ChromaDB yerel diskte tutuluyor. Ollama aktifse model de aynı makinede çalışıyor; harici bir sohbet servisine belge gönderilmiyor.”

## 3. Canlı demo sırası

Önce sol panelde indekslenmiş parça sayısını gösterin. Ardından şu soruyu sorun:

> Yemek masraf limiti ne kadar?

Cevapta **250 TL** bilgisini ve `01_masraf_ve_yemek_politikasi.pdf, s. 1` kaynağını gösterin. Sonra şu soruyu sorun:

> Donanım arızasında kime mail atmalıyım?

Cevapta önce IT Destek Portalı’nın, portal erişilemiyorsa `it-destek@demo-kurum.local` adresinin önerildiğini gösterin. Son olarak dokümanlarda olmayan bir soru sorun:

> Yıllık izin gün sayısı nedir?

Asistanın bilgi uydurmak yerine onboarding dokümanlarında bilgi bulunmadığını söylemesini vurgulayın.

## 4. Teknik akışı anlatma

Soru geldiğinde ChromaDB top-k retrieval ile soruya en yakın parçaları getirir. Bu parçalar kaynak dosya ve sayfa metadatasını taşır. Ollama açıksa Phi-3 mini yalnızca bu bağlamı kullanarak cevap üretir. Ollama kapalıysa uygulama, retrieved cümlelerden kaynaklı bir yedek yanıt üretir. Bu yedek davranış, demo sırasında model kurulumu veya servis kesintisi yaşansa bile uygulamanın tamamen bozulmasını önler.

## 5. Olası jüri soruları

| Soru | Önerilen cevap |
|---|---|
| Neden bulut tabanlı bir API kullanmadın? | Kurum içi belgelerin gizliliğini korumak ve verinin kontrolünü kurumda tutmak için tüm RAG akışını yerel tasarladım. |
| Model yanlış cevap verirse ne olur? | Prompt yalnızca retrieved bağlama izin veriyor, kaynak dosya/sayfa gösteriliyor ve dokümanda olmayan bilgi için kontrollü “bulunmuyor” cevabı var. Üretimde buna değerlendirme seti ve insan onayı eklenebilir. |
| ChromaDB neden kullanıldı? | PDF parçalarını vektör olarak kalıcı saklayıp doğal dil sorularında en benzer parçaları hızlıca getirmek için kullanıldı. |
| Ollama çalışmazsa uygulama çöker mi? | Hayır. Sistem otomatik olarak kaynaklı extractive fallback moduna geçer ve kullanıcıya modelin kullanılamadığını açıkça bildirir. |
| Gerçek Microsoft verisi var mı? | Hayır. Teslimdeki PDF’ler yalnızca demo için hazırlanmış kurgusal örnek dokümanlardır; gerçek kurum verileri için güvenlik onayı gerekir. |
