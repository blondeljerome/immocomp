import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from database import init_db, load_properties, save_property, update_property, delete_property

st.set_page_config(page_title="Comparateur Studio - SCI à l'IS", layout="wide")
init_db()

st.title("🏢 Real Estate Analyzer - Simulation Spéciale SCI à l'IS")

def calculate_metrics_sci_is(df):
    if df.empty:
        return df, pd.DataFrame()

    df['cout_projet'] = df['prix_achat'] + df['frais_notaire'] + df['travaux'] + df['meubles']
    df['emprunt'] = df['cout_projet'] - df['apport']

    def calc_pmt(row):
        r = (row['taux_credit'] / 100) / 12
        n = row['duree_credit'] * 12
        p = row['emprunt']
        if r == 0:
            return p / n
        return p * (r * (1 + r)**n) / ((1 + r)**n - 1)

    df['mensualite_credit'] = df.apply(calc_pmt, axis=1)

    cf_yearly_list = []

    def process_20y_sci(row):
        # Paramètres d'amortissement IS
        valeur_bati = (row['prix_achat'] + row['frais_notaire']) * (1 - row['part_terrain_pct'] / 100)
        amort_bati_annuel = valeur_bati / 30.0  # Amortissement immobilier sur 30 ans
        amort_travaux_annuel = row['travaux'] / 10.0 if row['travaux'] > 0 else 0  # Amortissement travaux 10 ans
        amort_meubles_annuel = row['meubles'] / 5.0 if row['meubles'] > 0 else 0  # Amortissement meubles 5 ans

        solde_capital = row['emprunt']
        taux_mensuel = (row['taux_credit'] / 100) / 12

        total_cf_apres_is = 0
        cumul_cf = 0

        for y in range(1, 21):
            # Intérêts et amortissement du capital sur l'année
            interets_annee = 0
            capital_amorti_annee = 0
            for _ in range(12):
                if solde_capital > 0:
                    i_mois = solde_capital * taux_mensuel
                    c_mois = row['mensualite_credit'] - i_mois
                    interets_annee += i_mois
                    capital_amorti_annee += c_mois
                    solde_capital -= c_mois
                    if solde_capital < 0:
                        solde_capital = 0

            # Prise en compte de la vacance locative
            mois_loues = 12 - (row['vacance_semaines'] / 4.33)
            loyer_annuel_brut = (row['loyer_mensuel'] * mois_loues) * ((1 + row['irl_annuel'] / 100) ** (y - 1))

            charges_exploit = row['charges_annuelles'] + row['taxe_fonciere'] + row['assurance_pno'] + row['frais_compta']
            
            # Amortissements fiscaux applicables
            amort_actuel = amort_bati_annuel
            if y <= 10:
                amort_actuel += amort_travaux_annuel
            if y <= 5:
                amort_actuel += amort_meubles_annuel

            # Résultat fiscal IS
            resultat_imposable = loyer_annuel_brut - charges_exploit - interets_annee - amort_actuel
            
            # Impôt IS à 15% (Tranche réduite < 42 500 €)
            impot_is = max(0.0, resultat_imposable * 0.15) if resultat_imposable > 0 else 0.0

            # Cash-Flow Trésorerie Réelle de la SCI
            cf_tresorerie_annee = loyer_annuel_brut - charges_exploit - (row['mensualite_credit'] * 12) - impot_is
            total_cf_apres_is += cf_tresorerie_annee
            cumul_cf += cf_tresorerie_annee

            cf_yearly_list.append({
                "Annee": y,
                "Bien": f"ID {row['id']} - {row['nom']}",
                "CashFlow_Net_IS": cf_tresorerie_annee,
                "Cumul_CashFlow_IS": cumul_cf,
                "Impot_IS_Paye": impot_is,
                "Amortissement_Deductible": amort_actuel
            })

        return total_cf_apres_is

    df['cf_20ans_apres_is'] = df.apply(process_20y_sci, axis=1)
    df_cf_details = pd.DataFrame(cf_yearly_list)

    # Calculs pour Année 1
    df['loyer_net_vacance_y1'] = df['loyer_mensuel'] * (12 - (df['vacance_semaines'] / 4.33))
    df['renta_brute'] = (df['loyer_net_vacance_y1'] / df['cout_projet']) * 100
    df['renta_nette'] = ((df['loyer_net_vacance_y1'] - df['charges_annuelles'] - df['taxe_fonciere'] - df['assurance_pno'] - df['frais_compta']) / df['cout_projet']) * 100
    
    # Cash-flow mensuel moyen Y1 après IS
    df_y1 = df_cf_details[df_cf_details['Annee'] == 1].set_index("Bien")
    df['cf_mensuel_y1_is'] = df.apply(lambda r: df_y1.loc[f"ID {r['id']} - {r['nom']}", "CashFlow_Net_IS"] / 12, axis=1)

    return df, df_cf_details

