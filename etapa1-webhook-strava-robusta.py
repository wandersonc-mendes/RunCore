from __future__ import annotations

import ast
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent
if not (ROOT / "src").is_dir():
    ROOT = Path.cwd().resolve()

INTEGRATIONS = ROOT / "src/api/routers/integrations.py"
INTEGRATION_REPOSITORY = ROOT / "src/repositories/integration_repository.py"
ACTIVITY_REPOSITORY = ROOT / "src/repositories/activity_repository.py"
TARGETS = (
    INTEGRATIONS,
    INTEGRATION_REPOSITORY,
    ACTIVITY_REPOSITORY,
)


def run(command: list[str], cwd: Path = ROOT) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        text=True,
        capture_output=True,
        check=False,
    )


def replace_once(source: str, old: str, new: str, label: str) -> str:
    count = source.count(old)
    if count != 1:
        raise RuntimeError(
            f"Estrutura inesperada em {label}: esperado 1 ponto de alteração, encontrado {count}."
        )
    return source.replace(old, new, 1)


def replace_between(
    source: str,
    start_marker: str,
    end_marker: str,
    replacement: str,
    label: str,
) -> str:
    if source.count(start_marker) != 1 or source.count(end_marker) != 1:
        raise RuntimeError(f"Estrutura inesperada em {label}.")
    start = source.index(start_marker)
    end = source.index(end_marker, start) + len(end_marker)
    return source[:start] + replacement + source[end:]


def tracked_changes() -> list[str]:
    result = run(["git", "status", "--porcelain", "--untracked-files=no"])
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "Não foi possível consultar o Git.")
    return [line for line in result.stdout.splitlines() if line]


if not (ROOT / ".git").exists():
    raise RuntimeError("Execute este script na raiz do RunCore.")

branch = run(["git", "branch", "--show-current"])
if branch.returncode != 0 or branch.stdout.strip() != "main":
    raise RuntimeError("A branch atual deve ser main.")

dirty = tracked_changes()
if dirty:
    raise RuntimeError(
        "A main precisa estar sem alterações rastreadas antes da Etapa 1:\n"
        + "\n".join(dirty)
    )

for target in TARGETS:
    if not target.is_file():
        raise RuntimeError(f"Arquivo esperado não encontrado: {target.relative_to(ROOT)}")

original = {path: path.read_text(encoding="utf-8") for path in TARGETS}

if any(
    marker in original[INTEGRATIONS]
    for marker in ('@router.get("/strava/webhook")', '@router.post("/strava/webhook")')
):
    raise RuntimeError("O webhook Strava já existe; nenhuma alteração foi feita.")

integrations = original[INTEGRATIONS]
integration_repository = original[INTEGRATION_REPOSITORY]
activity_repository = original[ACTIVITY_REPOSITORY]

integrations = replace_once(
    integrations,
    "import json\nimport time\n",
    "import json\nimport logging\nimport secrets\nimport time\n",
    "imports de integrations.py",
)
integrations = replace_once(
    integrations,
    "from fastapi import APIRouter, Depends, HTTPException, Query\n",
    "from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query\n",
    "import do FastAPI",
)
integrations = replace_once(
    integrations,
    "router = APIRouter(prefix=\"/integrations\", tags=[\"integrations\"])\n",
    "logger = logging.getLogger(__name__)\n\n\n"
    "router = APIRouter(prefix=\"/integrations\", tags=[\"integrations\"])\n",
    "declaração do router",
)

config_anchor = '''def strava_config_status():
    return {
        "client_id": bool(os.getenv("STRAVA_CLIENT_ID")),
        "client_secret": bool(os.getenv("STRAVA_CLIENT_SECRET")),
        "redirect_uri": bool(strava_redirect_uri()),
    }


'''

