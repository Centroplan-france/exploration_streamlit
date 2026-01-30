"""
Dashboard Sites PV - Streamlit + Supabase
Gestion des sites photovoltaïques (consultation + édition)
"""

import streamlit as st
import pandas as pd
from supabase import create_client

# =============================================================================
# Configuration
# =============================================================================

st.set_page_config(
    page_title="Sites PV - Dashboard",
    page_icon="☀️",
    layout="wide"
)

# =============================================================================
# Connexion Supabase
# =============================================================================

@st.cache_resource
def get_supabase_client():
    """Initialise le client Supabase (connexion unique)"""
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    return create_client(url, key)

supabase = get_supabase_client()

# =============================================================================
# Fonctions de données
# =============================================================================

@st.cache_data(ttl=60)  # Cache 60 secondes
def charger_sites():
    """Charge tous les sites depuis Supabase"""
    response = supabase.table("sites_mapping").select(
        "id, name, code, nominal_power, address, commission_date, client_map_id, ignore_site"
    ).eq("ignore_site", False).order("name").execute()
    return response.data

@st.cache_data(ttl=300)  # Cache 5 minutes
def charger_clients():
    """Charge les clients pour le filtre"""
    response = supabase.table("clients_mapping").select("id, name").order("name").execute()
    return {c["id"]: c["name"] for c in response.data}

def sauvegarder_site(site_id: int, data: dict):
    """Met à jour un site"""
    response = supabase.table("sites_mapping").update(data).eq("id", site_id).execute()
    # Invalider le cache
    charger_sites.clear()
    return response.data

def ajouter_site(data: dict):
    """Ajoute un nouveau site"""
    response = supabase.table("sites_mapping").insert(data).execute()
    charger_sites.clear()
    return response.data

# =============================================================================
# Interface
# =============================================================================

st.title("☀️ Dashboard Sites PV")

# Charger les données
sites = charger_sites()
clients = charger_clients()

if not sites:
    st.warning("Aucun site trouvé dans la base.")
    st.stop()

# Convertir en DataFrame pour faciliter le filtrage
df = pd.DataFrame(sites)
df["client_name"] = df["client_map_id"].map(clients).fillna("Non assigné")

# -----------------------------------------------------------------------------
# Sidebar : Filtres
# -----------------------------------------------------------------------------

st.sidebar.header("Filtres")

# Filtre par client
clients_uniques = ["Tous"] + sorted(df["client_name"].dropna().unique().tolist())
filtre_client = st.sidebar.selectbox("Client", clients_uniques)

# Filtre par puissance
puissance_min = st.sidebar.number_input(
    "Puissance min (kWc)", 
    min_value=0.0, 
    value=0.0,
    step=10.0
)
puissance_max = st.sidebar.number_input(
    "Puissance max (kWc)", 
    min_value=0.0, 
    value=float(df["nominal_power"].max() or 10000),
    step=10.0
)

# Appliquer filtres
df_filtre = df.copy()
if filtre_client != "Tous":
    df_filtre = df_filtre[df_filtre["client_name"] == filtre_client]
df_filtre = df_filtre[
    (df_filtre["nominal_power"].fillna(0) >= puissance_min) &
    (df_filtre["nominal_power"].fillna(0) <= puissance_max)
]

# -----------------------------------------------------------------------------
# Onglets principaux
# -----------------------------------------------------------------------------

tab_liste, tab_edit, tab_ajout = st.tabs(["📋 Liste des sites", "✏️ Modifier un site", "➕ Ajouter un site"])

# -----------------------------------------------------------------------------
# Tab 1 : Liste des sites
# -----------------------------------------------------------------------------