df_raw = load_properties()
df, df_cf_details = calculate_metrics_sci_is(df_raw)

# --- MENU LATÉRAL ---
st.sidebar.header("➕ Nouveau Studio (SCI IS)")
with st.sidebar.form("form_add", clear_on_submit=True):
    nom = st.text_input("Nom du bien (ex: Studio Gare)")
    ville = st.text_input("Ville")
    
    c1, c2 = st.columns(2)
    with c1:
        prix_achat = st.number_input("Prix d'achat (€)", min_value=0.0, value=90000.0, step=2000.0)
        frais_notaire = st.number_input("Notaire (€)", min_value=0.0, value=7500.0, step=500.0)
        travaux = st.number_input("Travaux (€)", min_value=0.0, value=8000.0, step=1000.0)
        meubles = st.number_input("Mobilier & Équipement (€)", min_value=0.0, value=3000.0, step=500.0)
        loyer_mensuel = st.number_input("Loyer Mensuel Cible (€)", min_value=0.0, value=580.0, step=20.0)
        vacance_semaines = st.number_input("Vacance (Semaines / An)", min_value=0, max_value=20, value=2)

    with c2:
        charges = st.number_input("Charges Copro Non Récup. (€/an)", min_value=0.0, value=450.0, step=50.0)
        taxe_f = st.number_input("Taxe Foncière (€/an)", min_value=0.0, value=500.0, step=50.0)
        assurance_pno = st.number_input("Assurance PNO (€/an)", min_value=0.0, value=120.0, step=10.0)
        frais_compta = st.number_input("Comptabilité SCI (€/an)", min_value=0.0, value=500.0, step=50.0)
        apport = st.number_input("Apport (€)", min_value=0.0, value=10000.0, step=1000.0)
        taux = st.number_input("Taux Crédit (%)", min_value=0.0, value=3.6, step=0.1)

    duree = st.number_input("Durée Crédit (ans)", min_value=1, max_value=30, value=20)
    irl = st.number_input("Indexation Loyer IRL (%/an)", min_value=0.0, value=1.5, step=0.1)
    part_terrain = st.number_input("Part Terrain Non Amortissable (%)", min_value=0.0, max_value=50.0, value=15.0, step=1.0)

    btn_add = st.form_submit_button("Ajouter à la SCI")
    if btn_add and nom:
        save_property({
            "nom": nom, "ville": ville, "prix_achat": prix_achat, "frais_notaire": frais_notaire,
            "travaux": travaux, "meubles": meubles, "loyer_mensuel": loyer_mensuel,
            "charges_annuelles": charges, "taxe_fonciere": taxe_f, "assurance_pno": assurance_pno,
            "frais_compta": frais_compta, "vacance_semaines": vacance_semaines, "apport": apport,
            "taux_credit": taux, "duree_credit": duree, "irl_annuel": irl, "part_terrain_pct": part_terrain
        })
        st.success("Studio sauvegardé !")
        st.rerun()

