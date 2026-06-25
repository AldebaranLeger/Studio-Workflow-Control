import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import json
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

# Nettoyage des données pour éviter les bugs avec le JSON
df_videos = df_videos.fillna("").astype(str)
df_clients = df_clients.fillna("").astype(str)
df_staff = df_staff.fillna("").astype(str)

client_dict = dict(zip(df_clients['id'], df_clients['name'])) if not df_clients.empty else {}
staff_dict = dict(zip(df_staff['id'], df_staff['name'])) if not df_staff.empty else {}

# 2. TRAITEMENT DES ACTIONS VIA PARAMÈTRES D'URL (BACKEND)
query_params = st.query_params
if "action" in query_params and query_params["action"] == "move_video":
    vid_id = query_params.get("vid_id")
    new_status = query_params.get("new_status")
    new_date = query_params.get("date", "")
    
    if vid_id and new_status:
        idx = df_videos[df_videos['id'] == vid_id].index
        if not idx.empty:
            df_videos.loc[idx, 'status'] = new_status
            df_videos.loc[idx, 'date'] = new_date if new_status == 'programme' else ""
            conn.update(worksheet="videos", data=df_videos)
            st.toast("🔄 Base mise à jour !", icon="✅")
        st.query_params.clear()
        st.rerun()

# 3. BARRE LATÉRALE - CONFIGURATION CLIENTS & STAFF
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

# 4. ONGLETS DE NAVIGATION PRINCIPAUX (RESTAURÉS)
tab_pipeline, tab_calendar, tab_actions = st.tabs(["📊 Pipeline (Kanban)", "📅 Calendrier de Publication", "➕ Ajouter / Modifier"])

