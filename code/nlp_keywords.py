# =======================================================
# nlp_keywords.py
# Mapping Keyword User -> Entity Ontologi (Validasi TTL)
# =======================================================

NLP_MAP = {
    # --- TIPE UTAMA (Mapping ke Nama Class) ---
    "hotel":        {"type": "class", "value": "Hotel"},
    "penginapan":   {"type": "class", "value": "Hotel"},
    "nginep":       {"type": "class", "value": "Hotel"},
    
    "wisata":       {"type": "class", "value": "TempatWisata"},
    "jalan":        {"type": "class", "value": "TempatWisata"},
    "liburan":      {"type": "class", "value": "TempatWisata"},
    "rekreasi":     {"type": "class", "value": "TempatWisata"},
    
    "makan":        {"type": "class", "value": "Restoran"},
    "restoran":     {"type": "class", "value": "Restoran"},
    "resto":        {"type": "class", "value": "Restoran"},
    "kuliner":      {"type": "class", "value": "Restoran"},
    "lapar":        {"type": "class", "value": "Restoran"},

    "transport":    {"type": "class", "value": "Transportasi"},
    "transportasi": {"type": "class", "value": "Transportasi"},
    "bus":          {"type": "class", "value": "Transportasi"},
    "angkot":       {"type": "class", "value": "Transportasi"},
    
    # --- LOKASI (Mapping ke Nama Individual Lokasi di TTL) ---
    "laweyan":      {"type": "lokasi", "value": "Laweyan"},
    "banjarsari":   {"type": "lokasi", "value": "Banjarsari"},
    "jebres":       {"type": "lokasi", "value": "Jebres"},
    "serengan":     {"type": "lokasi", "value": "Serengan"},
    "kliwon":       {"type": "lokasi", "value": "PasarKliwon"},
    "pasarkliwon":  {"type": "lokasi", "value": "PasarKliwon"},
    "tawamangu":    {"type": "lokasi", "value": "Tawamangu"},
    "tawangmangu":  {"type": "lokasi", "value": "Tawamangu"},

    # --- KATEGORI WISATA (Mapping ke Nilai Data Property 'kategoriDayaTarik') ---
    # Diambil dari instance: KeratonSolo (budaya), BukitSekipan (alam), dll.
    "alam":         {"type": "kategori", "value": "alam"},
    "budaya":       {"type": "kategori", "value": "budaya"},
    "sejarah":      {"type": "kategori", "value": "sejarah"},
    "religi":       {"type": "kategori", "value": "religi"},
    "edukasi":      {"type": "kategori", "value": "edukasi"},
    # "kuliner" juga ada di kategoriDayaTarik (PasarGede), tapi bentrok sama Restoran.
    # Kita bisa handle logic-nya di app.py nanti.

    # --- KATEGORI MAKANAN (Mapping ke Nilai Data Property 'kategoriMakanan') ---
    "tradisional":  {"type": "kategori", "value": "tradisional"},
    "jawa":         {"type": "kategori", "value": "tradisional"},
    "modern":       {"type": "kategori", "value": "makanan modern"}, # Sesuai instance WeTheFork
    "barat":        {"type": "kategori", "value": "makanan modern"}, # Sinonim
    "western":      {"type": "kategori", "value": "makanan modern"}, # Sinonim

    # --- WAKTU & STATUS (Mapping ke String Class Inferred) ---
    # Class ini ada di hierarchy WaktuBukaHarian/WaktuTutupHarian
    "pagi":         {"type": "waktu", "value": "Pagi"},
    "siang":        {"type": "waktu", "value": "Siang"},
    "sore":         {"type": "waktu", "value": "Sore"},
    "malam":        {"type": "waktu", "value": "Malam"},
    "buka":         {"type": "status", "value": "Buka"},
    "tutup":        {"type": "status", "value": "Tutup"},

    # --- HUBUNGAN / RELASI (BARU!) ---
    "dekat":        {"type": "relation", "value": "nearby"},
    "sekitar":      {"type": "relation", "value": "nearby"},
    "sebelah":      {"type": "relation", "value": "nearby"},
    "pinggir":      {"type": "relation", "value": "nearby"},
}