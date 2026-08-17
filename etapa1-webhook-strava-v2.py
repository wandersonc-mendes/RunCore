from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parent

INTEGRATIONS = ROOT / "src/api/routers/integrations.py"
INTEGRATION_REPOSITORY = (
    ROOT / "src/repositories/integration_repository.py"
)
ORIGIN_GUARD = ROOT / "src/api/origin_guard.py"

TARGETS = {
    "src/api/routers/integrations.py",
    "src/repositories/integration_repository.py",
    "src/api/origin_guard.py",
}


def run(cmd):
    return subprocess.run(
        cmd,
        cwd=ROOT,
        text=True,
        capture_output=True,
    )


def fail(message):
    raise RuntimeError(message)


if not (ROOT / ".git").exists():
    fail("Execute este arquivo na raiz do RunCore.")

branch = run(["git", "branch", "--show-current"])
if branch.returncode != 0:
    fail(branch.stderr or "Não foi possível identificar a branch.")

if branch.stdout.strip() != "main":
    fail("A branch atual deve ser main.")

for path in (
    INTEGRATIONS,
    INTEGRATION_REPOSITORY,
    ORIGIN_GUARD,
):
    if not path.exists():
        fail(f"Arquivo esperado não encontrado: {path}")

status = run(["git", "status", "--short"])
if status.returncode != 0:
    fail(status.stderr)

tracked = [
    line
    for line in status.stdout.splitlines()
    if line and not line.startswith("??")
]

if tracked:
    fail(
        "Existem alterações rastreadas não commitadas:\n"
        + "\n".join(tracked)
    )

integrations = INTEGRATIONS.read_text(encoding="utf-8")
repository = INTEGRATION_REPOSITORY.read_text(
    encoding="utf-8"
)
origin_guard = ORIGIN_GUARD.read_text(encoding="utf-8")

# 1. integrations.py

old_import = (
    "from fastapi import APIRouter, Depends, HTTPException, Query\n"
)
new_import = (
    "from fastapi import APIRouter, BackgroundTasks, Depends, "
    "HTTPException, Query\n"
)

if "BackgroundTasks" not in integrations:
    if integrations.count(old_import) != 1:
        fail(
            "Fingerprint do import FastAPI em integrations.py "
            "não confere."
        )
    integrations = integrations.replace(
        old_import,
        new_import,
        1,
    )

config_anchor = '''def strava_config_status():
    return {
        "client_id": bool(os.getenv("STRAVA_CLIENT_ID")),
        "client_secret": bool(os.getenv("STRAVA_CLIENT_SECRET")),
        "redirect_uri": bool(strava_redirect_uri()),
    }


'''

webhook_block = '''def strava_config_status():
    return {
        "client_id": bool(os.getenv("STRAVA_CLIENT_ID")),
        "client_secret": bool(os.getenv("STRAVA_CLIENT_SECRET")),
        "redirect_uri": bool(strava_redirect_uri()),
    }


def strava_webhook_verify_token():
    return os.getenv(
        "STRAVA_WEBHOOK_VERIFY_TOKEN",
        "",
    )


def process_strava_webhook_event(event):
    if event.get("object_type") != "activity":
        return

    if event.get("aspect_type") != "create":
        return

    owner_id = event.get("owner_id")
    object_id = event.get("object_id")

    if owner_id is None or object_id is None:
        return

    integration = repository.get_by_external_user_id(
        provider="strava",
        external_user_id=str(owner_id),
    )

    if integration is None or not integration.active:
        return

    try:
        integration = refresh_strava_token(
            integration,
        )

        activity = strava_request(
            (
                "https://www.strava.com/api/v3/activities/"
                f"{object_id}"
            ),
            integration.access_token,
        )

        athlete_id = access.athlete_for_student(
            integration.user_id,
        )

        activities.sync_strava_batch(
            integration.id,
            [activity],
            athlete_id=athlete_id,
        )

    except Exception:
        return


@router.get("/strava/webhook")
def validate_strava_webhook(
    mode: str = Query(alias="hub.mode"),
    challenge: str = Query(
        alias="hub.challenge",
    ),
    verify_token: str = Query(
        alias="hub.verify_token",
    ),
):
    expected_token = (
        strava_webhook_verify_token()
    )

    if (
        not expected_token
        or mode != "subscribe"
        or verify_token != expected_token
    ):
        raise HTTPException(
            status_code=403,
            detail=(
                "Verificação de webhook inválida."
            ),
        )

    return {
        "hub.challenge": challenge,
    }


@router.post("/strava/webhook")
def receive_strava_webhook(
    event: dict,
    background_tasks: BackgroundTasks,
):
    background_tasks.add_task(
        process_strava_webhook_event,
        event,
    )

    return {
        "received": True,
    }


'''

if '@router.get("/strava/webhook")' not in integrations:
    if integrations.count(config_anchor) != 1:
        fail(
            "Fingerprint de strava_config_status() "
            "não confere."
        )
    integrations = integrations.replace(
        config_anchor,
        webhook_block,
        1,
    )

