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
        
        for col in ['id', 'title', 'clientId', 'staffId', 'platform', 'date', 'status', 'link']:
            if col not in df_videos.columns:
                df_videos[col] = ""
        return df_videos, df_clients, df_staff
    except:
        df_v = pd.DataFrame(columns=['id', 'title', 'clientId', 'staffId', 'platform', 'date', 'status', 'link'])
        df_c = pd.DataFrame(columns=['id', 'name', 'color'])
        df_s = pd.DataFrame(columns=['id', 'name'])
        return df_v, df_c, df_s

df_videos, df_clients, df_staff = load_data()

# Nettoyage des données pour éviter les bugs d'affichage
df_videos = df_videos.fillna("").astype(str)
df_clients = df_clients.fillna("").astype(str)
df_staff = df_staff.fillna("").astype(str)

client_dict = dict(zip(df_clients['id'], df_clients['name'])) if not df_clients.empty else {}
client_color_dict = dict(zip(df_clients['id'], df_clients['color'])) if not df_clients.empty else {}
staff_dict = dict(zip(df_staff['id'], df_staff['name'])) if not df_staff.empty else {}

# Ordre logique des colonnes du Workflow
status_order = ["pool", "montage", "validation", "attente-prog", "programme"]
statuses = {
    "pool": "⏳ Pool d'attente",
    "montage": "🎬 En Montage",
    "validation": "👀 À valider",
    "attente-prog": "⏸️ Attente Prog",
    "programme": "📅 Programmées"
}

# 2. BARRE LATÉRALE - CONFIGURATION CLIENTS & STAFF
with st.sidebar:
    st.header("⚙️ Configuration")
    conf_tab = st.radio("Gérer :", ["Restaurateurs (Clients)", "Équipe / Staff"])
    
    if conf_tab == "Restaurateurs (Clients)":
        st.subheader("Ajouter un Client")
        with st.form("add_client_form", clear_on_submit=True):
            new_c_name = st.text_input("Nom du restaurant *")
            new_c_color = st.color_picker("Couleur", "#6366f1")
            if st.form_submit_button("Ajouter", use_container_width=True):
                if new_c_name:
                    new_c = pd.DataFrame([{'id': f"c_{int(datetime.now().timestamp())}", 'name': new_c_name, 'color': new_c_color}])
                    df_clients = pd.concat([df_clients, new_c], ignore_index=True)
                    conn.update(worksheet="clients", data=df_clients)
                    st.success("Client ajouté !")
                    st.rerun()

    elif conf_tab == "Équipe / Staff":
        st.subheader("Ajouter un Membre")
        with st.form("add_staff_form", clear_on_submit=True):
            new_s_name = st.text_input("Nom du collaborateur *")
            if st.form_submit_button("Ajouter", use_container_width=True):
                if new_s_name:
                    new_s = pd.DataFrame([{'id': f"s_{int(datetime.now().timestamp())}", 'name': new_s_name}])
                    df_staff = pd.concat([df_staff, new_s], ignore_index=True)
                    conn.update(worksheet="staff", data=df_staff)
                    st.success("Membre ajouté !")
                    st.rerun()

# 3. ONGLETS DE NAVIGATION PRINCIPAUX
tab_pipeline, tab_calendar, tab_actions = st.tabs(["📊 Pipeline (Kanban)", "📅 Calendrier de Publication", "➕ Ajouter / Modifier"])

