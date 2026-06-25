import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# Configuration de la page
st.set_page_config(layout="wide", page_title="Studio Cloud Workspace", page_icon="🎬")

st.title("🎬 Studio Cloud Workspace")
st.caption("Base de données d'équipe synchronisée en temps réel avec Google Sheets")

# 1. CONNEXION ET CHARGEMENT DES DONNÉES
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    try:
        df_videos = conn.read(worksheet="videos", ttl=0)
        df_clients = conn.read(worksheet="clients", ttl=0)
        df_staff = conn.read(worksheet="staff", ttl=0)
        
        # S'assurer que les colonnes nécessaires existent
        for col in ['id', 'title', 'clientId', 'staffId', 'platform', 'date', 'status', 'link']:
            if col not in df_videos.columns:
                df_videos[col] = ""
        return df_videos, df_clients, df_staff
    except Exception as e:
        # Dataframes par défaut si les feuilles sont complètement vides
        df_v = pd.DataFrame(columns=['id', 'title', 'clientId', 'staffId', 'platform', 'date', 'status', 'link'])
        df_c = pd.DataFrame(columns=['id', 'name', 'color'])
        df_s = pd.DataFrame(columns=['id', 'name'])
        return df_v, df_c, df_s

df_videos, df_clients, df_staff = load_data()

# Nettoyage des NaN pour éviter les bugs d'affichage
df_videos = df_videos.fillna("")
df_clients = df_clients.fillna("")
df_staff = df_staff.fillna("")

# Création de dictionnaires pour correspondance rapide ID -> Nom
client_dict = dict(zip(df_clients['id'], df_clients['name'])) if not df_clients.empty else {}
staff_dict = dict(zip(df_staff['id'], df_staff['name'])) if not df_staff.empty else {}

# 2. BARRE LATÉRALE - CONFIGURATION CLIENTS & STAFF
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # Onglet interne Configuration
    conf_tab = st.radio("Gérer :", ["Restaurateurs (Clients)", "Équipe / Staff"])
    
    if conf_tab == "Restaurateurs (Clients)":
        st.subheader("Ajouter un Client")
        with st.form("add_client_form", clear_on_submit=True):
            new_c_name = st.text_input("Nom du restaurant *")
            new_c_color = st.color_picker("Couleur de marquage", "#6366f1")
            if st.form_submit_button("Ajouter", use_container_width=True):
                if new_c_name:
                    new_c = pd.DataFrame([{'id': f"c_{int(datetime.now().timestamp())}", 'name': new_c_name, 'color': new_c_color}])
                    df_clients = pd.concat([df_clients, new_c], ignore_index=True)
                    conn.update(worksheet="clients", data=df_clients)
                    st.success(f"{new_c_name} ajouté !")
                    st.rerun()
                    
        st.subheader("Liste des Clients")
        for idx, row in df_clients.iterrows():
            st.text(f"• {row['name']}")

    elif conf_tab == "Équipe / Staff":
        st.subheader("Ajouter un Membre")
        with st.form("add_staff_form", clear_on_submit=True):
            new_s_name = st.text_input("Nom du collaborateur *")
            if st.form_submit_button("Ajouter", use_container_width=True):
                if new_s_name:
                    new_s = pd.DataFrame([{'id': f"s_{int(datetime.now().timestamp())}", 'name': new_s_name}])
                    df_staff = pd.concat([df_staff, new_s], ignore_index=True)
                    conn.update(worksheet="staff", data=df_staff)
                    st.success(f"{new_s_name} ajouté !")
                    st.rerun()
                    
        st.subheader("Membres de l'équipe")
        for idx, row in df_staff.iterrows():
            st.text(f"• {row['name']}")

# 3. ONGLETS DE NAVIGATION PRINCIPAUX
tab_pipeline, tab_calendar, tab_actions = st.tabs(["📊 Pipeline (Kanban)", "📅 Calendrier de Publication", "➕ Ajouter / Modifier"])

