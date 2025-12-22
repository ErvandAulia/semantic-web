# ===========================================
# app.py – Flask + Owlready2 Ontology Viewer
# ===========================================

from flask import Flask, render_template, request
from owlready2 import *

# ------------------------------------------------
# LOAD ONTOLOGY
# ------------------------------------------------
onto_path.append("ontology")  # Folder tempat file OWL berada
onto = get_ontology("ontology/L0122006-L0122056-Project.owl").load()

# Jalankan reasoner agar hasil inference ikut terbaca
with onto:
    sync_reasoner_pellet(infer_property_values = True, infer_data_property_values = True)

# ------------------------------------------------
# INISIASI FLASK
# ------------------------------------------------
app = Flask(__name__)

# print("Ontology loaded:", onto)
# print("Jumlah class:", len(list(onto.classes())))
# for c in onto.classes():
#     print(" -", c.name)

# ================================
# ROUTE : LANDING PAGE
# ================================
@app.route("/")
def landing():
    return render_template("landing.html")


# ================================
# ROUTE : HALAMAN ONTOLOGI
# ================================
@app.route("/ontology")
def ontology_home():
    kategori = [
        {
            "nama": "Hotel",
            "deskripsi": "Akomodasi wisata seperti hotel dan penginapan",
            "link": "/hotel",
            "icon": "🏨"
        },
        {
            "nama": "Tempat Wisata",
            "deskripsi": "Destinasi wisata alam, budaya, sejarah, dan edukasi",
            "link": "/wisata",
            "icon": "🗺️"
        },
        {
            "nama": "Restoran",
            "deskripsi": "Kuliner tradisional, modern, dan cepat saji",
            "link": "/restoran",
            "icon": "🍽️"
        },
        {
            "nama": "Event",
            "deskripsi": "Event budaya, religi, dan hiburan",
            "link": "/event",
            "icon": "🎉"
        },
        {
            "nama": "Transportasi",
            "deskripsi": "Transportasi umum dan online",
            "link": "/transportasi",
            "icon": "🚗"
        }
    ]

    return render_template("ontology_home.html", kategori=kategori)


# ------------------------------------------------
# ROUTE : LIST INSTANCES PER-CLASS
# Contoh: /class/Fasilitas
# ------------------------------------------------
@app.route("/class/<classname>")
def show_instances(classname):
    try:
        onto_class = onto[classname]     # mengambil class berdasarkan nama
    except KeyError:
        return f"Class '{classname}' tidak ditemukan dalam ontology."

    instances = list(onto_class.instances())
    return render_template("instances.html", classname=classname, instances=instances)

# ==========================================
# ROUTE : TABEL HOTEL
# ==========================================
@app.route("/hotel")
def hotel_table():
    Hotel = onto.Hotel

    hotel_data = []

    for h in Hotel.instances():
        # Nama hotel
        nama = h.name

        # Lokasi (object property)
        lokasi = "-"
        if hasattr(h, "berlokasiDi") and h.berlokasiDi:
            lokasi = h.berlokasiDi.name
        # Kategori bintang (dari class)
        bintang = "-"
        for cls in h.is_a:
            if "Bintang" in cls.name:
                bintang = cls.name.replace("Hotel", "").replace("Bintang", "⭐")
        
        hotel_data.append({
            "nama": nama,
            "lokasi": lokasi,
            "bintang": bintang,
            "id": h.name
        })

    return render_template("hotel_table.html", hotels=hotel_data)

