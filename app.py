import streamlit as st
import subprocess
import tempfile
import os

# 1. Configuración de la página
st.set_page_config(page_title="Preparador de Proteínas (PDBQT)", page_icon="🧬")

st.title("Preparación de Proteínas para Molecular Docking")
st.markdown("""
Sube un archivo PDB. El sistema utilizará el motor de **MGLTools** para limpiar la estructura, 
añadir hidrógenos, calcular cargas de Gasteiger y asignar los tipos de átomos de AutoDock.
""")

# 2. Cargar el archivo PDB
uploaded_file = st.file_uploader("Seleccionar archivo PDB (Receptor)", type="pdb")

if uploaded_file is not None:
    # 3. Usar TemporaryDirectory asegura que los archivos se borren al terminar, liberando memoria del servidor
    with tempfile.TemporaryDirectory() as tmpdir:
        input_pdb = os.path.join(tmpdir, "receptor_input.pdb")
        output_pdbqt = os.path.join(tmpdir, "receptor_output.pdbqt")

        # Guardar el PDB subido temporalmente
        with open(input_pdb, "wb") as f:
            f.write(uploaded_file.getvalue())

        st.info("Archivo cargado correctamente. Iniciando procesamiento in silico...")

        with st.spinner("Asignando cargas de Gasteiger y tipos de átomos (esto puede tardar unos segundos)..."):
            # 4. Llamar al comando global de MGLTools instalado vía GitHub
            # -A hydrogens: añade hidrógenos polares
            # -U waters: elimina moléculas de agua automáticamente
            command = [
                "prepare_receptor4", 
                "-r", input_pdb, 
                "-o", output_pdbqt, 
                "-A", "hydrogens",
                "-U", "waters"
            ]
            
            # Ejecutar el proceso en el contenedor de Streamlit
            result = subprocess.run(command, capture_output=True, text=True)

        # 5. Verificar si la conversión fue exitosa
        if os.path.exists(output_pdbqt) and os.path.getsize(output_pdbqt) > 0:
            st.success("¡Proteína preparada con éxito! Lista para ser usada en AutoDock Vina.")
            
            # Leer el archivo generado
            with open(output_pdbqt, "r") as f:
                pdbqt_content = f.read()

            # Botón de descarga
            st.download_button(
                label="📥 Descargar Receptor (PDBQT)",
                data=pdbqt_content,
                file_name=f"{uploaded_file.name.split('.')[0]}_preparado.pdbqt",
                mime="text/plain"
            )
            
            # Mostrar un fragmento del archivo
            with st.expander("Ver fragmento del archivo PDBQT generado"):
                st.code(pdbqt_content[:1000] + "\n...\n", language="text")
                
        else:
            st.error("Hubo un error durante la preparación del receptor.")
            st.markdown("**Detalles del error del sistema:**")
            # Mostrar el error exacto que arrojó el motor para poder diagnosticarlo
            st.code(result.stderr or result.stdout, language="bash")
