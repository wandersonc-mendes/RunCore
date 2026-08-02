from pathlib import Path
import subprocess

ROOT = Path.cwd()
STUDENT = ROOT / "src/api/routers/student.py"
FRONTEND = ROOT / "frontend"

if not (ROOT / ".git").exists():
    raise RuntimeError("Execute este arquivo na raiz do RunCore.")

if not STUDENT.exists():
    raise RuntimeError(f"Arquivo não encontrado: {STUDENT}")

branch = subprocess.check_output(
    ["git", "branch", "--show-current"],
    cwd=ROOT,
    text=True,
).strip()

if branch != "main":
    raise RuntimeError(
        f"Branch atual: {branch}. Troque para main."
    )

source = STUDENT.read_text(encoding="utf-8")

old_import = '''from repositories.access_repository import AccessRepository
from repositories.training_repository import TrainingRepository
'''

new_import = '''from repositories.access_repository import AccessRepository
from repositories.evaluation_repository import EvaluationRepository
from repositories.training_repository import TrainingRepository
'''

if old_import in source:
    source = source.replace(old_import, new_import, 1)
elif "EvaluationRepository" not in source:
    raise RuntimeError(
        "Não encontrei os imports de student.py."
    )

old_instances = '''access = AccessRepository()
trainings = TrainingRepository()
'''

new_instances = '''access = AccessRepository()
evaluations = EvaluationRepository()
trainings = TrainingRepository()
'''

if old_instances in source:
    source = source.replace(old_instances, new_instances, 1)
elif "evaluations = EvaluationRepository()" not in source:
    raise RuntimeError(
        "Não encontrei as instâncias do endpoint do aluno."
    )

old_flow = '''    athlete_id = access.athlete_for_student(user.id)
    if athlete_id is None:
        return None

    training = trainings.get_active_by_athlete(athlete_id)
    return serialize_training(training) if training else None
'''

new_flow = '''    athlete_id = access.athlete_for_student(user.id)

    if athlete_id is None:
        return None

    evaluation = evaluations.last_evaluation(
        athlete_id,
    )

    if evaluation is None:
        return None

    training = trainings.get_active_by_athlete(
        athlete_id,
    )

    return (
        serialize_training(training)
        if training
        else None
    )
'''

if old_flow in source:
    source = source.replace(old_flow, new_flow, 1)
elif "evaluation = evaluations.last_evaluation(" not in source:
    raise RuntimeError(
        "Não encontrei o fluxo de /student/training."
    )

STUDENT.write_text(
    source,
    encoding="utf-8",
    newline="\n",
)

compile_result = subprocess.run(
    [
        "python",
        "-m",
        "py_compile",
        str(STUDENT),
        str(ROOT / "src/repositories/evaluation_repository.py"),
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

print("\nEtapa 72 concluída.")
print(
    "O endpoint do aluno agora só retorna planejamento "
    "quando existe avaliação vinculada ao mesmo atleta."
)
print("\nExecute:")
print("git add src/api/routers/student.py")
print(
    'git commit -m "fix: exige avaliacao antes de exibir planilha"'
)
print("git push origin main")