# STYLES VISUELS POUR SIMULER DES CARTES KANBAN
st.markdown("""
    <style>
    .kanban-card {
        background-color: #1e293b;
        border-radius: 10px;
        padding: 12px;
        margin-bottom: 10px;
        border-left: 5px solid #6366f1;
    }
    .platform-badge {
        background-color: #334155;
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 10px;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# --- ONGLET 1 : PIPELINE / KANBAN ---
with tab_pipeline:
    # Définition des colonnes du workflow
    statuses = {
        "pool": "⏳ Pool d'attente",
        "montage": "🎬 En cours de montage",
        "validation": "👀 À valider",
        "attente-prog": "⏸️ En attente de Prog",
        "programme": "📅 Programmées"
    }
    
    cols = st.columns(len(statuses))
    
    for i, (status_key, status_label) in enumerate(statuses.items()):
        with cols[i]:
            st.markdown(f"### {status_label}")
            # Filtrer les vidéos pour ce statut
            vids_in_status = df_videos[df_videos['status'] == status_key]
            st.caption(f"{len(vids_in_status)} vidéo(s)")
            
            for _, vid in vids_in_status.iterrows():
                client_name = client_dict.get(vid['clientId'], "Inconnu")
                staff_name = staff_dict.get(vid['staffId'], "Non assigné")
                date_str = f" | 🗓️ {vid['date']}" if vid['date'] else ""
                
                # Rendu visuel propre
                st.markdown(f"""
                <div class="kanban-card">
                    <div style="display:flex; justify-content:space-between; margin-bottom:4px;">
                        <span class="platform-badge">{vid['platform']}</span>
                        <span style="font-size:11px; font-weight:bold; color:#a7f3d0;">{client_name}</span>
                    </div>
                    <strong style="font-size:13px; color:white;">{vid['title']}</strong><br>
                    <span style="font-size:11px; color:#94a3b8;">👤 {staff_name}{date_str}</span>
                </div>
                """, unsafe_allow_html=True)
                
                # Bouton natif pour changer rapidement de statut ou éditer
                if st.button("Changer le statut ⚙️", key=f"btn_move_{vid['id']}"):
                    st.info(f"Modifie la vidéo '**{vid['title']}**' dans l'onglet 'Ajouter / Modifier'")

# --- ONGLET 2 : CALENDRIER ---
with tab_calendar:
    st.subheader("Publications programmées")
    vids_programmed = df_videos[df_videos['status'] == "programme"].copy()
    if not vids_programmed.empty:
        # Recréer un affichage propre sous forme de liste chronologique claire
        vids_programmed['Restaurateur'] = vids_programmed['clientId'].map(client_dict)
        vids_programmed['Assigné à'] = vids_programmed['staffId'].map(staff_dict)
        
        # Tri par date de publication
        vids_programmed = vids_programmed.sort_values(by='date')
        
        st.dataframe(
            vids_programmed[['date', 'title', 'Restaurateur', 'Assigné à', 'platform', 'link']],
            column_config={
                "date": "Date de Publication",
                "title": "Titre de la Vidéo",
                "link": st.column_config.LinkColumn("Lien Drive/Livraison")
            },
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("Aucune vidéo n'est actuellement programmée avec une date précise.")

# --- ONGLET 3 : ACTIONS (AJOUTER / MODIFIER) ---
with tab_actions:
    act_mode = st.radio("Action :", ["Ajouter une vidéo", "Création groupée (Bulk)", "Modifier / Supprimer une vidéo"], horizontal=True)
    
    client_options = {row['id']: row['name'] for _, row in df_clients.iterrows()}
    staff_options = {"": "Non assigné"}
    for _, row in df_staff.iterrows():
        staff_options[row['id']] = row['name']
        
    if act_mode == "Ajouter une vidéo":
        if not client_options:
            st.warning("Veuillez d'abord ajouter un client dans la barre latérale.")
        else:
            with st.form("add_video_form", clear_on_submit=True):
                title = st.text_input("Titre de la vidéo *")
                c_id = st.selectbox("Restaurateur *", options=list(client_options.keys()), format_func=lambda x: client_options[x])
                s_id = st.selectbox("Assigner à", options=list(staff_options.keys()), format_func=lambda x: staff_options[x])
                platform = st.selectbox("Réseau Principal", ["TikTok", "Instagram", "Les deux"])
                status = st.selectbox("Étape du Workflow", list(statuses.keys()), format_func=lambda x: statuses[x])
                pub_date = st.date_input("Date de publication (Optionnel)", value=None)
                drive_link = st.text_input("Lien Drive / Livraison", placeholder="https://...")
                
                if st.form_submit_button("Enregistrer la vidéo", use_container_width=True):
                    if title:
                        new_vid = {
                            'id': str(int(datetime.now().timestamp())),
                            'title': title,
                            'clientId': c_id,
                            'staffId': s_id,
                            'platform': platform,
                            'date': str(pub_date) if pub_date else "",
                            'status': status,
                            'link': drive_link if drive_link else "#"
                        }
                        df_videos = pd.concat([df_videos, pd.DataFrame([new_vid])], ignore_index=True)
                        conn.update(worksheet="videos", data=df_videos)
                        st.success(f"Vidéo '{title}' enregistrée avec succès dans la base partagée !")
                        st.rerun()

    elif act_mode == "Création groupée (Bulk)":
        if not client_options:
            st.warning("Veuillez d'abord ajouter un client.")
        else:
            with st.form("bulk_form", clear_on_submit=True):
                c_id = st.selectbox("Restaurateur *", options=list(client_options.keys()), format_func=lambda x: client_options[x])
                platform = st.selectbox("Réseau Principal", ["TikTok", "Instagram", "Les deux"])
                bulk_titles = st.text_area("Titres des vidéos (un titre par ligne) *", placeholder="Concept Vidéo 1\nConcept Vidéo 2")
                
                if st.form_submit_button("Générer les vidéos", use_container_width=True):
                    if bulk_titles:
                        lines = [line.strip() for line in bulk_titles.split("\n") if line.strip()]
                        new_rows = []
                        timestamp_base = int(datetime.now().timestamp())
                        for idx, line in enumerate(lines):
                            new_rows.append({
                                'id': str(timestamp_base + idx),
                                'title': line,
                                'clientId': c_id,
                                'staffId': "",
                                'platform': platform,
                                'date': "",
                                'status': "pool",
                                'link': "#"
                            })
                        df_videos = pd.concat([df_videos, pd.DataFrame(new_rows)], ignore_index=True)
                        conn.update(worksheet="videos", data=df_videos)
                        st.success(f"{len(new_rows)} vidéos ajoutées au Pool d'attente !")
                        st.rerun()

    elif act_mode == "Modifier / Supprimer une vidéo":
        if df_videos.empty:
            st.info("Aucune vidéo dans la base de données.")
        else:
            video_options = {row['id']: f"[{client_dict.get(row['clientId'], '?')}] {row['title']}" for _, row in df_videos.iterrows()}
            selected_vid_id = st.selectbox("Sélectionner la vidéo à modifier", options=list(video_options.keys()), format_func=lambda x: video_options[x])
            
            # Récupérer les infos actuelles de la vidéo sélectionnée
            vid_data = df_videos[df_videos['id'] == selected_vid_id].iloc[0]
            
            with st.form("edit_form"):
                u_title = st.text_input("Titre de la vidéo", value=vid_data['title'])
                u_c_id = st.selectbox("Restaurateur", options=list(client_options.keys()), index=list(client_options.keys()).index(vid_data['clientId']) if vid_data['clientId'] in client_options else 0, format_func=lambda x: client_options[x])
                u_s_id = st.selectbox("Assigner à", options=list(staff_options.keys()), index=list(staff_options.keys()).index(vid_data['staffId']) if vid_data['staffId'] in staff_options else 0, format_func=lambda x: staff_options[x])
                u_platform = st.selectbox("Réseau Principal", ["TikTok", "Instagram", "Les deux"], index=["TikTok", "Instagram", "Les deux"].index(vid_data['platform']) if vid_data['platform'] in ["TikTok", "Instagram", "Les deux"] else 0)
                u_status = st.selectbox("Étape du Workflow", list(statuses.keys()), index=list(statuses.keys()).index(vid_data['status']) if vid_data['status'] in statuses else 0, format_func=lambda x: statuses[x])
                
                current_date_val = None
                if vid_data['date']:
                    try:
                        current_date_val = datetime.strptime(vid_data['date'], "%Y-%m-%d").date()
                    except:
                        pass
                u_pub_date = st.date_input("Date de publication", value=current_date_val)
                u_drive_link = st.text_input("Lien Drive / Livraison", value=vid_data['link'])
                
                col_save, col_del = st.columns([3, 1])
                
                with col_save:
                    save_trigger = st.form_submit_button("💾 Sauvegarder les modifications", use_container_width=True)
                with col_del:
                    delete_trigger = st.form_submit_button("🚨 Supprimer", use_container_width=True)
                
                if save_trigger:
                    df_videos.loc[df_videos['id'] == selected_vid_id, ['title', 'clientId', 'staffId', 'platform', 'status', 'date', 'link']] = [
                        u_title, u_c_id, u_s_id, u_platform, u_status, str(u_pub_date) if u_pub_date else "", u_drive_link
                    ]
                    conn.update(worksheet="videos", data=df_videos)
                    st.success("Modifications enregistrées !")
                    st.rerun()
                    
                if delete_trigger:
                    df_videos = df_videos[df_videos['id'] != selected_vid_id]
                    conn.update(worksheet="videos", data=df_videos)
                    st.warning("Vidéo supprimée du planning.")
                    st.rerun()