# --- ONGLET 1 : PIPELINE INTERACTIF (DRAG & DROP CORRIGÉ) ---
with tab_pipeline:
    
    # Code HTML/JS mis à jour avec une méthode de communication robuste (window.top.location)
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <script src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"></script>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
        <style>
            body { font-family: 'Inter', sans-serif; background-color: #0f172a; color: #f8fafc; }
            .kanban-col { min-height: 450px; }
            .drag-over { background-color: rgba(99, 102, 241, 0.1); border: 2px dashed #6366f1; }
        </style>
    </head>
    <body class="p-1 select-none">
        <div class="grid grid-cols-1 lg:grid-cols-5 gap-4">
            <div class="bg-slate-800/60 p-3 rounded-xl border border-slate-700">
                <h3 class="font-bold text-xs uppercase text-amber-400 mb-2 border-b border-slate-700 pb-1">⏳ Pool d'attente</h3>
                <div id="col-pool" class="kanban-col space-y-2 rounded-lg" ondragover="allowDrop(event)" ondrop="drop(event, 'pool')" ondragenter="dragEnter(event)" ondragleave="dragLeave(event)"></div>
            </div>
            <div class="bg-slate-800/60 p-3 rounded-xl border border-slate-700">
                <h3 class="font-bold text-xs uppercase text-blue-400 mb-2 border-b border-slate-700 pb-1">🎬 En Montage</h3>
                <div id="col-montage" class="kanban-col space-y-2 rounded-lg" ondragover="allowDrop(event)" ondrop="drop(event, 'montage')" ondragenter="dragEnter(event)" ondragleave="dragLeave(event)"></div>
            </div>
            <div class="bg-slate-800/60 p-3 rounded-xl border border-slate-700">
                <h3 class="font-bold text-xs uppercase text-purple-400 mb-2 border-b border-slate-700 pb-1">👀 À valider</h3>
                <div id="col-validation" class="kanban-col space-y-2 rounded-lg" ondragover="allowDrop(event)" ondrop="drop(event, 'validation')" ondragenter="dragEnter(event)" ondragleave="dragLeave(event)"></div>
            </div>
            <div class="bg-slate-800/60 p-3 rounded-xl border border-slate-700">
                <h3 class="font-bold text-xs uppercase text-pink-400 mb-2 border-b border-slate-700 pb-1">⏸️ Attente Prog</h3>
                <div id="col-attente-prog" class="kanban-col space-y-2 rounded-lg" ondragover="allowDrop(event)" ondrop="drop(event, 'attente-prog')" ondragenter="dragEnter(event)" ondragleave="dragLeave(event)"></div>
            </div>
            <div class="bg-slate-800/60 p-3 rounded-xl border border-slate-700">
                <h3 class="font-bold text-xs uppercase text-emerald-400 mb-2 border-b border-slate-700 pb-1">📅 Programmées</h3>
                <div id="col-programme" class="kanban-col space-y-2 rounded-lg" ondragover="allowDrop(event)" ondrop="drop(event, 'programme')" ondragenter="dragEnter(event)" ondragleave="dragLeave(event)"></div>
            </div>
        </div>

        <script>
            const clients = __CLIENTS__;
            const staff = __STAFF__;
            const videos = __VIDEOS__;

            function render() {
                videos.forEach(v => {
                    const c = clients.find(cl => String(cl.id) === String(v.clientId)) || { name: 'Inconnu', color: '#64748b' };
                    const s = staff.find(st => String(st.id) === String(v.staffId)) || { name: 'Non assigné' };
                    const platformClass = v.platform === 'TikTok' ? 'bg-cyan-500/20 text-cyan-300' : 'bg-fuchsia-500/20 text-fuchsia-300';
                    
                    const card = document.createElement('div');
                    card.id = v.id;
                    card.draggable = true;
                    card.className = "bg-slate-700/40 p-2.5 rounded-lg border-l-4 shadow cursor-grab active:cursor-grabbing hover:bg-slate-700/70 transition";
                    card.style.borderColor = c.color;
                    card.ondragstart = (e) => e.dataTransfer.setData("text/plain", e.target.id);
                    
                    card.innerHTML = `
                        <div class="flex justify-between text-[10px] mb-1 font-medium">
                            <span class="px-1 rounded ${platformClass}">${v.platform}</span>
                            <span style="color:${c.color}">${c.name}</span>
                        </div>
                        <h4 class="text-xs font-semibold text-white">${v.title}</h4>
                        <div class="text-[9px] text-slate-400 mt-1.5">👤 ${s.name} ${v.date ? ' | 🗓️ '+v.date : ''}</div>
                    `;
                    
                    const container = document.getElementById(`col-${v.status}`);
                    if(container) container.appendChild(card);
                });
            }

            function allowDrop(e) { e.preventDefault(); }
            function dragEnter(e) { const col = e.target.closest('.kanban-col'); if(col) col.classList.add('drag-over'); }
            function dragLeave(e) { const col = e.target.closest('.kanban-col'); if(col) col.classList.remove('drag-over'); }

            function drop(e, destStatus) {
                e.preventDefault();
                const col = e.target.closest('.kanban-col');
                if(col) col.classList.remove('drag-over');
                
                const id = e.dataTransfer.getData("text/plain");
                if(!id) return;

                let dateVal = "";
                if(destStatus === "programme") {
                    dateVal = prompt("Date de publication (AAAA-MM-JJ) :");
                    if(!dateVal) return;
                }

                // Utilisation de window.top pour forcer l'Iframe à casser son isolation de sécurité d'un clic
                try {
                    const url = new URL(window.top.location.href);
                    url.searchParams.set("action", "move_video");
                    url.searchParams.set("vid_id", id);
                    url.searchParams.set("new_status", destStatus);
                    if(dateVal) url.searchParams.set("date", dateVal);
                    window.top.location.href = url.href;
                } catch(err) {
                    // Alternative si le navigateur bloque toujours l'accès au top-level
                    const url = new URL(window.parent.location.href);
                    url.searchParams.set("action", "move_video");
                    url.searchParams.set("vid_id", id);
                    url.searchParams.set("new_status", destStatus);
                    if(dateVal) url.searchParams.set("date", dateVal);
                    window.parent.location.href = url.href;
                }
            }

            render();
        </script>
    </body>
    </html>
    """
    
    compiled_html = html_template.replace("__CLIENTS__", json.dumps(df_clients.to_dict(orient="records")))
    compiled_html = compiled_html.replace("__STAFF__", json.dumps(df_staff.to_dict(orient="records")))
    compiled_html = compiled_html.replace("__VIDEOS__", json.dumps(df_videos.to_dict(orient="records")))
    st.components.v1.html(compiled_html, height=550, scrolling=True)

# --- ONGLET 2 : VUE CALENDRIER (RESTAURÉE) ---
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
        st.info("Aucune vidéo n'est planifiée dans la colonne 'Programmées' pour le moment.")

# --- ONGLET 3 : ACTIONS & AJOUT GROUPÉ / BULK (RESTAURÉ) ---
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
            status = st.selectbox("Étape", ["pool", "montage", "validation", "attente-prog"])
            
            if st.form_submit_button("Enregistrer", use_container_width=True):
                if title:
                    new_vid = {'id': str(int(datetime.now().timestamp())), 'title': title, 'clientId': c_id, 'staffId': s_id, 'platform': platform, 'date': "", 'status': status, 'link': "#"}
                    df_videos = pd.concat([df_videos, pd.DataFrame([new_vid])], ignore_index=True)
                    conn.update(worksheet="videos", data=df_videos)
                    st.success(f"Vidéo enregistrée !")
                    st.rerun()

    elif act_mode == "Création groupée (Bulk)":
        with st.form("bulk_form", clear_on_submit=True):
            c_id = st.selectbox("Restaurateur *", options=list(client_options.keys()), format_func=lambda x: client_options[x])
            platform = st.selectbox("Réseau Principal", ["TikTok", "Instagram", "Les deux"])
            bulk_titles = st.text_area("Titres des vidéos (une par ligne) *", placeholder="Vidéo 1\nVidéo 2\nVidéo 3")
            
            if st.form_submit_button("Générer les vidéos en masse", use_container_width=True):
                if bulk_titles:
                    lines = [line.strip() for line in bulk_titles.split("\n") if line.strip()]
                    new_rows = []
                    ts = int(datetime.now().timestamp())
                    for idx, line in enumerate(lines):
                        new_rows.append({'id': str(ts + idx), 'title': line, 'clientId': c_id, 'staffId': "", 'platform': platform, 'date': "", 'status': "pool", 'link': "#"})
                    df_videos = pd.concat([df_videos, pd.DataFrame(new_rows)], ignore_index=True)
                    conn.update(worksheet="videos", data=df_videos)
                    st.success(f"{len(new_rows)} vidéos ajoutées avec succès au Pool d'attente !")
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
                u_status = st.selectbox("Étape", ["pool", "montage", "validation", "attente-prog", "programme"], index=["pool", "montage", "validation", "attente-prog", "programme"].index(vid_data['status']))
                
                col_save, col_del = st.columns([3, 1])
                if col_save.st.form_submit_button("💾 Sauvegarder"):
                    df_videos.loc[df_videos['id'] == selected_id, ['title', 'status']] = [u_title, u_status]
                    conn.update(worksheet="videos", data=df_videos)
                    st.success("Modifications enregistrées !")
                    st.rerun()
                if col_del.st.form_submit_button("🚨 Supprimer"):
                    df_videos = df_videos[df_videos['id'] != selected_id]
                    conn.update(worksheet="videos", data=df_videos)
                    st.rerun()
