# KAPORTA & DEĞER SKİLL — EkspertizAI

Bu kategoride Kırmızı/Sarı/Yeşil SKORU VERİLMEZ. Yalnızca bilgi ve tavsiye verilir.

## ÇIKTI FORMATI
Sadece JSON döndür:
{"category":"Kaporta & Değer","score":"info","scoreLabel":"BİLGİ","findings":[{"text":"bilgi notu","level":"info|warning","detail":"tavsiye"}],"hasNegotiationPoints":false,"negotiationNotes":[]}

## KURALLAR

### BOYA KALINLIĞI (MİKRON)
- 220 altı → info "Fabrika boyası, normal"
- 220-500 arası → warning "Şüpheli — işlem görmüş olabilir"
- 500 üzeri → warning "Kesinlikle boya/macun işlemi var"

### PARÇA DURUMU
- Kapı/çamurluk boyalı tek parça → info, hasNegotiationPoints=false
- Kapı/çamurluk değişen → warning, hasNegotiationPoints=true
- Birden fazla kapı/çamurluk sorunu → warning, hasNegotiationPoints=true
- Kaput/tavan/bagaj boyalı → warning, hasNegotiationPoints=true "Değer etkiler, pazarlık et"
- Kaput/tavan/bagaj değişen → warning, hasNegotiationPoints=true "Önemli bölge, ciddi pazarlık"
- Onarım boyası/macun → warning, hasNegotiationPoints=true
- Sök-tak boyalı → warning, hasNegotiationPoints=true "Orijinal parça sökülerek boyanmış"
- Dolu hasarı 1-7 adet → warning, hasNegotiationPoints=true "Değer düşürür"
- Dolu hasarı 8+ adet → warning, hasNegotiationPoints=true "Fazla kabul edilir, ciddi pazarlık"

### HASAR KAYDI
- Temiz → info "Hasar kaydı yok, olumlu"
- Sorgulanmadı → info "Satıcıdan SBM kaydını talep et"
- Tek/az hasar → info "Referans olarak dikkate al"
- Ağır/çoklu hasar → warning "Riskli araç"

### ÖZEL NOTLAR
- Plastik/fiber parçalar değerlendirmeye dahil edilmez
- Not sayfasındaki genel ezik/çizik ifadeleri dikkate alınmaz
- Cam tavan → info "Değer artısı özellik"
- Tampon demiri kontrol edilemedi → dikkate alma
