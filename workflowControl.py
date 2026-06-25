import streamlit as st
import streamlit.components.v1 as components
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import json

st.set_page_config(layout="wide", page_title="Studio Workflow Control PRO")

# 1. CONNEXION À LA BASE DE DONNÉES GOOGLE SHEETS
conn = st.connection("gsheets", type=GSheetsConnection)

# Fonctions de chargement
def load_data():
    try:
        df_videos = conn.read(worksheet="videos", ttl=0)
        df_clients = conn.read(worksheet="clients", ttl=0)
        df_staff = conn.read(worksheet="staff", ttl=0)
        return (
            df_videos.to_dict(orient="records"),
            df_clients.to_dict(orient="records"),
            df_staff.to_dict(orient="records")
        )
    except:
        # En cas de feuilles vides au démarrage
        return [], [], []

# Chargement initial des données partagées
videos_list, clients_list, staff_list = load_data()

# 2. TRAITEMENT DES ACTIONS REÇUES DE L'INTERFACE HTML/JS
# (Gestion des requêtes de mise à jour envoyées par le JavaScript)
query_params = st.query_params
if "action" in query_params:
    action = query_params["action"]
    data_payload = json.loads(query_params.get("data", "{}"))
    
    if action == "save_all":
        # On convertit les listes reçues en DataFrames et on écrase le Google Sheets
        df_v = pd.DataFrame(data_payload.get("videos", []))
        df_c = pd.DataFrame(data_payload.get("clients", []))
        df_s = pd.DataFrame(data_payload.get("staff", []))
        
        conn.update(worksheet="videos", data=df_v)
        conn.update(worksheet="clients", data=df_c)
        conn.update(worksheet="staff", data=df_s)
        st.toast("🔄 Base de données partagée mise à jour !", icon="✅")
        # Nettoyage des paramètres pour éviter les boucles
        st.query_params.clear()
        st.rerun()

