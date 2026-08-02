from pathlib import Path
import subprocess

ROOT = Path.cwd()
GOALS = ROOT / "src/repositories/goal_repository.py"
STUDENT = ROOT / "src/api/routers/student.py"
TRAININGS = ROOT / "src/api/routers/trainings.py"
FRONTEND = ROOT / "frontend"

if not (ROOT / ".git").exists():
    raise RuntimeError("Execute este arquivo na raiz do RunCore.")

for path in (GOALS, STUDENT, TRAININGS):
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
# GoalRepository: meta válida do próprio usuário.
# ---------------------------------------------------------
goals_source = GOALS.read_text(encoding="utf-8")

if "from datetime import date" not in goals_source:
    goals_source = goals_source.replace(
        "from sqlalchemy import select\n",
        "from datetime import date\n\nfrom sqlalchemy import select\n",
        1,
    )

anchor = '''    def create(self, goal):
'''

method = '''    def get_active_primary_for_user(
        self,
        user_id,
    ):
        with SessionLocal() as session:
            statement = (
                select(Goal)
                .where(
                    Goal.user_id == user_id,
                    Goal.target_date >= date.today(),
                    Goal.status == "Em andamento",
                )
                .order_by(
                    Goal.target_date.asc(),
                )
            )

            items = list(
                session.scalars(statement)
            )

            principal = next(
                (
                    item
                    for item in items
                    if str(
                        item.priority or "",
                    ).strip().lower()
                    == "principal"
                ),
                None,
            )

            selected = (
                principal
                or (items[0] if items else None)
            )

            if selected is not None:
                session.expunge(selected)

            return selected

    def create(self, goal):
'''

if "def get_active_primary_for_user(" not in goals_source:
    if anchor not in goals_source:
        raise RuntimeError(
            "Não encontrei o ponto para inserir a consulta de meta."
        )
    goals_source = goals_source.replace(anchor, method, 1)

GOALS.write_text(
    goals_source,
    encoding="utf-8",
    newline="\n",
)

# ---------------------------------------------------------
# Área do aluno: exige meta do usuário + avaliação.
# ---------------------------------------------------------
student_source = STUDENT.read_text(encoding="utf-8")

old_imports = '''from repositories.evaluation_repository import EvaluationRepository
from repositories.training_repository import TrainingRepository
'''

new_imports = '''from repositories.evaluation_repository import EvaluationRepository
from repositories.goal_repository import GoalRepository
from repositories.training_repository import TrainingRepository
'''

if old_imports in student_source:
    student_source = student_source.replace(
        old_imports,
        new_imports,
        1,
    )
elif "GoalRepository" not in student_source:
    raise RuntimeError(
        "Não encontrei os imports de student.py."
    )

old_instances = '''evaluations = EvaluationRepository()
trainings = TrainingRepository()
'''

new_instances = '''evaluations = EvaluationRepository()
goals = GoalRepository()
trainings = TrainingRepository()
'''

if old_instances in student_source:
    student_source = student_source.replace(
        old_instances,
        new_instances,
        1,
    )
elif "goals = GoalRepository()" not in student_source:
    raise RuntimeError(
        "Não encontrei as instâncias de student.py."
    )

old_evaluation_block = '''    evaluation = evaluations.last_evaluation(
        athlete_id,
    )

    if evaluation is None:
        return None

    training = trainings.get_active_by_athlete(
'''

new_evaluation_block = '''    goal = goals.get_active_primary_for_user(
        user.id,
    )

    if goal is None:
        return None

    evaluation = evaluations.last_evaluation(
        athlete_id,
    )

    if evaluation is None:
        return None

    training = trainings.get_active_by_athlete(
'''

if old_evaluation_block in student_source:
    student_source = student_source.replace(
        old_evaluation_block,
        new_evaluation_block,
        1,
    )
elif "goal = goals.get_active_primary_for_user(" not in student_source:
    raise RuntimeError(
        "Não encontrei o fluxo de validação da planilha do aluno."
    )

STUDENT.write_text(
    student_source,
    encoding="utf-8",
    newline="\n",
)

# ---------------------------------------------------------
# Criação do planejamento: meta deixa de ser opcional.
# ---------------------------------------------------------
training_source = TRAININGS.read_text(encoding="utf-8")

old_goal_flow = '''    goal = get_primary_goal(athlete_id, payload.start_date)
    goal_data = goal_training_data(goal, payload.start_date)

    if goal_data:
        objective = goal_data['objective']
        target_distance = goal_data['target_distance']
        target_date = goal_data['target_date']
        total_weeks = goal_data['total_weeks']
    else:
        weeks_from_date = (
            weeks_between_dates(
                payload.start_date,
                payload.target_date,
            )
            if payload.target_date
            else None
        )
        objective = payload.objective
        target_distance = payload.target_distance
        target_date = payload.target_date
        total_weeks = payload.total_weeks or weeks_from_date or 8
'''

new_goal_flow = '''    goal = get_primary_goal(
        athlete_id,
        payload.start_date,
    )

    if goal is None:
        raise HTTPException(
            status_code=409,
            detail=(
                "Cadastre uma meta ativa para o atleta "
                "antes de gerar o planejamento."
            ),
        )

    goal_data = goal_training_data(
        goal,
        payload.start_date,
    )

    objective = goal_data["objective"]
    target_distance = goal_data["target_distance"]
    target_date = goal_data["target_date"]
    total_weeks = goal_data["total_weeks"]
'''

if old_goal_flow in training_source:
    training_source = training_source.replace(
        old_goal_flow,
        new_goal_flow,
        1,
    )
elif 'Cadastre uma meta ativa para o atleta' not in training_source:
    raise RuntimeError(
        "Não encontrei o fluxo de criação de planejamento."
    )

TRAININGS.write_text(
    training_source,
    encoding="utf-8",
    newline="\n",
)

compile_result = subprocess.run(
    [
        "python",
        "-m",
        "py_compile",
        str(GOALS),
        str(STUDENT),
        str(TRAININGS),
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

print("\nEtapa 73 concluída.")
print(
    "O planejamento agora exige meta ativa do aluno "
    "e avaliação vinculada ao atleta."
)
print("\nExecute:")
print(
    "git add src/repositories/goal_repository.py "
    "src/api/routers/student.py "
    "src/api/routers/trainings.py"
)
print(
    'git commit -m "fix: exige meta e avaliacao para planejamento"'
)
print("git push origin main")
