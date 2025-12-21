# ===========================================
# app.py – Flask + Owlready2 Ontology Viewer
# ===========================================

from flask import Flask, render_template
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
        hotel = onto[instancename]
    except KeyError:
        return f"Instance '{instancename}' tidak ditemukan."

    # -----------------------------
    # Ambil informasi utama
    # -----------------------------
    nama = hotel.name

    # Lokasi
    lokasi = "-"
    if hasattr(hotel, "berlokasiDi") and hotel.berlokasiDi:
        lokasi = hotel.berlokasiDi.name

    # Kategori bintang (dari class)
    bintang = "-"
    for cls in hotel.is_a:
        if "Bintang" in cls.name:
            bintang = cls.name.replace("Hotel", "").replace("Bintang", " ⭐")

    # -----------------------------
    # Ambil fasilitas (object property)
    # -----------------------------
    fasilitas = []
    if hasattr(hotel, "memilikiFasilitas"):
        for f in hotel.memilikiFasilitas:
            fasilitas.append(f.name)

    # -----------------------------
    # Ambil rating (jika ada)
    # -----------------------------
    rating = "-"
    # Cek apakah properti ada dan tidak kosong (None)
    if hasattr(hotel, "nilaiRating") and hotel.nilaiRating is not None:
        raw_val = hotel.nilaiRating
        # Cek apakah hasilnya berupa List (jika property TIDAK Functional)
        if isinstance(raw_val, list):
            if len(raw_val) > 0:
                rating = raw_val[0]
        # Jika hasilnya langsung Angka/Float (jika property Functional)
        else:
            rating = raw_val

    # rating = r.name if hasattr(r, "name") else str(r)

    return render_template(
        "hotel_detail.html",
        nama=nama,
        lokasi=lokasi,
        bintang=bintang,
        fasilitas=fasilitas,
        rating=rating
    )

# ==========================================
# ROUTE : ONTOLOGY SELURUH CLASS
# ==========================================
@app.route("/ontology/structure")
def ontology_structure():
    all_classes = list(onto.classes())
    return render_template("ontology_strucure.html", all_classes=all_classes)


# ------------------------------------------------
# RUN FLASK SERVER
# ------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)
