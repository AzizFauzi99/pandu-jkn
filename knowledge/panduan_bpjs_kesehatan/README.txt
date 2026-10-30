# Paket Panduan BPJS Kesehatan untuk AI Assistant

**Tanggal pemeriksaan sumber:** 30 Oktober 2026  
**Bahasa:** Indonesia  
**Tujuan:** basis pengetahuan prosedural untuk tool `baca_panduan(topik)`.

## Cara menggunakan dengan tool

Tool membaca semua file `*.md` di direktori panduan dan menggunakan nama file tanpa ekstensi sebagai nilai `topik`.

Contoh:

- `baca_panduan("")` — menampilkan daftar semua topik.
- `baca_panduan("pendaftaran_peserta")` — membaca `pendaftaran_peserta.md`.
- `baca_panduan("pembayaran_iuran")` — membaca `pembayaran_iuran.md`.

Jangan masukkan ekstensi `.md` ke parameter `topik`.

## Daftar topik

| Nilai `topik` | Isi |
|---|---|
| `pendaftaran_peserta` | Pendaftaran peserta baru, terutama PBPU/mandiri, dan perbedaan segmen peserta |
| `dokumen_pendaftaran` | Data dan dokumen yang perlu disiapkan menurut jalur pendaftaran |
| `pembayaran_iuran` | Cek tagihan, pembayaran, autodebit, dan tunggakan |
| `ubah_faskes` | Perubahan Fasilitas Kesehatan Tingkat Pertama (FKTP) |
| `kartu_hilang` | Kartu fisik hilang dan penggunaan KIS Digital |
| `cek_status_kepesertaan` | Pemeriksaan status aktif, nomor peserta, dan FKTP |
| `alur_berobat_dan_rujukan` | Alur layanan FKTP, rujukan, dan kondisi gawat darurat |
| `pengaduan_layanan` | Pengaduan melalui Mobile JKN dan kanal bantuan |
| `kanal_resmi_bpjs` | Mobile JKN, PANDAWA, Care Center 165, dan situs resmi |

## Instruksi penting untuk AI

1. Gunakan isi file yang paling sesuai dengan pertanyaan. Jangan menyimpulkan prosedur hanya dari judul file.
2. Jangan menjawab prosedur BPJS berdasarkan ingatan apabila file tidak membahasnya. Beri tahu pengguna bahwa panduan tertulis belum tersedia, lalu arahkan ke Mobile JKN atau Care Center 165.
3. Jangan mengarang persyaratan, biaya, nominal iuran, tanggal jatuh tempo, denda, durasi proses, status aktif, ataupun hasil pengajuan.
4. Untuk nominal iuran dan tagihan, minta pengguna memeriksa angka terbaru di menu **Info Iuran** Mobile JKN atau kanal resmi. Jangan memakai angka dari artikel lama.
5. Ketentuan dapat berbeda berdasarkan segmen kepesertaan (PBI, PPU, PBPU/BP, atau peserta yang didaftarkan pemerintah daerah), riwayat kepesertaan, dan kondisi peserta. Jangan menganggap semua peserta memiliki alur administrasi yang sama.
6. Langkah dan nama menu aplikasi dapat berubah karena pembaruan Mobile JKN. Jika menu pada aplikasi pengguna berbeda, arahkan ke Care Center 165 atau PANDAWA.
7. Jangan meminta pengguna mengirimkan NIK, nomor KK, foto KTP, nomor kartu, OTP, PIN, kata sandi, atau data kesehatan sensitif ke percakapan AI. Pengguna hanya boleh memasukkan data tersebut pada kanal resmi BPJS yang sedang digunakan.
8. Jangan meminta atau menyimpan OTP/PIN. BPJS maupun AI assistant tidak memerlukan pengguna membagikan OTP atau PIN kepada petugas melalui chat tidak resmi.
9. Untuk keadaan darurat medis, jangan menunda pertolongan demi urusan administrasi. Arahkan pengguna ke IGD/fasilitas kesehatan terdekat dan jelaskan bahwa penetapan kondisi gawat darurat dilakukan oleh tenaga medis.
10. Sertakan kanal resmi dan tautan sumber yang relevan bila membantu. Hindari memberikan nomor WhatsApp selain nomor PANDAWA yang tercantum dalam file kanal resmi.
11. Jika panduan tidak menjawab kasus khusus, katakan secara eksplisit bahwa jawabannya perlu dikonfirmasi ke BPJS Kesehatan. Jangan membuat jawaban terdengar pasti.

## Catatan pemeliharaan

Periksa ulang isi paket secara berkala, terutama jika BPJS Kesehatan mengubah ketentuan kepesertaan, tarif iuran, alur aplikasi, nomor layanan, dan jam operasional. Sumber yang dirujuk adalah kanal resmi BPJS Kesehatan; tautan dapat berubah sewaktu-waktu.
