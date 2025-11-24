import streamlit as st
import json
import datetime
import os

# ==========================================
# 1. BASE DE DATOS MAESTRA & CONFIG
# ==========================================

FILE_NAME = "pau_ultimate_data.json"

# Datos extraídos de la Guía Maestra 
DEFAULT_SYLLABUS = {
    "Matemáticas II": {
        "category": "science",
        "topics": ["Matrices", "Rango y Inversa", "Determinantes", "Sistemas (Rouché)", "Límites & Continuidad", "Derivadas", "Aplic. Derivada (Optimiz.)", "Integrales", "Geometría Espacial", "Probabilidad"]
    },
    "Física": {
        "category": "science",
        "topics": ["Gravitación (Kepler)", "Campo Eléctrico", "Campo Magnético", "Inducción", "Ondas Mecánicas", "Óptica Geométrica", "Física S.XX (Relatividad/Cuántica)"]
    },
    "Química": {
        "category": "science",
        "topics": ["Estructura Atómica", "Enlace Químico", "Cinética", "Equilibrio Químico", "Ácido-Base", "Redox", "Orgánica"]
    },
    "Tecnología e Ing.": {
        "category": "science",
        "topics": ["Materiales", "Máquinas Térmicas", "Fluidos (Neumática)", "Sistemas Automáticos", "Electrónica Digital"]
    },
    "Historia de España": {
        "category": "memory",
        "topics": ["Raíces (Prehistoria-S.XVIII)", "S.XIX: Crisis A.R.", "S.XIX: Estado Liberal", "S.XX: Alfonso XIII/Primo", "S.XX: II República/Guerra", "S.XX: Franquismo", "Transición"]
    },
    "Hª Filosofía": {
        "category": "memory",
        "topics": ["Platón", "Aristóteles", "Tomás de Aquino", "Descartes", "Hume", "Rousseau", "Kant", "Marx", "Nietzsche", "Ortega y Gasset"]
    },
    "Inglés": {
        "category": "skills",
        "topics": ["Tenses Mix", "Passive Voice", "Reported Speech", "Conditionals", "Writing: Opinion", "Writing: For/Against"]
    }
}

# ==========================================
# 2. FUNCIONES DE GESTIÓN
# ==========================================

