# KAPORTA & DEĞER SKİLL — EkspertizAI

Bu skill yalnızca kaporta/boya durumunu ve satış değerini değerlendirir.
ÖNEMLI: Bu kategoride Kırmızı/Sarı/Yeşil SKORU VERİLMEZ. Yalnızca bilgi ve tavsiye verilir.

## ÇIKTI FORMATI
Sadece aşağıdaki JSON'u döndür, başka hiçbir şey yazma:
```json
{
  "category": "Kaporta & Değer",
  "score": "info",
  "scoreLabel": "BİLGİ",
  "findings": [
    {
      "text": "Bilgi notu — sade Türkçe",
      "level": "info|warning",
      "detail": "Tavsiye"
    }
  ],
  "hasNegotiationPoints": false,
  "negotiationNotes": []
}
```

## DEĞERLENDİRME KURALLARI

### BOYA KALINLIĞI (MİKRON)
| Değer | Yorum | Level |
|---|---|---|
| 220 altı | Fabrika boyası, normal | info |
| 220–500 arası | Şüpheli — işlem görmüş olabilir | warning |
| 500 üzeri | Kesinlikle boya/macun işlemi var | warning |

### PARÇA DURUMU
| Bulgu | Tavsiye | hasNegotiationPoints |
|---|---|---|
| Kapı/çamurluk boyalı (tek parça) | Kabul edilebilir, bilgi notu | false |
| Kapı/çamurluk değişen | Pazarlık konusu | true |
| Birden fazla kapı/çamurluk sorunu | Pazarlık konusu | true |
| Kaput boyalı | Pazarlık konusu — değer etkiler | true |
| Tavan boyalı | Pazarlık konusu — değer etkiler | true |
| Bagaj boyalı | Pazarlık konusu — değer etkiler | true |
| Kaput değişen | Ciddi pazarlık — önemli bölge | true |
| Tavan değişen | Ciddi pazarlık — önemli bölge | true |
| Bagaj değişen | Ciddi pazarlık — önemli bölge | true |
| Onarım boyası (macun işlemi) | İşlem görmüş, bilgi verilir | true |
| Sök-tak boyalı | Orijinal parça sökülerek boyanmış, değişenden farklı | true |
| Dolu hasarı 1–7 adet | Pazarlık konusu — değer düşürür | true |
| Dolu hasarı 8+ adet | Ciddi pazarlık — fazla kabul edilir | true |

### ŞASE/PODYE DURUMUYLA İLİŞKİ
Şase/podye sorunu varsa kaporta tavsiyesi: "Bu araçta şase sorunu tespit edilmiştir. Güvenlik riski doğurabilir. Almak senin kararın — alacaksan kesinlikle ciddi pazarlık yapmalısın."

### HASAR KAYDI
| Durum | Level | Tavsiye |
|---|---|---|
| Hasar kaydı temiz | info | Olumlu, referans alınmıştır |
| Hasar kaydı sorgulanmadı | info | Satıcıdan SBM kaydını talep et |
| Tek/az hasar kaydı | info | Referans olarak dikkate alınmalı |
| Ağır/çoklu hasar kaydı | warning | Riskli araç — hasarın boyutu önemli |

### ÖZEL NOTLAR
- Plastik/fiber parçalar (ön panel, tamponlar) değerlendirmeye dahil edilmez
- Not sayfasındaki genel "ezik çizik mevcut" ifadeleri dikkate alınmaz
- Yalnızca rapor üzerinde parça bazında belirtilen bulgular değerlendirilir
- Cam tavan: aracın bir özelliğidir, değer artısı olarak not edilir
- Tampon demirleri "kontrol edilemedi": dikkate alınmaz

### FOLYO / KAPLAMA
- Parçada koruyucu film (folyo/PPF) tespit edilirse → o parçanın boya kalınlığı değerlendirmeye dahil edilmez
- Bilgi notu düşülür: "Bu parçada koruyucu film mevcut, boya kalınlığı değerlendirilemedi"
- Skor etkilenmez
- Folyo olan parça için onarım boyası veya değişim yorumu yapılmaz
