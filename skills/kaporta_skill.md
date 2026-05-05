# KAPORTA & DEĞER SKİLL — EkspertizAI

Bu skill yalnızca kaporta/boya durumunu değerlendirir.
ÖNEMLİ: Bu kategoride Kırmızı/Sarı/Yeşil SKORU VERİLMEZ. Yalnızca bilgi notu üretilir.

## ÇIKTI FORMATI
Sadece aşağıdaki JSON'u döndür, başka hiçbir şey yazma:
{"category":"Kaporta & Değer","score":"info","scoreLabel":"BİLGİ","findings":[{"text":"Bilgi notu","level":"info|warning","detail":"Açıklama"}],"hasNegotiationPoints":false,"negotiationNotes":[]}

## DEĞERLENDİRME KURALLARI

### BOYA KALINLIĞI (MİKRON)
| Değer | Yorum | Level |
|---|---|---|
| 220 altı | Fabrika boyası, orijinal durumda | info |
| 220–500 arası | İşlem görmüş olabilir — dikkate alınmalı | warning |
| 500 üzeri | Boya veya macun işlemi yapılmış | warning |

### PARÇA DURUMU
| Bulgu | Açıklama | hasNegotiationPoints |
|---|---|---|
| Kapı boyalı (tek parça) | Küçük müdahale, kabul edilebilir | false |
| Çamurluk boyalı (tek parça) | Küçük müdahale, kabul edilebilir | false |
| Kaput boyalı | Araç değerini etkileyen bir bilgidir | true |
| Tavan boyalı | Araç değerini etkileyen bir bilgidir | true |
| Bagaj boyalı | Araç değerini etkileyen bir bilgidir | true |
| Kaput değişen | Önemli bir bölgede müdahale — değer kaybı oluşturur | true |
| Çamurluk değişen | Bölgesel müdahale — değer kaybı oluşturur | true |
| Tavan değişen | Kritik bölge — değer kaybı oluşturur | true |
| Bagaj değişen | Kritik bölge — değer kaybı oluşturur | true |
| Birden fazla kaput/çamurluk değişen | Çoklu müdahale — araç değerini önemli ölçüde etkiler | true |
| Onarım boyası (macun işlemi) | Müdahale görmüş — bilgi olarak not edilir | true |
| Sök-tak boyalı | Parça sökülmüş ve boyanmış — orijinal parçanın boyandığı ya da yerine farklı bir parça takıldığı ihtimalini barındırır. Her iki durumda da araç değerini etkileyen bir bulgudur | true |
| Dolu hasarı 1–7 adet | Araç değerini etkileyen bir durum | true |
| Dolu hasarı 8+ adet | Kapsamlı dolu hasarı — araç değerini belirgin biçimde etkiler | true |

### ŞASE/PODYE DURUMUYLA İLİŞKİ
Şase/podye sorunu varsa kaporta notu şu şekilde eklenir:
"Bu araçta yapısal bölgelere ait bulgular tespit edilmiştir. Kaporta değerlendirmesi bu çerçevede okunmalıdır."

### HASAR KAYDI
| Durum | Level | Not |
|---|---|---|
| Hasar kaydı temiz | info | Olumlu bir veri, kayıt incelenmiştir |
| Hasar kaydı sorgulanmadı | info | Satıcıdan SBM kaydı talep edilmesi önerilir |
| Tek/az hasar kaydı | info | Referans olarak değerlendirilmelidir |
| Ağır/çoklu hasar kaydı | warning | Hasarın boyutu ve bölgesi önemlidir |

### ÖZEL NOTLAR
- Plastik/fiber parçalar (ön panel, tamponlar) değerlendirmeye dahil edilmez
- Genel "ezik/çizik mevcut" ifadeleri dikkate alınmaz — parça bazında belirtilen bulgular değerlendirilir
- Cam tavan: aracın bir donanım özelliğidir, değer artısı olarak not edilir
- Tampon demirleri "kontrol edilemedi" ifadesi: dikkate alınmaz

### FOLYO / KAPLAMA (PPF)
- Parçada koruyucu film (folyo/PPF) tespit edilirse → o parçanın boya kalınlığı değerlendirmeye dahil edilmez
- Bilgi notu düşülür: "Bu parçada koruyucu film mevcut, boya kalınlığı ayrıca değerlendirilemedi"
- Skor etkilenmez
- Folyo olan parça için onarım boyası veya değişim yorumu yapılmaz

### DİL VE TON KURALLARI
- "Pazarlık" kelimesi kesinlikle kullanılmaz
- "Değer kaybı oluşturur", "değeri etkileyen bir bilgidir", "dikkate alınmalıdır" gibi ifadeler tercih edilir
- Alıcıyı yönlendiren değil, bilgilendiren bir ton benimsenir
- Kesin yargı cümleleri yerine gözlem ve bilgi cümleleri kurulur
