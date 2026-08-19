import os
import sqlite3
import pandas as pd
import streamlit as st
import libsql_client

def get_turso_client():
    """Vérifie si les clés Turso sont présentes et retourne un client Turso, sinon None."""
    url = None
    auth_token = None

    if "TURSO_DATABASE_URL" in st.secrets and "TURSO_AUTH_TOKEN" in st.secrets:
        url = st.secrets["TURSO_DATABASE_URL"]
        auth_token = st.secrets["TURSO_AUTH_TOKEN"]
    elif os.getenv("TURSO_DATABASE_URL") and os.getenv("TURSO_AUTH_TOKEN"):
        url = os.getenv("TURSO_DATABASE_URL")
        auth_token = os.getenv("TURSO_AUTH_TOKEN")

    if url and auth_token:
        # Convertit 'libsql://' en 'https://' si nécessaire pour libsql-client
        if url.startswith("libsql://"):
            url = url.replace("libsql://", "https://")
        return libsql_client.create_client_sync(url=url, auth_token=auth_token)
    return None

def init_db():
    client = get_turso_client()
    query = '''
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
    '''
    if client:
        client.execute(query)
        client.close()
    else:
        conn = sqlite3.connect("database.db")
        conn.execute(query)
        conn.commit()
        conn.close()

def load_properties():
    client = get_turso_client()
    if client:
        rs = client.execute("SELECT * FROM properties")
        client.close()
        # Conversion des résultats Turso en DataFrame Pandas
        columns = rs.columns
        rows = [list(r) for r in rs.rows]
        return pd.DataFrame(rows, columns=columns)
    else:
        conn = sqlite3.connect("database.db")
        df = pd.read_sql_query("SELECT * FROM properties", conn)
        conn.close()
        return df

def save_property(data):
    client = get_turso_client()
    query = '''
        INSERT INTO properties (nom, ville, prix_achat, frais_notaire, travaux, loyer_mensuel, charges_annuelles, taxe_fonciere, apport, taux_credit, duree_credit, irl_annuel)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    '''
    params = (
        data['nom'], data['ville'], data['prix_achat'], data['frais_notaire'],
        data['travaux'], data['loyer_mensuel'], data['charges_annuelles'],
        data['taxe_fonciere'], data['apport'], data['taux_credit'],
        data['duree_credit'], data['irl_annuel']
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