# 3. CODE INTERFACE (HTML/JS) ADAPTÉ POUR COMMUNIQUER AVEC LE PYTHON
# On injecte dynamiquement les données du Google Sheets dans le JS au démarrage
html_code = f"""
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <title>Video Studio Workspace Pro</title>
    <script src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://fonts.googleapis.com/icon?family=Material+Icons+Round">
    <style>
        body {{ font-family: 'Inter', sans-serif; }}
        .column-body {{ min-height: 450px; }}
        .dragging {{ opacity: 0.4; transform: scale(0.96); }}
        .calendar-grid {{ display: grid; grid-template-columns: repeat(7, minmax(0, 1fr)); }}
    </style>
</head>
<body class="bg-slate-900 text-slate-100 min-h-screen flex flex-col select-none">

    <header class="bg-slate-800 border-b border-slate-700 px-6 py-4 flex flex-col lg:flex-row justify-between items-center gap-4 shadow-lg">
        <div class="flex items-center space-x-3">
            <div class="bg-indigo-600 p-2 rounded-lg shadow-md">
                <span class="material-icons-round text-white block">cloud_sync</span>
            </div>
            <div>
                <h1 class="text-xl font-bold tracking-tight">Studio Cloud Workspace</h1>
                <p class="text-xs text-emerald-400 font-semibold flex items-center">
                    <span class="w-2 h-2 rounded-full bg-emerald-500 mr-1.5 animate-pulse"></span>
                    Base de données d'équipe synchronisée
                </p>
            </div>
        </div>

        <div class="bg-slate-900 p-1 rounded-xl border border-slate-700 flex space-x-1">
            <button onclick="switchView('kanban')" id="btn-view-kanban" class="px-4 py-2 text-xs font-semibold rounded-lg flex items-center space-x-2 bg-indigo-600 text-white shadow transition cursor-pointer">
                <span class="material-icons-round text-sm">view_kanban</span><span>Pipeline</span>
            </button>
            <button onclick="switchView('calendar')" id="btn-view-calendar" class="px-4 py-2 text-xs font-semibold rounded-lg flex items-center space-x-2 text-slate-400 hover:text-slate-200 transition cursor-pointer">
                <span class="material-icons-round text-sm">calendar_month</span><span>Calendrier</span>
            </button>
            <button onclick="switchView('settings')" id="btn-view-settings" class="px-4 py-2 text-xs font-semibold rounded-lg flex items-center space-x-2 text-slate-400 hover:text-slate-200 transition cursor-pointer">
                <span class="material-icons-round text-sm">badge</span><span>Clients & Staff</span>
            </button>
        </div>

        <div class="flex items-center space-x-2">
            <button onclick="openBulkModal()" class="bg-slate-700 hover:bg-slate-600 text-slate-200 px-3 py-2 rounded-lg font-medium text-xs flex items-center space-x-1.5 transition cursor-pointer">
                <span class="material-icons-round text-sm">library_add</span><span>Ajout Multiple</span>
            </button>
            <button onclick="openModalForAdd()" class="bg-indigo-600 hover:bg-indigo-500 text-white px-4 py-2 rounded-lg font-medium text-xs flex items-center space-x-1.5 transition shadow-md cursor-pointer">
                <span class="material-icons-round text-sm">add</span><span>Nouvelle Vidéo</span>
            </button>
        </div>
    </header>

    <div class="flex-1 flex overflow-hidden">
        <main id="view-kanban" class="flex-1 p-6 overflow-x-auto flex space-x-4 items-start content-start">
            <div class="bg-slate-800/60 border border-slate-700/50 w-72 shrink-0 rounded-xl p-4 flex flex-col max-h-[80vh]">
                <div class="flex justify-between items-center mb-4">
                    <h3 class="font-semibold text-xs text-slate-400 tracking-wide uppercase flex items-center"><span class="w-2 h-2 rounded-full bg-amber-500 mr-2"></span>Pool d'attente</h3>
                    <span id="count-pool" class="bg-slate-700 text-slate-300 text-xs px-2 py-0.5 rounded-full font-bold">0</span>
                </div>
                <div id="col-pool" class="column-body space-y-3 overflow-y-auto pr-1" ondragover="allowDrop(event)" ondrop="drop(event, 'pool')"></div>
            </div>
            <div class="bg-slate-800/60 border border-slate-700/50 w-72 shrink-0 rounded-xl p-4 flex flex-col max-h-[80vh]">
                <div class="flex justify-between items-center mb-4">
                    <h3 class="font-semibold text-xs text-slate-400 tracking-wide uppercase flex items-center"><span class="w-2 h-2 rounded-full bg-blue-500 mr-2"></span>En cours de montage</h3>
                    <span id="count-montage" class="bg-slate-700 text-slate-300 text-xs px-2 py-0.5 rounded-full font-bold">0</span>
                </div>
                <div id="col-montage" class="column-body space-y-3 overflow-y-auto pr-1" ondragover="allowDrop(event)" ondrop="drop(event, 'montage')"></div>
            </div>
            <div class="bg-slate-800/60 border border-slate-700/50 w-72 shrink-0 rounded-xl p-4 flex flex-col max-h-[80vh]">
                <div class="flex justify-between items-center mb-4">
                    <h3 class="font-semibold text-xs text-slate-400 tracking-wide uppercase flex items-center"><span class="w-2 h-2 rounded-full bg-purple-500 mr-2"></span>À valider</h3>
                    <span id="count-validation" class="bg-slate-700 text-slate-300 text-xs px-2 py-0.5 rounded-full font-bold">0</span>
                </div>
                <div id="col-validation" class="column-body space-y-3 overflow-y-auto pr-1" ondragover="allowDrop(event)" ondrop="drop(event, 'validation')"></div>
            </div>
            <div class="bg-slate-800/60 border border-slate-700/50 w-72 shrink-0 rounded-xl p-4 flex flex-col max-h-[80vh]">
                <div class="flex justify-between items-center mb-4">
                    <h3 class="font-semibold text-xs text-slate-400 tracking-wide uppercase flex items-center"><span class="w-2 h-2 rounded-full bg-pink-500 mr-2"></span>En attente de Prog</h3>
                    <span id="count-attente-prog" class="bg-slate-700 text-slate-300 text-xs px-2 py-0.5 rounded-full font-bold">0</span>
                </div>
                <div id="col-attente-prog" class="column-body space-y-3 overflow-y-auto pr-1" ondragover="allowDrop(event)" ondrop="drop(event, 'attente-prog')"></div>
            </div>
            <div class="bg-slate-800/60 border border-slate-700/50 w-72 shrink-0 rounded-xl p-4 flex flex-col max-h-[80vh]">
                <div class="flex justify-between items-center mb-4">
                    <h3 class="font-semibold text-xs text-slate-400 tracking-wide uppercase flex items-center"><span class="w-2 h-2 rounded-full bg-green-500 mr-2"></span>Programmées</h3>
                    <span id="count-programme" class="bg-slate-700 text-slate-300 text-xs px-2 py-0.5 rounded-full font-bold">0</span>
                </div>
                <div id="col-programme" class="column-body space-y-3 overflow-y-auto pr-1" ondragover="allowDrop(event)" ondrop="drop(event, 'programme')"></div>
            </div>
        </main>

        <main id="view-calendar" class="hidden flex-1 p-6 flex space-x-6 overflow-hidden">
            <div class="bg-slate-800/80 border border-slate-700 w-80 shrink-0 rounded-xl p-4 flex flex-col h-full">
                <h3 class="font-bold text-sm text-slate-200 mb-3 flex items-center">
                    <span class="material-icons-round text-pink-400 text-base mr-1.5">hourglass_empty</span>À programmer
                </h3>
                <div id="cal-sidebar-backlog" class="flex-1 space-y-3 overflow-y-auto pr-1" ondragover="allowDrop(event)" ondrop="drop(event, 'attente-prog')"></div>
            </div>
            <div class="flex-1 bg-slate-800/40 border border-slate-700 rounded-xl p-4 flex flex-col h-full overflow-y-auto">
                <div class="flex justify-between items-center mb-4">
                    <h2 id="calendar-month-year" class="text-lg font-bold text-white capitalize">Mois Année</h2>
                    <div class="flex space-x-2 bg-slate-800 rounded-lg p-0.5 border border-slate-700">
                        <button onclick="changeMonth(-1)" class="p-1.5 text-slate-400 hover:text-white rounded hover:bg-slate-700 cursor-pointer"><span class="material-icons-round block">chevron_left</span></button>
                        <button onclick="changeMonth(0)" class="px-3 text-xs font-medium text-slate-300 hover:text-white rounded hover:bg-slate-700 cursor-pointer">Aujourd'hui</button>
                        <button onclick="changeMonth(1)" class="p-1.5 text-slate-400 hover:text-white rounded hover:bg-slate-700 cursor-pointer"><span class="material-icons-round block">chevron_right</span></button>
                    </div>
                </div>
                <div class="calendar-grid text-center text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2 border-b border-slate-700/50 pb-2">
                    <div>Lun</div><div>Mar</div><div>Mer</div><div>Jeu</div><div>Ven</div><div>Sam</div><div>Dim</div>
                </div>
                <div id="calendar-days-grid" class="calendar-grid flex-1 gap-1.5 min-h-[500px]"></div>
            </div>
        </main>

        <main id="view-settings" class="hidden flex-1 p-6 grid grid-cols-1 md:grid-cols-2 gap-6 overflow-y-auto">
            <div class="bg-slate-800 border border-slate-700 rounded-xl p-5 flex flex-col h-fit">
                <h2 class="text-base font-bold text-white mb-4 flex items-center"><span class="material-icons-round text-indigo-400 mr-2">storefront</span>Restaurateurs (Clients)</h2>
                <form onsubmit="addClient(event)" class="flex gap-2 mb-4">
                    <input type="text" id="new-client-name" required placeholder="Nom du restaurant..." class="flex-1 bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-sm">
                    <input type="color" id="new-client-color" value="#6366f1" class="w-10 h-9 cursor-pointer">
                    <button type="submit" class="bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-medium px-4 rounded-lg">Ajouter</button>
                </form>
                <div id="settings-clients-list" class="space-y-2 max-h-60 overflow-y-auto"></div>
            </div>
            <div class="bg-slate-800 border border-slate-700 rounded-xl p-5 flex flex-col h-fit">
                <h2 class="text-base font-bold text-white mb-4 flex items-center"><span class="material-icons-round text-emerald-400 mr-2">groups</span>Équipe / Staff</h2>
                <form onsubmit="addStaff(event)" class="flex gap-2 mb-4">
                    <input type="text" id="new-staff-name" required placeholder="Nom du collaborateur..." class="flex-1 bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-sm">
                    <button type="submit" class="bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-medium px-4 rounded-lg">Ajouter</button>
                </form>
                <div id="settings-staff-list" class="space-y-2 max-h-60 overflow-y-auto"></div>
            </div>
        </main>
    </div>

    <div id="videoModal" class="hidden fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4">
        <div class="bg-slate-800 border border-slate-700 rounded-2xl w-full max-w-md p-6 shadow-2xl relative">
            <button onclick="toggleModal(false)" class="absolute top-4 right-4 text-slate-400 hover:text-white cursor-pointer"><span class="material-icons-round">close</span></button>
            <h2 id="modalTitle" class="text-lg font-bold mb-4 text-white">Créer une vidéo</h2>
            <form id="videoForm" class="space-y-4" onsubmit="handleFormSubmit(event)">
                <input type="hidden" id="edit-id">
                <div>
                    <label class="block text-xs font-semibold uppercase text-slate-400 mb-1">Titre de la vidéo *</label>
                    <input type="text" id="title" required class="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white">
                </div>
                <div class="grid grid-cols-2 gap-4">
                    <div>
                        <label class="block text-xs font-semibold uppercase text-slate-400 mb-1">Restaurateur *</label>
                        <select id="client-select" required class="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200"></select>
                    </div>
                    <div>
                        <label class="block text-xs font-semibold uppercase text-slate-400 mb-1">Assigné à</label>
                        <select id="assigned-select" class="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200"></select>
                    </div>
                </div>
                <div class="grid grid-cols-2 gap-4">
                    <div>
                        <label class="block text-xs font-semibold uppercase text-slate-400 mb-1">Réseau Principal</label>
                        <select id="platform" class="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-300">
                            <option value="TikTok">TikTok 📱</option>
                            <option value="Instagram">Instagram Reels 📸</option>
                            <option value="Les deux">Les deux ✨</option>
                        </select>
                    </div>
                    <div>
                        <label class="block text-xs font-semibold uppercase text-slate-400 mb-1">Étape du Workflow *</label>
                        <select id="status" class="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-300">
                            <option value="pool">Pool d'attente ⏳</option>
                            <option value="montage">En cours de montage 🎬</option>
                            <option value="validation">À valider 👀</option>
                            <option value="attente-prog">En attente de prog ⏸️</option>
                            <option value="programme">Programmé 📅</option>
                        </select>
                    </div>
                </div>
                <div>
                    <label class="block text-xs font-semibold uppercase text-slate-400 mb-1">Date de programmation</label>
                    <input type="date" id="prodDate" class="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-300">
                </div>
                <div>
                    <label class="block text-xs font-semibold uppercase text-slate-400 mb-1">Lien de livraison / Drive</label>
                    <input type="url" id="driveLink" class="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white" placeholder="https://...">
                </div>
                <div class="pt-2 flex space-x-3">
                    <button type="button" id="btn-delete" onclick="triggerDelete()" class="hidden bg-rose-600/20 text-rose-400 hover:bg-rose-600 hover:text-white px-3 rounded-lg text-sm transition"><span class="material-icons-round block">delete</span></button>
                    <button type="button" onclick="toggleModal(false)" class="flex-1 bg-slate-700 text-slate-200 py-2 rounded-lg font-medium text-xs">Annuler</button>
                    <button type="submit" class="flex-1 bg-indigo-600 text-white py-2 rounded-lg font-medium text-xs shadow-md">Enregistrer</button>
                </div>
            </form>
        </div>
    </div>

    <div id="bulkModal" class="hidden fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4">
        <div class="bg-slate-800 border border-slate-700 rounded-2xl w-full max-w-lg p-6 shadow-2xl relative">
            <button onclick="toggleBulkModal(false)" class="absolute top-4 right-4 text-slate-400 hover:text-white cursor-pointer"><span class="material-icons-round">close</span></button>
            <h2 class="text-lg font-bold mb-2 text-white">Création groupée de vidéos</h2>
            <form onsubmit="handleBulkSubmit(event)" class="space-y-4">
                <div class="grid grid-cols-2 gap-4">
                    <div>
                        <label class="block text-xs font-semibold uppercase text-slate-400 mb-1">Restaurateur *</label>
                        <select id="bulk-client-select" required class="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200"></select>
                    </div>
                    <div>
                        <label class="block text-xs font-semibold uppercase text-slate-400 mb-1">Réseau Principal</label>
                        <select id="bulk-platform" class="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-300">
                            <option value="TikTok">TikTok 📱</option>
                            <option value="Instagram">Instagram Reels 📸</option>
                            <option value="Les deux">Les deux ✨</option>
                        </select>
                    </div>
                </div>
                <div>
                    <label class="block text-xs font-semibold uppercase text-slate-400 mb-1">Titres des Vidéos (Un par ligne) *</label>
                    <textarea id="bulk-titles" required rows="5" placeholder="Vidéo 1&#10;Vidéo 2" class="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white"></textarea>
                </div>
                <div class="pt-2 flex space-x-3">
                    <button type="button" onclick="toggleBulkModal(false)" class="w-1/3 bg-slate-700 text-slate-200 py-2 rounded-lg font-medium text-xs">Annuler</button>
                    <button type="submit" class="flex-1 bg-indigo-600 text-white py-2 rounded-lg font-medium text-xs">Générer</button>
                </div>
            </form>
        </div>
    </div>

    <script>
        let currentView = 'kanban';
        let currentDate = new Date();

        // INJECTION DIRECTE DES DONNÉES DU GOOGLE SHEETS DEPUIS PYTHON
        let clients = {json.dumps(clients_list)};
        let staff = {json.dumps(staff_list)};
        let videos = {json.dumps(videos_list)};

        // Nettoyage des formats de données Pandas (NaN vers chaînes vides)
        videos = videos.map(v => ({{
            id: String(v.id || ''),
            title: String(v.title || ''),
            clientId: String(v.clientId || ''),
            staffId: String(v.staffId || ''),
            platform: String(v.platform || 'TikTok'),
            date: String(v.date || '') === 'nan' ? '' : String(v.date || ''),
            link: String(v.link || '#'),
            status: String(v.status || 'pool')
        }}));

        // FONCTION DE SAUVEGARDE EN LIGNE (Envoi vers Python Streamlit)
        function saveAll() {{
            const payload = JSON.stringify({{ videos, clients, staff }});
            // On utilise l'URL de Streamlit pour lui passer les nouvelles données
            const url = new URL(window.location.href);
            url.searchParams.set("action", "save_all");
            url.searchParams.set("data", payload);
            window.location.href = url.href; // Provoque le rafraîchissement et la sauvegarde Cloud
        }}

        function switchView(view) {{
            currentView = view;
            document.getElementById('view-kanban').classList.toggle('hidden', view !== 'kanban');
            document.getElementById('view-calendar').classList.toggle('hidden', view !== 'calendar');
            document.getElementById('view-settings').classList.toggle('hidden', view !== 'settings');
            renderAll();
        }}

        function populateDropdowns() {{
            const selects = ['client-select', 'bulk-client-select'];
            selects.forEach(sId => {{
                const el = document.getElementById(sId);
                if(!el) return;
                el.innerHTML = '';
                clients.forEach(c => el.innerHTML += `<option value="${{c.id}}">${{c.name}}</option>`);
            }});
            const staffSelect = document.getElementById('assigned-select');
            if(staffSelect) {{
                staffSelect.innerHTML = '<option value="">Non assigné</option>';
                staff.forEach(s => staffSelect.innerHTML += `<option value="${{s.id}}">${{s.name}}</option>`);
            }}
        }}

        function addClient(e) {{
            e.preventDefault();
            const name = document.getElementById('new-client-name').value;
            const color = document.getElementById('new-client-color').value;
            clients.push({{ id: 'c_' + Date.now(), name, color }});
            saveAll();
        }}

        function removeClient(id) {{
            if(confirm("Supprimer ce restaurateur ?")) {{
                clients = clients.filter(c => c.id !== id);
                saveAll();
            }}
        }}

        function addStaff(e) {{
            e.preventDefault();
            const name = document.getElementById('new-staff-name').value;
            staff.push({{ id: 's_' + Date.now(), name }});
            saveAll();
        }}

        function removeStaff(id) {{
            if(confirm("Supprimer ce membre ?")) {{
                staff = staff.filter(s => s.id !== id);
                saveAll();
            }}
        }}

        function toggleModal(show) {{ document.getElementById('videoModal').classList.toggle('hidden', !show); }}
        function toggleBulkModal(show) {{ document.getElementById('bulkModal').classList.toggle('hidden', !show); }}

        function openModalForAdd(defaultDate = '') {{
            if(clients.length === 0) {{ alert("Ajoutez d'abord un client dans Clients & Staff."); return; }}
            document.getElementById('modalTitle').innerText = "Créer une vidéo";
            document.getElementById('videoForm').reset();
            document.getElementById('edit-id').value = '';
            document.getElementById('status').value = defaultDate ? 'programme' : 'pool';
            document.getElementById('prodDate').value = defaultDate;
            document.getElementById('btn-delete').classList.add('hidden');
            toggleModal(true);
        }}

        function openModalForEdit(id) {{
            const v = videos.find(item => item.id === id);
            if(!v) return;
            document.getElementById('modalTitle').innerText = "Paramètres";
            document.getElementById('edit-id').value = v.id;
            document.getElementById('title').value = v.title;
            document.getElementById('client-select').value = v.clientId;
            document.getElementById('assigned-select').value = v.staffId || "";
            document.getElementById('platform').value = v.platform;
            document.getElementById('status').value = v.status;
            document.getElementById('prodDate').value = v.date;
            document.getElementById('driveLink').value = v.link === "#" ? "" : v.link;
            document.getElementById('btn-delete').classList.remove('hidden');
            toggleModal(true);
        }}

        function handleFormSubmit(e) {{
            e.preventDefault();
            const id = document.getElementById('edit-id').value;
            const status = document.getElementById('status').value;
            const date = document.getElementById('prodDate').value;

            if (status === 'programme' && !date) {{ alert('Date requise.'); return; }}

            const data = {{
                title: document.getElementById('title').value,
                clientId: document.getElementById('client-select').value,
                staffId: document.getElementById('assigned-select').value,
                platform: document.getElementById('platform').value,
                status: status,
                date: status === 'programme' ? date : '',
                link: document.getElementById('driveLink').value || "#"
            }};

            if(id) {{
                const idx = videos.findIndex(v => v.id === id);
                if(idx !== -1) videos[idx] = {{ id, ...data }};
            }} else {{
                videos.push({{ id: String(Date.now()), ...data }});
            }}
            saveAll();
        }}

        function triggerDelete() {{
            const id = document.getElementById('edit-id').value;
            if(id && confirm("Supprimer ?")) {{
                videos = videos.filter(v => v.id !== id);
                saveAll();
            }}
        }}

        function openBulkModal() {{
            if(clients.length === 0) {{ alert("Configurez un client d'abord."); return; }}
            document.getElementById('bulk-titles').value = '';
            toggleBulkModal(true);
        }}

        function handleBulkSubmit(e) {{
            e.preventDefault();
            const clientId = document.getElementById('bulk-client-select').value;
            const platform = document.getElementById('bulk-platform').value;
            const rawTitles = document.getElementById('bulk-titles').value.split('\n');

            rawTitles.forEach(t => {{
                const clean = t.trim();
                if(clean.length > 0) {{
                    videos.push({{
                        id: 'b_' + Math.random().toString(36).substr(2, 5),
                        title: clean,
                        clientId: clientId,
                        staffId: "",
                        platform: platform,
                        status: 'pool',
                        date: '',
                        link: '#'
                    }});
                }}
            }});
            saveAll();
        }}

        function createCard(v) {{
            const clientObj = clients.find(c => String(c.id) === String(v.clientId)) || {{ name: 'Inconnu', color: '#64748b' }};
            const staffObj = staff.find(s => String(s.id) === String(v.staffId)) || {{ name: 'Non assigné' }};
            const pColor = v.platform === 'TikTok' ? 'bg-cyan-500/20 text-cyan-300' : v.platform === 'Instagram' ? 'bg-fuchsia-500/20 text-fuchsia-300' : 'bg-indigo-500/20 text-indigo-300';
            const dateBadge = v.date ? `<div class="mt-2 text-[10px] text-green-400 font-medium flex items-center"><span class="material-icons-round text-xs mr-1">calendar_today</span> ${{formatDateString(v.date)}}</div>` : '';

            return `
                <div class="bg-slate-700/60 hover:bg-slate-700 border-l-4 p-3 rounded-xl shadow transition-all cursor-grab active:cursor-grabbing group relative" 
                     style="border-color: ${{clientObj.color}}" draggable="true" id="${{v.id}}" ondragstart="drag(event)" ondragend="dragEnd(event)" onclick="openModalForEdit('${{v.id}}')">
                    <div class="flex items-center justify-between mb-1">
                        <span class="text-[9px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded ${pColor}">${{v.platform}}</span>
                        <span class="text-[10px] font-bold px-2 py-0.5 rounded-full" style="background-color: ${{clientObj.color}}20; color: ${{clientObj.color}}">${{clientObj.name}}</span>
                    </div>
                    <h4 class="font-semibold text-xs text-white leading-tight mb-2">${{v.title}}</h4>
                    <div class="flex items-center text-[10px] text-slate-400">
                        <span class="material-icons-round text-xs mr-1 text-slate-500">account_circle</span>
                        <span class="truncate">${{staffObj.name}}</span>
                    </div>
                    ${{dateBadge}}
                </div>
            `;
        }

        function renderAll() {{
            populateDropdowns();
            if(currentView === 'kanban') {{
                const cols = {{ pool: [], montage: [], validation: [], 'attente-prog': [], programme: [] }};
                videos.forEach(v => {{ if(cols[v.status]) cols[v.status].push(v); }});
                Object.keys(cols).forEach(cName => {{
                    document.getElementById(`count-${{cName}}`).innerText = cols[cName].length;
                    const box = document.getElementById(`col-${{cName}}`);
                    box.innerHTML = '';
                    cols[cName].forEach(v => box.innerHTML += createCard(v));
                }});
            } else if(currentView === 'calendar') {{
                const side = document.getElementById('cal-sidebar-backlog');
                side.innerHTML = '';
                videos.filter(v => v.status === 'attente-prog').forEach(v => side.innerHTML += createCard(v));
                renderCalendarGrid();
            }} else {{
                const cBox = document.getElementById('settings-clients-list');
                cBox.innerHTML = '';
                clients.forEach(c => {{
                    cBox.innerHTML += `
                        <div class="flex justify-between items-center bg-slate-900 px-3 py-2 rounded-lg border border-slate-700">
                            <div class="flex items-center space-x-2">
                                <span class="w-3 h-3 rounded-full" style="background-color: ${{c.color}}"></span>
                                <span class="text-sm font-medium text-slate-200">${{c.name}}</span>
                            </div>
                            <button onclick="removeClient('${{c.id}}')" class="text-slate-500 hover:text-rose-400 transition cursor-pointer"><span class="material-icons-round text-sm">delete</span></button>
                        </div>
                    `;
                }});
                const sBox = document.getElementById('settings-staff-list');
                sBox.innerHTML = '';
                staff.forEach(s => {{
                    sBox.innerHTML += `
                        <div class="flex justify-between items-center bg-slate-900 px-3 py-2 rounded-lg border border-slate-700">
                            <span class="text-sm text-slate-200 font-medium">${{s.name}}</span>
                            <button onclick="removeStaff('${{s.id}}')" class="text-slate-500 hover:text-rose-400 transition cursor-pointer"><span class="material-icons-round text-sm">delete</span></button>
                        </div>
                    `;
                }});
            }}
        }

        function renderCalendarGrid() {{
            const grid = document.getElementById('calendar-days-grid');
            grid.innerHTML = '';
            const y = currentDate.getFullYear();
            const m = currentDate.getMonth();
            document.getElementById('calendar-month-year').innerText = currentDate.toLocaleDateString('fr-FR', {{ month: 'long', year: 'numeric' }});
            const firstDay = (new Date(y, m, 1).getDay() + 6) % 7;
            const totalDays = new Date(y, m + 1, 0).getDate();

            for (let i = 0; i < firstDay; i++) grid.innerHTML += `<div class="bg-slate-800/10 border border-slate-800/30 rounded-lg opacity-10"></div>`;

            for (let d = 1; d <= totalDays; d++) {{
                const dStr = `${{y}}-${{String(m + 1).padStart(2, '0')}}-${{String(d).padStart(2, '0')}}`;
                const matchedVids = videos.filter(v => v.status === 'programme' && v.date === dStr);
                let inlineHTML = '';
                matchedVids.forEach(v => {{
                    const cObj = clients.find(c => String(c.id) === String(v.clientId)) || {{ name: '?', color: '#indigo' }};
                    inlineHTML += `
                        <div onclick="event.stopPropagation(); openModalForEdit('${{v.id}}')" class="text-[10px] p-1 rounded font-medium truncate border mb-1 text-white" 
                             style="background-color: ${{cObj.color}}cc; border-color: ${{cObj.color}}">
                            [${{cObj.name}}] ${{v.title}}
                        </div>
                    `;
                }});
                const isToday = new Date().toDateString() === new Date(y, m, d).toDateString() ? 'border-2 border-indigo-500 bg-slate-800' : 'border-slate-700/60 bg-slate-800/40';
                const cell = document.createElement('div');
                cell.className = `${{isToday}} border rounded-xl p-1.5 flex flex-col min-h-[95px] overflow-hidden hover:bg-slate-800/70 transition`;
                cell.setAttribute('ondragover', 'allowDrop(event)');
                cell.setAttribute('ondrop', `dropOnDate(event, '${{dStr}}')`);
                cell.setAttribute('onclick', `openModalForAdd('${{dStr}}')`);
                cell.innerHTML = `<div class="text-right text-xs font-bold text-slate-500 mb-1">${{d}}</div><div class="flex-1 overflow-y-auto space-y-0.5">${{inlineHTML}}</div>`;
                grid.appendChild(cell);
            }}
        }

        function changeMonth(dir) {{
            if(dir === 0) currentDate = new Date();
            else currentDate.setMonth(currentDate.getMonth() + dir);
            renderCalendarGrid();
        }}

        function formatDateString(str) {{
            return new Date(str).toLocaleDateString('fr-FR', {{ day: 'numeric', month: 'short' }});
        }}

        function drag(ev) {{ ev.dataTransfer.setData("text/plain", ev.target.id); ev.target.classList.add('dragging'); }}
        function dragEnd(ev) {{ ev.target.classList.remove('dragging'); }}
        function allowDrop(ev) {{ ev.preventDefault(); }}
        
        function drop(ev, destStatus) {{
            ev.preventDefault();
            const id = ev.dataTransfer.getData("text/plain");
            const idx = videos.findIndex(v => v.id === id);
            if(idx !== -1) {{
                if(destStatus === 'programme' && !videos[idx].date) {{
                    const d = prompt("Date requise (AAAA-MM-JJ) :");
                    if(!d) return;
                    videos[idx].date = d;
                }}
                if(destStatus !== 'programme') videos[idx].date = '';
                videos[idx].status = destStatus;
                saveAll();
            }}
        }

        function dropOnDate(ev, dateStr) {{
            ev.preventDefault(); ev.stopPropagation();
            const id = ev.dataTransfer.getData("text/plain");
            const idx = videos.findIndex(v => v.id === id);
            if(idx !== -1) {{
                videos[idx].status = 'programme';
                videos[idx].date = dateStr;
                saveAll();
            }}
        }}

        renderAll();
    </script>
</body>
</html>
"""

components.html(html_code, height=950, scrolling=True)
