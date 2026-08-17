from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TARGET = ROOT / "src" / "repositories" / "training_session_repository.py"


def run(cmd):
    return subprocess.run(
        cmd,
        cwd=ROOT,
        text=True,
        capture_output=True,
    )


def replace_once(text, old, new, label):
    if old not in text:
        raise RuntimeError(
            f"Trecho não encontrado: {label}. "
            "O arquivo do GitHub pode ter mudado."
        )
    return text.replace(old, new, 1)


if not (ROOT / ".git").exists():
    raise RuntimeError("Execute este arquivo na raiz do RunCore.")

branch = run(["git", "branch", "--show-current"])
if branch.returncode != 0 or branch.stdout.strip() != "main":
    raise RuntimeError("Esta etapa deve ser aplicada na branch main.")

status = run(["git", "status", "--short"])
if status.returncode != 0:
    raise RuntimeError(status.stderr)

tracked_changes = [
    line
    for line in status.stdout.splitlines()
    if line and not line.startswith("??")
]

if tracked_changes:
    raise RuntimeError(
        "Existem alterações rastreadas não commitadas:\n"
        + "\n".join(tracked_changes)
    )

if not TARGET.exists():
    raise RuntimeError(
        "Arquivo não encontrado: "
        "src/repositories/training_session_repository.py"
    )

text = TARGET.read_text(encoding="utf-8")

text = replace_once(
    text,
    "from sqlalchemy import select\n",
    "from sqlalchemy import delete, select\n",
    "import SQLAlchemy delete",
)

text = replace_once(
    text,
    '''from models.training_session import (
    TrainingSession,
)
''',
    '''from models.training_session import (
    TrainingSession,
)
from models.training_step import TrainingStep
''',
    "import TrainingStep",
)

text = replace_once(
    text,
    '''    def delete_by_training(self, training_id):
        session = SessionLocal()

        try:
            items = session.scalars(
                select(TrainingSession)
                .where(
                    TrainingSession.training_id == training_id
                )
            ).all()

            for item in items:
                session.delete(item)

            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
''',
    '''    def delete_by_training(self, training_id):
        session = SessionLocal()

        try:
            session_ids = (
                select(TrainingSession.id)
                .where(
                    TrainingSession.training_id
                    == training_id
                )
            )

            session.execute(
                delete(TrainingStep)
                .where(
                    TrainingStep.session_id.in_(
                        session_ids
                    )
                )
            )

            session.execute(
                delete(TrainingSession)
                .where(
                    TrainingSession.training_id
                    == training_id
                )
            )

            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
''',
    "delete_by_training ORM -> bulk delete",
)

TARGET.write_text(
    text,
    encoding="utf-8",
    newline="\n",
)

compile_check = run([
    "python",
    "-m",
    "compileall",
    "-q",
    "src/repositories/training_session_repository.py",
])

if compile_check.returncode != 0:
    print(compile_check.stdout)
    print(compile_check.stderr)
    raise SystemExit(
        "Compilação falhou. "
        "Não faça commit; envie este retorno."
    )

updated = TARGET.read_text(encoding="utf-8")

assert "for item in items:" not in updated
assert "delete(TrainingStep)" in updated
assert "delete(TrainingSession)" in updated
assert "session_ids =" in updated

print()
print("ETAPA: OTIMIZA REGENERAÇÃO DO PLANEJAMENTO")
print("=" * 60)
print("Validação OK.")
print()
print("Alteração aplicada:")
print("  - remove exclusão ORM sessão por sessão")
print("  - exclui training_steps em lote")
print("  - exclui training_sessions em lote")
print("  - usa uma única transação/commit")
print()
print("Arquivo alterado:")
print("  src/repositories/training_session_repository.py")
print()
print("Comandos para commit:")
print(
    "git add "
    "src/repositories/training_session_repository.py"
)
print(
    'git commit -m '
    '"perf: otimiza regeneracao do planejamento"'
)
print("git push")
