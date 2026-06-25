import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import json
from datetime import datetime

# Configuration de la page
st.set_page_config(layout="wide", page_title="Studio Cloud Workspace", page_icon="🎬")

# 1. CONNEXION ET CHARGEMENT DES DONNÉES (Service Account sécurisé)
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    try:
        df_videos = conn.read(worksheet="videos", ttl=0)
        df_clients = conn.read(worksheet="clients", ttl=0)
        df_staff = conn.read(worksheet="staff", ttl=0)
        
        # Validation des colonnes requises
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

# Nettoyage des données pour JSON
df_videos = df_videos.fillna("").astype(str)
df_clients = df_clients.fillna("").astype(str)
df_staff = df_staff.fillna("").astype(str)

# 2. TRAITEMENT DU DRAG & DROP PROVENANT DE L'INTERFACE
# Détection si le JavaScript nous envoie une mise à jour de statut
query_params = st.query_params
if "action" in query_params and query_params["action"] == "move_video":
    vid_id = query_params.get("vid_id")
    new_status = query_params.get("new_status")
    new_date = query_params.get("date", "")
    
    if vid_id and new_status:
        # Trouver la ligne et mettre à jour
        idx = df_videos[df_videos['id'] == vid_id].index
        if not idx.empty:
            df_videos.loc[idx, 'status'] = new_status
            if new_status == 'programme' and new_date:
                df_videos.loc[idx, 'date'] = new_date
            elif new_status != 'programme':
                df_videos.loc[idx, 'date'] = ""
                
            # Sauvegarde immédiate et sécurisée dans Google Sheets
            conn.update(worksheet="videos", data=df_videos)
            st.toast("🔄 Statut mis à jour sur Google Sheets !", icon="✅")
            
        # Nettoyage de l'URL et rafraîchissement
        st.query_params.clear()
        st.rerun()

# 3. BARRE LATÉRALE - CONFIGURATION CLIENTS & STAFF
with st.sidebar:
    st.header("⚙️ Configuration")
    conf_tab = st.radio("Gérer :", ["Restaurateurs (Clients)", "Équipe / Staff", "Ajouter une vidéo (Formulaire)"])
    
    client_options = {row['id']: row['name'] for _, row in df_clients.iterrows()}
    staff_options = {"": "Non assigné"}
    for _, row in df_staff.iterrows():
        staff_options[row['id']] = row['name']

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
                    
    elif conf_tab == "Ajouter une vidéo (Formulaire)":
        st.subheader("Nouvelle Vidéo")
        if not client_options:
            st.warning("Ajoutez un client d'abord.")
        else:
            with st.form("sidebar_video_form", clear_on_submit=True):
                title = st.text_input("Titre *")
                c_id = st.selectbox("Client *", options=list(client_options.keys()), format_func=lambda x: client_options[x])
                s_id = st.selectbox("Staff", options=list(staff_options.keys()), format_func=lambda x: staff_options[x])
                platform = st.selectbox("Réseau", ["TikTok", "Instagram", "Les deux"])
                status = st.selectbox("Statut initial", ["pool", "montage", "validation", "attente-prog"])
                if st.form_submit_button("Enregistrer", use_container_width=True):
                    if title:
                        new_vid = {'id': str(int(datetime.now().timestamp())), 'title': title, 'clientId': c_id, 'staffId': s_id, 'platform': platform, 'date': "", 'status': status, 'link': "#"}
                        df_videos = pd.concat([df_videos, pd.DataFrame([new_vid])], ignore_index=True)
                        conn.update(worksheet="videos", data=df_videos)
                        st.success("Vidéo ajoutée au pipeline !")
                        st.rerun()

