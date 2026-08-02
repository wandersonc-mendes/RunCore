from pathlib import Path
import subprocess

ROOT = Path.cwd()
ACCESS = ROOT / "src/repositories/access_repository.py"
FRONTEND = ROOT / "frontend"

if not (ROOT / ".git").exists():
    raise RuntimeError("Execute este arquivo na raiz do RunCore.")

if not ACCESS.exists():
    raise RuntimeError(f"Arquivo não encontrado: {ACCESS}")

branch = subprocess.check_output(
    ["git", "branch", "--show-current"],
    cwd=ROOT,
    text=True,
).strip()

if branch != "main":
    raise RuntimeError(f"Branch atual: {branch}. Troque para main.")

content = ACCESS.read_text(encoding="utf-8")

old_method = '''    def athlete_for_student(self, user_id):
        with SessionLocal() as session:
            profile = session.get(
                AthleteProfile,
                user_id,
            )

            if profile is not None:
                return profile.athlete_id

            athlete_id = session.scalar(
                select(Athlete.id).where(
                    Athlete.user_id == user_id,
                )
            )

            if athlete_id is None:
                return None

            session.add(
                AthleteProfile(
                    user_id=user_id,
                    athlete_id=athlete_id,
                )
            )
            session.commit()

            return athlete_id
'''

new_method = '''    def athlete_for_student(self, user_id):
        with SessionLocal() as session:
            profile = session.get(
                AthleteProfile,
                user_id,
            )

            if profile is not None:
                return profile.athlete_id

            return session.scalar(
                select(Athlete.id).where(
                    Athlete.user_id == user_id,
                )
            )
'''

if old_method in content:
    content = content.replace(old_method, new_method, 1)
elif new_method not in content:
    raise RuntimeError(
        "Não encontrei athlete_for_student no formato esperado."
    )

ACCESS.write_text(content, encoding="utf-8", newline="\n")

compile_result = subprocess.run(
    ["python", "-m", "py_compile", str(ACCESS)],
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

print("\nEtapa 64C concluída.")
print(
    "A resolução do aluno agora consulta os dois vínculos "
    "sem tentar inserir registros durante a leitura."
)
print("\nExecute:")
print("git add src/repositories/access_repository.py")
print('git commit -m "fix: evita conflito ao localizar perfil do aluno"')
print("git push origin main")
