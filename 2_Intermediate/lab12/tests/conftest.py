import os
import sys

# Permite ejecutar `pytest` desde la raíz del proyecto sin instalar el
# paquete: agrega la raíz al path para que `import src...` funcione.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
