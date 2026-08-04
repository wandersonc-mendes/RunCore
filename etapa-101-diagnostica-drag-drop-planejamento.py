from pathlib import Path
from datetime import datetime

ROOT = Path.cwd()
OUTPUT = ROOT / "diagnostico-etapa-101.txt"

if not (ROOT / ".git").exists():
    raise RuntimeError("Execute este arquivo na raiz do RunCore.")

frontend = ROOT / "frontend" / "src"
backend = ROOT / "src"

patterns = [
    "Planejamento",
    "Adicionar",
    "weekday",
    "week",
    "planned_distance",
    "updateSession",
    "update_session",
    "training-session",
    "training_session",
    "calendar",
    "drag",
    "drop",
]

lines = [
    "=== RUNCORE | DIAGNÓSTICO ETAPA 101 ===",
    "Movimentação de treinos por arrastar e soltar",
    f"Gerado em: {datetime.now().isoformat(timespec='seconds')}",
    "",
]

def scan(base: Path, suffixes: tuple[str, ...]):
    if not base.exists():
        lines.append(f"PASTA NÃO ENCONTRADA: {base}")
        lines.append("")
        return

    for path in sorted(base.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in suffixes:
            continue

        text = path.read_text(
            encoding="utf-8",
            errors="ignore",
        )

        matches = []
        for number, source_line in enumerate(
            text.splitlines(),
            start=1,
        ):
            if any(
                pattern.lower() in source_line.lower()
                for pattern in patterns
            ):
                matches.append(
                    f"{number:04d}: {source_line}"
                )

        if matches:
            lines.append(
                f"ARQUIVO: {path.relative_to(ROOT)}"
            )
            lines.append("-" * 100)
            lines.extend(matches[:220])
            lines.append("")

lines.append("FRONTEND")
lines.append("=" * 100)
scan(
    frontend,
    (".js", ".jsx", ".ts", ".tsx", ".css"),
)

lines.append("BACKEND")
lines.append("=" * 100)
scan(
    backend,
    (".py",),
)

lines.append("RESULTADO")
lines.append("=" * 100)
lines.append("Nenhum arquivo foi alterado.")
lines.append(
    "Envie este TXT para preparar a implementação."
)

OUTPUT.write_text(
    "\n".join(lines),
    encoding="utf-8",
    newline="\n",
)

print("Diagnóstico concluído.")
print(f"Arquivo gerado em: {OUTPUT}")
print("Envie esse arquivo no chat.")
