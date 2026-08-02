from pathlib import Path
import shutil
import subprocess


ROOT = Path.cwd()
FRONTEND = ROOT / "frontend"
PUBLIC = FRONTEND / "public"
SRC = FRONTEND / "src"
INDEX = FRONTEND / "index.html"


if not (ROOT / ".git").exists():
    raise RuntimeError("Execute este arquivo na raiz do RunCore.")

if not PUBLIC.exists():
    raise RuntimeError("Não encontrei frontend/public.")

required = [
    PUBLIC / "logo-horizontal.png",
    PUBLIC / "logo-symbol.png",
    PUBLIC / "favicon.ico",
    PUBLIC / "icon-16.png",
    PUBLIC / "icon-32.png",
    PUBLIC / "icon-180.png",
    PUBLIC / "icon-192.png",
    PUBLIC / "icon-512.png",
    PUBLIC / "icon-maskable-512.png",
    PUBLIC / "manifest.webmanifest",
]

missing = [str(path.relative_to(ROOT)) for path in required if not path.exists()]

if missing:
    raise RuntimeError(
        "Arquivos ausentes:\n- " + "\n- ".join(missing)
    )


# Cria aliases compatíveis com o index.html e navegadores.
aliases = {
    "icon-16.png": "favicon-16x16.png",
    "icon-32.png": "favicon-32x32.png",
    "icon-180.png": "apple-touch-icon.png",
}

for source_name, target_name in aliases.items():
    shutil.copy2(
        PUBLIC / source_name,
        PUBLIC / target_name,
    )


# Atualiza o index e adiciona cache busting.
index = INDEX.read_text(encoding="utf-8")

replacements = {
    'href="/favicon.ico"': 'href="/favicon.ico?v="',
    'href="/favicon-32x32.png"': 'href="/favicon-32x32.png?v=3"',
    'href="/favicon-16x16.png"': 'href="/favicon-16x16.png?v=3"',
    'href="/apple-touch-icon.png"': 'href="/apple-touch-icon.png?v=3"',
    'href="/manifest.webmanifest"': 'href="/manifest.webmanifest?v=3"',
    'href="/icon-192.png"': 'href="/icon-192.png?v=3"',
}

for old, new in replacements.items():
    index = index.replace(old, new)

INDEX.write_text(
    index,
    encoding="utf-8",
    newline="\n",
)


# Atualiza referências de logo em todos os arquivos do frontend.
extensions = {".jsx", ".js", ".tsx", ".ts", ".css", ".html"}

for path in SRC.rglob("*"):
    if not path.is_file() or path.suffix not in extensions:
        continue

    content = path.read_text(
        encoding="utf-8",
        errors="ignore",
    )

    updated = (
        content
        .replace("/logo-horizontal.png?v=1", "/logo-horizontal.png?v=2")
        .replace("/logo-horizontal.png\"", "/logo-horizontal.png?v=2\"")
        .replace("/logo-horizontal.png'", "/logo-horizontal.png?v=2'")
        .replace("/logo-symbol.png?v=1", "/logo-symbol.png?v=2")
        .replace("/logo-symbol.png\"", "/logo-symbol.png?v=2\"")
        .replace("/logo-symbol.png'", "/logo-symbol.png?v=2'")
    )

    if updated != content:
        path.write_text(
            updated,
            encoding="utf-8",
            newline="\n",
        )


result = subprocess.run(
    ["npm.cmd", "run", "build"],
    cwd=FRONTEND,
)

if result.returncode:
    raise SystemExit(result.returncode)


print("\nEtapa 28 concluída.")
print("Os arquivos receberam aliases e versão v=3.")
print("\nExecute:")
print("git add frontend/index.html frontend/public frontend/src")
print('git commit -m "fix: atualiza cache dos brand assets"')
print("git push origin main")
