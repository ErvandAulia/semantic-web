from flask import Flask, render_template, request
from owlready2 import *
import nltk
from nltk.tokenize import word_tokenize

# --- IMPORT KEYWORDS ---
from nlp_keywords import NLP_MAP

# ==========================================
# SETUP NLTK (FIX: Tambah punkt_tab)
# ==========================================
def install_nltk_dependencies():
    # Daftar resource yang wajib ada
    resources = ['punkt', 'punkt_tab']
    
    for r in resources:
        try:
            nltk.data.find(f'tokenizers/{r}')
        except LookupError:
            print(f"Downloading NLTK resource: {r}...")
            nltk.download(r)

install_nltk_dependencies()

# ------------------------------------------------
# 1. SETUP & LOAD ONTOLOGY
# ------------------------------------------------
onto_path.append("ontology")
# Pastikan nama file sesuai dengan yang di folder kamu
onto = get_ontology("ontology/L0122006-L0122056-Project.owl").load()

with onto:
    sync_reasoner_pellet(infer_property_values=True, infer_data_property_values=True)

app = Flask(__name__)

# ===================# ==========================================
# HELPER: NLP SEARCH ENGINE (UPGRADED)
# ==========================================
def nlp_search_engine(query_text):
    tokens = word_tokenize(query_text.lower())
    
    filters = {
        "target_class": None,
        "lokasi": None,
        "kategori": None,
        "waktu": None,
        "status": None,
        "relation_prop": None # Filter Baru: Properti Relasi
    }
    
    # Set untuk melacak token yang sudah terpakai sebagai objek relasi
    skip_indices = set()

    # 1. SCAN RELASI ("... dekat Hotel")
    # Kita scan dulu apakah ada kata "dekat" diikuti Tipe Tempat
    for i, token in enumerate(tokens):
        if token in NLP_MAP and NLP_MAP[token]["type"] == "relation":
            # Cek token setelahnya (Next Token)
            if i + 1 < len(tokens):
                next_token = tokens[i+1]
                if next_token in NLP_MAP and NLP_MAP[next_token]["type"] == "class":
                    # Mapping Class Target -> Nama Properti di Ontologi
                    target_obj_type = NLP_MAP[next_token]["value"] # e.g. "Hotel"
                    
                    if target_obj_type == "Hotel":
                        filters["relation_prop"] = "dekatDenganHotel"
                    elif target_obj_type == "Restoran":
                        filters["relation_prop"] = "dekatDenganRestoran"
                    elif target_obj_type == "Transportasi":
                        filters["relation_prop"] = "dekatDenganTransportasi"
                    
                    # Tandai token ini agar tidak dianggap sebagai Tipe Utama
                    skip_indices.add(i+1) 

    # 2. PARSING STANDARD
    for i, token in enumerate(tokens):
        # Skip jika token ini adalah objek dari relasi "dekat X"
        if i in skip_indices:
            continue

        if token in NLP_MAP:
            mapping = NLP_MAP[token]
            val = mapping["value"]
            typ = mapping["type"]

            if typ == "class":
                # Hanya set jika belum ada (Prioritaskan subjek di awal kalimat)
                if not filters["target_class"]: 
                    filters["target_class"] = onto[val]
            elif typ == "lokasi":
                filters["lokasi"] = val
            elif typ == "kategori":
                filters["kategori"] = val
            elif typ == "waktu":
                filters["waktu"] = val
            elif typ == "status":
                filters["status"] = val

    # 3. TENTUKAN KANDIDAT
    candidates = []
    if filters["target_class"]:
        candidates = list(filters["target_class"].instances())
    else:
        # Jika user cuma ketik "yang dekat hotel" (tanpa subjek), cari di semua tempat
        candidates = list(onto.TempatWisata.instances()) + \
                     list(onto.Restoran.instances()) + \
                     list(onto.Hotel.instances())
        candidates = list(set(candidates))

    results = []
    
    # 4. FILTERING
    for obj in candidates:
        match = True
        
        # --- Filter Lokasi ---
        if filters["lokasi"]:
            obj_loc = "-"
            if hasattr(obj, "berlokasiDi") and obj.berlokasiDi:
                loc_data = obj.berlokasiDi
                # Handle list or single value
                loc_name = loc_data[0].name if isinstance(loc_data, list) else loc_data.name
                if filters["lokasi"].lower() not in loc_name.lower().replace("_", " "):
                    match = False
            else:
                match = False

        # --- Filter Kategori ---
        if match and filters["kategori"]:
            obj_cat = []
            if hasattr(obj, "kategoriDayaTarik") and obj.kategoriDayaTarik: obj_cat.extend(obj.kategoriDayaTarik)
            if hasattr(obj, "kategoriEvent") and obj.kategoriEvent: obj_cat.extend(obj.kategoriEvent)
            if hasattr(obj, "kategoriMakanan") and obj.kategoriMakanan: obj_cat.extend(obj.kategoriMakanan)
            
            found_cat = False
            for cat in obj_cat:
                if filters["kategori"].lower() in cat.lower(): found_cat = True; break
            if not found_cat: match = False

        # --- Filter Waktu ---
        if match and (filters["waktu"] or filters["status"]):
            has_time = False
            t_waktu = filters["waktu"] if filters["waktu"] else ""
            t_status = filters["status"] if filters["status"] else ""
            for cls in obj.is_a:
                if hasattr(cls, "name"):
                    c_name = cls.name
                    if "Harian" in c_name: continue
                    if (not t_status or t_status in c_name) and (not t_waktu or t_waktu in c_name) and ("Buka" in c_name or "Tutup" in c_name):
                        has_time = True; break
            if not has_time: match = False

        # --- FILTER RELASI (BARU!) ---
        # Cek apakah objek ini punya properti 'dekatDenganX'
        if match and filters["relation_prop"]:
            # getattr akan mengambil value properti secara dinamis
            # misal: obj.dekatDenganHotel
            rel_value = getattr(obj, filters["relation_prop"], None)
            
            # Jika properti kosong atau None, berarti tidak dekat -> match False
            if not rel_value:
                match = False

        # --- HASIL ---
        if match:
            nama = obj.name.replace("_", " ")
            if hasattr(obj, "namaTempat") and obj.namaTempat: nama = obj.namaTempat[0]
            elif hasattr(obj, "namaRestoran") and obj.namaRestoran: nama = obj.namaRestoran[0]
            elif hasattr(obj, "namaHotel") and obj.namaHotel: nama = obj.namaHotel[0]
            
            lokasi_display = "-"
            if hasattr(obj, "berlokasiDi") and obj.berlokasiDi:
                 l = obj.berlokasiDi
                 if isinstance(l, list): lokasi_display = l[0].name.replace("_", " ")
                 else: lokasi_display = l.name.replace("_", " ")
            
            tipe = "Tempat Wisata"
            if onto.Hotel in obj.is_a: tipe = "Hotel"
            elif onto.Restoran in obj.is_a: tipe = "Restoran"
            elif onto.Transportasi in obj.is_a: tipe = "Transportasi"

            results.append({
                "id": obj.name,
                "nama": nama,
                "lokasi": lokasi_display,
                "tipe": tipe
            })
            
    return results, filters

