# Running the API
## With UV
```bash
uv sync
uv run fastapi dev src/main.py
```
## With Pip
**Linux/macOS**
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
fastapi dev src/main.py
```


**Windows**
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
fastapi dev src/main.py
```

# Documentation
Documentation can be accessed at 127.0.0.1:8000/docs once the API is running 