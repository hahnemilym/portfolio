source rearc_project/bin/activate

which python > py_data_dir.txt
read -r PY_DATA_DIR < py_data_dir.txt
export PY_DATA_DIR

jupyter --data-dir > jupyter_data_dir.txt
read -r JUPYTER_DATA_DIR < jupyter_data_dir.txt
export JUPYTER_DATA_DIR
mkdir $JUPYTER_DATA_DIR/kernels/
mkdir ${JUPYTER_DATA_DIR}/kernels/rearc_project

cat > "$JUPYTER_DATA_DIR/kernels/rearc_project/kernel.json" << EOL
{
  "argv": [
    "${PY_DATA_DIR}",
    "-m", "ipykernel",
    "-f", "{connection_file}"
  ],
  "display_name": "rearc_project",
  "language": "python"
}
EOL