# ==========================================
# ROUTE : HALAMAN PENCARIAN NLP
# ==========================================
@app.route("/search", methods=["GET", "POST"])
def search_page():
    results = []
    query = ""
    detected_filters = {}
    
    if request.method == "POST":
        query = request.form.get("query", "")
        if query:
            results, detected_filters = nlp_search_engine(query)
    
    return render_template("search_page.html", 
                           results=results, 
                           query=query, 
                           filters=detected_filters)

# ==========================================
# ROUTE: LANDING PAGE
# ==========================================
@app.route("/")
def landing():
    return render_template("landing.html")

# ================================
# ROUTE : HALAMAN ONTOLOGI (MENU 2x2)
# ================================
@app.route("/ontology")
def ontology_home():
    kategori = [
        {
            "nama": "Hotel",
            "deskripsi": "Akomodasi penginapan",
            "link": "/hotel",
            "icon": "🏨",
            "bg": "border-primary"
        },
        {
            "nama": "Tempat Wisata",
            "deskripsi": "Destinasi & Event",
            "link": "/wisata",
            "icon": "🗺️",
            "bg": "border-success"
        },
        {
            "nama": "Restoran",
            "deskripsi": "Wisata Kuliner",
            "link": "/restoran",
            "icon": "🍽️",
            "bg": "border-warning"
        },
        {
            "nama": "Transportasi",
            "deskripsi": "Transportasi Umum",
            "link": "/transportasi",
            "icon": "🚌",
            "bg": "border-info"
        }
    ]
    return render_template("ontology_home.html", kategori=kategori)


