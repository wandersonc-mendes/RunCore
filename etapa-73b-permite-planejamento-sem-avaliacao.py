from pathlib import Path
import subprocess

ROOT = Path.cwd()
STUDENT = ROOT / "src/api/routers/student.py"
TRAININGS = ROOT / "src/api/routers/trainings.py"
PERSISTENCE = ROOT / "src/core/training/training_persistence_service.py"
FRONTEND = ROOT / "frontend"

if not (ROOT / ".git").exists():
    raise RuntimeError("Execute este arquivo na raiz do RunCore.")

for path in (STUDENT, TRAININGS, PERSISTENCE):
    if not path.exists():
        raise RuntimeError(f"Arquivo não encontrado: {path}")

branch = subprocess.check_output(
    ["git", "branch", "--show-current"],
    cwd=ROOT,
    text=True,
).strip()

if branch != "main":
    raise RuntimeError(
        f"Branch atual: {branch}. Troque para main."
    )

# ---------------------------------------------------------
# Persistência: VDOT opcional e sem geração automática.
# ---------------------------------------------------------
persistence = PERSISTENCE.read_text(encoding="utf-8")

persistence = persistence.replace(
    "        vdot: float,\n",
    "        vdot: float | None,\n",
    1,
)

old_generate = '''        self._generate_sessions(
            training.id,
            vdot,
            total_weeks,
            ipt_profile,
            target_distance=target_distance,
        )

        return training
'''

new_generate = '''        if vdot is not None:
            self._generate_sessions(
                training.id,
                vdot,
                total_weeks,
                ipt_profile,
                target_distance=target_distance,
            )

        return training
'''

if old_generate in persistence:
    persistence = persistence.replace(
        old_generate,
        new_generate,
        1,
    )
elif "if vdot is not None:" not in persistence:
    raise RuntimeError(
        "Não encontrei a geração automática em "
        "training_persistence_service.py."
    )

PERSISTENCE.write_text(
    persistence,
    encoding="utf-8",
    newline="\n",
)

# ---------------------------------------------------------
# Criação: meta obrigatória, avaliação opcional.
# ---------------------------------------------------------
trainings = TRAININGS.read_text(encoding="utf-8")

old_evaluation = '''    evaluation = get_latest_evaluation(athlete_id)
    goal = get_primary_goal(
'''

new_evaluation = '''    evaluation = evaluation_repository.last_evaluation(
        athlete_id,
    )

    goal = get_primary_goal(
'''

if old_evaluation in trainings:
    trainings = trainings.replace(
        old_evaluation,
        new_evaluation,
        1,
    )
elif "evaluation = evaluation_repository.last_evaluation(" not in trainings:
    raise RuntimeError(
        "Não encontrei a avaliação na criação do planejamento."
    )

old_create_call = '''    training = persistence_service.create_training(
        athlete_id=athlete_id,
        vdot=evaluation.vdot,
        name=payload.name,
        methodology="Jack Daniels",
        objective=objective,
'''

new_create_call = '''    has_evaluation = evaluation is not None

    training = persistence_service.create_training(
        athlete_id=athlete_id,
        vdot=(
            evaluation.vdot
            if has_evaluation
            else None
        ),
        name=payload.name,
        methodology=(
            "Jack Daniels"
            if has_evaluation
            else "Observação inicial"
        ),
        objective=objective,
'''

if old_create_call in trainings:
    trainings = trainings.replace(
        old_create_call,
        new_create_call,
        1,
    )
elif '"Observação inicial"' not in trainings:
    raise RuntimeError(
        "Não encontrei a chamada de criação do planejamento."
    )

TRAININGS.write_text(
    trainings,
    encoding="utf-8",
    newline="\n",
)

# ---------------------------------------------------------
# Área do aluno: meta obrigatória, avaliação opcional.
# Planejamento automático legado sem avaliação fica oculto.
# ---------------------------------------------------------
student = STUDENT.read_text(encoding="utf-8")

evaluation_gate = '''    evaluation = evaluations.last_evaluation(
        athlete_id,
    )

    if evaluation is None:
        return None

'''

student = student.replace(
    evaluation_gate,
    "",
)

training_anchor = '''    training = trainings.get_active_by_athlete(
        athlete_id,
    )

    return (
'''

replacement = '''    training = trainings.get_active_by_athlete(
        athlete_id,
    )

    if training is None:
        return None

    evaluation = evaluations.last_evaluation(
        athlete_id,
    )

    if (
        evaluation is None
        and training.methodology
        != "Observação inicial"
    ):
        return None

    return (
'''

if training_anchor in student:
    student = student.replace(
        training_anchor,
        replacement,
        1,
    )
elif 'training.methodology\n        != "Observação inicial"' not in student:
    raise RuntimeError(
        "Não encontrei o retorno do planejamento do aluno."
    )

STUDENT.write_text(
    student,
    encoding="utf-8",
    newline="\n",
)

compile_result = subprocess.run(
    [
        "python",
        "-m",
        "py_compile",
        str(STUDENT),
        str(TRAININGS),
        str(PERSISTENCE),
    ],
    cwd=ROOT,
)

if compile_result.returncode:
    raise SystemExit(compile_result.returncode)

build = subprocess.run(
    ["npm.cmd", "run", "build"],
    cwd=FRONTEND,
)

if build.returncode:
    raise SystemExit(build.returncode)

print("\nEtapa 73B concluída.")
print(
    "A meta continua obrigatória. A avaliação passa a ser "
    "opcional no ciclo inicial de observação."
)
print("\nExecute:")
print(
    "git add src/api/routers/student.py "
    "src/api/routers/trainings.py "
    "src/core/training/training_persistence_service.py"
)
print(
    'git commit -m "fix: permite planejamento inicial sem avaliacao"'
)
print("git push origin main")