# Styles CSS pour habiller le Kanban natif
st.markdown("""
    <style>
    .kanban-box {
        background-color: #1e293b;
        border-radius: 8px;
        padding: 10px;
        margin-bottom: 8px;
        border-left: 4px solid #6366f1;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .badge-pt {
        background-color: #334155;
        padding: 1px 5px;
        border-radius: 4px;
        font-size: 10px;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# --- ONGLET 1 : PIPELINE KANBAN (VERSION NATIVE ULTRA-FIABLE) ---
with tab_pipeline:
    cols = st.columns(len(status_order))
    
    for i, status_key in enumerate(status_order):
        with cols[i]:
            st.markdown(f"### {statuses[status_key]}")
            vids_in_status = df_videos[df_videos['status'] == status_key]
            st.caption(f"{len(vids_in_status)} vidéo(s)")
            st.write("---")
            
            for _, vid in vids_in_status.iterrows():
                client_name = client_dict.get(vid['clientId'], "Inconnu")
                client_color = client_color_dict.get(vid['clientId'], "#6366f1")
                staff_name = staff_dict.get(vid['staffId'], "Non assigné")
                date_str = f" | 🗓️ {vid['date']}" if vid['date'] else ""
                
                # Carte visuelle
                st.markdown(f"""
                <div class="kanban-box" style="border-left-color: {client_color}">
                    <div style="display:flex; justify-content:between; font-size:11px; margin-bottom:2px;">
                        <span class="badge-pt" style="color:#a7f3d0;">{vid['platform']}</span>
                        <span style="font-weight:bold; margin-left:auto; color:{client_color};">{client_name}</span>
                    </div>
                    <strong style="font-size:13px; color:white;">{vid['title']}</strong><br>
                    <span style="font-size:10px; color:#94a3b8;">👤 {staff_name}{date_str}</span>
                </div>
                """, unsafe_allow_html=True)
                
                # Boutons de déplacement sous chaque carte
                btn_cols = st.columns([1, 1])
                
                # Bouton reculer (sauf si on est sur la première colonne)
                if i > 0:
                    if btn_cols[0].button("◀️", key=f"left_{vid['id']}", use_container_width=True):
                        df_videos.loc[df_videos['id'] == vid['id'], 'status'] = status_order[i-1]
                        if status_order[i-1] != 'programme':
                            df_videos.loc[df_videos['id'] == vid['id'], 'date'] = ""
                        conn.update(worksheet="videos", data=df_videos)
                        st.rerun()
                        
                # Bouton avancer (sauf si on est sur la dernière colonne)
                if i < len(status_order) - 1:
                    next_status = status_order[i+1]
                    if btn_cols[1].button("▶️", key=f"right_{vid['id']}", use_container_width=True):
                        # Si on envoie vers le statut planifié, on demande une date
                        if next_status == "programme":
                            st.warning("Pour planifier, passez par l'onglet 'Ajouter / Modifier'")
                        else:
                            df_videos.loc[df_videos['id'] == vid['id'], 'status'] = next_status
                            conn.update(worksheet="videos", data=df_videos)
                            st.rerun()

# --- ONGLET 2 : VUE CALENDRIER ---
with tab_calendar:
    st.subheader("🗓️ Planning des Publications Programmées")
    vids_programmed = df_videos[df_videos['status'] == "programme"].copy()
    
    if not vids_programmed.empty:
        vids_programmed['Restaurateur'] = vids_programmed['clientId'].map(client_dict)
        vids_programmed['Assigné à'] = vids_programmed['staffId'].map(staff_dict)
        vids_programmed = vids_programmed.sort_values(by='date')
        
        st.dataframe(
            vids_programmed[['date', 'title', 'Restaurateur', 'Assigné à', 'platform', 'link']],
            column_config={
                "date": "Date de Publication",
                "title": "Titre",
                "link": st.column_config.LinkColumn("Lien Drive")
            },
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("Aucune vidéo planifiée avec une date précise pour le moment.")

# --- ONGLET 3 : ACTIONS & AJOUT GROUPÉ / BULK ---
with tab_actions:
    act_mode = st.radio("Action :", ["Ajouter une vidéo", "Création groupée (Bulk)", "Modifier / Supprimer"], horizontal=True)
    
    client_options = {row['id']: row['name'] for _, row in df_clients.iterrows()}
    staff_options = {"": "Non assigné"}
    for _, row in df_staff.iterrows():
        staff_options[row['id']] = row['name']
        
    if act_mode == "Ajouter une vidéo":
        with st.form("add_video_form", clear_on_submit=True):
            title = st.text_input("Titre de la vidéo *")
            c_id = st.selectbox("Restaurateur *", options=list(client_options.keys()), format_func=lambda x: client_options[x])
            s_id = st.selectbox("Assigner à", options=list(staff_options.keys()), format_func=lambda x: staff_options[x])
            platform = st.selectbox("Réseau Principal", ["TikTok", "Instagram", "Les deux"])
            status = st.selectbox("Étape", list(statuses.keys()), format_func=lambda x: statuses[x])
            pub_date = st.date_input("Date (uniquement si programmée)", value=None)
            
            if st.form_submit_button("Enregistrer", use_container_width=True):
                if title:
                    new_vid = {
                        'id': str(int(datetime.now().timestamp())), 'title': title, 'clientId': c_id, 
                        'staffId': s_id, 'platform': platform, 'date': str(pub_date) if pub_date else "", 'status': status, 'link': "#"
                    }
                    df_videos = pd.concat([df_videos, pd.DataFrame([new_vid])], ignore_index=True)
                    conn.update(worksheet="videos", data=df_videos)
                    st.success("Vidéo enregistrée !")
                    st.rerun()

    elif act_mode == "Création groupée (Bulk)":
        with st.form("bulk_form", clear_on_submit=True):
            c_id = st.selectbox("Restaurateur *", options=list(client_options.keys()), format_func=lambda x: client_options[x])
            platform = st.selectbox("Réseau Principal", ["TikTok", "Instagram", "Les deux"])
            bulk_titles = st.text_area("Titres des vidéos (une par ligne) *")
            
            if st.form_submit_button("Générer en masse", use_container_width=True):
                if bulk_titles:
                    lines = [line.strip() for line in bulk_titles.split("\n") if line.strip()]
                    new_rows = []
                    ts = int(datetime.now().timestamp())
                    for idx, line in enumerate(lines):
                        new_rows.append({'id': str(ts + idx), 'title': line, 'clientId': c_id, 'staffId': "", 'platform': platform, 'date': "", 'status': "pool", 'link': "#"})
                    df_videos = pd.concat([df_videos, pd.DataFrame(new_rows)], ignore_index=True)
                    conn.update(worksheet="videos", data=df_videos)
                    st.success(f"{len(new_rows)} vidéos ajoutées au Pool !")
                    st.rerun()

    elif act_mode == "Modifier / Supprimer":
        if df_videos.empty:
            st.info("Aucune vidéo disponible.")
        else:
            video_options = {row['id']: f"[{client_dict.get(row['clientId'], '?')}] {row['title']}" for _, row in df_videos.iterrows()}
            selected_id = st.selectbox("Sélectionner la vidéo", options=list(video_options.keys()), format_func=lambda x: video_options[x])
            vid_data = df_videos[df_videos['id'] == selected_id].iloc[0]
            
            with st.form("edit_form"):
                u_title = st.text_input("Titre", value=vid_data['title'])
                u_s_id = st.selectbox("Assigner à", options=list(staff_options.keys()), index=list(staff_options.keys()).index(vid_data['staffId']) if vid_data['staffId'] in staff_options else 0, format_func=lambda x: staff_options[x])
                u_status = st.selectbox("Étape", list(statuses.keys()), index=list(statuses.keys()).index(vid_data['status']), format_func=lambda x: statuses[x])
                
                current_date = None
                if vid_data['date']:
                    try: current_date = datetime.strptime(vid_data['date'], "%Y-%m-%d").date()
                    except: pass
                u_date = st.date_input("Date de publication", value=current_date)
                
                col_save, col_del = st.columns([3, 1])
                if col_save.st.form_submit_button("💾 Sauvegarder"):
                    df_videos.loc[df_videos['id'] == selected_id, ['title', 'staffId', 'status', 'date']] = [u_title, u_s_id, u_status, str(u_date) if u_date else ""]
                    conn.update(worksheet="videos", data=df_videos)
                    st.success("Modifications enregistrées !")
                    st.rerun()
                if col_del.st.form_submit_button("🚨 Supprimer"):
                    df_videos = df_videos[df_videos['id'] != selected_id]
                    conn.update(worksheet="videos", data=df_videos)
                    st.rerun()