webhook_code = config_anchor + '''def strava_webhook_verify_token():
    return os.getenv("STRAVA_WEBHOOK_VERIFY_TOKEN", "")


def process_strava_webhook_event(event):
    if (
        event.get("object_type") != "activity"
        or event.get("aspect_type") != "create"
    ):
        return

    owner_id = event.get("owner_id")
    object_id = event.get("object_id")
    if not isinstance(owner_id, int) or not isinstance(object_id, int):
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
            f"https://www.strava.com/api/v3/activities/{object_id}",
            integration.access_token,
        )
        athlete_id = access.athlete_for_student(integration.user_id)
        activities.sync_strava_batch(
            integration.id,
            [activity],
            athlete_id=athlete_id,
        )
    except Exception:
        logger.exception(
            "Falha ao processar evento Strava da atividade %s.",
            object_id,
        )


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
        or not secrets.compare_digest(verify_token, expected_token)
    ):
        raise HTTPException(
            status_code=403,
            detail="Verificação de webhook inválida.",
        )
    return {"hub.challenge": challenge}


@router.post("/strava/webhook")
def receive_strava_webhook(
    event: dict,
    background_tasks: BackgroundTasks,
):
    background_tasks.add_task(process_strava_webhook_event, event)
    return {"received": True}


'''
integrations = replace_once(
    integrations,
    config_anchor,
    webhook_code,
    "configuração Strava",
)

new_sync_body = '''    athlete_id = access.athlete_for_student(user.id)
    return activities.sync_strava_batch(
        integration.id,
        data,
        athlete_id=athlete_id,
    )
'''
integrations = replace_between(
    integrations,
    "    imported = 0\n    for activity in data:\n",
    '    return {"imported": imported, "activities": activities.list_for_integration(integration.id)}\n',
    new_sync_body,
    "sincronização manual do Strava",
)

repo_anchor = '''    def save(self, item):
        session = SessionLocal()
'''
repo_method = '''    def get_by_external_user_id(
        self,
        provider,
        external_user_id,
    ):
        with SessionLocal() as session:
            item = session.scalars(
                select(ExternalIntegration).where(
                    ExternalIntegration.provider == provider,
                    ExternalIntegration.external_user_id
                    == str(external_user_id),
                )
            ).first()
            if item is not None:
                session.expunge(item)
            return item

    def save(self, item):
        session = SessionLocal()
'''
integration_repository = replace_once(
    integration_repository,
    repo_anchor,
    repo_method,
    "IntegrationRepository",
)

activity_repository = replace_once(
    activity_repository,
    "from sqlalchemy import select\n",
    "from datetime import datetime\n\nfrom sqlalchemy import select\n",
    "imports de ActivityRepository",
)
activity_anchor = '''    def link_training_session(
        self,
        activity_id,
        athlete_id,
        activity_day,
    ):
'''
batch_method = '''    def sync_strava_batch(
        self,
        integration_id,
        payload,
        athlete_id=None,
    ):
        imported = 0
        for activity in payload:
            provider_id = activity.get("id")
            if provider_id is None:
                continue

            item = self.get_by_provider_id(provider_id)
            if item is None:
                item = ImportedActivity(
                    integration_id=integration_id,
                    provider_activity_id=str(provider_id),
                )
                imported += 1

            item.integration_id = integration_id
            item.name = activity.get("name", "Atividade")
            item.sport_type = (
                activity.get("sport_type")
                or activity.get("type", "")
            )
            item.distance = round(activity.get("distance", 0) / 1000, 3)
            item.moving_time = activity.get("moving_time", 0)
            item.elapsed_time = activity.get("elapsed_time")
            item.average_speed = activity.get("average_speed")
            item.max_speed = activity.get("max_speed")
            item.average_heartrate = activity.get("average_heartrate")
            item.max_heartrate = activity.get("max_heartrate")
            item.average_cadence = activity.get("average_cadence")
            item.total_elevation_gain = activity.get("total_elevation_gain")

            start_at = activity.get("start_date")
            item.start_at = (
                datetime.fromisoformat(start_at.replace("Z", "+00:00"))
                if start_at
                else None
            )
            saved_item = self.save(item)

            sport_type = str(item.sport_type or "").lower()
            local_start = activity.get("start_date_local")
            local_day = (
                datetime.fromisoformat(
                    local_start.replace("Z", "+00:00")
                ).date()
                if local_start
                else None
            )
            if sport_type in {"run", "virtualrun", "trailrun"}:
                self.link_training_session(
                    saved_item.id,
                    athlete_id,
                    local_day,
                )

        return {
            "imported": imported,
            "activities": self.list_for_integration(integration_id),
        }

    def link_training_session(
        self,
        activity_id,
        athlete_id,
        activity_day,
    ):
'''
activity_repository = replace_once(
    activity_repository,
    activity_anchor,
    batch_method,
    "ActivityRepository",
)

