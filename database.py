import os
import sqlite3
import pandas as pd
import streamlit as st
import libsql_client
import ssl
import certifi

# Correctif SSL macOS / Cloud
ssl_context = ssl.create_default_context(cafile=certifi.where())
ssl._create_default_https_context = lambda: ssl_context

def get_turso_client():
    url = None
    auth_token = None

    if "TURSO_DATABASE_URL" in st.secrets and "TURSO_AUTH_TOKEN" in st.secrets:
        url = st.secrets["TURSO_DATABASE_URL"]
        auth_token = st.secrets["TURSO_AUTH_TOKEN"]
    elif os.getenv("TURSO_DATABASE_URL") and os.getenv("TURSO_AUTH_TOKEN"):
        url = os.getenv("TURSO_DATABASE_URL")
        auth_token = os.getenv("TURSO_AUTH_TOKEN")

    if url and auth_token:
        if url.startswith("libsql://"):
            url = url.replace("libsql://", "https://")
        return libsql_client.create_client_sync(url=url, auth_token=auth_token)
    return None

def init_db():
    client = get_turso_client()
    query_create = '''
        CREATE TABLE IF NOT EXISTS properties (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL,
            ville TEXT,
            prix_achat REAL,
            frais_notaire REAL,
            travaux REAL,
            meubles REAL DEFAULT 0,
            loyer_mensuel REAL,
            charges_annuelles REAL,
            taxe_fonciere REAL,
            assurance_pno REAL DEFAULT 120,
            frais_compta REAL DEFAULT 500,
            vacance_semaines INTEGER DEFAULT 2,
            apport REAL DEFAULT 0,
            taux_credit REAL DEFAULT 3.5,
            duree_credit INTEGER DEFAULT 20,
            irl_annuel REAL DEFAULT 1.5,
            part_terrain_pct REAL DEFAULT 15.0
        )
    '''
    
    # Colonnes à ajouter automatiquement sur les bases existantes si absentes
    migrations = [
        ("meubles", "REAL DEFAULT 0"),
        ("assurance_pno", "REAL DEFAULT 120"),
        ("frais_compta", "REAL DEFAULT 500"),
        ("vacance_semaines", "INTEGER DEFAULT 2"),
        ("apport", "REAL DEFAULT 0"),
        ("taux_credit", "REAL DEFAULT 3.5"),
        ("duree_credit", "INTEGER DEFAULT 20"),
        ("irl_annuel", "REAL DEFAULT 1.5"),
        ("part_terrain_pct", "REAL DEFAULT 15.0")
    ]

    if client:
        client.execute(query_create)
        for col, col_type in migrations:
            try:
                client.execute(f"ALTER TABLE properties ADD COLUMN {col} {col_type}")
            except Exception:
                pass  # La colonne existe déjà
        client.close()
    else:
        conn = sqlite3.connect("database.db")
        conn.execute(query_create)
        cursor = conn.cursor()
        for col, col_type in migrations:
            try:
                cursor.execute(f"ALTER TABLE properties ADD COLUMN {col} {col_type}")
            except sqlite3.OperationalError:
                pass  # La colonne existe déjà
        conn.commit()
        conn.close()

def load_properties():
    client = get_turso_client()
    if client:
        rs = client.execute("SELECT * FROM properties")
        client.close()
        columns = rs.columns
        rows = [list(r) for r in rs.rows]
        df = pd.DataFrame(rows, columns=columns)
    else:
        conn = sqlite3.connect("database.db")
        df = pd.read_sql_query("SELECT * FROM properties", conn)
        conn.close()

    # Sécurité supplémentaire : s'assurer que toutes les colonnes requises existent dans le DataFrame
    defaults = {
        'meubles': 0.0, 'assurance_pno': 120.0, 'frais_compta': 500.0,
        'vacance_semaines': 2, 'apport': 0.0, 'taux_credit': 3.5,
        'duree_credit': 20, 'irl_annuel': 1.5, 'part_terrain_pct': 15.0
    }
    for col, default_val in defaults.items():
        if col not in df.columns:
            df[col] = default_val

    return df

def save_property(data):
    client = get_turso_client()
    query = '''
        INSERT INTO properties (
            nom, ville, prix_achat, frais_notaire, travaux, meubles,
            loyer_mensuel, charges_annuelles, taxe_fonciere, assurance_pno,
            frais_compta, vacance_semaines, apport, taux_credit, duree_credit,
            irl_annuel, part_terrain_pct
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    '''
    params = (
        data['nom'], data['ville'], float(data['prix_achat']), float(data['frais_notaire']),
        float(data['travaux']), float(data['meubles']), float(data['loyer_mensuel']),
        float(data['charges_annuelles']), float(data['taxe_fonciere']), float(data['assurance_pno']),
        float(data['frais_compta']), int(data['vacance_semaines']), float(data['apport']),
        float(data['taux_credit']), int(data['duree_credit']), float(data['irl_annuel']),
        float(data['part_terrain_pct'])
    )
    if client:
        client.execute(query, params)
        client.close()
    else:
        conn = sqlite3.connect("database.db")
        conn.execute(query, params)
        conn.commit()
        conn.close()

def update_property(prop_id, data):
    client = get_turso_client()
    query = '''
        UPDATE properties
        SET nom = ?, ville = ?, prix_achat = ?, frais_notaire = ?, travaux = ?, meubles = ?,
            loyer_mensuel = ?, charges_annuelles = ?, taxe_fonciere = ?, assurance_pno = ?,
            frais_compta = ?, vacance_semaines = ?, apport = ?, taux_credit = ?,
            duree_credit = ?, irl_annuel = ?, part_terrain_pct = ?
        WHERE id = ?
    '''
    params = (
        data['nom'], data['ville'], float(data['prix_achat']), float(data['frais_notaire']),
        float(data['travaux']), float(data['meubles']), float(data['loyer_mensuel']),
        float(data['charges_annuelles']), float(data['taxe_fonciere']), float(data['assurance_pno']),
        float(data['frais_compta']), int(data['vacance_semaines']), float(data['apport']),
        float(data['taux_credit']), int(data['duree_credit']), float(data['irl_annuel']),
        float(data['part_terrain_pct']), int(prop_id)
    )
    if client:
        client.execute(query, params)
        client.close()
    else:
        conn = sqlite3.connect("database.db")
        conn.execute(query, params)
        conn.commit()
        conn.close()

def delete_property(prop_id):
    client = get_turso_client()
    query = "DELETE FROM properties WHERE id = ?"
    if client:
        client.execute(query, (prop_id,))
        client.close()
    else:
        conn = sqlite3.connect("database.db")
        conn.execute(query, (prop_id,))
        conn.commit()
        conn.close()