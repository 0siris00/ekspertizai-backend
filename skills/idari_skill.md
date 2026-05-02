# İDARİ KONTROLLER SKİLL — EkspertizAI

Bu kategoride skor verilmez, yalnızca bilgi notu üretilir.

## ÇIKTI FORMATI
Sadece JSON döndür:
{"category":"İdari Kontroller","score":"info","findings":[{"text":"bilgi notu","level":"green|info|warning","detail":"açıklama"}]}

## KURALLAR

### OGS/HGS/KGS BORCU
- Borç YOK → green "Araçta geçiş/trafik cezası borcu bulunmamaktadır."
- Borç VAR → info "Araçta OGS/HGS/KGS borcu bulunmaktadır. Satış öncesi netleştirilmesi önerilir."
- Sorgulanmadı → info "Satıcıdan kontrol etmesini isteyebilirsiniz."

### MTV BORCU
- YOK → green "MTV borcu bulunmamaktadır."
- VAR → info "Araçta MTV borcu bulunmaktadır. Satış öncesi ödenmesi gerekir."

### EGZOZ EMİSYON
- Geçerli → green
- Tarihi geçmiş → info "Aracın egzoz emisyon muayene süresi dolmuştur."

### KM SORGUSU
- Tutarlı → green "Kilometre kaydı tutarlı."
- Yapılmamış → warning "Km verisi analiz edilemedi. Km geçmişini satıcıdan talep ediniz."
- Farklı km → red "Kilometre manipülasyonu şüphesi var. Dikkatli olunmalıdır."
- Resim olarak çekilmiş → info "Km sorgusu sisteme yansımamış. Satıcıdan talep ediniz."

### RUHSAT
- Aslı görüldü → green
- Görülmedi → info

### RECALL
Her raporda standart not: "Aracın kronik arızalı parça geri çağırma (Recall) kaydı olup olmadığını yetkili servisten sorgulatmayı unutmayınız."
