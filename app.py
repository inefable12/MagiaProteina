import streamlit as st
import subprocess
import tempfile
import os
import requests
import py3Dmol
from stmol import showmol

def clean_pdb(pdb_content):
    """
    Filtra el contenido del PDB crudo. 
    Elimina ligandos cocristalizados, moléculas de agua y heteroátomos (HETATM).
    """
    cleaned_lines = []
    for line in pdb_content.splitlines():
        if line.startswith("HETATM") or line.startswith("CONECT"):
            continue
        cleaned_lines.append(line)
    return "\n".join(cleaned_lines)

def render_receptor(pdbqt_string):
    """
    Configura y renderiza el visor 3D para la proteína.
    """
    view = py3Dmol.view(width=700, height=500)
    # py3Dmol lee las coordenadas topológicas del PDBQT al interpretarlo como PDB
    view.addModel(pdbqt_string, 'pdb')
    view.setStyle({'cartoon': {'color': 'spectrum'}, 'stick': {'radius': 0.1}})
    view.zoomTo()
    showmol(view, height=500, width=700)

# Configuración de la página
st.set_page_config(page_title="Preparador de Proteínas", page_icon="🧬")

st.title("Preparación de Proteínas (PDB a PDBQT)")
st.markdown("""
Esta herramienta utiliza el motor nativo de **MGLTools** para añadir hidrógenos, calcular cargas de Gasteiger y asignar los tipos de átomos de AutoDock.
""")

# Interfaz con pestañas
tab_subida, tab_descarga = st.tabs([
    "📁 Subir Archivo PDB (Recomendado)", 
    "⬇️ Descargar desde PDB (No recomendable)"
])

pdb_content_raw = None
nombre_archivo = "receptor"

# --- PESTAÑA 1: SUBIDA MANUAL (RECOMENDADA) ---
with tab_subida:
    st.info("Recomendado: Sube un archivo PDB que ya hayas inspeccionado y curado visualmente (reparación de loops, selección de cadenas, etc.).")
    uploaded_file = st.file_uploader("Seleccionar archivo PDB local", type="pdb")
    
    if uploaded_file is not None:
        pdb_content_raw = uploaded_file.getvalue().decode("utf-8")
        nombre_archivo = uploaded_file.name.split('.')[0]
        pdb_content_raw = clean_pdb(pdb_content_raw)

# --- PESTAÑA 2: DESCARGA DESDE PDB (NO RECOMENDABLE) ---
with tab_descarga:
    st.warning("⚠️ **No recomendable:** La descarga directa automatizada remueve heteroátomos y ligandos a ciegas. No permite reparar residuos faltantes ni seleccionar estados conformacionales específicos, lo cual es crítico para un docking riguroso.")
    
    pdb_id = st.text_input("Ingrese el identificador PDB (Ej. 1HSG):", max_chars=4).upper()
    
    if st.button("Descargar y Procesar"):
        if len(pdb_id) == 4:
            with st.spinner(f"Obteniendo {pdb_id} desde el Protein Data Bank..."):
                url = f"https://files.rcsb.org/download/{pdb_id}.pdb"
                response = requests.get(url)
                
                if response.status_code == 200:
                    st.success(f"Estructura {pdb_id} obtenida correctamente.")
                    nombre_archivo = pdb_id
                    pdb_content_raw = clean_pdb(response.text)
                else:
                    st.error("No se pudo encontrar el identificador PDB en el servidor.")
        else:
            st.error("El identificador PDB debe contener exactamente 4 caracteres.")

# --- PROCESAMIENTO IN SILICO ---
if pdb_content_raw is not None:
    with tempfile.TemporaryDirectory() as tmpdir:
        input_pdb = os.path.join(tmpdir, f"{nombre_archivo}_input.pdb")
        output_pdbqt = os.path.join(tmpdir, f"{nombre_archivo}.pdbqt")

        with open(input_pdb, "w") as f:
            f.write(pdb_content_raw)

        with st.spinner("Preparando receptor con MGLTools..."):
            command = [
                "prepare_receptor4", 
                "-r", input_pdb, 
                "-o", output_pdbqt, 
                "-A", "hydrogens",
                "-U", "waters" 
            ]
            result = subprocess.run(command, capture_output=True, text=True)

        if os.path.exists(output_pdbqt) and os.path.getsize(output_pdbqt) > 0:
            st.success("¡Estructura preparada con éxito!")
            
            with open(output_pdbqt, "r") as f:
                pdbqt_content = f.read()

            col1, col2 = st.columns([1, 2])
            
            with col1:
                st.download_button(
                    label="📥 Descargar Receptor (PDBQT)",
                    data=pdbqt_content,
                    file_name=f"{nombre_archivo}_preparado.pdbqt",
                    mime="text/plain",
                    type="primary"
                )
                
                with st.expander("Vista previa del texto PDBQT"):
                    st.code(pdbqt_content[:1500] + "\n...\n", language="text")
            
            with col2:
                st.markdown("### Visualización 3D")
                render_receptor(pdbqt_content)
                
        else:
            st.error("Falló la conversión. Revisa el registro del sistema:")
            st.code(result.stderr or result.stdout, language="bash")
