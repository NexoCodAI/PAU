import streamlit as st
import json
import datetime
import os

# ==========================================
# CONFIGURACIÓN Y DATOS
# ==========================================

FILE_NAME = "pau_data.json"

# Datos iniciales por defecto (si no hay archivo guardado)
DEFAULT_SYLLABUS = {
    "Matemáticas II": ["Matrices", "Determinantes", "Sistemas Ecuaciones", "Límites", "Derivadas", "Integrales", "Geometría Espacial", "Probabilidad"],
    "Física": ["Gravitación", "Campo Eléctrico", "Campo Magnético", "Inducción", "Ondas", "Óptica", "Física Moderna"],
    "Historia de España": ["Raíces Históricas", "S.XIX: Crisis A.R.", "S.XIX: Liberalismo", "S.XX: Dictadura y República", "S.XX: Guerra y Franquismo"],
    "Inglés": ["Tenses", "Passive Voice", "Conditionals", "Reported Speech", "Writing: Opinion", "Writing: For/Against"]
}

# ==========================================
# FUNCIONES DE GESTIÓN DE DATOS
# ==========================================

def load_data():
    if os.path.exists(FILE_NAME):
        with open(FILE_NAME, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        # Inicializar estructura vacía basada en el default
        new_data = {}
        for subject, topics in DEFAULT_SYLLABUS.items():
            new_data[subject] = []
            for topic in topics:
                new_data[subject].append({
                    "name": topic,
                    "unlocked": False,  # No visto
                    "level": 0,         # 0-5 dominio
                    "next_review": str(datetime.date.today()),
                    "extra_queue": False
                })
        return new_data

def save_data(data):
    with open(FILE_NAME, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

# Cargar datos al inicio
if 'data' not in st.session_state:
    st.session_state.data = load_data()

# ==========================================
# INTERFAZ (STREAMLIT)
# ==========================================

st.set_page_config(page_title="PAU Tracker", page_icon="🎓", layout="centered")

# CSS para mejorar la vista en móvil
st.markdown("""
    <style>
    .stButton button { width: 100%; border-radius: 10px; font-weight: bold; }
    .css-15zrgzn {padding: 1rem;} 
    h1 { color: #00adb5; }
    </style>
""", unsafe_allow_html=True)

st.title("🎓 PAU Elite Mobile")

# Navegación
tab1, tab2, tab3 = st.tabs(["📅 Agenda", "📚 Temario", "⚙️ Config"])

# ==========================================
# PESTAÑA 1: AGENDA (DASHBOARD)
# ==========================================
with tab1:
    st.header("Plan de Hoy")
    today_str = str(datetime.date.today())
    
    # Recopilar tareas pendientes
    tasks = []
    data = st.session_state.data
    
    for subj, topic_list in data.items():
        for i, topic in enumerate(topic_list):
            # Mostrar si está desbloqueado Y (vence hoy O es urgente)
            if (topic["unlocked"] or topic["extra_queue"]) and (topic["next_review"] <= today_str or topic["extra_queue"]):
                tasks.append({"subj": subj, "topic": topic, "idx": i})
    
    # Ordenar: Urgentes primero
    tasks.sort(key=lambda x: (not x["topic"]["extra_queue"], x["topic"]["next_review"]))
    
    if not tasks:
        st.success("🎉 ¡Todo limpio por hoy! Adelanta materia en la pestaña 'Temario'.")
    else:
        # Mostrar tareas como tarjetas
        for t in tasks:
            subj = t["subj"]
            idx = t["idx"]
            topic = t["topic"]
            
            # Estilo visual de la tarjeta
            prefix = "🔥 " if topic["extra_queue"] else ""
            with st.container():
                st.markdown(f"**{subj}** | {prefix}{topic['name']}")
                st.progress(topic['level'] / 5)
                
                c1, c2, c3 = st.columns(3)
                
                # Botones de acción
                if c1.button("✅ Fácil", key=f"e_{subj}_{idx}"):
                    topic["level"] = min(topic["level"] + 2, 5)
                    days = topic["level"] * 7
                    topic["next_review"] = str(datetime.date.today() + datetime.timedelta(days=days))
                    topic["extra_queue"] = False
                    save_data(st.session_state.data)
                    st.rerun()

                if c2.button("🆗 Normal", key=f"n_{subj}_{idx}"):
                    topic["level"] = min(topic["level"] + 1, 5)
                    days = topic["level"] * 3
                    topic["next_review"] = str(datetime.date.today() + datetime.timedelta(days=days))
                    topic["extra_queue"] = False
                    save_data(st.session_state.data)
                    st.rerun()

                if c3.button("🔴 Difícil", key=f"h_{subj}_{idx}"):
                    topic["level"] = 1
                    days = 1
                    topic["next_review"] = str(datetime.date.today() + datetime.timedelta(days=days))
                    topic["extra_queue"] = False
                    save_data(st.session_state.data)
                    st.rerun()
            st.divider()

# ==========================================
# PESTAÑA 2: TEMARIO (ACTIVAR TEMAS)
# ==========================================
with tab2:
    st.header("Gestor de Temario")
    st.info("Marca los temas que has dado en clase para que empiecen a salir en la Agenda.")
    
    data = st.session_state.data
    
    for subj in data:
        with st.expander(f"📖 {subj}"):
            # Checkbox para cada tema
            for i, topic in enumerate(data[subj]):
                # Usamos una key única para que Streamlit sepa cuál es cuál
                is_checked = st.checkbox(
                    f"{topic['name']}", 
                    value=topic["unlocked"],
                    key=f"chk_{subj}_{i}"
                )
                
                # Si el estado cambia, guardamos
                if is_checked != topic["unlocked"]:
                    data[subj][i]["unlocked"] = is_checked
                    # Si se activa, fecha de repaso = Hoy
                    if is_checked:
                        data[subj][i]["next_review"] = str(datetime.date.today())
                    save_data(data)
                    st.rerun()

# ==========================================
# PESTAÑA 3: CONFIGURACIÓN (EDITAR)
# ==========================================
with tab3:
    st.header("⚙️ Editar Asignaturas y Temas")
    
    data = st.session_state.data
    
    # 1. AÑADIR NUEVA ASIGNATURA
    with st.expander("➕ Añadir Nueva Asignatura"):
        new_subj_name = st.text_input("Nombre de la asignatura")
        if st.button("Crear Asignatura"):
            if new_subj_name and new_subj_name not in data:
                data[new_subj_name] = []
                save_data(data)
                st.success(f"Asignatura '{new_subj_name}' creada.")
                st.rerun()
            elif new_subj_name in data:
                st.error("Esa asignatura ya existe.")

    st.divider()

    # 2. GESTIONAR TEMAS DE UNA ASIGNATURA
    subj_to_edit = st.selectbox("Selecciona Asignatura para editar", list(data.keys()))
    
    if subj_to_edit:
        # AÑADIR TEMA
        st.subheader(f"Añadir tema a {subj_to_edit}")
        new_topic_name = st.text_input("Nombre del nuevo tema/tarea")
        is_urgent = st.checkbox("¿Es urgente (examen/entrega)?")
        
        if st.button("Añadir Tema"):
            if new_topic_name:
                new_entry = {
                    "name": new_topic_name,
                    "unlocked": True, # Desbloqueado por defecto si lo añades manualmente
                    "level": 0,
                    "next_review": str(datetime.date.today()),
                    "extra_queue": is_urgent
                }
                # Insertar al principio
                data[subj_to_edit].insert(0, new_entry)
                save_data(data)
                st.success("Tema añadido.")
                st.rerun()
        
        st.divider()
        
        # ELIMINAR TEMAS
        st.subheader("🗑️ Eliminar temas")
        topics_list = [t["name"] for t in data[subj_to_edit]]
        topic_to_delete = st.selectbox("Selecciona tema a borrar", ["-- Seleccionar --"] + topics_list)
        
        if st.button("Borrar Tema Seleccionado"):
            if topic_to_delete != "-- Seleccionar --":
                # Filtrar la lista quitando el seleccionado
                data[subj_to_edit] = [t for t in data[subj_to_edit] if t["name"] != topic_to_delete]
                save_data(data)
                st.warning(f"Borrado: {topic_to_delete}")
                st.rerun()

    st.divider()
    # 3. BORRAR ASIGNATURA COMPLETA
    with st.expander("⚠️ Zona de Peligro"):
        if st.button(f"Borrar Asignatura '{subj_to_edit}' y todos sus datos"):
            del data[subj_to_edit]
            save_data(data)
            st.rerun()
