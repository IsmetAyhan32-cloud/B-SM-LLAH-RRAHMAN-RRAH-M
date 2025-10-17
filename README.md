# Online Yoklama Sistemi

Bu proje, öğretmenlerin ders yoklamalarını dijital ortamda yönetmesini ve öğrencilerin katılımlarını hızlıca bildirmesini sağlayan basit bir web uygulamasıdır.

## Özellikler

- Öğretmenler Excel dosyası yükleyerek ders oturumu oluşturabilir.
- Öğrenci listeleri 14 haftalık yoklama sütunlarını içerir.
- Öğretmen panelinde öğrencilerin haftalık devam durumları `+` işaretleri ile görüntülenir.
- Öğrenciler öğrenci numarası ile giriş yaparak aktif oturumlarda yoklamaya katılabilir.
- Öğretmenler hangi haftanın aktif olduğunu belirleyerek o haftanın yoklamasını açabilir.

## Kurulum

1. Gerekli paketleri yükleyin:

   ```bash
   pip install -r requirements.txt
   ```

2. Uygulamayı başlatın:

   ```bash
   flask --app app run
   ```

   veya

   ```bash
   python app.py
   ```

3. Tarayıcınızdan [http://localhost:5000](http://localhost:5000) adresine giderek uygulamayı kullanmaya başlayın.

## Excel Şablonu

Excel dosyası aşağıdaki sütunları içermelidir:

| Sütun | Açıklama          |
| ----- | ----------------- |
| A     | Öğrenci Numarası  |
| B     | Öğrenci Adı Soyadı|
| C     | Öğrenci Bölümü    |
| D-Q   | Hafta 1 - Hafta 14|

Yoklaması alınmış haftalar `+` işareti ile işaretlenmelidir.

## Geliştirme Notları

- Veriler `data/sessions.json` dosyasında saklanır.
- Varsayılan gizli anahtar geliştirme amaçlıdır. Üretim ortamında `ATTENDANCE_APP_SECRET` değişkenini özelleştirin.
