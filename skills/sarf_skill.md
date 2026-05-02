# SARF MASRAF SKİLL — EkspertizAI

Bu skill yalnızca sarf masraf kategorisini skorlamak için kullanılır.

## ÇIKTI FORMATI
Sadece JSON döndür:
{"category":"Sarf Masraf","score":"green|yellow|red","scoreLabel":"İYİ|DİKKAT|MASRAFLI","findings":[{"text":"açıklama","level":"green|yellow|red|info","detail":"ne yapmalısın"}],"estimatedCosts":[{"label":"masraf","amount":"X.XXX – Y.YYY ₺","urgent":true}]}

## KURALLAR

### TRİGER
- Bakım periyoduna göre yapılmış → green
- Satıcı beyanı var belge yok → yellow
- Yapılmamış/bilgi yok → red (5.000-15.000₺) ("Kopması halinde motor tamamen çökebilir.")

### LASTİK
- 5 yıl altı diş yeterli → green
- Lastik diş/basınç normal → green
- Kılcal çatlak → red (8.000-20.000₺)
- 5 yıl üzeri → red (8.000-20.000₺)

### ÖN TAKIM
- Rotlarda boşluk → yellow (2.000-4.000₺)
- Rot başı/alt rotil/Z rot deformasyon → red (4.000-8.000₺) ("Direksiyon kontrolü bozulur.")
- Süspansiyon takoz çatlak → yellow (1.500-3.000₺)
- Süspansiyon takoz yırtık → red (1.500-3.000₺)
- Süspansiyon terleme → yellow
- Süspansiyon kaçak → red (6.000-15.000₺)
- Motor/şanziman takozu yıpranmış → yellow (2.000-5.000₺)
- Süspansiyon tutunma %78 üzeri → green

### SOĞUTMA
- Radyatör/su hortumu leke → yellow
- Radyatör/su hortumu çatlak/kaçak → red (3.000-8.000₺) ("Motor aşırı ısınırsa silindir kapağı yanabilir.")
- Yedek su deposu orta/üst kaçak → red (5.000-15.000₺)
- Yağ soğutucusu patlamış → red (20.000-60.000₺+)

### YAĞ BAKIMI
Her araç için standart masraf — costs listesine ekle: 2.500-5.000₺

### CONTA
- Conta kaçak testi temiz → green
- Conta açık/kaçak → red

## KATEGORİ SKORU
- En az bir red → score=red
- Red yok yellow var → score=yellow
- Tümü green/info → score=green
