from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TARGET = ROOT / "src" / "api" / "routers" / "trainings.py"


def run(cmd):
    return subprocess.run(
        cmd,
        cwd=ROOT,
        text=True,
        capture_output=True,
    )


def replace_once(text, old, new, label):
    if old not in text:
        raise RuntimeError(f"Trecho não encontrado: {label}")
    return text.replace(old, new, 1)


if not (ROOT / ".git").exists():
    raise RuntimeError("Execute este arquivo na raiz do RunCore.")

branch = run(["git", "branch", "--show-current"])
if branch.returncode != 0 or branch.stdout.strip() != "main":
    raise RuntimeError("Esta etapa deve ser aplicada na branch main.")

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

if not TARGET.exists():
    raise RuntimeError(
        "Arquivo não encontrado: src/api/routers/trainings.py"
    )

text = TARGET.read_text(encoding="utf-8")

text = replace_once(
    text,
    '''def serialize_training(training):
    sessions = session_repository.list_by_training(training.id)
''',
    '''def session_calendar_date(
    training_start,
    session_week: int,
    session_weekday: int,
):
    if training_start is None:
        return None

    cycle_week_monday = (
        training_start
        - timedelta(days=training_start.weekday())
    )

    session_date = (
        cycle_week_monday
        + timedelta(
            weeks=max(session_week - 1, 0),
            days=session_weekday,
        )
    )

    if session_date < training_start:
        return None

    return session_date


def calendar_week_number(
    training_start,
    reference_date,
) -> int:
    if training_start is None or reference_date <= training_start:
        return 1

    cycle_week_monday = (
        training_start
        - timedelta(days=training_start.weekday())
    )
    reference_week_monday = (
        reference_date
        - timedelta(days=reference_date.weekday())
    )

    return max(
        1,
        ((reference_week_monday - cycle_week_monday).days // 7)
        + 1,
    )


def serialize_training(training):
    sessions = session_repository.list_by_training(training.id)
''',
    "helpers de calendário",
)

text = replace_once(
    text,
    '''    current_week = 1
    if training.start_date:
        current_week = max(1, ((date.today() - training.start_date).days // 7) + 1)
    current_week = min(current_week, total_weeks)
''',
    '''    current_week = calendar_week_number(
        training.start_date,
        date.today(),
    )
    current_week = min(current_week, total_weeks)
''',
    "cálculo de current_week",
)

text = replace_once(
    text,
    '''                "session_date": session.scheduled_date or ((training.start_date + timedelta(days=((session.week - 1) * 7) + session.weekday)) if training.start_date else None),
''',
    '''                "session_date": (
                    session.scheduled_date
                    or session_calendar_date(
                        training.start_date,
                        session.week,
                        session.weekday,
                    )
                ),
''',
    "cálculo de session_date",
)

text = replace_once(
    text,
    '''            }
            for session in sessions
        ],
''',
    '''            }
            for session in sessions
            if (
                session.scheduled_date is not None
                or session_calendar_date(
                    training.start_date,
                    session.week,
                    session.weekday,
                ) is not None
            )
        ],
''',
    "filtro de sessões anteriores ao início",
)

TARGET.write_text(text, encoding="utf-8", newline="\n")

compile_check = run([
    "python",
    "-m",
    "compileall",
    "-q",
    "src/api/routers/trainings.py",
])

if compile_check.returncode != 0:
    print(compile_check.stdout)
    print(compile_check.stderr)
    raise SystemExit(
        "Compilação falhou. Não faça commit; envie este retorno."
    )

validation_code = (
    "from datetime import date, timedelta\n"
    "start = date(2026, 8, 12)\n"
    "monday = start - timedelta(days=start.weekday())\n"
    "def session_date(week, weekday):\n"
    "    return monday + timedelta(weeks=week - 1, days=weekday)\n"
    "assert session_date(1, 0) == date(2026, 8, 10)\n"
    "assert session_date(1, 2) == date(2026, 8, 12)\n"
    "assert session_date(1, 4) == date(2026, 8, 14)\n"
    "assert session_date(2, 0) == date(2026, 8, 17)\n"
    "print('Calendário validado:')\n"
    "print('Semana 1: Qua 12/08, Sex 14/08')\n"
    "print('Semana 2: Seg 17/08')\n"
)

validation = run([
    "python",
    "-c",
    validation_code,
])

print(validation.stdout)
print(validation.stderr)

if validation.returncode != 0:
    raise SystemExit(
        "Validação de calendário falhou. "
        "Não faça commit; envie este retorno."
    )

print()
print("ETAPA: CORRIGE SEMANA CIVIL DO PLANEJAMENTO")
print("=" * 58)
print("Esperado para início em quarta 12/08/2026:")
print("  Semana 1: Qua 12/08 e Sex 14/08")
print("  Segunda 10/08 não aparece")
print("  Semana 2: Seg 17/08, Qua 19/08, Sex 21/08")
print("  current_week vira 2 na segunda 17/08")
print()
print("Arquivo alterado:")
print("  src/api/routers/trainings.py")
print()
print("Comandos:")
print("git add src/api/routers/trainings.py")
print('git commit -m "fix: corrige calendario semanal do planejamento"')
print("git push")
