import streamlit as st
import json
import datetime
import os
import time
import pytz
import gspread
from google.oauth2.service_account import Credentials
from streamlit.components.v1 import html as components_html

# ==========================================
# 1. CONFIGURACIÓN Y ESTILO
# ==========================================

st.set_page_config(
    page_title="PAU Tracker Elite", 
    page_icon="🎓", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# Constantes del Sistema
MIN_MINUTES_PER_TASK = 40  # Mínimo tiempo productivo por tarea (Técnica Pomodoro)

# Estilos CSS Personalizados para modo Dark/Elite
st.markdown("""
    <style>
    .stButton button { width: 100%; border-radius: 6px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px;}
    div[data-testid="stMetricValue"] { font-size: 2.2rem; color: #ff4b4b; font-weight: 700;}
    h1, h2, h3 { font-family: 'Helvetica Neue', sans-serif; }
    .css-1d391kg { padding-top: 1rem; }
    div.stProgress > div > div > div > div { background-color: #ff4b4b; }
    /* Estilo para notas */
    .stTextArea textarea { font-family: 'Courier New', monospace; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. BASE DE DATOS (SYLLABUS COMPLETO 2025)
# ==========================================

DEFAULT_SYLLABUS = {
    "Matemáticas II": {
        "category": "science",
        "topics": [
            "1. Límites y Continuidad (Asíntotas, Bolzano)",
            "2. Derivadas (Reglas, L'Hôpital, Rolle/Lagrange)",
            "3. Representación de Funciones (Optimización, Curvatura)",
            "4. Integral Indefinida (Métodos: Partes, Racionales, Trigonométricas)",
            "5. Integral Definida (Áreas, Regla de Barrow)",
            "6. Matrices (Operaciones, Rango, Inversa)",
            "7. Determinantes (Sarrus, Propiedades, Menores)",
            "8. Sistemas de Ecuaciones (Gauss, Rouché-Frobenius, Cramer)",
            "9. Vectores (Producto Escalar, Vectorial y Mixto)",
            "10. Rectas y Planos (Ecuaciones, Haz de planos)",
            "11. Posiciones Relativas (Rectas y Planos)",
            "12. Ángulos y Distancias (Métrica espacial)"
        ]
    },
    "Física": {
        "category": "science",
        "topics": [
            "Herramientas matemáticas (Vectores)",
            "Vibraciones: M.A.S.",
            "Ondas Mecánicas y Sonido",
            "Óptica Geométrica (Espejos y Lentes)",
            "Campo Gravitatorio (Fuerzas y Energías)",
            "Campo Eléctrico (Cargas y Potencial)",
            "Campo Magnético (Fuentes y Fuerzas)",
            "Inducción Electromagnética",
            "Física Moderna: Relatividad Especial",
            "Física Cuántica (Efecto Fotoeléctrico)",
            "Física Nuclear (Radiactividad)"
        ]
    },
    "Química": {
        "category": "science",
        "topics": [
            "T1: Estructura de la materia (Átomo)",
            "T2: Enlace Químico (Iónico, Covalente, Metálico)",
            "T3: Termoquímica (Entalpía y Entropía)",
            "T4: Cinética Química (Velocidad reacción)",
            "T5: Equilibrio Químico (Le Chatelier)",
            "T6: Reacciones Ácido-Base",
            "T7: Reacciones REDOX (Pilas y Electrólisis)",
            "T8: Química del Carbono (Orgánica)"
        ]
    },
    "Historia de España": {
        "category": "memory",
        "topics": [
            "B1-B2: Raíces Históricas (Prehistoria - Edad Media)",
            "B3: Edad Moderna (RRCC, América, Austrias)",
            "B4: Crisis Antiguo Régimen (1788-1833)",
            "B5: Estado Liberal (Isabel II y Sexenio)",
            "B6: La Restauración (1874-1902)",
            "B7: Transformaciones Económicas s.XIX",
            "B8: Alfonso XIII y Crisis de la Restauración",
            "B9: La Segunda República (1931-1936)",
            "B10: La Guerra Civil (1936-1939)",
            "B11: La Dictadura Franquista (1939-1975)",
            "B12: La Transición (1975-1982)",
            "B13: Democracia y Constitución 1978"
        ]
    },
    "Historia de la Filosofía": {
        "category": "memory",
        "topics": [
            "Platón",
            "Aristóteles",
            "Agustín de Hipona",
            "Tomás de Aquino",
            "Descartes",
            "Hume",
            "Rousseau",
            "Kant",
            "Marx",
            "Nietzsche",
            "Ortega y Gasset",
            "Hannah Arendt"
        ]
    },
    "Lengua y Literatura": {
        "category": "memory",
        "topics": [
            "Semántica y Lexicología (Sinonimia, Campos semánticos)",
            "Morfología (Análisis de palabras)",
            "Sintaxis (Oración Simple y Compuesta)",
            "Lit: Realismo y Naturalismo (s.XIX)",
            "Lit: Generación del 98 y Modernismo",
            "Lit: Novecentismo y Vanguardias (Gen 14)",
            "Lit: Generación del 27",
            "Lit: Teatro y Poesía tras 1936",
            "Lit: Novela Española 1939-1975",
            "Lit: Novela Española desde 1975",
            "Lit: Literatura Hispanoamericana (Boom)"
        ]
    },
    "Inglés": {
        "category": "skills",
        "topics": [
            "Grammar: Tenses Mix & Passive Voice",
            "Grammar: Reported Speech",
            "Grammar: Conditionals & Wish Clauses",
            "Grammar: Modals & Relative Clauses",
            "Vocabulary: Connectors & Synonyms",
            "Writing: Opinion Essay",
            "Writing: For & Against Essay",
            "Reading Comprehension Practice"
        ]
    }
}

# ==========================================
# 3. GESTIÓN DE DATOS (CONECTADO A GOOGLE SHEETS)
# ==========================================

@st.cache_resource
def get_google_sheet():
    """Conecta con Google Sheets usando st.secrets"""
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds_dict = dict(st.secrets["gcp_service_account"])
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    client = gspread.authorize(creds)
    sh = client.open_by_url(st.secrets["sheets"]["sheet_url"])
    return sh.sheet1 

def create_defaults():
    new_data = {
        "general_notes": [] # Estructura para notas manuales
    }
    for subject, info in DEFAULT_SYLLABUS.items():
        new_data[subject] = []
        for topic in info["topics"]:
            new_data[subject].append({
                "name": topic,
                "category": info["category"],
                "unlocked": False,       
                "level": 0,              
                "next_review": str(datetime.date.today()),
                "last_error": "",
                "extra_queue": False     
            })
    return new_data

def load_data():
    """Carga los datos desde la celda A1 de Google Sheets"""
    try:
        sheet = get_google_sheet()
        raw_data = sheet.acell('A1').value
        
        if raw_data:
            data = json.loads(raw_data)
            # Asegurar compatibilidad si se añaden claves nuevas (como notas)
            if "general_notes" not in data:
                data["general_notes"] = []
            
            # Chequeo de integridad: Si hay nuevas asignaturas en el código que no están en la BD, añadirlas
            for subj, info in DEFAULT_SYLLABUS.items():
                if subj not in data:
                    data[subj] = []
                    for topic in info["topics"]:
                        data[subj].append({
                            "name": topic,
                            "category": info["category"],
                            "unlocked": False, "level": 0, 
                            "next_review": str(datetime.date.today()), 
                            "last_error": "", "extra_queue": False
                        })
            return data
        else:
            defaults = create_defaults()
            save_data(defaults)
            return defaults
    except Exception as e:
        st.error(f"Error conectando con la base de datos: {e}")
        return create_defaults()

def save_data(data):
    """Guarda los datos en la celda A1 de Google Sheets"""
    try:
        sheet = get_google_sheet()
        json_str = json.dumps(data)
        sheet.update_acell('A1', json_str)
    except Exception as e:
        st.error(f"Error guardando datos: {e}")

# ==========================================
# 4. FUNCIONES VISUALES (RELOJ)
# ==========================================

def show_modern_clock(target_hour_float):
    """
    Reloj renderizado en HTML/JS para evitar desconexiones, 
    con estilo ajustado para que no se corte el borde.
    """
    if not target_hour_float: return

    th = int(target_hour_float)
    tm = int(round((target_hour_float - th) * 60))
    uid = f"clock_{int(time.time()*1000)}"

    html = f"""
    <div class="clock-container">
        <div class="clock-box" id="{uid}_wrap">
          <div class="clock-label">TIEMPO RESTANTE DE BLOQUE</div>
          <div id="{uid}" class="clock-time">--:--:--</div>
          <div class="clock-target">Objetivo: {th:02d}:{tm:02d}</div>
        </div>
    </div>

    <style>
      /* Reset básico para evitar márgenes extraños */
      body {{ margin: 0; padding: 0; box-sizing: border-box; }}
      
      .clock-container {{
        display: flex;
        justify-content: center;
        align-items: center;
        padding: 5px; /* Un poco de margen interno para el borde */
        font-family: system-ui, -apple-system, sans-serif;
      }}

      .clock-box {{
        background-color: #11141c;
        border: 2px solid #ff4b4b;
        border-radius: 12px;
        padding: 15px 10px;
        text-align: center;
        width: 100%;
        max-width: 350px; /* Evita que se estire demasiado en pantallas grandes */
        box-sizing: border-box; /* CRUCIAL: Para que el padding no rompa el ancho */
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
      }}

      .clock-label {{ 
        color: #cfcfcf; 
        font-size: 0.7rem; 
        text-transform: uppercase; 
        letter-spacing: 1.5px; 
        margin-bottom: 5px;
      }}

      .clock-time {{ 
        font-size: 2.5rem; 
        font-weight: 700; 
        color: #ff4b4b; 
        line-height: 1.1; 
        margin: 5px 0;
        text-shadow: 0 0 10px rgba(255, 75, 75, 0.2);
      }}

      .clock-target {{ 
        color: #888; 
        font-size: 0.85rem; 
        margin-top: 5px;
      }}
    </style>

    <script>
    (function(){{
      const elId = "{uid}";
      function pad(n) {{ return n < 10 ? "0" + n : n; }}
      
      function updateOnce() {{
        const el = document.getElementById(elId);
        if(!el) return false;
        
        const now = new Date();
        const target = new Date();
        target.setHours({th}, {tm}, 0, 0);
        
        let diff = target - now;
        
        // Si ya pasó la hora, mostrar 00:00:00
        if (diff <= 0) {{ 
            el.innerText = "00:00:00"; 
            return true; 
        }}
        
        const h = Math.floor(diff / 3600000);
        const m = Math.floor((diff % 3600000) / 60000);
        const s = Math.floor((diff % 60000) / 1000);
        
        el.innerText = pad(h) + ":" + pad(m) + ":" + pad(s);
        return true;
      }}

      // Lógica de reintento para asegurar que el elemento existe antes de iniciar
      let tries = 0;
      const waiter = setInterval(function() {{
        const ok = updateOnce();
        tries++;
        if (ok || tries > 50) {{ 
            clearInterval(waiter); 
            if (ok) setInterval(updateOnce, 1000); 
        }}
      }}, 100);
    }})();
    </script>
    """
    
    # Aumentamos el height a 160 para dar espacio al borde y la sombra sin que se corte
    components_html(html, height=160, scrolling=False)

# ==========================================
# 5. LÓGICA DE HORARIO
# ==========================================

def get_current_block():
    madrid_tz = pytz.timezone('Europe/Madrid')
    now = datetime.datetime.now(madrid_tz) 
    weekday = now.weekday() 
    hour = now.hour + now.minute / 60.0

    # Miércoles (Día específico según tus notas)
    if weekday in [2]: 
        if 16.0 <= hour < 17.5: return "science", "🔄 Tareas diarias", 90, 17.5
        if 17.5 <= hour < 19.0: return "gym", "🏋️ Gimnasio / Reset", 90, 19.0
        if 19.0 <= hour < 20.5: return "science", "🧪 Bloque Ciencia", 90, 20.5
        if 20.5 <= hour < 21.0: return "break", "🚿 Ducha", 30, 21.0
        if 21.0 <= hour < 21.5: return "break", "🥗 Cena", 30, 21.5
        if 21.5 <= hour < 23.0: return "memory", "🧠 Bloque Memoria (Gold)", 90, 23.0
        if hour > 23.0: return "sleep", "😴 DORMIR", 0, 0

    # Lunes, Martes, Jueves
    elif weekday in [0, 1, 3]: 
        if 15.5 <= hour < 17.0: return "science", "🔄 Tareas diarias", 90, 17.0
        if 17.0 <= hour < 18.5: return "gym", "🏋️ Gimnasio / Reset", 90, 18.5
        if 18.5 <= hour < 20.0: return "science", "🧪 Bloque Ciencia", 90, 20.0
        if 20.0 <= hour < 20.5: return "mix", "Buffer / Inglés", 30, 20.5
        if 20.5 <= hour < 21.0: return "break", "Ducha", 30, 21.0
        if 21.0 <= hour < 21.5: return "break", "🥗 Cena", 30, 21.5
        if 21.5 <= hour < 23.0: return "memory", "🧠 Bloque Memoria (Gold)", 90, 23.0
        if hour >= 23.0: return "sleep", "😴 DORMIR", 0, 0

    # Viernes
    elif weekday == 4: 
        if 16.0 <= hour < 20.0: return "mix", "🔄 Repaso Buffer / Inglés", 240, 20.0
    
    # Sábado
    elif weekday == 5: 
        if 9.5 <= hour < 13.5: return "simulacro", "📝 SIMULACRO REAL", 240, 13.5
    
    # Domingo
    elif weekday == 6: 
        if 18.0 <= hour < 20.0: return "review", "📅 Planificación + Errores", 120, 20.0

    return "free", "⏳ Tiempo Libre", 0, 0

# ==========================================
# 6. INTERFAZ PRINCIPAL
# ==========================================

if 'data' not in st.session_state:
    st.session_state.data = load_data()

data = st.session_state.data
real_type, block_name, duration, end_hour = get_current_block()

with st.sidebar:
    st.title("PAU TRACKER")
    show_modern_clock(end_hour)
    st.markdown("### Estado Actual")
    force_study = st.checkbox("🔥 MODO INTENSO", value=False)
    st.info(f"**{block_name}**")
    if duration > 0: st.metric("Tiempo Bloque", f"{duration} min")
    
    st.divider()
    # Cálculo estadísticas
    total_unlocked = 0
    for subj in data:
        if subj == "general_notes": continue
        total_unlocked += sum(1 for t in data[subj] if t.get("unlocked"))
    st.write(f"📈 Temas activos: **{total_unlocked}**")

tab1, tab2, tab3, tab4 = st.tabs(["🚀 Agenda", "📚 Temario", "📓 Notas y Errores", "⚙️ Ajustes"])

# ==========================================
# TAB 1: AGENDA INTELIGENTE
# ==========================================
with tab1:
    st.header(f"Plan de Acción: {block_name}")
    
    if force_study and real_type in ["gym", "break", "free", "sleep"]: target_type = "mix"
    else: target_type = real_type

    if target_type in ["gym", "break", "sleep", "free"]:
        st.success(f"🛑 **STOP.** Descansa. El cerebro consolida lo estudiado ahora.")
    elif target_type == "review":
        st.info("📅 **Domingo:** Ve a la pestaña '📓 Notas y Errores' y organiza la semana.")
    else:
        tasks = []
        today_date = datetime.date.today()
        
        for subj, topic_list in data.items():
            if subj == "general_notes": continue # Ignorar notas generales aquí
            for i, topic in enumerate(topic_list):
                is_due = (topic["next_review"] <= str(today_date)) or topic["extra_queue"]
                
                # Filtrado inteligente por bloque horario
                match_category = False
                if target_type in ["simulacro", "mix"]: match_category = True
                elif target_type == "science" and (topic["category"] in ["science", "skills"]): match_category = True
                elif target_type == "memory" and topic["category"] == "memory": match_category = True
                
                if topic["unlocked"] and is_due and match_category:
                    due_date = datetime.datetime.strptime(topic["next_review"], "%Y-%m-%d").date()
                    days_overdue = (today_date - due_date).days
                    tasks.append({"subj": subj, "topic": topic, "idx": i, "days_overdue": days_overdue})

        # Algoritmo de Prioridad: 1. Fuego manual, 2. Retraso, 3. Nivel (más difícil primero)
        tasks.sort(key=lambda x: (not x["topic"]["extra_queue"], -x["days_overdue"], x["topic"]["level"]))
        max_tasks = int(duration / MIN_MINUTES_PER_TASK) if duration > 0 else 5
        if max_tasks < 1: max_tasks = 1
        
        selected = tasks[:max_tasks]
        
        if not selected:
            st.success("✅ **¡Al día!** No tienes repasos pendientes. Avanza materia en 'Temario'.")
        else:
            time_per = int(duration / len(selected)) if duration > 0 else 30
            c1, c2, c3 = st.columns(3)
            c1.metric("Tareas Hoy", f"{len(selected)}")
            c2.metric("Min/Tarea", f"{time_per} min")
            c3.metric("Pendientes", f"+{len(tasks) - len(selected)}")
            
            st.divider()

            for t in selected:
                subj = t["subj"]
                idx = t["idx"]
                topic = t["topic"]
                
                with st.container(border=True):
                    col_det, col_acc = st.columns([0.7, 0.3])
                    with col_det:
                        badges = []
                        if topic["extra_queue"]: badges.append("🔥 URGENTE")
                        if t["days_overdue"] > 5: badges.append("💀 RETRASADO")
                        st.caption(f"{' '.join(badges)} • {subj}")
                        st.subheader(topic["name"])
                        st.progress(topic['level']/5)
                        if topic["last_error"]: st.error(f"⚠️ Fallo previo: {topic['last_error']}")
                    
                    with col_acc:
                        st.write("**Evaluación**")
                        b1, b2, b3 = st.columns(3)
                        # Botones Repaso Espaciado
                        if b1.button("✅", key=f"ok_{subj}_{idx}"):
                            topic["level"] = min(topic["level"] + 1, 5)
                            days = (topic["level"] * 5) + 3 
                            topic["next_review"] = str(datetime.date.today() + datetime.timedelta(days=days))
                            topic["extra_queue"] = False
                            save_data(st.session_state.data)
                            st.rerun()
                        if b2.button("🆗", key=f"mid_{subj}_{idx}"):
                            topic["next_review"] = str(datetime.date.today() + datetime.timedelta(days=3))
                            topic["extra_queue"] = False
                            save_data(st.session_state.data)
                            st.rerun()
                        if b3.button("❌", key=f"bad_{subj}_{idx}"):
                            st.session_state[f"fail_{subj}_{idx}"] = True
                            topic["level"] = 1
                            topic["next_review"] = str(datetime.date.today() + datetime.timedelta(days=1))
                            save_data(st.session_state.data)
                            st.rerun()
                    
                    if st.session_state.get(f"fail_{subj}_{idx}", False):
                        with st.form(key=f"frm_{subj}_{idx}"):
                            err_txt = st.text_input("¿Motivo del fallo? (Se guardará en Errores)")
                            if st.form_submit_button("Guardar"):
                                topic["last_error"] = err_txt
                                del st.session_state[f"fail_{subj}_{idx}"]
                                save_data(st.session_state.data)
                                st.rerun()

# ==========================================
# TAB 2: GESTIÓN DE TEMARIO (CON MEMORIA ANTI-CIERRE)
# ==========================================
with tab2:
    st.header("📚 Temario (Syllabus)")
    st.info("Activa (✅) los temas vistos en clase para que entren en la rotación.")
    query = st.text_input("🔍 Buscar tema...")

    # Iteramos sobre una copia de las claves
    for subj in list(data.keys()):
        if subj == "general_notes": continue
        
        try:
            topic_list = data[subj]
            if not isinstance(topic_list, list):
                st.error(f"⚠️ Datos corruptos en: {subj}")
                continue 

            # Cálculos
            count_active = sum(1 for x in topic_list if isinstance(x, dict) and x.get('unlocked'))
            count_total = len(topic_list)
            
            label_expander = str(f"**{subj}** ({count_active}/{count_total})")
            
            # --- TRUCO DE MEMORIA ---
            # Verificamos si esta asignatura fue la última tocada para forzar que se abra
            should_be_expanded = (st.session_state.get("last_active_subj") == subj)

            # Usamos 'expanded=' en lugar de 'key='
            with st.expander(label_expander, expanded=should_be_expanded):
                
                safe_key = f"k_{str(subj).strip().replace(' ', '_')}"
                
                # Input Añadir Tema
                c_in, c_bt = st.columns([0.8, 0.2])
                new_t = c_in.text_input(f"Nuevo tema en {subj}", key=f"new_{safe_key}")
                
                if c_bt.button("➕", key=f"add_{safe_key}") and new_t:
                    if not topic_list:
                        new_category = DEFAULT_SYLLABUS.get(subj, {}).get("category", "memory")
                    else:
                        new_category = topic_list[0].get("category", "memory")

                    topic_list.append({
                        "name": new_t, 
                        "category": new_category, 
                        "unlocked": True, 
                        "level": 0, 
                        "next_review": str(datetime.date.today()), 
                        "last_error": "", 
                        "extra_queue": True
                    })
                    
                    # GUARDAMOS LA ASIGNATURA ACTIVA ANTES DEL RERUN
                    st.session_state["last_active_subj"] = subj
                    save_data(data)
                    st.rerun()
                
                st.markdown("---")
                
                # Listado de temas
                for i, topic in enumerate(topic_list):
                    if not isinstance(topic, dict): continue

                    if query.lower() in topic.get("name", "").lower():
                        cols = st.columns([0.1, 0.6, 0.2, 0.1])
                        
                        # Checkbox
                        is_unlocked = topic.get("unlocked", False)
                        act = cols[0].checkbox("", value=is_unlocked, key=f"chk_{safe_key}_{i}")
                        
                        if act != is_unlocked:
                            topic["unlocked"] = act
                            if act: topic["next_review"] = str(datetime.date.today())
                            
                            # GUARDAMOS LA ASIGNATURA ACTIVA ANTES DEL RERUN
                            st.session_state["last_active_subj"] = subj
                            save_data(data)
                            st.rerun() 
                        
                        cols[1].write(topic.get("name", "Sin nombre"))
                        cols[2].caption(f"Nv. {topic.get('level', 0)}")
                        
                        # Toggle Fuego
                        is_urgent = topic.get("extra_queue", False)
                        urg = cols[3].toggle("🔥", value=is_urgent, key=f"urg_{safe_key}_{i}")
                        
                        if urg != is_urgent:
                            topic["extra_queue"] = urg
                            
                            # GUARDAMOS LA ASIGNATURA ACTIVA ANTES DEL RERUN
                            st.session_state["last_active_subj"] = subj
                            save_data(data)
                            st.rerun()

        except Exception as e:
            st.error(f"Error interno en '{subj}': {e}")
            continue
                        
# ==========================================
# TAB 3: NOTAS Y ERRORES (MODIFICADO)
# ==========================================
with tab3:
    st.header("📓 Notas y Errores")
    
    # --- SECCIÓN 1: AGENDA / NOTAS LIBRES ---
    st.subheader("📝 Agenda & Notas Rápidas")
    
    with st.container(border=True):
        # Input para nueva nota
        c_note, c_add = st.columns([0.85, 0.15])
        new_general_note = c_note.text_input("Escribe una nota, tarea o recordatorio...", key="input_new_note")
        if c_add.button("Añadir", key="btn_add_note") and new_general_note:
            data["general_notes"].insert(0, {"text": new_general_note, "date": str(datetime.date.today())})
            save_data(data)
            st.rerun()
        
        # Listado de notas
        if not data["general_notes"]:
            st.caption("No hay notas guardadas.")
        else:
            for i, note in enumerate(data["general_notes"]):
                cn1, cn2 = st.columns([0.9, 0.1])
                cn1.markdown(f"• {note['text']} <span style='color:grey; font-size:0.8em'>({note['date']})</span>", unsafe_allow_html=True)
                if cn2.button("🗑️", key=f"del_note_{i}"):
                    data["general_notes"].pop(i)
                    save_data(data)
                    st.rerun()

    st.divider()

    # --- SECCIÓN 2: CUADERNO DE ERRORES AUTOMÁTICO ---
    st.subheader("📉 Registro de Fallos (Algoritmo)")
    st.markdown("Errores detectados al estudiar. Elimínalos cuando los hayas superado.")

    has_errors = False
    for subj, topic_list in data.items():
        if subj == "general_notes": continue
        err_topics = [t for t in topic_list if t.get("last_error")]
        if err_topics:
            has_errors = True
            st.markdown(f"**{subj}**")
            for t in err_topics:
                with st.container(border=True):
                    ce1, ce2 = st.columns([0.85, 0.15])
                    with ce1:
                        st.write(f"**{t['name']}**")
                        st.error(f"❌ {t['last_error']}")
                    with ce2:
                        if st.button("Superado", key=f"fix_{t['name']}"):
                            t["last_error"] = ""
                            save_data(data)
                            st.rerun()
    
    if not has_errors:
        st.success("¡Excelente! No hay errores pendientes de repaso en el temario.")

# ==========================================
# TAB 4: AJUSTES
# ==========================================
with tab4:
    st.header("⚙️ Ajustes")
    with st.expander("Gestionar Asignaturas"):
        ns = st.text_input("Nombre Asignatura")
        nc = st.selectbox("Tipo", ["science", "memory", "skills"])
        if st.button("Crear"):
            if ns and ns not in data:
                data[ns] = [{"name": "Tema 1", "category": nc, "unlocked": True, "level": 0, "next_review": str(datetime.date.today()), "last_error": "", "extra_queue": False}]
                save_data(data)
                st.rerun()
        
        st.divider()
        ds = st.selectbox("Eliminar", [k for k in data.keys() if k != "general_notes"])
        if st.button("Eliminar Asignatura"):
            del data[ds]
            save_data(data)
            st.rerun()

    st.markdown("---")
    if st.button("☠️ RESET DE FÁBRICA (Borrar todo)"):
        new_defaults = create_defaults()
        save_data(new_defaults)
        st.session_state.data = new_defaults
        st.rerun()
