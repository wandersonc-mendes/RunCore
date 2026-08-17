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

status = run(["git", "status", "--short"])
if status.returncode != 0:
    raise RuntimeError(status.stderr)

tracked = [
    line for line in status.stdout.splitlines()
    if line and not line.startswith("??")
]
if tracked:
    raise RuntimeError(
        "Existem alterações rastreadas não commitadas:\n"
        + "\n".join(tracked)
    )

integrations = INTEGRATIONS.read_text(encoding="utf-8")
repository = REPOSITORY.read_text(encoding="utf-8")

old_fastapi = (
    "from fastapi import APIRouter, Depends, HTTPException, Query\n"
)
new_fastapi = (
    "from fastapi import APIRouter, BackgroundTasks, Depends, "
    "HTTPException, Query\n"
)

if integrations.count(old_fastapi) != 1:
    raise RuntimeError("Fingerprint do import FastAPI não confere.")

integrations = integrations.replace(old_fastapi, new_fastapi, 1)

anchor = '''def strava_config_status():
    return {
        "client_id": bool(os.getenv("STRAVA_CLIENT_ID")),
        "client_secret": bool(os.getenv("STRAVA_CLIENT_SECRET")),
        "redirect_uri": bool(strava_redirect_uri()),
    }


'''

addition = '''def strava_config_status():
    return {
        "client_id": bool(os.getenv("STRAVA_CLIENT_ID")),
        "client_secret": bool(os.getenv("STRAVA_CLIENT_SECRET")),
        "redirect_uri": bool(strava_redirect_uri()),
    }


def strava_webhook_verify_token():
    return os.getenv("STRAVA_WEBHOOK_VERIFY_TOKEN", "")


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
        "strava",
        str(owner_id),
    )

    if integration is None or not integration.active:
        return

    try:
        integration = refresh_strava_token(integration)
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
    challenge: str = Query(alias="hub.challenge"),
    verify_token: str = Query(alias="hub.verify_token"),
):
    expected_token = strava_webhook_verify_token()

    if (
        not expected_token
        or mode != "subscribe"
        or verify_token != expected_token
    ):
        raise HTTPException(
            status_code=403,
            detail="Verificação de webhook inválida.",
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

if integrations.count(anchor) != 1:
    raise RuntimeError("Fingerprint da configuração Strava não confere.")

integrations = integrations.replace(anchor, addition, 1)

repo_anchor = '''    def get_by_id(self, integration_id):
        session = SessionLocal()
        item = session.get(
            ExternalIntegration,
            integration_id,
        )
        session.close()
        return item

'''

repo_addition = '''    def get_by_id(self, integration_id):
        session = SessionLocal()
        item = session.get(
            ExternalIntegration,
            integration_id,
        )
        session.close()
        return item

    def get_by_external_user_id(
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

if repository.count(repo_anchor) != 1:
    raise RuntimeError(
        "Fingerprint do IntegrationRepository não confere."
    )

repository = repository.replace(
    repo_anchor,
    repo_addition,
    1,
)

INTEGRATIONS.write_text(
    integrations,
    encoding="utf-8",
    newline="\n",
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

after = run(["git", "status", "--short"])
allowed = {
    "src/api/routers/integrations.py",
    "src/repositories/integration_repository.py",
}
unexpected = []

for line in after.stdout.splitlines():
    if not line or line.startswith("??"):
        continue
    path = line[3:].strip()
    if path not in allowed:
        unexpected.append(line)

if unexpected:
    raise RuntimeError(
        "Há alterações rastreadas inesperadas:\n"
        + "\n".join(unexpected)
    )

combined = integrations + repository
for required in (
    '@router.get("/strava/webhook")',
    '@router.post("/strava/webhook")',
    "background_tasks.add_task(",
    "process_strava_webhook_event",
    "get_by_external_user_id",
):
    if required not in combined:
        raise RuntimeError(
            f"Validação estrutural falhou: {required}"
        )

print()
print("STRAVA WEBHOOK — ETAPA 1")
print("=" * 50)
print("Validação OK.")
print("Callback GET de verificação criado.")
print("Callback POST criado com processamento em background.")
print("Eventos CREATE de atividade reutilizam sync_strava_batch.")
print("Nenhuma migração ou alteração de dados foi feita.")
print()
print("IMPORTANTE:")
print("Ainda falta configurar STRAVA_WEBHOOK_VERIFY_TOKEN")
print("e registrar a assinatura no Strava após o deploy.")
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
