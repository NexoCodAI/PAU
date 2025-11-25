import streamlit as st
import json
import datetime
import os
import time

# ==========================================
# 1. CONFIGURACIÓN Y CONSTANTES
# ==========================================

st.set_page_config(
    page_title="PAU Tracker Elite", 
    page_icon="🎓", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

FILE_NAME = "pau_ultimate_data.json"
MIN_MINUTES_PER_TASK = 25  # Tiempo mínimo para estudiar un tema con profundidad

# Colores y Estilos CSS
st.markdown("""
    <style>
    .stButton button { width: 100%; border-radius: 8px; font-weight: 600; }
    div[data-testid="stMetricValue"] { font-size: 1.8rem; color: #ff4b4b; }
    .css-1d391kg { padding-top: 1rem; }
    .card { background-color: #262730; padding: 20px; border-radius: 10px; border: 1px solid #444; margin-bottom: 10px; }
    </style>
""", unsafe_allow_html=True)

# Datos Maestros por Defecto (Si no hay archivo)
DEFAULT_SYLLABUS = {
    "Matemáticas II": {
        "category": "science",
        "topics": ["Matrices", "Rango e Inversa", "Determinantes", "Sistemas (Rouché)", "Límites & Continuidad", "Derivadas", "Optimización", "Integrales Indef.", "Integrales Def.", "Geo: Rectas y Planos", "Geo: Métrico", "Probabilidad Total", "Binomial/Normal"]
    },
    "Física": {
        "category": "science",
        "topics": ["Campo Gravitatorio", "Campo Eléctrico", "Campo Magnético", "Inducción EM", "Ondas Mecánicas", "Ondas Sonoras", "Óptica Geométrica", "Física Relativista", "Física Cuántica", "Física Nuclear"]
    },
    "Química": {
        "category": "science",
        "topics": ["Estructura Atómica", "Sistema Periódico", "Enlace Químico", "Cinética Química", "Equilibrio Químico", "Ácido-Base", "Redox", "Química del Carbono"]
    },
    "Historia de España": {
        "category": "memory",
        "topics": ["Raíces Hcas", "Crisis A.R. (1808-1833)", "Estado Liberal (1833-1874)", "Restauración (1875-1902)", "Alfonso XIII (1902-1931)", "II República", "Guerra Civil", "Franquismo", "Transición"]
    },
    "Hª Filosofía": {
        "category": "memory",
        "topics": ["Platón: Ideas", "Platón: Política", "Aristóteles", "Tomás de Aquino", "Descartes", "Hume", "Rousseau", "Kant: Conocimiento", "Kant: Ética", "Marx", "Nietzsche", "Ortega y Gasset"]
    },
    "Inglés": {
        "category": "skills",
        "topics": ["Tenses Mix", "Passive Voice", "Reported Speech", "Conditionals & Wishes", "Modals", "Relative Clauses", "Writing: Opinion", "Writing: For/Against"]
    }
}

# ==========================================
# 2. GESTIÓN DE DATOS
# ==========================================

def load_data():
    if os.path.exists(FILE_NAME):
        try:
            with open(FILE_NAME, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            st.error("Archivo corrupto. Cargando defaults.")
            return create_defaults()
    else:
        return create_defaults()

def create_defaults():
    new_data = {}
    for subject, info in DEFAULT_SYLLABUS.items():
        new_data[subject] = []
        for topic in info["topics"]:
            new_data[subject].append({
                "name": topic,
                "category": info["category"],
                "unlocked": False,       # ¿Visto en clase?
                "level": 0,              # 0-5 (Dominio)
                "next_review": str(datetime.date.today()),
                "last_error": "",        # Texto del error
                "extra_queue": False     # Urgencia manual
            })
    return new_data

def save_data(data):
    with open(FILE_NAME, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

# ==========================================
# 3. LÓGICA DEL TIEMPO (HORARIO)
# ==========================================

def get_current_block():
    now = datetime.datetime.now()
    weekday = now.weekday() # 0=Lunes, 6=Domingo
    hour = now.hour + now.minute / 60.0

    # LUNES (0) Y MIÉRCOLES (2) - Tarde Larga
    if weekday in [0, 2]:
        if 16.0 <= hour < 17.5: return "science", "🐸 Bloque Ciencia 1", 90
        if 17.5 <= hour < 19.0: return "gym", "🏋️ Gimnasio / Descanso", 90
        if 19.0 <= hour < 19.5: return "break", "🚿 Ducha / Snack", 30
        if 19.5 <= hour < 21.0: return "science", "🧪 Bloque Ciencia 2", 90
        if 21.0 <= hour < 21.5: return "break", "🥗 Cena", 30
        if 21.5 <= hour < 22.75: return "memory", "🧠 Bloque Memoria", 75
        if hour >= 23.0: return "sleep", "😴 DORMIR", 0
    
    # MARTES (1) Y JUEVES (3) - Tarde Corta / Gym
    elif weekday in [1, 3]:
        if 15.5 <= hour < 17.0: return "science", "🐸 Bloque Ciencia 1", 90
        if 17.0 <= hour < 18.5: return "gym", "🏋️ Gimnasio", 90
        if 19.0 <= hour < 20.5: return "science", "🧪 Bloque Ciencia 2", 90
        if 21.5 <= hour < 22.75: return "memory", "🧠 Bloque Memoria", 75
        if hour >= 23.0: return "sleep", "😴 DORMIR", 0

    # VIERNES (4) - Buffer
    elif weekday == 4:
        if 16.0 <= hour < 20.0: return "mix", "🔄 Repaso Buffer / Inglés", 240
    
    # SÁBADO (5) - Simulacro
    elif weekday == 5:
        if 9.5 <= hour < 13.5: return "simulacro", "📝 SIMULACRO REAL EXAMEN", 240
        if hour >= 14.0: return "free", "🎉 FINDE LIBRE", 0
    
    # DOMINGO (6) - Planning
    elif weekday == 6:
        if 18.0 <= hour < 20.0: return "review", "📅 Planificación + Errores", 120

    return "free", "⏳ Tiempo Libre / Buffer", 0

# ==========================================
# 4. INTERFAZ PRINCIPAL
# ==========================================

# Carga inicial
if 'data' not in st.session_state:
    st.session_state.data = load_data()

data = st.session_state.data
real_type, block_name, duration = get_current_block()

# --- SIDEBAR DASHBOARD ---
with st.sidebar:
    st.title("🎓 PAU Elite")
    st.markdown("---")
    
    # Panel de Control
    st.metric("Bloque Actual", f"{duration} min", delta=block_name, delta_color="normal")
    
    force_study = st.checkbox("💪 Forzar Modo Estudio", value=False, help="Ignora descansos y muestra tareas")
    
    # Progreso Global rápido
    st.markdown("---")
    st.write("**Resumen de Dominio**")
    total_topics = 0
    mastered_topics = 0
    for s in data:
        for t in data[s]:
            if t["unlocked"]:
                total_topics += 1
                if t["level"] >= 4: mastered_topics += 1
    
    if total_topics > 0:
        st.progress(mastered_topics / total_topics)
        st.caption(f"{mastered_topics}/{total_topics} Temas dominados")
    else:
        st.caption("Configura el temario para ver estadísticas.")

# --- PESTAÑAS ---
tab1, tab2, tab3, tab4 = st.tabs(["🚀 Agenda Inteligente", "📚 Temario y Syllabus", "📓 Cuaderno de Errores", "⚙️ Configuración"])

# ==========================================
# TAB 1: AGENDA (TIME BOXING LOGIC)
# ==========================================
with tab1:
    col_header, col_date = st.columns([3, 1])
    col_header.header(f"Agenda: {block_name}")
    col_date.caption(f"📅 {datetime.date.today().strftime('%d %b, %Y')}")
    
    # Determinar tipo de tarea objetivo
    if force_study and real_type in ["gym", "break", "free", "sleep"]:
        target_type = "mix"
        st.warning("⚠️ Modo Forzado Activado: Saltándose el descanso programado.")
    else:
        target_type = real_type

    # Pantallas de descanso
    if target_type in ["gym", "break", "sleep", "free"] and not force_study:
        #st.balloons()
        st.success(f"🚫 **TIEMPO DE DESCANSO / GYM**")
        st.markdown(f"### Toca: {block_name}")
        st.info("Recuerda: El descanso es parte del entrenamiento. Desconecta para rendir luego.")
        
    elif target_type == "review":
        st.warning("📅 **DOMINGO TARDE:** Ve a la pestaña '📓 Cuaderno de Errores' y repasa tus fallos de la semana.")
        
    else:
        # --- ALGORITMO DE SELECCIÓN ---
        tasks = []
        today_date = datetime.date.today()
        today_str = str(today_date)
        
        for subj, topic_list in data.items():
            for i, topic in enumerate(topic_list):
                # 1. Filtro: Está desbloqueado y Toca hoy (o está atrasado/urgente)
                is_due = (topic["next_review"] <= today_str) or topic["extra_queue"]
                
                # 2. Filtro: Coincide con el bloque actual
                match_category = False
                if target_type in ["simulacro", "mix"]: match_category = True
                elif target_type == "science" and (topic["category"] in ["science", "skills"]): match_category = True
                elif target_type == "memory" and topic["category"] == "memory": match_category = True
                
                if topic["unlocked"] and is_due and match_category:
                    # Calcular retraso
                    due_date = datetime.datetime.strptime(topic["next_review"], "%Y-%m-%d").date()
                    days_overdue = (today_date - due_date).days
                    
                    tasks.append({
                        "subj": subj, 
                        "topic": topic, 
                        "idx": i, 
                        "days_overdue": days_overdue
                    })

        # --- ORDENACIÓN POR PRIORIDAD ---
        # 1. Marcado manual urgente
        # 2. Más días de retraso
        # 3. Menor nivel (más difícil)
        tasks.sort(key=lambda x: (not x["topic"]["extra_queue"], -x["days_overdue"], x["topic"]["level"]))
        
        # --- TIME BOXING (CORTE DE TAREAS) ---
        total_tasks_available = len(tasks)
        
        if duration > 0:
            max_tasks_fit = int(duration / MIN_MINUTES_PER_TASK)
            if max_tasks_fit < 1: max_tasks_fit = 1 # Mínimo 1 siempre
        else:
            max_tasks_fit = 99 # Sin límite aparente
            
        selected_tasks = tasks[:max_tasks_fit]
        hidden_tasks = total_tasks_available - len(selected_tasks)
        
        # --- RENDERIZADO ---
        if not selected_tasks:
            st.success("✅ **¡Todo al día!** No tienes tareas pendientes para este bloque.")
            st.markdown("Puedes ir a la pestaña **Temario** y adelantar materia nueva.")
        else:
            # Calcular tiempo real por tarea
            real_time_per_task = int(duration / len(selected_tasks)) if duration > 0 else 30
            
            # Resumen de sesión
            c1, c2, c3 = st.columns(3)
            c1.metric("Tareas Hoy", len(selected_tasks))
            c2.metric("Tiempo/Tarea", f"{real_time_per_task} min")
            c3.metric("Pendientes (Backlog)", f"+{hidden_tasks}", help="Tareas ocultas por falta de tiempo")
            
            st.markdown("---")
            
            for t in selected_tasks:
                subj = t["subj"]
                idx = t["idx"]
                topic = t["topic"]
                
                # Diseño de Tarjeta
                with st.container(border=True):
                    col_info, col_act = st.columns([0.65, 0.35])
                    
                    with col_info:
                        # Badges
                        badges = []
                        if topic["extra_queue"]: badges.append("🔥 URGENTE")
                        if t["days_overdue"] > 5: badges.append("💀 RETRASADO")
                        if topic["level"] < 2: badges.append("🐸 DIFÍCIL")
                        
                        st.caption(f"{' '.join(badges)} | {subj}")
                        st.subheader(topic['name'])
                        
                        # Barra nivel
                        st.write(f"Nivel: {topic['level']}/5")
                        st.progress(topic['level']/5)
                        
                        if topic["last_error"]:
                            st.error(f"⚠️ Ojo al último error: {topic['last_error']}")
                    
                    with col_act:
                        st.write("¿Qué tal ha ido?")
                        b1, b2, b3 = st.columns(3)
                        
                        # Lógica SRS (Algoritmo de espaciado)
                        if b1.button("✅", key=f"easy_{subj}_{idx}", help="Fácil (+Nivel)"):
                            topic["level"] = min(topic["level"] + 1, 5)
                            days_add = (topic["level"] * 6) + 2 # Progresión: 8, 14, 20, 26, 32 días
                            topic["next_review"] = str(datetime.date.today() + datetime.timedelta(days=days_add))
                            topic["extra_queue"] = False
                            save_data(st.session_state.data)
                            st.rerun()
                        
                        if b2.button("🆗", key=f"ok_{subj}_{idx}", help="Bien (Mantener)"):
                            days_add = 4
                            topic["next_review"] = str(datetime.date.today() + datetime.timedelta(days=days_add))
                            topic["extra_queue"] = False
                            save_data(st.session_state.data)
                            st.rerun()
                            
                        if b3.button("❌", key=f"fail_{subj}_{idx}", help="Mal (Reset)"):
                            st.session_state[f"fail_mode_{subj}_{idx}"] = True
                            topic["level"] = 1
                            topic["next_review"] = str(datetime.date.today() + datetime.timedelta(days=1)) # Mañana
                            save_data(st.session_state.data)
                            st.rerun()

                    # Formulario de fallo (Condicional)
                    if st.session_state.get(f"fail_mode_{subj}_{idx}", False):
                        st.markdown("---")
                        with st.form(key=f"frm_{subj}_{idx}"):
                            st.error("📉 El fallo es la mejor forma de aprender.")
                            err_input = st.text_input("Describe brevemente el fallo para revisarlo el domingo:")
                            if st.form_submit_button("Guardar en Cuaderno de Errores"):
                                topic["last_error"] = err_input
                                del st.session_state[f"fail_mode_{subj}_{idx}"]
                                save_data(st.session_state.data)
                                st.success("Error registrado.")
                                st.rerun()

# ==========================================
# TAB 2: TEMARIO (CHECKLIST)
# ==========================================
with tab2:
    st.header("📚 Gestión de Temario")
    st.markdown("Marca los temas a medida que los des en clase para activarlos en el algoritmo.")
    
    col_search, col_add = st.columns([3, 1])
    search_query = col_search.text_input("🔍 Buscar tema...")
    
    for subj in data:
        with st.expander(f"**{subj}** ({len([t for t in data[subj] if t['unlocked']])}/{len(data[subj])})"):
            # Añadir nuevo
            c_new, c_btn = st.columns([0.8, 0.2])
            new_t_name = c_new.text_input(f"Nuevo tema en {subj}", key=f"new_input_{subj}")
            if c_btn.button("➕ Añadir", key=f"add_btn_{subj}") and new_t_name:
                data[subj].append({
                    "name": new_t_name, "category": data[subj][0]["category"],
                    "unlocked": True, "level": 0, "next_review": str(datetime.date.today()),
                    "last_error": "", "extra_queue": True
                })
                save_data(data)
                st.rerun()

            st.divider()
            
            # Listado
            for i, topic in enumerate(data[subj]):
                # Filtro de búsqueda visual
                if search_query.lower() in topic["name"].lower():
                    c1, c2, c3, c4 = st.columns([0.05, 0.6, 0.15, 0.2])
                    
                    # Checkbox Activación
                    is_active = c1.checkbox("", value=topic["unlocked"], key=f"chk_{subj}_{i}")
                    if is_active != topic["unlocked"]:
                        topic["unlocked"] = is_active
                        if is_active: topic["next_review"] = str(datetime.date.today())
                        save_data(data)
                        st.rerun()
                    
                    # Nombre
                    c2.write(topic["name"])
                    
                    # Nivel
                    c3.caption(f"Nv. {topic['level']}")
                    
                    # Toggle Urgencia
                    is_urg = c4.toggle("🔥", value=topic["extra_queue"], key=f"urg_{subj}_{i}")
                    if is_urg != topic["extra_queue"]:
                        topic["extra_queue"] = is_urg
                        save_data(data)
                        st.rerun()

# ==========================================
# TAB 3: CUADERNO DE ERRORES
# ==========================================
with tab3:
    st.header("📓 Cuaderno de Errores")
    st.markdown("> *Revisa esto cada domingo. Si entiendes el error, bórralo.*")
    
    errors_found = False
    
    for subj, topic_list in data.items():
        # Filtrar temas con errores
        errored_topics = [t for t in topic_list if t.get("last_error")]
        
        if errored_topics:
            errors_found = True
            st.subheader(subj)
            for t in errored_topics:
                with st.container(border=True):
                    col_txt, col_act = st.columns([0.8, 0.2])
                    with col_txt:
                        st.markdown(f"**Tema:** {t['name']}")
                        st.error(f"❌ {t['last_error']}")
                    with col_act:
                        if st.button("🗑️ Superado", key=f"clean_{t['name']}"):
                            t["last_error"] = ""
                            save_data(data)
                            st.rerun()
    
    if not errors_found:
        st.image("https://media.giphy.com/media/111ebonMs90YLu/giphy.gif", width=200)
        st.success("¡Limpio! No hay errores registrados. ¡Sigue así!")

# ==========================================
# TAB 4: CONFIGURACIÓN
# ==========================================
with tab4:
    st.header("⚙️ Configuración del Sistema")
    
    with st.expander("➕ Crear Nueva Asignatura"):
        ns_name = st.text_input("Nombre Asignatura")
        ns_cat = st.selectbox("Categoría", ["science", "memory", "skills"])
        if st.button("Crear"):
            if ns_name and ns_name not in data:
                data[ns_name] = [{"name": "Tema Ejemplo", "category": ns_cat, "unlocked": True, "level": 0, "next_review": str(datetime.date.today()), "last_error": "", "extra_queue": False}]
                save_data(data)
                st.rerun()

    with st.expander("🗑️ Zona de Peligro"):
        subj_del = st.selectbox("Borrar Asignatura", options=list(data.keys()))
        if st.button("Eliminar Asignatura"):
            del data[subj_del]
            save_data(data)
            st.rerun()
            
        st.divider()
        if st.button("☠️ RESET DE FÁBRICA (BORRA TODO)"):
            if os.path.exists(FILE_NAME):
                os.remove(FILE_NAME)
            st.session_state.clear()
            st.rerun()

# Footer
st.markdown("---")
st.caption("🎓 PAU Ultimate Tracker v2.0 | Time Boxing Enabled")