# ==========================================
# ROUTE : ONTOLOGY STRUCTURE
# ==========================================
@app.route("/ontology/structure")
def ontology_structure():
    data_class = []
    for cls in onto.classes():
        data_class.append({
            "nama": cls.name,
            "iri": cls.iri,
            "jumlah": len(cls.instances())
        })
    
    data_class.sort(key=lambda x: x["nama"])

    # [FIX] Typo: structure, bukan strucure
    return render_template("ontology_strucure.html", all_classes=data_class)


# ==========================================
# ROUTE : LIST INSTANCE PER CLASS
# ==========================================
@app.route("/ontology/class/<classname>")
def show_class_instances(classname):
    target_class = onto[classname]
    
    if not target_class:
        return f"Class {classname} tidak ditemukan", 404

    instances_data = []
    for i in target_class.instances():
        nama = i.name.replace("_", " ")
        if hasattr(i, "namaTempat") and i.namaTempat: nama = i.namaTempat[0]
        elif hasattr(i, "namaEvent") and i.namaEvent: nama = i.namaEvent[0]
        elif hasattr(i, "namaHotel") and i.namaHotel: nama = i.namaHotel[0]
        elif hasattr(i, "namaRestoran") and i.namaRestoran: nama = i.namaRestoran[0]
        
        instances_data.append({
            "id": i.name,
            "nama": nama,
            "uri": i.iri
        })

    # [FIX] Nama template harus sesuai file yg dibuat (class_instances.html)
    return render_template("classes.html", 
                           classname=classname, 
                           instances=instances_data)

# ==========================================
# ROUTE : TABEL HOTEL
# ==========================================
@app.route("/hotel")
def hotel_table():
    Hotel = onto.Hotel
    selected_bintang = request.args.get("bintang", "")
    selected_lokasi = request.args.get("lokasi", "")

    hotel_data = []
    daftar_bintang = set()
    daftar_lokasi = set()

    for h in Hotel.instances():
        nama = h.name.replace("_", " ")
        if hasattr(h, "namaHotel") and h.namaHotel: nama = h.namaHotel[0]

        lokasi = "-"
        if hasattr(h, "berlokasiDi") and h.berlokasiDi:
            loc_obj = h.berlokasiDi
            lokasi = loc_obj[0].name.replace("_", " ") if isinstance(loc_obj, list) else loc_obj.name.replace("_", " ")
            daftar_lokasi.add(lokasi)

        bintang = "-"
        if hasattr(h, "bintangHotel") and h.bintangHotel:
            val = h.bintangHotel
            bintang = str(val[0] if isinstance(val, list) else val)
        if bintang == "-":
            for cls in h.is_a:
                if hasattr(cls, "name") and "Bintang" in cls.name:
                    bintang = cls.name.replace("Hotel", "").replace("Bintang", "")
        
        if bintang != "-": daftar_bintang.add(bintang)

        rating = "-"
        if hasattr(h, "nilaiRating") and h.nilaiRating:
            val = h.nilaiRating
            rating = val[0] if isinstance(val, list) else val

        if selected_bintang and bintang != selected_bintang: continue
        if selected_lokasi and lokasi != selected_lokasi: continue
        
        bintang_display = f"{bintang} ⭐" if bintang != "-" else "-"

        hotel_data.append({"id": h.name, "nama": nama, "lokasi": lokasi, "bintang": bintang_display, "rating": rating})

    return render_template("hotel_table.html", hotels=hotel_data, daftar_bintang=sorted(list(daftar_bintang)), daftar_lokasi=sorted(list(daftar_lokasi)), selected_bintang=selected_bintang, selected_lokasi=selected_lokasi)