# 2. integration_repository.py

if "def get_by_external_user_id(" not in repository:
    save_anchor = "    def save(self, item):\n"

    if repository.count(save_anchor) != 1:
        fail(
            "Fingerprint de IntegrationRepository.save() "
            "não confere."
        )

    method = '''    def get_by_external_user_id(
        self,
        provider,
        external_user_id,
    ):
        session = SessionLocal()

        item = session.scalars(
            select(ExternalIntegration).where(
                ExternalIntegration.provider
                == provider,
                ExternalIntegration.external_user_id
                == str(external_user_id),
            )
        ).first()

        session.close()
        return item

'''

    repository = repository.replace(
        save_anchor,
        method + save_anchor,
        1,
    )

# 3. origin_guard.py

old_exempt = (
    'ORIGIN_GUARD_EXEMPT_PATHS = {"/health"}\n'
)

new_exempt = '''ORIGIN_GUARD_EXEMPT_PATHS = {
    "/health",
    "/api/integrations/strava/webhook",
}
'''

if (
    '"/api/integrations/strava/webhook"'
    not in origin_guard
):
    if origin_guard.count(old_exempt) != 1:
        fail(
            "Fingerprint de ORIGIN_GUARD_EXEMPT_PATHS "
            "não confere."
        )
    origin_guard = origin_guard.replace(
        old_exempt,
        new_exempt,
        1,
    )

# Valida tudo ANTES de gravar

required_integrations = (
    "BackgroundTasks",
    "STRAVA_WEBHOOK_VERIFY_TOKEN",
    "def process_strava_webhook_event(event):",
    '@router.get("/strava/webhook")',
    '@router.post("/strava/webhook")',
    "activities.sync_strava_batch(",
    "repository.get_by_external_user_id(",
)

for marker in required_integrations:
    if marker not in integrations:
        fail(
            "Validação estrutural de integrations.py "
            f"falhou: {marker}"
        )

required_repository = (
    "def get_by_external_user_id(",
    "ExternalIntegration.external_user_id",
)

for marker in required_repository:
    if marker not in repository:
        fail(
            "Validação estrutural do repositório "
            f"falhou: {marker}"
        )

if (
    '"/api/integrations/strava/webhook"'
    not in origin_guard
):
    fail(
        "O webhook não foi liberado no origin_guard."
    )

# Só agora grava.

INTEGRATIONS.write_text(
    integrations,
    encoding="utf-8",
    newline="\n",
)

INTEGRATION_REPOSITORY.write_text(
    repository,
    encoding="utf-8",
    newline="\n",
)

ORIGIN_GUARD.write_text(
    origin_guard,
    encoding="utf-8",
    newline="\n",
)

# Compilação

compile_check = run([
    "python",
    "-m",
    "py_compile",
    str(INTEGRATIONS),
    str(INTEGRATION_REPOSITORY),
    str(ORIGIN_GUARD),
])

if compile_check.returncode != 0:
    print(compile_check.stdout)
    print(compile_check.stderr)
    raise SystemExit(
        "Compilação falhou. Não faça commit."
    )

# Confere escopo final

after = run(["git", "status", "--short"])
if after.returncode != 0:
    fail(after.stderr)

tracked_after = [
    line
    for line in after.stdout.splitlines()
    if line and not line.startswith("??")
]

unexpected = [
    line
    for line in tracked_after
    if line[3:].strip() not in TARGETS
]

if unexpected:
    fail(
        "Há alterações rastreadas inesperadas:\n"
        + "\n".join(unexpected)
    )

changed_paths = {
    line[3:].strip()
    for line in tracked_after
}

missing_targets = TARGETS - changed_paths

if missing_targets:
    fail(
        "Nem todos os arquivos esperados ficaram "
        "modificados:\n"
        + "\n".join(sorted(missing_targets))
    )

print()
print("STRAVA WEBHOOK — ETAPA 1")
print("=" * 56)
print("Validação OK.")
print()
print("Implementado:")
print("- GET de validação do webhook")
print("- POST para receber eventos")
print("- processamento em BackgroundTasks")
print("- busca da integração por owner_id")
print("- reaproveitamento de sync_strava_batch()")
print("- exceção do callback no origin_guard")
print()
print("Nenhuma migração ou alteração de dados foi feita.")
print()
print("Ainda NÃO está ativo no Strava.")
print(
    "Após o deploy vamos configurar "
    "STRAVA_WEBHOOK_VERIFY_TOKEN e registrar a assinatura."
)
print()
print("Agora execute:")
print(
    "git add "
    "src/api/routers/integrations.py "
    "src/repositories/integration_repository.py "
    "src/api/origin_guard.py"
)
print(
    'git commit -m '
    '"feat: adiciona webhook de atividades Strava"'
)
print("git push")
