from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
INTEGRATIONS = ROOT / "src/api/routers/integrations.py"
REPOSITORY = ROOT / "src/repositories/integration_repository.py"


def run(cmd):
    return subprocess.run(
        cmd,
        cwd=ROOT,
        text=True,
        capture_output=True,
    )


if not (ROOT / ".git").exists():
    raise RuntimeError("Execute este arquivo na raiz do RunCore.")

branch = run(["git", "branch", "--show-current"])
if branch.returncode != 0 or branch.stdout.strip() != "main":
    raise RuntimeError("A branch atual deve ser main.")

if not INTEGRATIONS.exists() or not REPOSITORY.exists():
    raise RuntimeError("Arquivos esperados da integração Strava não encontrados.")

status = run(["git", "status", "--short"])
if status.returncode != 0:
    raise RuntimeError(status.stderr)

tracked = [
    line
    for line in status.stdout.splitlines()
    if line and not line.startswith("??")
]

allowed = {
    "src/api/routers/integrations.py",
    "src/repositories/integration_repository.py",
}

unexpected = [
    line
    for line in tracked
    if line[3:].strip() not in allowed
]

if unexpected:
    raise RuntimeError(
        "Existem alterações rastreadas inesperadas:\n"
        + "\n".join(unexpected)
    )

integrations = INTEGRATIONS.read_text(encoding="utf-8")
repository = REPOSITORY.read_text(encoding="utf-8")

required_partial = (
    "BackgroundTasks",
    "def process_strava_webhook_event(event):",
    '@router.get("/strava/webhook")',
    '@router.post("/strava/webhook")',
    "STRAVA_WEBHOOK_VERIFY_TOKEN",
)

missing = [
    marker
    for marker in required_partial
    if marker not in integrations
]

if missing:
    raise RuntimeError(
        "A primeira parte do script anterior não está completa.\n"
        "Faltando:\n"
        + "\n".join(missing)
    )

if "def get_by_external_user_id(" not in repository:
    save_anchor = "    def save(self, item):\n"

    if repository.count(save_anchor) != 1:
        raise RuntimeError(
            "Não foi possível localizar de forma segura o método save()."
        )

    new_method = '''    def get_by_external_user_id(
        self,
        provider,
        external_user_id,
    ):
        session = SessionLocal()
        item = session.scalars(
            select(ExternalIntegration).where(
                ExternalIntegration.provider == provider,
                ExternalIntegration.external_user_id
                == str(external_user_id),
            )
        ).first()
        session.close()
        return item

'''

    repository = repository.replace(
        save_anchor,
        new_method + save_anchor,
        1,
    )

    REPOSITORY.write_text(
        repository,
        encoding="utf-8",
        newline="\n",
    )

compile_check = run([
    "python",
    "-m",
    "py_compile",
    str(INTEGRATIONS),
    str(REPOSITORY),
])

if compile_check.returncode != 0:
    print(compile_check.stdout)
    print(compile_check.stderr)
    raise SystemExit("Compilação falhou. Não faça commit.")

repository = REPOSITORY.read_text(encoding="utf-8")

for marker in (
    "def get_by_external_user_id(",
    "ExternalIntegration.external_user_id",
):
    if marker not in repository:
        raise RuntimeError(
            f"Validação estrutural falhou: {marker}"
        )

after = run(["git", "status", "--short"])
tracked_after = [
    line
    for line in after.stdout.splitlines()
    if line and not line.startswith("??")
]

unexpected_after = [
    line
    for line in tracked_after
    if line[3:].strip() not in allowed
]

if unexpected_after:
    raise RuntimeError(
        "Há alterações rastreadas inesperadas após a correção:\n"
        + "\n".join(unexpected_after)
    )

changed_paths = {
    line[3:].strip()
    for line in tracked_after
}

if "src/api/routers/integrations.py" not in changed_paths:
    raise RuntimeError(
        "integrations.py não aparece modificado. "
        "A parte anterior pode não ter sido aplicada."
    )

if "src/repositories/integration_repository.py" not in changed_paths:
    raise RuntimeError(
        "integration_repository.py não aparece modificado."
    )

print()
print("STRAVA WEBHOOK — ETAPA 1 / CONTINUAÇÃO")
print("=" * 54)
print("Validação OK.")
print("Webhook GET/POST confirmado em integrations.py.")
print("Busca por external_user_id adicionada ao repositório.")
print("Os dois arquivos compilam normalmente.")
print()
print("Agora execute:")
print(
    "git add src/api/routers/integrations.py "
    "src/repositories/integration_repository.py"
)
print(
    'git commit -m "feat: adiciona webhook de atividades Strava"'
)
print("git push")
