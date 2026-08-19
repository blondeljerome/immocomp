import os
import sqlite3
import libsql_experimental as libsql

def get_connection():
    # Détection des identifiants cloud
    url = os.getenv("TURSO_DATABASE_URL")
    auth_token = os.getenv("TURSO_AUTH_TOKEN")
    
    if url and auth_token:
        # Connexion à Turso (Cloud)
        return libsql.connect(database=url, auth_token=auth_token)
    else:
        # Connexion locale de secours (SQLite local)
        return sqlite3.connect("database.db")

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
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
    ''')
    conn.commit()
    conn.close()

def load_properties():
    conn = get_connection()
    import pandas as pd
    df = pd.read_sql_query("SELECT * FROM properties", conn)
    conn.close()
    return df

def save_property(data):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO properties (nom, ville, prix_achat, frais_notaire, travaux, loyer_mensuel, charges_annuelles, taxe_fonciere, apport, taux_credit, duree_credit, irl_annuel)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        data['nom'], data['ville'], data['prix_achat'], data['frais_notaire'],
        data['travaux'], data['loyer_mensuel'], data['charges_annuelles'],
        data['taxe_fonciere'], data['apport'], data['taux_credit'],
        data['duree_credit'], data['irl_annuel']
    ))
    conn.commit()
    conn.close()

def delete_property(prop_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM properties WHERE id = ?", (prop_id,))
    conn.commit()
    conn.close()