# ==========================================
# ROUTE: TABEL WISATA (UPDATE FILTER BUKA/TUTUP SWRL)
# ==========================================
@app.route("/wisata")
def wisata_table():
    # 1. AMBIL DATA
    list_wisata = set(onto.TempatWisata.instances())
    list_restoran = set(onto.Restoran.instances())
    semua_objek = list_wisata.union(list_restoran)

    # 2. AMBIL PARAMETER FILTER
    selected_daya_tarik = request.args.get("daya_tarik", "")
    selected_lokasi = request.args.get("lokasi", "")
    
    # Filter Baru: Buka & Tutup
    selected_buka = request.args.get("waktu_buka", "")   # ex: Pagi, Siang
    selected_tutup = request.args.get("waktu_tutup", "") # ex: Malam, Sore

    wisata_data = []
    
    # Set data untuk dropdown
    daftar_daya_tarik = set()
    daftar_lokasi = set()
    
    # List statis untuk filter waktu (sesuai class di ontologi lu)
    opsi_waktu = ["Pagi", "Siang", "Sore", "Malam"]

    for w in semua_objek:
        # --- A. Normalisasi Nama ---
        nama = w.name.replace("_", " ")
        if hasattr(w, "namaTempat") and w.namaTempat: nama = w.namaTempat[0]
        elif hasattr(w, "namaEvent") and w.namaEvent: nama = w.namaEvent[0]
        elif hasattr(w, "namaRestoran") and w.namaRestoran: nama = w.namaRestoran[0]

        # --- B. Normalisasi Kategori ---
        kategori = "-"
        if hasattr(w, "kategoriDayaTarik") and w.kategoriDayaTarik:
            val = w.kategoriDayaTarik; kategori = val[0] if isinstance(val, list) else val
        elif hasattr(w, "kategoriEvent") and w.kategoriEvent:
            val = w.kategoriEvent; kategori = val[0] if isinstance(val, list) else val
        elif hasattr(w, "kategoriMakanan") and w.kategoriMakanan:
            val = w.kategoriMakanan; kategori = val[0] if isinstance(val, list) else val
        
        if kategori != "-": daftar_daya_tarik.add(kategori)

        # --- C. Normalisasi Lokasi ---
        lokasi = "-"
        if hasattr(w, "berlokasiDi") and w.berlokasiDi:
            loc_obj = w.berlokasiDi
            lokasi = loc_obj[0].name.replace("_", " ") if isinstance(loc_obj, list) else loc_obj.name.replace("_", " ")
            daftar_lokasi.add(lokasi)

        # --- D. Rating ---
        rating = "-"
        if hasattr(w, "nilaiRating") and w.nilaiRating:
            val = w.nilaiRating; rating = val[0] if isinstance(val, list) else val

        # --- E. LOGIC SWRL BUKA/TUTUP ---
        # Kita cari Class Inferred: BukaPagi, TutupMalam, dll.
        waktu_buka = "-"
        waktu_tutup = "-"
        
        for cls in w.is_a:
            if hasattr(cls, "name"):
                c_name = cls.name
                # Cek Buka (BukaPagi, BukaSiang, dll)
                if "Buka" in c_name and "Harian" not in c_name:
                    waktu_buka = c_name.replace("Buka", "") # Ambil "Pagi"/"Siang"
                
                # Cek Tutup (TutupMalam, TutupSore, dll)
                if "Tutup" in c_name and "Harian" not in c_name:
                    waktu_tutup = c_name.replace("Tutup", "") # Ambil "Malam"/"Sore"

        # --- FILTERING ---
        if selected_daya_tarik and kategori != selected_daya_tarik: continue
        if selected_lokasi and lokasi != selected_lokasi: continue
        
        # Filter Waktu Buka (Cek apakah hasil inference 'Pagi' sama dengan filter 'Pagi')
        if selected_buka and waktu_buka != selected_buka: continue
        
        # Filter Waktu Tutup
        if selected_tutup and waktu_tutup != selected_tutup: continue

        # Append Data
        wisata_data.append({
            "id": w.name,
            "nama": nama,
            "daya_tarik": kategori,
            "rating": rating,
            "lokasi": lokasi,
            "buka": waktu_buka,   # Dikirim ke HTML buat ditampilin
            "tutup": waktu_tutup
        })

    return render_template(
        "wisata_table.html",
        wisata=wisata_data,
        daftar_daya_tarik=sorted(list(daftar_daya_tarik)),
        daftar_lokasi=sorted(list(daftar_lokasi)),
        opsi_waktu=opsi_waktu, # Kirim list ["Pagi", "Siang"...] buat dropdown
        selected_daya_tarik=selected_daya_tarik,
        selected_lokasi=selected_lokasi,
        selected_buka=selected_buka,
        selected_tutup=selected_tutup
    )

