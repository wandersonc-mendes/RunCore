from pathlib import Path
import subprocess


ROOT = Path.cwd()
REPOSITORY = ROOT / "src/repositories/athlete_repository.py"
FRONTEND = ROOT / "frontend"

if not (ROOT / ".git").exists():
    raise RuntimeError("Execute este arquivo na raiz do RunCore.")

if not REPOSITORY.exists():
    raise RuntimeError(f"Arquivo não encontrado: {REPOSITORY}")

branch = subprocess.check_output(
    ["git", "branch", "--show-current"],
    cwd=ROOT,
    text=True,
).strip()

if branch != "main":
    raise RuntimeError(f"Branch atual: {branch}. Troque para main.")


content = REPOSITORY.read_text(encoding="utf-8")

anchor = '''    def link_user_and_coach(
        self,
        athlete_id: int,
        user_id: int,
        coach_user_id: int,
    ) -> Athlete | None:
'''

method = '''    def update_phone(
        self,
        athlete_id: int,
        phone: str,
    ) -> bool:

        with SessionLocal() as session:

            athlete = session.get(
                Athlete,
                athlete_id,
            )

            if athlete is None:
                return False

            athlete.phone = str(
                phone or "",
            ).strip()

            session.commit()

            return True

    def link_user_and_coach(
        self,
        athlete_id: int,
        user_id: int,
        coach_user_id: int,
    ) -> Athlete | None:
'''

if "    def update_phone(" not in content:
    if anchor not in content:
        raise RuntimeError(
            "Não encontrei o ponto para inserir update_phone."
        )

    content = content.replace(
        anchor,
        method,
        1,
    )


REPOSITORY.write_text(
    content,
    encoding="utf-8",
    newline="\n",
)


compile_result = subprocess.run(
    [
        "python",
        "-m",
        "py_compile",
        str(REPOSITORY),
        str(ROOT / "src/api/routers/profiles.py"),
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


print("\nEtapa 66B concluída.")
print(
    "O método update_phone agora existe e o salvamento "
    "do perfil pode concluir a operação."
)
print("\nExecute:")
print(
    "git add src/repositories/athlete_repository.py"
)
print(
    'git commit -m "fix: corrige salvamento do telefone no perfil"'
)
print("git push origin main")