with tab_liste:
    st.subheader(f"Sites ({len(df_filtre)} résultats)")
    
    # Colonnes à afficher
    colonnes_affichage = ["name", "code", "nominal_power", "address", "client_name", "commission_date"]
    colonnes_renommees = {
        "name": "Nom",
        "code": "Code",
        "nominal_power": "Puissance (kWc)",
        "address": "Adresse",
        "client_name": "Client",
        "commission_date": "Mise en service"
    }
    
    df_affichage = df_filtre[colonnes_affichage].rename(columns=colonnes_renommees)
    
    st.dataframe(
        df_affichage,
        use_container_width=True,
        hide_index=True
    )
    
    # Export CSV
    if st.button("📥 Exporter en CSV"):
        csv = df_affichage.to_csv(index=False)
        st.download_button(
            label="Télécharger",
            data=csv,
            file_name="sites_pv.csv",
            mime="text/csv"
        )

# -----------------------------------------------------------------------------
# Tab 2 : Modifier un site
# -----------------------------------------------------------------------------

with tab_edit:
    st.subheader("Modifier un site existant")
    
    # Sélection du site
    sites_options = {f"{s['name']} ({s['code']})": s for s in df_filtre.to_dict('records')}
    
    if not sites_options:
        st.info("Aucun site à afficher avec les filtres actuels.")
    else:
        site_choisi = st.selectbox(
            "Sélectionner un site",
            options=list(sites_options.keys()),
            key="edit_select"
        )
        
        site = sites_options[site_choisi]
        
        st.divider()
        
        # Formulaire d'édition
        with st.form("form_edit"):
            col1, col2 = st.columns(2)
            
            with col1:
                new_name = st.text_input("Nom", value=site["name"] or "")
                new_code = st.text_input("Code", value=site["code"] or "")
                new_power = st.number_input(
                    "Puissance (kWc)", 
                    value=float(site["nominal_power"] or 0),
                    min_value=0.0,
                    step=1.0
                )
            
            with col2:
                new_address = st.text_area("Adresse", value=site["address"] or "")
                new_date = st.date_input(
                    "Date mise en service",
                    value=pd.to_datetime(site["commission_date"]).date() if site["commission_date"] else None
                )
            
            submitted = st.form_submit_button("💾 Sauvegarder", type="primary")
            
            if submitted:
                update_data = {
                    "name": new_name,
                    "code": new_code,
                    "nominal_power": new_power,
                    "address": new_address,
                    "commission_date": new_date.isoformat() if new_date else None
                }
                try:
                    sauvegarder_site(site["id"], update_data)
                    st.success(f"Site '{new_name}' mis à jour !")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erreur lors de la sauvegarde : {e}")

# -----------------------------------------------------------------------------
# Tab 3 : Ajouter un site
# -----------------------------------------------------------------------------

with tab_ajout:
    st.subheader("Ajouter un nouveau site")
    
    with st.form("form_ajout"):
        col1, col2 = st.columns(2)
        
        with col1:
            add_name = st.text_input("Nom *")
            add_code = st.text_input("Code")
            add_power = st.number_input(
                "Puissance (kWc)", 
                value=0.0,
                min_value=0.0,
                step=1.0
            )
        
        with col2:
            add_address = st.text_area("Adresse")
            add_date = st.date_input("Date mise en service", value=None)
            
            # Sélection client
            clients_list = [("", "-- Aucun --")] + [(str(k), v) for k, v in clients.items()]
            add_client = st.selectbox(
                "Client",
                options=[c[0] for c in clients_list],
                format_func=lambda x: dict(clients_list).get(x, "")
            )
        
        submitted = st.form_submit_button("➕ Ajouter le site", type="primary")
        
        if submitted:
            if not add_name:
                st.error("Le nom est obligatoire.")
            else:
                insert_data = {
                    "name": add_name,
                    "code": add_code or None,
                    "nominal_power": add_power or None,
                    "address": add_address or None,
                    "commission_date": add_date.isoformat() if add_date else None,
                    "client_map_id": int(add_client) if add_client else None
                }
                try:
                    ajouter_site(insert_data)
                    st.success(f"Site '{add_name}' ajouté !")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erreur lors de l'ajout : {e}")

# -----------------------------------------------------------------------------
# Footer
# -----------------------------------------------------------------------------

st.divider()
st.caption("Dashboard Centroplan - Streamlit + Supabase")