@app.route("/instance/<instancename>")
def show_instance_detail(instancename):
    try:
        instance = onto[instancename]
    except KeyError:
        return f"Instance '{instancename}' tidak ditemukan."

    # =====================================================
    # CASE 1: HOTEL
    # =====================================================
    if onto.Hotel in instance.is_a:

        nama = instance.name

        # Lokasi
        lokasi = "-"
        if hasattr(instance, "berlokasiDi") and instance.berlokasiDi:
            lokasi = instance.berlokasiDi.name

        # Bintang (dari class)
        bintang = "-"
        for cls in instance.is_a:
            if "Bintang" in cls.name:
                bintang = cls.name.replace("Hotel", "").replace("Bintang", " ⭐")
                break

        # Fasilitas
        fasilitas = []
        if hasattr(instance, "memilikiFasilitas"):
            for f in instance.memilikiFasilitas:
                fasilitas.append(f.name)

        # Rating
        rating = "-"
        if hasattr(instance, "nilaiRating") and instance.nilaiRating is not None:
            raw_val = instance.nilaiRating
            if isinstance(raw_val, list):
                if len(raw_val) > 0:
                    rating = raw_val[0]
            else:
                rating = raw_val

        return render_template(
            "hotel_detail.html",
            nama=nama,
            lokasi=lokasi,
            bintang=bintang,
            fasilitas=fasilitas,
            rating=rating
        )

    # =====================================================
    # CASE 2: TEMPAT WISATA
    # =====================================================
    if onto.TempatWisata in instance.is_a:

        nama = instance.name

        # Lokasi
        lokasi = "-"
        if hasattr(instance, "berlokasiDi") and instance.berlokasiDi:
            lokasi = instance.berlokasiDi.name

        # -----------------------------
        # Daya Tarik (HASIL REASONING)
        # -----------------------------
        daya_tarik = "-"
        for cls in instance.is_a:
            if cls.name.startswith("Wisata"):
                daya_tarik = cls.name.replace("Wisata", "")
                break

        # Rating
        rating = "-"
        if hasattr(instance, "nilaiRating") and instance.nilaiRating is not None:
            raw_val = instance.nilaiRating
            if isinstance(raw_val, list):
                if len(raw_val) > 0:
                    rating = raw_val[0]
            else:
                rating = raw_val

        # Fasilitas
        fasilitas = []
        if hasattr(instance, "memilikiFasilitas"):
            for f in instance.memilikiFasilitas:
                fasilitas.append(f.name)

        return render_template(
            "wisata_detail.html",
            nama=nama,
            lokasi=lokasi,
            daya_tarik=daya_tarik,
            rating=rating,
            fasilitas=fasilitas
        )

    # =====================================================
    # FALLBACK
    # =====================================================
    return "Tipe instance belum didukung."

# ==========================================
# ROUTE : ONTOLOGY SELURUH CLASS
# ==========================================
@app.route("/ontology/structure")
def ontology_structure():
    all_classes = list(onto.classes())
    return render_template("ontology_strucure.html", all_classes=all_classes)

# ==========================================
# ROUTE : TABEL TEMPAT WISATA
# ==========================================
@app.route("/wisata")
def wisata_table():
    TempatWisata = onto.TempatWisata

    # =========================
    # Ambil parameter filter
    # =========================
    selected_daya_tarik = request.args.get("daya_tarik", "")
    selected_lokasi = request.args.get("lokasi", "")

    wisata_data = []
    daftar_daya_tarik = set()
    daftar_lokasi = set()

    for w in TempatWisata.instances():

        # -----------------------------
        # Nama
        # -----------------------------
        nama = w.name

        # -----------------------------
        # Daya Tarik (data property)
        # -----------------------------
        daya_tarik = "-"

        if hasattr(w, "kategoriDayaTarik") and w.kategoriDayaTarik:
            raw_dt = w.kategoriDayaTarik
            if isinstance(raw_dt, list):
                daya_tarik = raw_dt[0]
            else:
                daya_tarik = raw_dt

        if daya_tarik != "-":
            daftar_daya_tarik.add(daya_tarik)

        # -----------------------------
        # Lokasi (object property)
        # -----------------------------
        lokasi = "-"

        if hasattr(w, "berlokasiDi") and w.berlokasiDi:
            lokasi = w.berlokasiDi.name
            daftar_lokasi.add(lokasi)

        # -----------------------------
        # Rating (data property)
        # -----------------------------
        rating = "-"

        if hasattr(w, "nilaiRating") and w.nilaiRating is not None:
            raw_rating = w.nilaiRating
            if isinstance(raw_rating, list):
                if len(raw_rating) > 0:
                    rating = raw_rating[0]
            else:
                rating = raw_rating

        # -----------------------------
        # FILTERING
        # -----------------------------
        if selected_daya_tarik and daya_tarik != selected_daya_tarik:
            continue

        if selected_lokasi and lokasi != selected_lokasi:
            continue

        # -----------------------------
        # Tambahkan ke tabel
        # -----------------------------
        wisata_data.append({
            "id": w.name,
            "nama": nama,
            "daya_tarik": daya_tarik,
            "rating": rating,
            "lokasi": lokasi
        })

    return render_template(
        "wisata_table.html",
        wisata=wisata_data,
        daftar_daya_tarik=sorted(daftar_daya_tarik),
        daftar_lokasi=sorted(daftar_lokasi),
        selected_daya_tarik=selected_daya_tarik,
        selected_lokasi=selected_lokasi
    )

# ------------------------------------------------
# RUN FLASK SERVER
# ------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)
