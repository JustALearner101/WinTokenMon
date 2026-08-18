/**
 * ==============================================================================
 * 🐾 WinTokenMon (v0.1.0-beta) — Internal Beta Testing Feedback Form Generator
 * ==============================================================================
 * Cara Penggunaan:
 * 1. Buka https://script.google.com/
 * 2. Klik "New Project" (Proyek Baru)
 * 3. Hapus kode default, lalu Paste seluruh isi script ini ke editor
 * 4. Klik icon "Save" (💾) lalu klik "Run" (▶️) fungsi `createBetaTestingForm()`
 * 5. Buka tab "Execution log" di bagian bawah untuk melihat link Google Form yang baru dibuat!
 * ==============================================================================
 */

function createBetaTestingForm() {
  // 1. Inisialisasi Google Form Baru
  const formTitle = "🐾 WinTokenMon (v0.1.0-beta) — Internal Beta Tester Feedback";
  const form = FormApp.create(formTitle);

  form.setDescription(
    "Halo teman-teman tester! 👋\n\n" +
    "Terima kasih banyak sudah meluangkan waktu buat nyobain WinTokenMon (aplikasi desktop Windows pemantau token AI koding dengan pendamping Pokémon hidup).\n\n" +
    "Formulir ini bertujuan buat mengumpulkan feedback, laporan bug, serta pengalaman kalian selama menggunakan versi Beta ini. Pengisian cuma butuh waktu sekitar 3–5 menit kok!\n\n" +
    "Semua masukan dan kritik jujur kalian bakal sangat ngebantu buat persiapan rilis publik! 🚀"
  );

  form.setConfirmationMessage(
    "🎉 Terima kasih banyak atas feedback dan masukannya!\n" +
    "Laporan bug dan saran kalian bakal langsung kita review dan tindak lanjuti untuk update versi berikutnya. Happy coding with your Pokémon companion! 🐾✨"
  );

  form.setAllowResponseEdits(true);
  form.setProgressBar(true);

  // ==============================================================================
  // SECTION 1: Profil Tester & Lingkungan Pengujian
  // ==============================================================================
  form.addSectionHeaderItem()
    .setTitle("💻 Bagian 1: Profil Tester & Spesifikasi Perangkat")
    .setHelpText("Informasi ini membantu kita menganalisis kompatibilitas hardware dan environment Windows.");

  // Q1: Nama / Alias
  form.addTextItem()
    .setTitle("1. Nama / Panggilan Tester")
    .setHelpText("Biar kita tahu siapa yang ngasih feedback (boleh nama asli atau username Discord/GitHub).")
    .setRequired(true);

  // Q2: Versi OS Windows
  form.addMultipleChoiceItem()
    .setTitle("2. Versi Windows yang kamu gunakan?")
    .setChoiceValues([
      "Windows 11 (64-bit)",
      "Windows 10 (64-bit)",
      "Windows 10 (32-bit)",
      "Windows melalui VM / Parallels / Wine",
      "Lainnya"
    ])
    .showOtherOption(true)
    .setRequired(true);

  // Q3: Setup Monitor
  form.addMultipleChoiceItem()
    .setTitle("3. Setup Layar / Monitor kamu saat testing?")
    .setChoiceValues([
      "Single Monitor (1 Layar Laptop atau 1 Monitor PC biasa)",
      "Dual Monitor dengan resolusi & scaling DPI yang sama",
      "Dual Monitor dengan resolusi/scaling DPI berbeda (misal 4K + 1080p, atau 125% + 100%)",
      "3 Monitor atau lebih"
    ])
    .setRequired(true);

  // Q4: AI Tools yang dipakai
  form.addCheckboxItem()
    .setTitle("4. AI Coding Tools apa saja yang biasa kamu pakai di PC ini?")
    .setHelpText("Pilih semua yang kamu gunakan (aplikasi akan otomatis mendeteksi log lokalnya).")
    .setChoiceValues([
      "Antigravity CLI (Gemini)",
      "Cursor IDE",
      "Claude Code (CLI)",
      "Codex CLI",
      "GitHub Copilot CLI",
      "Tool lain (Aider / Windsurf / Continue / Roo Code)",
      "Belum pakai AI coding tool (hanya coba jalanin pet-nya)"
    ])
    .showOtherOption(true)
    .setRequired(true);

  // ==============================================================================
  // SECTION 2: Pengalaman Instalasi & Kestabilan (First Launch & Stability)
  // ==============================================================================
  form.addPageBreakItem()
    .setTitle("🛠️ Bagian 2: Pengalaman First Launch & Kestabilan Aplikasi")
    .setHelpText("Menilai kemudahan saat pertama kali membuka aplikasi dan apakah ada kendala teknis.");

  // Q5: Kelancaran First Launch (Scale 1-5)
  form.addScaleItem()
    .setTitle("5. Seberapa lancar saat kamu pertama kali membuka file .exe?")
    .setBounds(1, 5)
    .setLabels("Bermasalah / Gagal Buka", "Lancar Jaya Langsung Muncul")
    .setRequired(true);

  // Q6: Windows SmartScreen / Antivirus Prompt
  form.addMultipleChoiceItem()
    .setTitle("6. Apakah sempat muncul peringatan Windows SmartScreen / Antivirus?")
    .setChoiceValues([
      "Tidak muncul apa-apa, langsung jalan mulus",
      "Muncul popup biru 'Windows protected your PC', tapi bisa klik 'More info' -> 'Run anyway'",
      "Sempat diblokir / dikarantina oleh Antivirus pihak ketiga",
      "Muncul error missing DLL atau file corrupt"
    ])
    .showOtherOption(true)
    .setRequired(true);

  // Q7: Crash / Freeze
  form.addMultipleChoiceItem()
    .setTitle("7. Apakah aplikasi sempat mengalami crash atau freeze (hang) tiba-tiba?")
    .setChoiceValues([
      "Tidak pernah sama sekali (100% stabil)",
      "Sempat freeze/lag sebentar saat pertama kali buka Dashboard",
      "Pernah crash / tertutup sendiri 1-2 kali",
      "Sering crash / tidak bisa dibuka sama sekali"
    ])
    .setRequired(true);

  // Q8: Kronologi Bug / Error
  form.addParagraphTextItem()
    .setTitle("8. Jika mengalami error, freeze, atau keanehan visual, ceritakan kronologinya di sini:")
    .setHelpText("Boleh cantumkan pesan error yang muncul, atau tindakan apa yang sedang kamu lakukan pas error terjadi (Opsional).")
    .setRequired(false);

  // ==============================================================================
  // SECTION 3: Fitur & Visual UX (Gameplay, Animasi & Kenyamanan)
  // ==============================================================================
  form.addPageBreakItem()
    .setTitle("🎮 Bagian 3: Fitur, Animasi & Visual Companion")
    .setHelpText("Menilai daya tarik visual Pokémon di desktop dan kepuasan fitur.");

  // Q9: Rating Animasi Pet (Scale 1-5)
  form.addScaleItem()
    .setTitle("9. Bagaimana penilaianmu terhadap animasi melangkah & kelucuan Pokémon di desktop?")
    .setBounds(1, 5)
    .setLabels("Kaku / Kurang Menarik", "Sangat Lucu & Hidup!")
    .setRequired(true);

  // Q10: Fitur Favorit
  form.addCheckboxItem()
    .setTitle("10. Fitur mana yang paling kamu suka atau sering kamu coba?")
    .setChoiceValues([
      "🐾 Pokémon jalan-jalan otomatis di layar desktop (Auto-Roaming)",
      "❤️ Loncatan ceria & emoji reaksi pas pet diklik",
      "📊 Dashboard Analitik grafik 7 hari & tema warna adaptif",
      "📖 Pokédex lengkap (search spesies, filter rarity & varian Shiny)",
      "🛍️ Toko Item (Rare Candy +100M EXP, Nature Mint, Telur Baru)",
      "🔊 Suara asli cry Pokémon & synthesizer musik Level-Up 8-bit",
      "🔔 Peringatan limit harian token via Windows Native Toast Notification",
      "📌 Fitur Snap nempel di atas Taskbar"
    ])
    .setRequired(true);

  // Q11: Akurasi Pembacaan Token
  form.addMultipleChoiceItem()
    .setTitle("11. Apakah jumlah token AI kodingmu bertambah secara akurat di aplikasi?")
    .setChoiceValues([
      "Ya, angka token bertambah dan EXP Pokémon naik pas lagi koding",
      "Bertambah, tapi ada jeda beberapa detik (wajar karena log flush)",
      "Angka token tetap 0 / tidak bertambah meski sedang aktif koding",
      "Belum memperhatikan / Belum koding pakai AI saat testing"
    ])
    .setRequired(true);

  // Q12: Kenyamanan di Layar
  form.addMultipleChoiceItem()
    .setTitle("12. Apakah keberadaan pet terasa mengganggu fokus koding atau menutupi jendela kerjamu?")
    .setChoiceValues([
      "Pas banget & sama sekali tidak mengganggu",
      "Kadang menutupi tombol penting, tapi terbantu karena bisa digeser / di-snap ke taskbar",
      "Terlalu besar / ingin opsi ukuran yang lebih kecil",
      "Ingin opsi mode sembunyikan cepat (hide to tray)"
    ])
    .showOtherOption(true)
    .setRequired(true);

  // ==============================================================================
  // SECTION 4: Feedback Terbuka, Wishlist & Net Promoter Score (NPS)
  // ==============================================================================
  form.addPageBreakItem()
    .setTitle("💡 Bagian 4: Saran Fitur Baru & Rekomendasi")
    .setHelpText("Bantu kami memprioritaskan fitur-fitur yang paling diinginkan untuk update berikutnya.");

  // Q13: Wishlist Fitur Mendatang
  form.addCheckboxItem()
    .setTitle("13. Fitur dari rencana update mendatang mana yang paling kamu tunggu?")
    .setChoiceValues([
      "🏆 Sistem Badge & Achievement Developer (Night Owl, Overclock 1M Token, Shiny Hunter)",
      "🍬 Minigame interaktif lempar makan permen/berry langsung di lantai desktop",
      "⚔️ Arena pertarungan Pokémon antar teman di jaringan lokal (LAN)",
      "💊 Mode Floating HUD Pill minimalis (kapsul kecil ringkas di dekat jam taskbar)",
      "🔌 Scanner untuk AI tool tambahan (Aider, Windsurf, Roo Code, Cline)",
      "🎨 Opsi kustomisasi tema / sprite pet selain Pokémon"
    ])
    .showOtherOption(true)
    .setRequired(true);

  // Q14: Kritik & Saran Bebas
  form.addParagraphTextItem()
    .setTitle("14. Kritik, saran bebas, atau hal yang menurutmu masih kurang enak dipakai:")
    .setHelpText("Tuliskan secara jujur apa saja yang ada di pikiranmu! (Kritik pedas sangat diterima 🙏)")
    .setRequired(false);

  // Q15: Net Promoter Score (Scale 1-10)
  form.addScaleItem()
    .setTitle("15. Seberapa besar kemungkinan kamu bakal merekomendasikan WinTokenMon ke teman sesama developer/koder?")
    .setBounds(1, 10)
    .setLabels("Kecil Kemungkinan (1)", "Pasti Direkomendasikan! (10)")
    .setRequired(true);

  // ==============================================================================
  // Output Log URLs
  // ==============================================================================
  const editUrl = form.getEditUrl();
  const publishedUrl = form.getPublishedUrl();

  Logger.log("=================================================================");
  Logger.log("🎉 GOOGLE FORM FEEDBACK BETA BERHASIL DIBUAT!");
  Logger.log("=================================================================");
  Logger.log("📝 Link Edit & Kelola Form: " + editUrl);
  Logger.log("🔗 Link Publik (Kirim ke Teman Tester): " + publishedUrl);
  Logger.log("=================================================================");
}