# 4. PRÉPARATION DU CODE DE L'INTERFACE INTERACTIVE AVEC DRAG & DROP
html_template = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <script src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://fonts.googleapis.com/icon?family=Material+Icons+Round">
    <style>
        body { font-family: 'Inter', sans-serif; background-color: #0f172a; color: #f8fafc; }
        .kanban-col { min-height: 500px; transition: background-color 0.2s ease; }
        .drag-over { background-color: rgba(99, 102, 241, 0.1) !important; border: 2px dashed #6366f1 !important; }
        .card-dragging { opacity: 0.4; transform: scale(0.98); }
    </style>
</head>
<body class="p-2 select-none">

    <div class="grid grid-cols-1 lg:grid-cols-5 gap-4 items-start">
        <div class="bg-slate-800/80 border border-slate-700 p-4 rounded-xl">
            <div class="flex justify-between items-center mb-3 border-b border-slate-700 pb-2">
                <h3 class="font-bold text-xs uppercase tracking-wider text-amber-400 flex items-center">⏳ Pool d'attente</h3>
                <span id="badge-pool" class="bg-slate-700 text-slate-300 text-xs px-2 py-0.5 rounded-full font-bold">0</span>
            </div>
            <div id="col-pool" class="kanban-col space-y-3 rounded-lg p-1" ondragover="allowDrop(event)" ondragenter="dragEnter(event)" ondragleave="dragLeave(event)" ondrop="drop(event, 'pool')"></div>
        </div>

        <div class="bg-slate-800/80 border border-slate-700 p-4 rounded-xl">
            <div class="flex justify-between items-center mb-3 border-b border-slate-700 pb-2">
                <h3 class="font-bold text-xs uppercase tracking-wider text-blue-400 flex items-center">🎬 En Montage</h3>
                <span id="badge-montage" class="bg-slate-700 text-slate-300 text-xs px-2 py-0.5 rounded-full font-bold">0</span>
            </div>
            <div id="col-montage" class="kanban-col space-y-3 rounded-lg p-1" ondragover="allowDrop(event)" ondragenter="dragEnter(event)" ondragleave="dragLeave(event)" ondrop="drop(event, 'montage')"></div>
        </div>

        <div class="bg-slate-800/80 border border-slate-700 p-4 rounded-xl">
            <div class="flex justify-between items-center mb-3 border-b border-slate-700 pb-2">
                <h3 class="font-bold text-xs uppercase tracking-wider text-purple-400 flex items-center">👀 À valider</h3>
                <span id="badge-validation" class="bg-slate-700 text-slate-300 text-xs px-2 py-0.5 rounded-full font-bold">0</span>
            </div>
            <div id="col-validation" class="kanban-col space-y-3 rounded-lg p-1" ondragover="allowDrop(event)" ondragenter="dragEnter(event)" ondragleave="dragLeave(event)" ondrop="drop(event, 'validation')"></div>
        </div>

        <div class="bg-slate-800/80 border border-slate-700 p-4 rounded-xl">
            <div class="flex justify-between items-center mb-3 border-b border-slate-700 pb-2">
                <h3 class="font-bold text-xs uppercase tracking-wider text-pink-400 flex items-center">⏸️ Attente Prog</h3>
                <span id="badge-attente-prog" class="bg-slate-700 text-slate-300 text-xs px-2 py-0.5 rounded-full font-bold">0</span>
            </div>
            <div id="col-attente-prog" class="kanban-col space-y-3 rounded-lg p-1" ondragover="allowDrop(event)" ondragenter="dragEnter(event)" ondragleave="dragLeave(event)" ondrop="drop(event, 'attente-prog')"></div>
        </div>

        <div class="bg-slate-800/80 border border-slate-700 p-4 rounded-xl">
            <div class="flex justify-between items-center mb-3 border-b border-slate-700 pb-2">
                <h3 class="font-bold text-xs uppercase tracking-wider text-emerald-400 flex items-center">📅 Programmées</h3>
                <span id="badge-programme" class="bg-slate-700 text-slate-300 text-xs px-2 py-0.5 rounded-full font-bold">0</span>
            </div>
            <div id="col-programme" class="kanban-col space-y-3 rounded-lg p-1" ondragover="allowDrop(event)" ondragenter="dragEnter(event)" ondragleave="dragLeave(event)" ondrop="drop(event, 'programme')"></div>
        </div>
    </div>

    <script>
        // Récupération sécurisée des données injectées par Python
        const clients = __CLIENTS__;
        const staff = __STAFF__;
        const videos = __VIDEOS__;

        function buildPipeline() {
            const counts = { pool: 0, montage: 0, validation: 0, 'attente-prog': 0, programme: 0 };
            
            // Nettoyage des zones
            Object.keys(counts).forEach(k => document.getElementById(`col-${k}`).innerHTML = '');

            videos.forEach(v => {
                const clientObj = clients.find(c => String(c.id) === String(v.clientId)) || { name: 'Inconnu', color: '#64748b' };
                const staffObj = staff.find(s => String(s.id) === String(v.staffId)) || { name: 'Non assigné' };
                
                const badgeColor = v.platform === 'TikTok' ? 'bg-cyan-500/20 text-cyan-300' : v.platform === 'Instagram' ? 'bg-fuchsia-500/20 text-fuchsia-300' : 'bg-indigo-500/20 text-indigo-300';
                const dateHtml = v.date ? `<div class="text-[10px] text-emerald-400 font-semibold mt-2 flex items-center"><span class="material-icons-round text-xs mr-1">calendar_today</span>${v.date}</div>` : '';

                const cardHTML = `
                    <div id="${v.id}" draggable="true" ondragstart="dragStart(event)" ondragend="dragEnd(event)" 
                         class="bg-slate-700/50 hover:bg-slate-700 border-l-4 p-3 rounded-xl shadow-md cursor-grab active:cursor-grabbing transition"
                         style="border-color: ${clientObj.color}">
                        <div class="flex justify-between items-center mb-1">
                            <span class="text-[9px] font-bold px-1.5 py-0.5 rounded ${badgeColor}">${v.platform}</span>
                            <span class="text-[10px] font-bold" style="color: ${clientObj.color}">${clientObj.name}</span>
                        </div>
                        <h4 class="text-xs font-semibold text-white leading-tight">${v.title}</h4>
                        <div class="text-[10px] text-slate-400 mt-2 flex items-center">
                            <span class="material-icons-round text-xs mr-1 text-slate-500">account_circle</span>${staffObj.name}
                        </div>
                        ${dateHtml}
                    </div>
                `;

                const colTarget = document.getElementById(`col-${v.status}`);
                if (colTarget) {
                    colTarget.innerHTML += cardHTML;
                    counts[v.status]++;
                }
            });

            // Mise à jour des compteurs globaux
            Object.keys(counts).forEach(k => document.getElementById(`badge-${k}`).innerText = counts[k]);
        }

        // GESTION DES EVENEMENTS DU GLISSER-DEPOSER (DRAG & DROP)
        function dragStart(ev) {
            ev.dataTransfer.setData("text/plain", ev.target.id);
            ev.target.classList.add('card-dragging');
        }

        function dragEnd(ev) {
            ev.target.classList.remove('card-dragging');
        }

        function allowDrop(ev) {
            ev.preventDefault();
        }

        function dragEnter(ev) {
            const targetCol = ev.target.closest('.kanban-col');
            if(targetCol) targetCol.classList.add('drag-over');
        }

        function dragLeave(ev) {
            const targetCol = ev.target.closest('.kanban-col');
            if(targetCol) targetCol.classList.remove('drag-over');
        }

        function drop(ev, destStatus) {
            ev.preventDefault();
            const targetCol = ev.target.closest('.kanban-col');
            if(targetCol) targetCol.classList.remove('drag-over');

            const id = ev.dataTransfer.getData("text/plain");
            if(!id) return;

            let dateParam = "";
            if (destStatus === "programme") {
                const inputDate = prompt("Entrez la date de programmation (AAAA-MM-JJ) :");
                if (!inputDate) return; // Annule si aucune date n'est saisie
                dateParam = "&date=" + encodeURIComponent(inputDate);
            }

            // ENVOI SÉCURISÉ DE L'ORDRE DE MISE À JOUR À PYTHON (via l'URL parente de Streamlit)
            const parentUrl = new URL(window.parent.location.href);
            parentUrl.searchParams.set("action", "move_video");
            parentUrl.searchParams.set("vid_id", id);
            parentUrl.searchParams.set("new_status", destStatus);
            if(dateParam) {
                parentUrl.searchParams.set("date", parentUrl.searchParams.get("date") || dateParam.split("=")[1]);
            }
            
            // Redirection transparente pour exécuter le code Python d'écriture Sheets
            window.parent.location.href = parentUrl.href;
        }

        // Lancement initial
        buildPipeline();
    </script>
</body>
</html>
"""

# 5. INJECTION COMPATIBLE DANS LA VUE STREAMLIT
compiled_html = html_template.replace("__CLIENTS__", json.dumps(df_clients.to_dict(orient="records")))
compiled_html = compiled_html.replace("__STAFF__", json.dumps(df_staff.to_dict(orient="records")))
compiled_html = compiled_html.replace("__VIDEOS__", json.dumps(df_videos.to_dict(orient="records")))

# Rendu de l'interface Kanban interactive
st.components.v1.html(compiled_html, height=650, scrolling=True)
