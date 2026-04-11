# Pasos para ejecutar el laboratorio

#### 1. Instalación de dependencias
```
brew install python@3.12
brew install poetry
```

#### 2. Crear proyecto
```
poetry new lab1
cd lab1
```

#### 3. Configurar pyproject.toml

Editar el [project.toml](/1_Fundamental/lab1/pyproject.toml) para agregar las herramientas que verifican la calidad

```
# Creamos y activamos el entorno virtual
poetry env use python3.12
poetry env info
poetry install

# Verificamos instalación
poetry run black --version
poetry run isort --version
poetry run ruff --version
poetry run pre-commit --version
```

#### 4. Crear codigos con infracciones PEP8
```
# Tambien se puede usando VSCode
nano src/lab1/main.py
```

#### 5. Configurar el pre-commit

Se genera el archivo [.pre-commit-config.yaml](/fundamental_lab1/.pre-commit-config.yaml) y se ejecuta:
```
poetry run pre-commit install
```

#### 6 Verificar código antes de corregir
```
# Ver problemas con ruff
poetry run ruff check src/lab1/main.py

# Ver qué cambiaría black
poetry run black --check src/lab1/main.py

# Ver qué cambiaría isort
poetry run isort --check-only src/lab1/main.py
```

#### 7. Corregir automaticamente
```
# 1. Ordenar imports
poetry run isort src/lab1/main.py

# 2. Formatear código
poetry run black src/lab1/main.py

# 3. Corregir linting
poetry run ruff check --fix src/lab1/main.py

# 4. Verificar que todo está OK
poetry run ruff check src/lab1/
```

#### 8. Probar el pre-commit
```
git init
git add .
git commit -m "Commit inicial con codigo corregido"
```
