# GÜVENLİK SKİLL — EkspertizAI

Bu skill yalnızca güvenlik kategorisini skorlamak için kullanılır.

## ÇIKTI FORMATI
Sadece JSON döndür:
{"category":"Güvenlik","score":"green|yellow|red","scoreLabel":"İYİ|DİKKAT|RİSKLİ","findings":[{"text":"açıklama","level":"green|yellow|red|info","detail":"ne yapmalısın"}],"isRiskyVehicle":false,"riskyReason":""}

## KURALLAR

### AİRBAG
- Orijinal, uyumlu → green
- Tamirli, belgelendi → yellow
- Direnç ile kandırılmış → red + isRiskyVehicle=true ("Kaza anında açılmaz. Can güvenliği riski.")
- Emniyet kemeri uyumsuz → red + isRiskyVehicle=true
- Pakete dahil değil → info

### ŞASE & PODYE
- Tüm parçalar orijinal → green
- Mini ezik → yellow
- Kaynak/punto/boya/macun → red + isRiskyVehicle=true ("Yapısal güvenlik garanti edilemez. Almak senin kararın — kesinlikle pazarlık et.")
- Eğrilik → red + isRiskyVehicle=true
- Tampon demiri kontrol edilemedi → info (skoru etkilemez)

### FREN
- Test uyumlu → green
- Test orantısız → red + isRiskyVehicle=true ("Ani frende araç yoldan çıkabilir.")
- Balata/disk kritik → yellow
- Balata/disk değişim gerekli → red
- Hortum/merkez sorunlu → yellow
- Pakete dahil değil → info

## KATEGORİ SKORU
- En az bir red → score=red
- Red yok, yellow var → score=yellow
- Tümü green/info → score=green
