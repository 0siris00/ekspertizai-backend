# MEKANİK SKİLL — EkspertizAI

Bu skill yalnızca mekanik kategoriyi skorlamak için kullanılır.

## ÇIKTI FORMATI
Sadece JSON döndür:
{"category":"Mekanik","score":"green|yellow|red","scoreLabel":"İYİ|DİKKAT|RİSKLİ","findings":[{"text":"açıklama","level":"green|yellow|red|info","detail":"ne yapmalısın"}],"isRiskyVehicle":false,"riskyReason":"","estimatedCosts":[{"label":"masraf","amount":"X.XXX – Y.YYY ₺","urgent":true}]}

## KURALLAR

### MOTOR PERFORMANSI
- %85 üzeri → green
- %78-85 arası → yellow
- %78 altı → red

### MOTOR GENEL
- Vuruntulu çalışma (her seviyede) → red + isRiskyVehicle=true ("Zamanla artabilir. Motor açtırılarak kontrol edilmeli.")
- Mavi duman → red + isRiskyVehicle=true ("Motor yağı yanma odasına kaçıyor.")
- Kara duman benzinli → red
- Siyah duman yüksek km dizel/DPF iptalli → yellow
- Conta kaçak testi temiz → green
- Motor sesli/yağlama sesi → yellow

### TURBO
- Terleme + ıslık sesi → yellow
- Terleme/hortum boşluğu → yellow
- Sesli/basınç kaybı/çekiş düşük → red (15.000-50.000₺)
- İntercooler/hortumda yağ → red (15.000-50.000₺)

### ŞANZIMAN
- Otomatik sorunsuz → green
- Otomatik vuruntu hafif → yellow
- Otomatik vuruntu belirgin → red (30.000-100.000₺+)
- Kavrama boşluğu 180bin km altı → red (8.000-20.000₺)
- Kavrama boşluğu 180bin km üzeri → yellow
- Manuel senkromeç/vites geçmeme → red (10.000-25.000₺)
- Şanziman terleme → yellow
- Şanziman yağ kaçağı → red (3.000-8.000₺)

### SIVI KAÇAKLARI
- Karter terleme → yellow
- Karter yağ kaçağı → red ("Yağ biterse yatak sarması — motor çöker.")
- Turbo/enjektör terleme → yellow
- Turbo/enjektör sıvı kaçağı → red
- Terleme + tamir işlemli → yellow
- Terleme + ıslık sesi → yellow

### ENJEKTÖRö& EGZOZ
- Enjektör sesli/sızıntı → red
- LPG araç oksijen sensörü → info (ihmal et)
- Benzinli oksijen sensörü → yellow

### DİĞER
- Rulman sesli → yellow
- Km/yaş servis müdahalesi → info
- Direksiyon terleme/boşluk → yellow
- Motor/şanziman takozu yıpranmış → yellow
- Yol testi yapılmadı → yellow
- Dinamometre yok → info

## KATEGORİ SKORU
- En az bir red → score=red
- Red yok yellow var → score=yellow
- Tümü green/info → score=green
