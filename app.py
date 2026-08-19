import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from database import init_db, load_properties, save_property, update_property, delete_property

# Configuration de la page
st.set_page_config(page_title="Comparateur Immobilier Pro", layout="wide")
init_db()

st.title("🏠 Real Estate Analyzer & Comparateur 20 Ans")

# --- CALCULS FINANCIERS ---
def calculate_metrics(df):
    if df.empty:
        return df, pd.DataFrame()
    
    # Coût total
    df['cout_total'] = df['prix_achat'] + df['frais_notaire'] + df['travaux']
    df['emprunt'] = df['cout_total'] - df['apport']
    
    # Mensualité crédit
    def pmt(row):
        r = (row['taux_credit'] / 100) / 12
        n = row['duree_credit'] * 12
        p = row['emprunt']
        if r == 0:
            return p / n
        return p * (r * (1 + r)**n) / ((1 + r)**n - 1)
        
    df['mensualite'] = df.apply(pmt, axis=1)
    
    # Rentabilités Y1
    df['renta_brute'] = (df['loyer_mensuel'] * 12) / df['cout_total'] * 100
    df['renta_nette'] = ((df['loyer_mensuel'] * 12) - df['charges_annuelles'] - df['taxe_fonciere']) / df['cout_total'] * 100
    df['cash_flow_mois'] = df['loyer_mensuel'] - df['mensualite'] - (df['charges_annuelles'] / 12) - (df['taxe_fonciere'] / 12)
    
    # Calcul détaillé sur 20 ans
    cf_yearly_list = []
    
    def cf_cumule_20ans(row):
        total_cf = 0
        cumul_acc = 0
        for y in range(1, 21):
            loyer_y = (row['loyer_mensuel'] * 12) * ((1 + row['irl_annuel'] / 100) ** (y - 1))
            cf_y = loyer_y - (row['mensualite'] * 12) - row['charges_annuelles'] - row['taxe_fonciere']
            total_cf += cf_y
            cumul_acc += cf_y
            
            cf_yearly_list.append({
                "Annee": y,
                "Bien": f"ID {row['id']} - {row['nom']}",
                "CashFlow_Annuel": cf_y,
                "CashFlow_Cumule": cumul_acc
            })
        return total_cf

    df['cf_cumule_20ans'] = df.apply(cf_cumule_20ans, axis=1)
    df_cf_details = pd.DataFrame(cf_yearly_list)
    
    return df, df_cf_details

df_raw = load_properties()
df, df_cf_details = calculate_metrics(df_raw)

# --- MENU LATÉRAL (AJOUT D'UN BIEN) ---
st.sidebar.header("➕ Ajouter un Bien")
with st.sidebar.form("property_form", clear_on_submit=True):
    nom = st.text_input("Nom du bien (ex: T2 Hypercentre)")
    ville = st.text_input("Ville")
    
    col1, col2 = st.columns(2)
    with col1:
        prix_achat = st.number_input("Prix d'achat (€)", min_value=0.0, value=120000.0, step=5000.0)
        frais_notaire = st.number_input("Notaire (€)", min_value=0.0, value=9000.0, step=500.0)
        travaux = st.number_input("Travaux (€)", min_value=0.0, value=10000.0, step=1000.0)
        loyer_mensuel = st.number_input("Loyer Mensuel (€)", min_value=0.0, value=700.0, step=50.0)
    
    with col2:
        charges = st.number_input("Charges / An (€)", min_value=0.0, value=800.0, step=100.0)
        taxe_f = st.number_input("Taxe Foncière / An (€)", min_value=0.0, value=650.0, step=50.0)
        apport = st.number_input("Apport (€)", min_value=0.0, value=15000.0, step=1000.0)
        taux = st.number_input("Taux Crédit (%)", min_value=0.0, value=3.5, step=0.1)
    
    duree = st.number_input("Durée Emprunt (ans)", min_value=1, max_value=30, value=20)
    irl = st.number_input("Indexation IRL / An (%)", min_value=0.0, max_value=10.0, value=1.5, step=0.1)
    
    submitted = st.form_submit_button("Sauvegarder le Bien")
    if submitted and nom:
        new_data = {
            "nom": nom, "ville": ville, "prix_achat": prix_achat, "frais_notaire": frais_notaire,
            "travaux": travaux, "loyer_mensuel": loyer_mensuel, "charges_annuelles": charges,
            "taxe_fonciere": taxe_f, "apport": apport, "taux_credit": taux,
            "duree_credit": duree, "irl_annuel": irl
        }
        save_property(new_data)
        st.success("Bien enregistré avec succès !")
        st.rerun()