# ==========================================
# ROUTE : TABEL RESTORAN (UPDATE: 4 FILTER + SWRL)
# ==========================================
@app.route("/restoran")
def restoran_table():
    Restoran = onto.Restoran
    
    # 1. AMBIL PARAMETER FILTER
    selected_kategori = request.args.get("kategori", "")
    selected_lokasi = request.args.get("lokasi", "")
    selected_buka = request.args.get("waktu_buka", "")   # Filter SWRL Buka
    selected_tutup = request.args.get("waktu_tutup", "") # Filter SWRL Tutup

    resto_data = []
    
    # Set data untuk dropdown
    daftar_kategori = set()
    daftar_lokasi = set()
    opsi_waktu = ["Pagi", "Siang", "Sore", "Malam"] # Opsi hardcoded sesuai class ontologi

    for r in Restoran.instances():
        # --- A. Normalisasi Nama ---
        nama = r.name.replace("_", " ")
        if hasattr(r, "namaRestoran") and r.namaRestoran:
            nama = r.namaRestoran[0]
        
        # --- B. Kategori Makanan ---
        kategori = "-"
        if hasattr(r, "kategoriMakanan") and r.kategoriMakanan:
            val = r.kategoriMakanan
            kategori = val[0] if isinstance(val, list) else val
            daftar_kategori.add(kategori)

        # --- C. Lokasi ---
        lokasi = "-"
        if hasattr(r, "berlokasiDi") and r.berlokasiDi:
            loc = r.berlokasiDi
            # Handle list/single object
            if isinstance(loc, list):
                 lokasi = loc[0].name.replace("_", " ")
            else:
                 lokasi = loc.name.replace("_", " ")
            daftar_lokasi.add(lokasi)

        # --- D. Rating ---
        rating = "-"
        if hasattr(r, "nilaiRating") and r.nilaiRating:
            val = r.nilaiRating
            rating = val[0] if isinstance(val, list) else val

        # --- E. LOGIC SWRL BUKA/TUTUP ---
        waktu_buka = "-"
        waktu_tutup = "-"
        
        for cls in r.is_a:
            if hasattr(cls, "name"):
                c_name = cls.name
                # Cari class inferred (misal: BukaPagi, TutupMalam)
                if "Buka" in c_name and "Harian" not in c_name:
                    waktu_buka = c_name.replace("Buka", "")
                if "Tutup" in c_name and "Harian" not in c_name:
                    waktu_tutup = c_name.replace("Tutup", "")

        # --- FILTERING ---
        if selected_kategori and kategori != selected_kategori: continue
        if selected_lokasi and lokasi != selected_lokasi: continue
        if selected_buka and waktu_buka != selected_buka: continue
        if selected_tutup and waktu_tutup != selected_tutup: continue

        resto_data.append({
            "id": r.name,
            "nama": nama,
            "kategori": kategori,
            "lokasi": lokasi,
            "rating": rating,
            "buka": waktu_buka,
            "tutup": waktu_tutup
        })

    return render_template("resto_table.html", 
                           restos=resto_data,
                           daftar_kategori=sorted(list(daftar_kategori)),
                           daftar_lokasi=sorted(list(daftar_lokasi)),
                           opsi_waktu=opsi_waktu,
                           selected_kategori=selected_kategori,
                           selected_lokasi=selected_lokasi,
                           selected_buka=selected_buka,
                           selected_tutup=selected_tutup)

# ==========================================
# ROUTE : TABEL TRANSPORTASI
# ==========================================
@app.route("/transportasi")
def transport_table():
    Transport = onto.Transportasi
    transport_data = []
    ignored_classes = ["Transportasi", "TransportasiUmum", "Thing", "TutupMalam", "TutupPagi", "TutupSore", "TutupSiang", "BukaPagi", "BukaSiang", "BukaSore", "BukaMalam", "WaktuBukaHarian", "WaktuTutupHarian"]

    for t in Transport.instances():
        nama = t.name.replace("_", " ")
        if hasattr(t, "namaTransportasi") and t.namaTransportasi: nama = t.namaTransportasi[0]
        
        jenis = "Transportasi Umum"
        for cls in t.is_a:
            if hasattr(cls, "name") and cls.name not in ignored_classes:
                 jenis = cls.name.replace("_", " ")
        
        jam = "-"
        buka = t.jamBuka[0] if hasattr(t, "jamBuka") and t.jamBuka else None
        tutup = t.jamTutup[0] if hasattr(t, "jamTutup") and t.jamTutup else None
        
        if buka is not None and tutup is not None:
            def fmt_jam(j): return f"{str(int(j)).zfill(4)[:2]}:{str(int(j)).zfill(4)[2:]}"
            jam = f"{fmt_jam(buka)} - {fmt_jam(tutup)} WIB"

        transport_data.append({"id": t.name, "nama": nama, "jenis": jenis, "jam": jam})

    return render_template("transport_table.html", transports=transport_data)

