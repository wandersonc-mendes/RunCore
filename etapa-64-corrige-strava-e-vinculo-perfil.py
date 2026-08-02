from pathlib import Path
import subprocess


ROOT = Path.cwd()
ACCESS = ROOT / "src/repositories/access_repository.py"
INTEGRATIONS = ROOT / "src/api/routers/integrations.py"
FRONTEND = ROOT / "frontend"

if not (ROOT / ".git").exists():
    raise RuntimeError("Execute este arquivo na raiz do RunCore.")

for required in (ACCESS, INTEGRATIONS):
    if not required.exists():
        raise RuntimeError(f"Arquivo não encontrado: {required}")

branch = subprocess.check_output(
    ["git", "branch", "--show-current"],
    cwd=ROOT,
    text=True,
).strip()

if branch != "main":
    raise RuntimeError(f"Branch atual: {branch}. Troque para main.")


access = ACCESS.read_text(encoding="utf-8")

old_method = '''    def athlete_for_student(self, user_id):
        session = SessionLocal()
        profile = session.get(AthleteProfile, user_id)
        session.close()
        return profile.athlete_id if profile else None
'''

new_method = '''    def athlete_for_student(self, user_id):
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

if old_method in access:
    access = access.replace(
        old_method,
        new_method,
        1,
    )
elif new_method not in access:
    raise RuntimeError(
        "Não encontrei athlete_for_student no formato esperado."
    )

ACCESS.write_text(
    access,
    encoding="utf-8",
    newline="\n",
)


integrations = INTEGRATIONS.read_text(encoding="utf-8")

constant_anchor = '''access = AccessRepository()


'''

constant_block = '''access = AccessRepository()

DEFAULT_STRAVA_REDIRECT_URI = (
    "https://api.runcoreapp.com.br"
    "/api/integrations/strava/callback"
)


def strava_redirect_uri():
    return (
        os.getenv("STRAVA_REDIRECT_URI")
        or DEFAULT_STRAVA_REDIRECT_URI
    )


'''

if "DEFAULT_STRAVA_REDIRECT_URI" not in integrations:
    if constant_anchor not in integrations:
        raise RuntimeError(
            "Não encontrei o ponto de configuração do Strava."
        )

    integrations = integrations.replace(
        constant_anchor,
        constant_block,
        1,
    )


old_configured = '''def strava_configured():
    return bool(os.getenv("STRAVA_CLIENT_ID") and os.getenv("STRAVA_CLIENT_SECRET") and os.getenv("STRAVA_REDIRECT_URI"))
'''

new_configured = '''def strava_configured():
    return bool(
        os.getenv("STRAVA_CLIENT_ID")
        and os.getenv("STRAVA_CLIENT_SECRET")
        and strava_redirect_uri()
    )
'''

if old_configured in integrations:
    integrations = integrations.replace(
        old_configured,
        new_configured,
        1,
    )
elif new_configured not in integrations:
    raise RuntimeError(
        "Não encontrei strava_configured no formato esperado."
    )


old_status = '''        "redirect_uri": bool(os.getenv("STRAVA_REDIRECT_URI")),
'''

new_status = '''        "redirect_uri": bool(strava_redirect_uri()),
'''

if old_status in integrations:
    integrations = integrations.replace(
        old_status,
        new_status,
        1,
    )


old_query = '''    query = urlencode({"client_id": os.environ["STRAVA_CLIENT_ID"], "redirect_uri": os.environ["STRAVA_REDIRECT_URI"], "response_type": "code", "approval_prompt": "auto", "scope": "activity:read_all", "state": state})
'''

new_query = '''    query = urlencode({
        "client_id": os.environ["STRAVA_CLIENT_ID"],
        "redirect_uri": strava_redirect_uri(),
        "response_type": "code",
        "approval_prompt": "auto",
        "scope": "activity:read_all",
        "state": state,
    })
'''

if old_query in integrations:
    integrations = integrations.replace(
        old_query,
        new_query,
        1,
    )
elif new_query not in integrations:
    raise RuntimeError(
        "Não encontrei a montagem da autorização do Strava."
    )


old_form = '''    form = urlencode({
        "client_id": os.environ["STRAVA_CLIENT_ID"],
        "client_secret": os.environ["STRAVA_CLIENT_SECRET"],
        "code": code,
        "grant_type": "authorization_code",
    }).encode()
'''

new_form = '''    form = urlencode({
        "client_id": os.environ["STRAVA_CLIENT_ID"],
        "client_secret": os.environ["STRAVA_CLIENT_SECRET"],
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": strava_redirect_uri(),
    }).encode()
'''

if old_form in integrations:
    integrations = integrations.replace(
        old_form,
        new_form,
        1,
    )
elif new_form not in integrations:
    raise RuntimeError(
        "Não encontrei a troca do código OAuth do Strava."
    )


INTEGRATIONS.write_text(
    integrations,
    encoding="utf-8",
    newline="\n",
)


compile_result = subprocess.run(
    [
        "python",
        "-m",
        "py_compile",
        str(ACCESS),
        str(INTEGRATIONS),
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


print("\nEtapa 64 concluída.")
print("Perfil antigo recuperado pelo user_id.")
print(
    "Callback padrão do Strava: "
    "https://api.runcoreapp.com.br"
    "/api/integrations/strava/callback"
)
print()
print("No painel do Strava, configure:")
print("Authorization Callback Domain: api.runcoreapp.com.br")
print()
print("No Railway, remova STRAVA_REDIRECT_URI incorreta")
print("ou defina exatamente:")
print(
    "STRAVA_REDIRECT_URI=https://api.runcoreapp.com.br"
    "/api/integrations/strava/callback"
)
print("\nExecute:")
print(
    "git add src/repositories/access_repository.py "
    "src/api/routers/integrations.py"
)
print(
    'git commit -m "fix: corrige vinculo do atleta e callback do strava"'
)
print("git push origin main")
