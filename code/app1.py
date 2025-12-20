# ===========================================
# app.py – Flask + Owlready2 Ontology Viewer
# ===========================================

from flask import Flask, render_template
from owlready2 import *

# ------------------------------------------------
# 1. LOAD ONTOLOGY
# ------------------------------------------------
onto_path.append("ontology")  # Folder tempat file OWL berada
onto = get_ontology("ontology/L0122006-Project-Ver2.owx").load()

# Jalankan reasoner agar hasil inference ikut terbaca
with onto:
    sync_reasoner()

# ------------------------------------------------
# 2. INISIASI FLASK
# ------------------------------------------------
app = Flask(__name__)

# Ambil class penting dari ontology
# Fasilitas = onto.search_one(iri="*Fasilitas")
# Hotel = onto.search_one(iri="*Hotel")
# TempatWisata = onto.search_one(iri="*TempatWisata")

# -----------------------------
# 3. ROUTE HOME (Halaman Utama)
# -----------------------------
@app.route("/")
def home():
    # Fasilitas = onto.search_one(iri=".*#TempatWisata$") 
    Fasilitas = onto.search_one(iri="*Fasilitas")

    all_fasilitas = list(Fasilitas.instances())
    # all_fasilitas = list(onto.Fasilitas.instances()) #munculin instances pake IRI yang sama
    # for f in all_fasilitas:
    #     print(f'f: {f}')
        # for prop in f.get_properties(f):
        #     values = prop[f]  # ambil target values
        #     print(f"Property: {prop.name}")
        #     for v in values:
        #         print("  ->", v.name)

    return render_template("home.html", all_fasilitas=all_fasilitas)

# -----------------------------
# 6. Menjalankan Server Flask
# -----------------------------
if __name__ == "__main__":
    app.run(debug=True)


# INI ADALAH CODE BARU UNTUK COBA COBA