# ==========================================
# ROUTE : DETAIL INSTANCE
# ==========================================
@app.route("/instance/<instancename>")
def show_instance_detail(instancename):
    instance = onto.search_one(iri=f"*{instancename}")
    if not instance: return f"Instance '{instancename}' tidak ditemukan.", 404

    nama = instance.name.replace("_", " ")
    for attr in ["namaTempat", "namaEvent", "namaRestoran", "namaHotel", "namaTransportasi"]:
        if hasattr(instance, attr) and getattr(instance, attr): nama = getattr(instance, attr)[0]; break

    lokasi = "-"
    if hasattr(instance, "berlokasiDi") and instance.berlokasiDi:
         loc = instance.berlokasiDi
         lokasi = loc[0].name.replace("_", " ") if isinstance(loc, list) else loc.name.replace("_", " ")

    fasilitas = []
    if hasattr(instance, "memilikiFasilitas"):
        for f in instance.memilikiFasilitas: fasilitas.append(f.name.replace("_", " "))

    rating = "-"
    if hasattr(instance, "nilaiRating") and instance.nilaiRating:
         val = instance.nilaiRating; rating = val[0] if isinstance(val, list) else val

    if isinstance(instance, onto.Hotel):
        bintang = "-"
        for cls in instance.is_a:
            if hasattr(cls, "name") and "Bintang" in cls.name: bintang = cls.name.replace("Hotel", "").replace("Bintang", " ⭐")
        return render_template("hotel_detail.html", nama=nama, lokasi=lokasi, fasilitas=fasilitas, rating=rating, bintang=bintang)

    elif isinstance(instance, onto.Restoran):
        return render_template("resto_detail.html", nama=nama, lokasi=lokasi, fasilitas=fasilitas, rating=rating)

    elif isinstance(instance, onto.Transportasi):
        jam = "-"
        buka = instance.jamBuka[0] if hasattr(instance, "jamBuka") and instance.jamBuka else None
        tutup = instance.jamTutup[0] if hasattr(instance, "jamTutup") and instance.jamTutup else None
        if buka is not None and tutup is not None:
             b_str = str(int(buka)).zfill(4); t_str = str(int(tutup)).zfill(4)
             jam = f"{b_str[:2]}:{b_str[2:]} - {t_str[:2]}:{t_str[2:]} WIB"

        jenis = "Transportasi Umum"
        ignored = ["Transportasi", "TransportasiUmum", "Thing", "TutupMalam", "TutupPagi", "TutupSore", "TutupSiang", "BukaPagi", "BukaSiang", "BukaSore", "BukaMalam", "WaktuBukaHarian", "WaktuTutupHarian"]
        for cls in instance.is_a:
             if hasattr(cls, "name") and cls.name not in ignored: jenis = cls.name.replace("_", " ")
        return render_template("transport_detail.html", nama=nama, jam=jam, jenis=jenis)

    else:
        daya_tarik = "-"
        if hasattr(instance, "kategoriDayaTarik") and instance.kategoriDayaTarik: daya_tarik = instance.kategoriDayaTarik[0]
        elif hasattr(instance, "kategoriEvent") and instance.kategoriEvent: daya_tarik = instance.kategoriEvent[0]
        if daya_tarik == "-":
             for cls in instance.is_a:
                 if hasattr(cls, "name") and cls.name.startswith("Wisata") and cls.name != "TempatWisata": daya_tarik = cls.name.replace("Wisata", "")
        return render_template("wisata_detail.html", nama=nama, lokasi=lokasi, fasilitas=fasilitas, rating=rating, daya_tarik=daya_tarik, tipe="Objek Wisata")

if __name__ == "__main__":
    app.run(debug=True)