import streamlit as st
import subprocess
import tempfile
import os

# Configuración de la página
st.set_page_config(page_title="Preparador de Proteínas (PDBQT)", page_icon="🧬")

st.title("Preparación de Proteínas para Molecular Docking")
st.markdown("""
Sube un archivo PDB. El sistema utilizará **MGLTools (Python 3)** para limpiar la estructura, 
añadir hidrógenos, calcular cargas de Gasteiger y asignar los tipos de átomos de AutoDock.
""")

# Advertencia si faltan los archivos de MGLTools en el repositorio
if not os.path.exists("prepare_receptor4.py") or not os.path.exists("AutoDockTools") or not os.path.exists("MolKit"):
    st.warning("⚠️ Atención: Asegúrese de subir las carpetas `AutoDockTools`, `MolKit` y el script `prepare_receptor4.py` a la raíz de su repositorio en GitHub.")

# Cargar el archivo PDB
uploaded_file = st.file_uploader("Seleccionar archivo PDB (Receptor)", type="pdb")

if uploaded_file is not None:
    # Usar TemporaryDirectory asegura que los archivos se borren al terminar
    with tempfile.TemporaryDirectory() as tmpdir:
        input_pdb = os.path.join(tmpdir, "receptor_input.pdb")
        output_pdbqt = os.path.join(tmpdir, "receptor_output.pdbqt")

        # Guardar el PDB subido en el directorio temporal
        with open(input_pdb, "wb") as f:
            f.write(uploaded_file.getvalue())

        st.info("Archivo cargado correctamente. Iniciando procesamiento...")

        with st.spinner("Asignando cargas de Gasteiger y tipos de átomos..."):
            # Comando para ejecutar el script de MGLTools
            # -A hydrogens: añade hidrógenos
            # -U waters: elimina moléculas de agua automáticamente (muy útil para docking)
            command = [
                "python", 
                "prepare_receptor4.py", 
                "-r", input_pdb, 
                "-o", output_pdbqt, 
                "-A", "hydrogens",
                "-U", "waters"
            ]
            
            # Ejecutar el subproceso
            result = subprocess.run(command, capture_output=True, text=True)

        # Verificar si la conversión fue exitosa
        if os.path.exists(output_pdbqt) and os.path.getsize(output_pdbqt) > 0:
            st.success("¡Proteína preparada con éxito! Lista para AutoDock Vina.")
            
            # Leer el archivo generado para ofrecer la descarga
            with open(output_pdbqt, "r") as f:
                pdbqt_content = f.read()

            st.download_button(
                label="📥 Descargar Receptor (PDBQT)",
                data=pdbqt_content,
                file_name=f"{uploaded_file.name.split('.')[0]}_preparado.pdbqt",
                mime="text/plain"
            )
            
            # Opcional: Mostrar un fragmento del archivo generado para verificación rápida
            with st.expander("Ver fragmento del archivo PDBQT generado"):
                st.code(pdbqt_content[:1000] + "\n...\n", language="text")
                
        else:
            st.error("Hubo un error durante la preparación del receptor.")
            st.markdown("**Detalles del error del sistema:**")
            st.code(result.stderr or result.stdout, language="bash")
