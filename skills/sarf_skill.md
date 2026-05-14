# SARF MASRAF SKİLL — EkspertizAI

## KRİTİK KURAL
Raporda mekanik kontrol yapılmamışsa (dinamometre, yağ, motor kontrolleri yoksa) bu kategori ANALİZ EDİLEMEDİ olarak işaretlenir.
Yalnızca kaporta/boya ekspertizi yapılmışsa sarf masraf hesaplanmaz.

## ÇIKTI FORMATI
{"category":"Sarf Masraf","score":"yellow","scoreLabel":"DİKKAT","findings":[...],"estimatedCosts":[...]}

## KONTROL KURALI
Raporda şu ifadelerden HİÇBİRİ yoksa → kategori ATLA:
- "yağ", "motor", "dinamometre", "vites", "şanzıman", "yakıt", "filtre", "bakım"

Eğer kaporta/boya raporu ise şunu döndür:
{"category":"Sarf Masraf","score":"info","scoreLabel":"DEĞERLENDİRİLMEDİ","findings":[{"text":"Bu rapor kapsamında mekanik kontrol yapılmamıştır. Sarf masraf değerlendirmesi için mekanik ekspertiz gereklidir.","level":"info","detail":""}],"estimatedCosts":[]}
