# MEKANİK SKİLL — EkspertizAI

Bu skill yalnızca mekanik kategoriyi skorlamak için kullanılır.

## ÇIKTI FORMATI
Sadece JSON döndür:
{"category":"Mekanik","score":"green|yellow|red","scoreLabel":"İYİ|DİKKAT|RİSKLİ","findings":[{"text":"açıklama","level":"green|yellow|red|info","detail":"ne yapmalısın"}],"isRiskyVehicle":false,"riskyReason":"","estimatedCosts":[{"label":"masraf","amount":"X.XXX – Y.YYY ₺","urgent":true}]}

## KURALLAR

### MOTOR PERFORMANSI (Dyno/Yol Testi)
- Yüzde 85 üzeri → green
- Yüzde 78-85 arası → yellow
- Yüzde 78 altı → red
- Test yapılmadı → yellow bilgi notu
- Dyno test süresi 15 saniye üzeri benzinli → yellow "Debriyaj geç kavraması şüphesi"
- Grafikte aşırı dalgalanma → yellow "Yakıt veya ateşleme sistemi kontrolü önerilir"

### MOTOR GENEL
- Vuruntulu çalışma her seviyede → red isRiskyVehicle=true "Motor açtırılarak kontrol edilmeli. Zamanla artabilir."
- Mavi duman → red isRiskyVehicle=true "Motor yağ yakıyor. Pistonlar veya supap contaları aşınmış."
- Yoğun beyaz duman → red "Silindir kapak contası hasarı şüphesi. Su eksiltmesi kontrol edilmeli."
- İnce beyaz duman soğuk hava → ihmal et
- Gri duman → red "Turbo yağ sızıntısı veya şanzıman yağı motora karışıyor olabilir."
- Siyah duman km 180000 ALTI → red "Yakıt veya enjektör sorunu. Düşük km araçta bu normal değil."
- Siyah duman km 180000 ÜSTÜ veya DPF iptalli → yellow "Yüksek km veya DPF iptalli araçlarda görülebilir."
- Conta kaçak testi temiz değer 1 → green "Silindir kapak contası sağlam."
- Motor sesli yağlama sesi → yellow

### TURBO
- Terleme artı ıslık sesi → yellow "Kontrol önerilir"
- Terleme veya hortum boşluğu → yellow
- Sesli çalışma veya basınç kaybı veya çekiş düşük → red 15000-50000 TL
- İntercooler veya hortumda yağ → red 15000-50000 TL
- Turbo grafik bozuk veya devreye girmeme şüphesi → yellow

### ŞANZIMAN
- Otomatik sorunsuz → green
- Otomatik vuruntu hafif → yellow
- Otomatik vuruntu belirgin → red 30000-100000 TL
- DSG veya EDC tipi hafif sarsıntı → yellow "Bu şanzıman tipinde görülebilir, takip et"
- CVT sesi veya kayış problemi → red 20000-50000 TL
- Robotize sert geçiş → yellow
- Kavrama boşluğu 180000 km altı → red 8000-20000 TL "Erken aşınma"
- Kavrama boşluğu 180000 km üzeri → yellow
- Manuel senkromeç sesi veya vites geçmeme → red 10000-25000 TL
- Şanziman terleme → yellow
- Şanziman yağ kaçağı → red 3000-8000 TL

### SIVI KAÇAKLARI
- Karter terleme → yellow
- Karter yağ kaçağı → red "Yağ biterse yatak sarması motoru çökertir. Acil."
- Turbo veya enjektör terleme → yellow
- Turbo veya enjektör sıvı kaçağı → red
- Terleme tamir işlemli → yellow
- Terleme ıslık sesi → yellow

### ENJEKTÖR VE EGZOZ
- Enjektör sesli veya sızıntı → red
- LPG araç oksijen sensörü → info ihmal et
- Benzinli oksijen sensörü → yellow

### DİĞER
- Rulman sesli → yellow
- Km yaş servis müdahalesi → info
- Direksiyon terleme veya boşluk → yellow
- Motor veya şanziman takozu yıpranmış → yellow
- Yol testi yapılmadı → yellow
- Dinamometre yok → info

## KATEGORİ SKORU
- En az bir red varsa score=red scoreLabel=RİSKLİ
- Red yok yellow var ise score=yellow scoreLabel=DİKKAT
- Tümü green veya info ise score=green scoreLabel=İYİ
