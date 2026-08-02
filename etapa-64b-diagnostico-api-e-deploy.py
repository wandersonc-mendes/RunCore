from pathlib import Path
import os
import subprocess
import sys
import urllib.error
import urllib.request

ROOT = Path.cwd()
OUTPUT = ROOT / "diagnostico-etapa-64b.txt"

if not (ROOT / ".git").exists():
    raise RuntimeError("Execute este arquivo na raiz do RunCore.")

lines = ["=== DIAGNÓSTICO ETAPA 64B ===", ""]

def add(title, content):
    lines.append(title)
    lines.append("-" * 78)
    lines.extend(str(content).splitlines())
    lines.append("")

files = [
    ROOT / "src/repositories/access_repository.py",
    ROOT / "src/api/routers/integrations.py",
    ROOT / "src/api/main.py",
]

for path in files:
    add(
        f"ARQUIVO: {path.relative_to(ROOT)}",
        "encontrado" if path.exists() else "NÃO ENCONTRADO",
    )

for title, command in [
    ("BRANCH ATUAL", ["git", "branch", "--show-current"]),
    ("GIT STATUS", ["git", "status", "--short"]),
    ("ÚLTIMOS COMMITS", ["git", "log", "-5", "--oneline"]),
]:
    try:
        output = subprocess.check_output(
            command,
            cwd=ROOT,
            text=True,
            stderr=subprocess.STDOUT,
        ).strip()
        add(title, output or "sem saída")
    except Exception as exc:
        add(title, repr(exc))

try:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "py_compile",
            *[str(path) for path in files if path.exists()],
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    add(
        "PY_COMPILE",
        f"returncode={result.returncode}\n"
        f"stdout={result.stdout}\n"
        f"stderr={result.stderr}",
    )
except Exception as exc:
    add("PY_COMPILE", repr(exc))

try:
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import sys; sys.path.insert(0, 'src'); from api.main import app; print(type(app).__name__)",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=30,
    )
    add(
        "IMPORTAÇÃO DA API",
        f"returncode={result.returncode}\n"
        f"stdout={result.stdout}\n"
        f"stderr={result.stderr}",
    )
except Exception as exc:
    add("IMPORTAÇÃO DA API", repr(exc))

env_report = []
for key in [
    "STRAVA_CLIENT_ID",
    "STRAVA_CLIENT_SECRET",
    "STRAVA_REDIRECT_URI",
    "FRONTEND_URL",
    "DATABASE_URL",
]:
    value = os.getenv(key)
    if value is None:
        env_report.append(f"{key}=não definido localmente")
    elif key == "STRAVA_REDIRECT_URI":
        env_report.append(f"{key}={value}")
    else:
        env_report.append(f"{key}=<configurado>")

add("VARIÁVEIS LOCAIS", "\n".join(env_report))

for url in [
    "https://api.runcoreapp.com.br/",
    "https://api.runcoreapp.com.br/docs",
    "https://api.runcoreapp.com.br/openapi.json",
]:
    try:
        request = urllib.request.Request(
            url,
            headers={"User-Agent": "RunCore-Diagnostic/1.0"},
        )
        with urllib.request.urlopen(request, timeout=20) as response:
            body = response.read(500).decode("utf-8", errors="replace")
            add(
                f"TESTE HTTP: {url}",
                f"status={response.status}\n"
                f"content-type={response.headers.get('content-type')}\n"
                f"body={body}",
            )
    except urllib.error.HTTPError as exc:
        body = exc.read(500).decode("utf-8", errors="replace")
        add(
            f"TESTE HTTP: {url}",
            f"HTTPError={exc.code}\nbody={body}",
        )
    except Exception as exc:
        add(f"TESTE HTTP: {url}", repr(exc))

lines.extend([
    "=== INSTRUÇÃO ADICIONAL ===",
    "",
    "No Railway, abra o deploy mais recente e copie as linhas do log",
    "desde o início da aplicação até a primeira exceção ou mensagem de erro.",
    "",
    "=== FIM DO DIAGNÓSTICO ===",
])

OUTPUT.write_text("\n".join(lines), encoding="utf-8", newline="\n")

print("Diagnóstico concluído.")
print(f"Arquivo gerado em: {OUTPUT}")
print("Envie esse arquivo no chat.")