# --- TABLEAU DE BORD ---
if not df.empty:
    # 1. KPIs
    col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)
    col_kpi1.metric("Meilleure Renta Nette", f"{df['renta_nette'].max():.2f} %")
    col_kpi2.metric("Max Cash-Flow / Mois", f"{df['cash_flow_mois'].max():.0f} €")
    col_kpi3.metric("Renta Nette Moyenne", f"{df['renta_nette'].mean():.2f} %")
    col_kpi4.metric("Max CF Cumulé 20 Ans", f"{df['cf_cumule_20ans'].max():,.0f} €".replace(",", " "))

    st.markdown("---")

    # 2. Graphiques Globaux
    st.subheader("📊 Comparatif Global")
    col_chart1, col_chart2 = st.columns(2)
    with col_chart1:
        fig1 = px.bar(df, x="nom", y="renta_nette", color="renta_nette", 
                      title="Rentabilité Nette par Bien (%)", labels={"nom": "Bien", "renta_nette": "Renta Nette (%)"})
        st.plotly_chart(fig1, use_container_width=True)

    with col_chart2:
        fig2 = px.bar(df, x="nom", y="cf_cumule_20ans", color="cf_cumule_20ans",
                      title="Cash-Flow Cumulé sur 20 Ans avec IRL (€)", labels={"nom": "Bien", "cf_cumule_20ans": "CF 20 Ans (€)"})
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("---")

    # 3. GRAPHIQUES AGRANDIS : ÉVOLUTION DU CASH-FLOW SUR 20 ANS
    st.subheader("📈 Évolution et Détails du Cash-Flow sur 20 Ans")
    
    # Graphique 1 : Cash-Flow Annuel (Pleine Largeur & Hauteur 600px)
    fig_cf_annuel = px.line(
        df_cf_details, x="Annee", y="CashFlow_Annuel", color="Bien", markers=True,
        title="Évolution du Cash-Flow Annuel par Bien (€)",
        labels={"Annee": "Année", "CashFlow_Annuel": "Cash-Flow Annuel (€)"},
        height=600
    )
    fig_cf_annuel.update_layout(hovermode="x unified")
    st.plotly_chart(fig_cf_annuel, use_container_width=True)

    # Graphique 2 : Cash-Flow Cumulé (Pleine Largeur & Hauteur 600px)
    fig_cf_cumule = px.line(
        df_cf_details, x="Annee", y="CashFlow_Cumule", color="Bien", markers=True,
        title="Progression du Cash-Flow Cumulé sur 20 Ans (€)",
        labels={"Annee": "Année", "CashFlow_Cumule": "Cumul (€)"},
        height=600
    )
    fig_cf_cumule.update_layout(hovermode="x unified")
    st.plotly_chart(fig_cf_cumule, use_container_width=True)

    st.markdown("---")

    # 4. Tableau complet
    st.subheader("📋 Classement et Détails des Biens")
    st.dataframe(
        df[["id", "nom", "ville", "prix_achat", "cout_total", "loyer_mensuel", "renta_brute", "renta_nette", "cash_flow_mois", "cf_cumule_20ans"]],
        column_config={
            "id": st.column_config.NumberColumn("ID", format="%d"),
            "prix_achat": st.column_config.NumberColumn("Prix Achat", format="%.0f €"),
            "cout_total": st.column_config.NumberColumn("Coût Total", format="%.0f €"),
            "loyer_mensuel": st.column_config.NumberColumn("Loyer/Mois", format="%.0f €"),
            "renta_brute": st.column_config.NumberColumn("Renta Brute", format="%.2f %%"),
            "renta_nette": st.column_config.NumberColumn("Renta Nette", format="%.2f %%"),
            "cash_flow_mois": st.column_config.NumberColumn("CF/Mois Y1", format="%.0f €"),
            "cf_cumule_20ans": st.column_config.NumberColumn("CF 20 Ans", format="%.0f €")
        },
        use_container_width=True
    )

    st.markdown("---")

    # 5. GESTION DES BIENS (MODIFICATION & SUPPRESSION)
    st.subheader("⚙️ Gestion des Biens")
    
    options_dict = {f"ID {row['id']} - {row['nom']} ({row['ville']})": int(row['id']) for _, row in df.iterrows()}
    
    # SECTION MODIFICATION
    with st.expander("✏️ Modifier un bien"):
        selected_edit_label = st.selectbox("Choisir le bien à modifier", options=list(options_dict.keys()), key="select_edit")
        edit_id = options_dict[selected_edit_label]
        
        bien = df[df['id'] == edit_id].iloc[0]
        
        with st.form("edit_form"):
            u_nom = st.text_input("Nom du bien", value=str(bien['nom']))
            u_ville = st.text_input("Ville", value=str(bien['ville']))
            
            uc1, uc2 = st.columns(2)
            with uc1:
                u_prix_achat = st.number_input("Prix d'achat (€)", min_value=0.0, value=float(bien['prix_achat']), step=5000.0)
                u_frais_notaire = st.number_input("Notaire (€)", min_value=0.0, value=float(bien['frais_notaire']), step=500.0)
                u_travaux = st.number_input("Travaux (€)", min_value=0.0, value=float(bien['travaux']), step=1000.0)
                u_loyer_mensuel = st.number_input("Loyer Mensuel (€)", min_value=0.0, value=float(bien['loyer_mensuel']), step=50.0)
            
            with uc2:
                u_charges = st.number_input("Charges / An (€)", min_value=0.0, value=float(bien['charges_annuelles']), step=100.0)
                u_taxe_f = st.number_input("Taxe Foncière / An (€)", min_value=0.0, value=float(bien['taxe_fonciere']), step=50.0)
                u_apport = st.number_input("Apport (€)", min_value=0.0, value=float(bien['apport']), step=1000.0)
                u_taux = st.number_input("Taux Crédit (%)", min_value=0.0, value=float(bien['taux_credit']), step=0.1)
            
            u_duree = st.number_input("Durée Emprunt (ans)", min_value=1, max_value=30, value=int(bien['duree_credit']))
            u_irl = st.number_input("Indexation IRL / An (%)", min_value=0.0, max_value=10.0, value=float(bien['irl_annuel']), step=0.1)
            
            update_btn = st.form_submit_button("💾 Enregistrer les modifications", type="primary")
            if update_btn and u_nom:
                updated_data = {
                    "nom": u_nom, "ville": u_ville, "prix_achat": u_prix_achat,
                    "frais_notaire": u_frais_notaire, "travaux": u_travaux,
                    "loyer_mensuel": u_loyer_mensuel, "charges_annuelles": u_charges,
                    "taxe_fonciere": u_taxe_f, "apport": u_apport, "taux_credit": u_taux,
                    "duree_credit": u_duree, "irl_annuel": u_irl
                }
                update_property(edit_id, updated_data)
                st.success("Bien mis à jour avec succès !")
                st.rerun()

    # SECTION SUPPRESSION
    with st.expander("🗑️ Supprimer un bien"):
        selected_del_label = st.selectbox("Choisir le bien à supprimer", options=list(options_dict.keys()), key="select_del")
        
        if st.button("Confirmer la suppression", type="primary"):
            id_to_del = options_dict[selected_del_label]
            delete_property(id_to_del)
            st.success("Bien supprimé avec succès.")
            st.rerun()
else:
    st.info("Aucun bien enregistré pour le moment. Utilisez le panneau latéral pour en ajouter.")