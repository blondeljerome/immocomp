import sqlite3
import pandas as pd

DB_FILE = "data.db"

def init_db():
    """Crée la table des biens immobiliers si elle n'existe pas."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS properties (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL,
            ville TEXT,
            prix_achat REAL,
            frais_notaire REAL,
            travaux REAL,
            loyer_mensuel REAL,
            charges_annuelles REAL,
            taxe_fonciere REAL,
            apport REAL,
            taux_credit REAL,
            duree_credit INTEGER,
            irl_annuel REAL
        )
    """)
    conn.commit()
    conn.close()

def load_properties():
    """Charge tous les biens sous forme de DataFrame Pandas."""
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM properties", conn)
    conn.close()
    return df

def save_property(data):
    """Ajoute ou met à jour un bien immobilier."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    if data.get("id"):
        # Modification
        cursor.execute("""
            UPDATE properties SET 
            nom=?, ville=?, prix_achat=?, frais_notaire=?, travaux=?,
            loyer_mensuel=?, charges_annuelles=?, taxe_fonciere=?,
            apport=?, taux_credit=?, duree_credit=?, irl_annuel=?
            WHERE id=?
        """, (
            data['nom'], data['ville'], data['prix_achat'], data['frais_notaire'],
            data['travaux'], data['loyer_mensuel'], data['charges_annuelles'],
            data['taxe_fonciere'], data['apport'], data['taux_credit'],
            data['duree_credit'], data['irl_annuel'], data['id']
        ))
    else:
        # Insertion
        cursor.execute("""
            INSERT INTO properties (
                nom, ville, prix_achat, frais_notaire, travaux,
                loyer_mensuel, charges_annuelles, taxe_fonciere,
                apport, taux_credit, duree_credit, irl_annuel
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data['nom'], data['ville'], data['prix_achat'], data['frais_notaire'],
            data['travaux'], data['loyer_mensuel'], data['charges_annuelles'],
            data['taxe_fonciere'], data['apport'], data['taux_credit'],
            data['duree_credit'], data['irl_annuel']
        ))
    conn.commit()
    conn.close()

def delete_property(property_id):
    """Supprime un bien par son ID."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM properties WHERE id=?", (property_id,))
    conn.commit()
    conn.close()