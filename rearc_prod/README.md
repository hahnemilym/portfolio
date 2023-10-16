
### Steps
1. `source create_env.zsh`
2. `source create_kernel.zsh`
4. `jupyter-lab rearc_tc_all.ipynb` (answers for steps 1-3: select kernel + run all cells)
5. `python main.py` (answers for step 4)

### Overview

* `info.txt` must have key values inputted (AWS configuration)

* `*.ipynb` file contains directions (in markdown cells) on how to complete the data processing/visualizations (steps 1-3) & pipeline (step 4) 

* `*.zsh` scripts must be run before notebook cells or pipeline can be run - that sets up environment+dependencies for the notebook cells (steps 1-3) & pipeline (step 4) 