updated = {
    INTEGRATIONS: integrations,
    INTEGRATION_REPOSITORY: integration_repository,
    ACTIVITY_REPOSITORY: activity_repository,
}

required = {
    INTEGRATIONS: (
        '@router.get("/strava/webhook")',
        '@router.post("/strava/webhook")',
        "background_tasks.add_task(process_strava_webhook_event, event)",
        "repository.get_by_external_user_id(",
        "activities.sync_strava_batch(",
    ),
    INTEGRATION_REPOSITORY: ("def get_by_external_user_id(",),
    ACTIVITY_REPOSITORY: ("def sync_strava_batch(",),
}

for path, source in updated.items():
    ast.parse(source, filename=str(path))
    for marker in required[path]:
        if source.count(marker) < 1:
            raise RuntimeError(
                f"Validação estrutural falhou em {path.name}: {marker}"
            )

if integrations.count("activities.sync_strava_batch(") != 2:
    raise RuntimeError(
        "A sincronização em lote deve ser usada exatamente pelo webhook e pelo botão manual."
    )

with tempfile.TemporaryDirectory(prefix="runcore-strava-") as temp_dir:
    temp_root = Path(temp_dir)
    temp_files = []
    for path, source in updated.items():
        temp_path = temp_root / path.name
        temp_path.write_text(source, encoding="utf-8", newline="\n")
        temp_files.append(str(temp_path))
    compiled = run(["python", "-m", "py_compile", *temp_files], cwd=temp_root)
    if compiled.returncode != 0:
        raise RuntimeError(
            "py_compile falhou antes da gravação:\n"
            + (compiled.stderr.strip() or compiled.stdout.strip())
        )

# Grava somente depois de todas as validações passarem. Em qualquer falha de
# escrita, restaura os três arquivos para evitar uma aplicação parcial.
written = []
try:
    for path, source in updated.items():
        path.write_text(source, encoding="utf-8", newline="\n")
        written.append(path)
except Exception:
    for path in written:
        path.write_text(original[path], encoding="utf-8", newline="\n")
    raise

post_compile = run(["python", "-m", "py_compile", *map(str, TARGETS)])
if post_compile.returncode != 0:
    for path, source in original.items():
        path.write_text(source, encoding="utf-8", newline="\n")
    raise RuntimeError(
        "py_compile falhou após a gravação; os arquivos foram restaurados:\n"
        + (post_compile.stderr.strip() or post_compile.stdout.strip())
    )

changed = tracked_changes()
expected = {
    "src/api/routers/integrations.py",
    "src/repositories/integration_repository.py",
    "src/repositories/activity_repository.py",
}
actual = {line[3:].replace("\\", "/") for line in changed}
if actual != expected:
    raise RuntimeError(
        "Alterações rastreadas inesperadas após a aplicação:\n"
        + "\n".join(changed)
    )

print("\nSTRAVA WEBHOOK — ETAPA 1")
print("=" * 50)
print("Validação estrutural e py_compile: OK")
print("GET e POST /api/integrations/strava/webhook: OK")
print("Lookup por external_user_id: OK")
print("Botão manual e webhook reutilizam sync_strava_batch(): OK")
print("Nenhuma migração ou alteração de dados foi executada.")
print("\nRevise o diff e execute:")
print(
    "git add src/api/routers/integrations.py "
    "src/repositories/integration_repository.py "
    "src/repositories/activity_repository.py"
)
print('git commit -m "feat: adiciona webhook de atividades Strava"')
print("git push origin main")