# --- TABLEAU DE BORD ---
if not df.empty:
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Max Renta Nette (A1)", f"{df['renta_nette'].max():.2f} %")
    k2.metric("Meilleur Cash-Flow Mensuel IS (A1)", f"{df['cf_mensuel_y1_is'].max():.0f} €")
    k3.metric("Renta Nette Moyenne", f"{df['renta_nette'].mean():.2f} %")
    k4.metric("Max Cash-Flow Cumulé 20 Ans (IS)", f"{df['cf_20ans_apres_is'].max():,.0f} €".replace(",", " "))

    st.markdown("---")

    st.subheader("📊 Comparatif Général (Après Fiscalité IS)")
    ch1, ch2 = st.columns(2)
    with ch1:
        fig1 = px.bar(df, x="nom", y="renta_nette", color="renta_nette", title="Rentabilité Nette Année 1 (%)")
        st.plotly_chart(fig1, use_container_width=True)
    with ch2:
        fig2 = px.bar(df, x="nom", y="cf_20ans_apres_is", color="cf_20ans_apres_is", title="Cash-Flow Cumulé Réel 20 Ans dans la SCI (€)")
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("---")

    st.subheader("📈 Projection de Trésorerie SCI sur 20 Ans")
    
    fig_annuel = px.line(
        df_cf_details, x="Annee", y="CashFlow_Net_IS", color="Bien", markers=True,
        title="Trésorerie Annuelle Nette d'Impôt IS (€)", height=550
    )
    st.plotly_chart(fig_annuel, use_container_width=True)

    fig_cumul = px.line(
        df_cf_details, x="Annee", y="Cumul_CashFlow_IS", color="Bien", markers=True,
        title="Trésorerie Cumulée Conservée dans la SCI (€)", height=550
    )
    st.plotly_chart(fig_cumul, use_container_width=True)

    st.markdown("---")

    st.subheader("📋 Tableau Synthétique SCI")
    st.dataframe(
        df[["id", "nom", "ville", "prix_achat", "cout_projet", "loyer_mensuel", "renta_brute", "renta_nette", "cf_mensuel_y1_is", "cf_20ans_apres_is"]],
        column_config={
            "prix_achat": st.column_config.NumberColumn("Prix Achat", format="%.0f €"),
            "cout_projet": st.column_config.NumberColumn("Coût Total Projet", format="%.0f €"),
            "loyer_mensuel": st.column_config.NumberColumn("Loyer/Mois Cible", format="%.0f €"),
            "renta_brute": st.column_config.NumberColumn("Renta Brute", format="%.2f %%"),
            "renta_nette": st.column_config.NumberColumn("Renta Nette", format="%.2f %%"),
            "cf_mensuel_y1_is": st.column_config.NumberColumn("CF Net/Mois (A1)", format="%.0f €"),
            "cf_20ans_apres_is": st.column_config.NumberColumn("CF Cumulé 20 Ans IS", format="%.0f €")
        },
        use_container_width=True
    )

    st.markdown("---")

    # --- ÉDITION ET SUPPRESSION ---
    st.subheader("⚙️ Modifier / Supprimer un Studio")
    options_dict = {f"ID {row['id']} - {row['nom']} ({row['ville']})": int(row['id']) for _, row in df.iterrows()}
    
    with st.expander("✏️ Modifier un studio"):
        sel_edit = st.selectbox("Sélectionner le studio", options=list(options_dict.keys()), key="edit_sel")
        edit_id = options_dict[sel_edit]
        b = df[df['id'] == edit_id].iloc[0]
        
        with st.form("form_edit"):
            u_nom = st.text_input("Nom", value=str(b['nom']))
            u_ville = st.text_input("Ville", value=str(b['ville']))
            
            uc1, uc2 = st.columns(2)
            with uc1:
                u_prix = st.number_input("Prix d'achat (€)", value=float(b['prix_achat']))
                u_notaire = st.number_input("Notaire (€)", value=float(b['frais_notaire']))
                u_travaux = st.number_input("Travaux (€)", value=float(b['travaux']))
                u_meubles = st.number_input("Meubles (€)", value=float(b['meubles']))
                u_loyer = st.number_input("Loyer Mensuel (€)", value=float(b['loyer_mensuel']))
                u_vacance = st.number_input("Vacance (semaines)", value=int(b['vacance_semaines']))
            with uc2:
                u_charges = st.number_input("Charges Copro (€/an)", value=float(b['charges_annuelles']))
                u_tf = st.number_input("Taxe Foncière (€/an)", value=float(b['taxe_fonciere']))
                u_pno = st.number_input("Assurance PNO (€/an)", value=float(b['assurance_pno']))
                u_compta = st.number_input("Comptabilité (€/an)", value=float(b['frais_compta']))
                u_apport = st.number_input("Apport (€)", value=float(b['apport']))
                u_taux = st.number_input("Taux Crédit (%)", value=float(b['taux_credit']))
            
            u_duree = st.number_input("Durée Crédit (ans)", value=int(b['duree_credit']))
            u_irl = st.number_input("Indexation IRL (%)", value=float(b['irl_annuel']))
            u_terrain = st.number_input("Part Terrain (%)", value=float(b['part_terrain_pct']))

            if st.form_submit_button("Enregistrer les modifications"):
                update_property(edit_id, {
                    "nom": u_nom, "ville": u_ville, "prix_achat": u_prix, "frais_notaire": u_notaire,
                    "travaux": u_travaux, "meubles": u_meubles, "loyer_mensuel": u_loyer,
                    "charges_annuelles": u_charges, "taxe_fonciere": u_tf, "assurance_pno": u_pno,
                    "frais_compta": u_compta, "vacance_semaines": u_vacance, "apport": u_apport,
                    "taux_credit": u_taux, "duree_credit": u_duree, "irl_annuel": u_irl, "part_terrain_pct": u_terrain
                })
                st.success("Données du studio mises à jour !")
                st.rerun()

    with st.expander("🗑️ Supprimer un studio"):
        sel_del = st.selectbox("Sélectionner le studio à supprimer", options=list(options_dict.keys()), key="del_sel")
        if st.button("Confirmer la suppression", type="primary"):
            delete_property(options_dict[sel_del])
            st.success("Studio supprimé.")
            st.rerun()
else:
    st.info("Aucun studio enregistré. Ajoutez-en un depuis le menu latéral.")