def load_data():
    if os.path.exists(FILE_NAME):
        with open(FILE_NAME, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        new_data = {}
        for subject, info in DEFAULT_SYLLABUS.items():
            new_data[subject] = []
            for topic in info["topics"]:
                new_data[subject].append({
                    "name": topic,
                    "category": info["category"],
                    "unlocked": False,      # Si ya se dio en clase
                    "level": 0,             # 0-5
                    "next_review": str(datetime.date.today()),
                    "last_error": "",       # Para el cuaderno de errores
                    "extra_queue": False    # Urgencia manual
                })
        return new_data

def save_data(data):
    with open(FILE_NAME, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

def get_current_block():
    """Lógica del Horario Bloqueado """
    now = datetime.datetime.now()
    weekday = now.weekday() # 0=Lunes
    hour = now.hour + now.minute / 60.0

    # Lunes (0) y Miércoles (2) -> Salida Tardía
    if weekday in [0, 2]:
        if 16.0 <= hour < 17.5: return "science", "🐸 Bloque Ciencia 1", 90
        if 17.5 <= hour < 19.0: return "gym", "🏋️ Gimnasio/Descanso", 90
        if 19.0 <= hour < 19.5: return "break", "🚿 Ducha/Merienda", 30
        if 19.5 <= hour < 21.0: return "science", "🧪 Bloque Ciencia 2", 90
        if 21.0 <= hour < 21.5: return "break", "🥗 Cena (No pantallas)", 30
        if 21.5 <= hour < 22.75: return "memory", "🧠 Bloque Memoria", 75
        if hour >= 23.0: return "sleep", "😴 DORMIR", 0
    
    # Martes (1) y Jueves (3) -> Salida Temprana
    elif weekday in [1, 3]:
        if 15.5 <= hour < 17.0: return "science", "🐸 Bloque Ciencia 1", 90
        if 17.0 <= hour < 18.5: return "gym", "🏋️ Gimnasio", 90
        if 19.0 <= hour < 20.5: return "science", "🧪 Bloque Ciencia 2", 90
        if 21.5 <= hour < 22.75: return "memory", "🧠 Bloque Memoria", 75
        if hour >= 23.0: return "sleep", "😴 DORMIR", 0

    # Viernes (4) - Repaso / Buffer (Asumido libre o mix)
    elif weekday == 4:
        if 16.0 <= hour < 20.0: return "mix", "🔄 Repaso General / Buffer", 240

    # Sábado (5) - Simulacro 
    elif weekday == 5:
        if 9.5 <= hour < 13.5: return "simulacro", "📝 SIMULACRO REAL", 240
        if hour > 14: return "free", "🎉 Tarde Libre", 0

    # Domingo (6) - Planificación 
    elif weekday == 6:
        if hour >= 18.0: return "review", "📅 Planificación + Cuaderno Errores", 60

    return "free", "⏳ Tiempo Libre / Buffer", 0

# ==========================================
# 3. INTERFAZ (STREAMLIT)
# ==========================================

st.set_page_config(page_title="PAU Tracker Ultimate", page_icon="🦁", layout="centered")

# CSS Personalizado
st.markdown("""
    <style>
    .stButton button { width: 100%; border-radius: 8px; font-weight: bold; }
    h1 { color: #ff4b4b; }
    .css-15zrgzn {padding: 1rem;} 
    </style>
""", unsafe_allow_html=True)

# Carga de datos
if 'data' not in st.session_state:
    st.session_state.data = load_data()

data = st.session_state.data

# --- SIDEBAR (Barra Lateral) ---
with st.sidebar:
    st.header("🦁 PAU Elite")
    st.write("Sistema de Alto Rendimiento")
    
    # Toggle para forzar estudio (por si quieres estudiar en horario de gimnasio)
    force_study = st.checkbox("💪 Forzar Modo Estudio", value=False)
    
    # Estado del Horario
    real_type, block_name, duration = get_current_block()
    
    if force_study and real_type in ["gym", "break", "free", "sleep"]:
        target_type = "mix" # Muestra todo
        st.warning("⚠️ Saltándose el descanso.")
    else:
        target_type = real_type
        
    st.info(f"**Bloque Actual:**\n{block_name}")
    
    st.metric("Duración Bloque", f"{duration} min")

# --- PESTAÑAS PRINCIPALES ---
tab1, tab2, tab3, tab4 = st.tabs(["🚀 Agenda", "📚 Temario", "📓 Errores", "⚙️ Config"])

# ==========================================
# TAB 1: AGENDA INTELIGENTE
# ==========================================
with tab1:
    st.header(f"Plan de Acción: {block_name}")
    
    # Lógica de "No molestar" en descansos
    if target_type in ["gym", "break", "sleep", "free"] and not force_study:
        st.success(f"🚫 **Stop.** Toca: {block_name}")
        st.markdown("> *El sueño es sagrado (23:00) y el gimnasio resetea tu cerebro.* [cite: 148, 150]")
    
    elif target_type == "review":
        st.warning("📅 **Domingo Tarde:** Revisa la pestaña '📓 Errores' y planifica la semana.")
        
    else:
        # 1. RECOLECCIÓN DE TAREAS
        tasks = []
        today_str = str(datetime.date.today())
        
        for subj, topic_list in data.items():
            for i, topic in enumerate(topic_list):
                # Filtros:
                # A. Está desbloqueado (visto en clase)
                # B. Toca hoy (next_review <= hoy) O es urgente (extra_queue)
                # C. Coincide con el bloque (Ciencias vs Memoria) O es Simulacro/Mix
                
                is_due = (topic["next_review"] <= today_str) or topic["extra_queue"]
                
                # Definir si la asignatura encaja en el bloque actual
                match_category = False
                if target_type in ["simulacro", "mix"]:
                    match_category = True
                elif target_type == "science" and (topic["category"] in ["science", "skills"]):
                    match_category = True # Inglés se mete en huecos de ciencia si hace falta
                elif target_type == "memory" and topic["category"] == "memory":
                    match_category = True
                
                if topic["unlocked"] and is_due and match_category:
                    tasks.append({"subj": subj, "topic": topic, "idx": i})

        # 2. ORDENACIÓN (Eat the Frog )
        # Primero lo urgente manual, luego por nivel (más bajo = más difícil primero)
        tasks.sort(key=lambda x: (not x["topic"]["extra_queue"], x["topic"]["level"]))
        
        # 3. VISUALIZACIÓN
        if not tasks:
            st.balloons()
            st.success("✅ ¡Bloque completado! Adelanta materia en 'Temario' o descansa.")
        else:
            # Calcular tiempo por tarea
            time_per_task = int(duration / len(tasks)) if duration > 0 else 30
            st.caption(f"Tienes **{len(tasks)} tareas**. Tiempo sugerido: **{time_per_task} min/tarea**.")
            
            for t in tasks:
                subj = t["subj"]
                idx = t["idx"]
                topic = t["topic"]
                
                # Tarjeta
                with st.container():
                    col1, col2 = st.columns([0.7, 0.3])
                    prefix = "🔥" if topic["extra_queue"] else "🐸" if topic["level"] < 2 else "📝"
                    
                    with col1:
                        st.markdown(f"**{prefix} {subj}**")
                        st.write(f"{topic['name']}")
                        st.progress(topic['level']/5)
                    
                    with col2:
                        st.write(f"⏱️ {time_per_task}m")
                        
                    # Botones SRS
                    b1, b2, b3 = st.columns(3)
                    
                    if b1.button("✅ Fácil", key=f"e_{subj}_{idx}"):
                        topic["level"] = min(topic["level"] + 1, 5)
                        days = topic["level"] * 5 + 2 # Espaciado agresivo
                        topic["next_review"] = str(datetime.date.today() + datetime.timedelta(days=days))
                        topic["extra_queue"] = False
                        save_data(st.session_state.data)
                        st.rerun()

                    if b2.button("🆗 Normal", key=f"n_{subj}_{idx}"):
                        days = 3
                        topic["next_review"] = str(datetime.date.today() + datetime.timedelta(days=days))
                        topic["extra_queue"] = False
                        save_data(st.session_state.data)
                        st.rerun()

                    if b3.button("🔴 Fallé", key=f"h_{subj}_{idx}"):
                        # Activa modo error
                        st.session_state[f"fail_mode_{subj}_{idx}"] = True
                        topic["level"] = 1 # Reset nivel
                        topic["next_review"] = str(datetime.date.today() + datetime.timedelta(days=1)) # Mañana
                        save_data(st.session_state.data)
                        st.rerun()
                    
                    # INPUT DE ERROR (Si se pulsó Fallé)
                    if st.session_state.get(f"fail_mode_{subj}_{idx}", False):
                        st.error("📉 Registrando en Cuaderno de Errores ")
                        err_text = st.text_input("¿Cuál fue el fallo exacto?", key=f"txt_{subj}_{idx}")
                        if st.button("Guardar Error", key=f"save_{subj}_{idx}"):
                            topic["last_error"] = err_text
                            del st.session_state[f"fail_mode_{subj}_{idx}"] # Limpiar estado
                            save_data(st.session_state.data)
                            st.success("Guardado.")
                            st.rerun()
                    
                    st.divider()

# ==========================================
# TAB 2: TEMARIO (CHECK-LIST)
# ==========================================
with tab2:
    st.header("Gestor de Temario")
    st.write("Marca los temas vistos en clase para activarlos.")
    
    for subj in data:
        with st.expander(f"{subj}"):
            # Botón para añadir tema rápido aquí
            c_add1, c_add2 = st.columns([3, 1])
            new_top = c_add1.text_input(f"Añadir tema a {subj}", key=f"new_t_{subj}")
            if c_add2.button("➕", key=f"btn_add_{subj}") and new_top:
                data[subj].append({
                    "name": new_top, "category": data[subj][0]["category"], 
                    "unlocked": True, "level": 0, 
                    "next_review": str(datetime.date.today()), "last_error": "", "extra_queue": True
                })
                save_data(data)
                st.rerun()

            # Lista de temas
            for i, topic in enumerate(data[subj]):
                col_chk, col_urg = st.columns([4, 1])
                
                # Checkbox activacion
                is_checked = col_chk.checkbox(
                    f"{topic['name']}", 
                    value=topic["unlocked"], 
                    key=f"chk_{subj}_{i}"
                )
                
                # Toggle Urgente
                is_urgent = col_urg.checkbox("🔥", value=topic["extra_queue"], key=f"urg_{subj}_{i}", help="Marcar para estudiar hoy sí o sí")
                
                # Guardar cambios
                if is_checked != topic["unlocked"] or is_urgent != topic["extra_queue"]:
                    topic["unlocked"] = is_checked
                    topic["extra_queue"] = is_urgent
                    if is_checked and not topic["unlocked"]: # Si se acaba de activar
                        topic["next_review"] = str(datetime.date.today())
                    save_data(data)
                    st.rerun()

# ==========================================
# TAB 3: CUADERNO DE ERRORES
# ==========================================
with tab3:
    st.header("📓 Cuaderno de Errores")
    st.markdown("> *Revisar obligatoriamente los domingos.* [cite: 164]")
    
    count = 0
    for subj, topic_list in data.items():
        for topic in topic_list:
            if topic.get("last_error"):
                count += 1
                with st.container():
                    st.error(f"**{subj} - {topic['name']}**")
                    st.write(f"❌ Fallo: *{topic['last_error']}*")
                    if st.button("🗑️ Ya lo aprendí (Borrar)", key=f"del_err_{topic['name']}"):
                        topic["last_error"] = ""
                        save_data(data)
                        st.rerun()
    
    if count == 0:
        st.success("¡Cuaderno limpio! Buen trabajo.")

# ==========================================
# TAB 4: CONFIGURACIÓN (CRUD COMPLETO)
# ==========================================
with tab4:
    st.header("⚙️ Configuración Total")
    
    # 1. AÑADIR ASIGNATURA
    with st.expander("➕ Crear Nueva Asignatura"):
        n_subj = st.text_input("Nombre Asignatura")
        n_cat = st.selectbox("Categoría", ["science", "memory", "skills"])
        if st.button("Crear Asignatura"):
            if n_subj and n_subj not in data:
                data[n_subj] = [] # Lista vacía, el usuario añadirá temas
                # Hack: añadir un tema dummy para guardar la categoría
                data[n_subj].append({
                    "name": "Tema 1 (Editar)", "category": n_cat, "unlocked": True, 
                    "level": 0, "next_review": str(datetime.date.today()), "last_error": "", "extra_queue": False
                })
                save_data(data)
                st.success(f"Creada: {n_subj}")
                st.rerun()

    # 2. BORRAR COSAS
    with st.expander("🗑️ Borrar Asignaturas/Temas"):
        subj_del = st.selectbox("Elige Asignatura", list(data.keys()))
        
        # Borrar tema específico
        if subj_del:
            topics = [t["name"] for t in data[subj_del]]
            t_del = st.selectbox("Elige Tema a borrar", ["-- Seleccionar --"] + topics)
            if st.button("Borrar TEMA"):
                data[subj_del] = [t for t in data[subj_del] if t["name"] != t_del]
                save_data(data)
                st.rerun()
            
            st.divider()
            
            # Borrar asignatura entera
            if st.button(f"⚠️ BORRAR ASIGNATURA COMPLETA: {subj_del}"):
                del data[subj_del]
                save_data(data)
                st.rerun()

    # 3. RESET DE FÁBRICA
    st.divider()
    if st.button("☠️ RESET TOTAL (Borrar todos los datos)"):
        if os.path.exists(FILE_NAME):
            os.remove(FILE_NAME)
        st.session_state.clear()
        st.rerun()
