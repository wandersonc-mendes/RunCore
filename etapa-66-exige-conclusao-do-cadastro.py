from pathlib import Path
import subprocess


ROOT = Path.cwd()
APP = ROOT / "frontend/src/App.jsx"
PROFILE = ROOT / "frontend/src/ProfilePanel.jsx"
BACKEND = ROOT / "src/api/routers/profiles.py"
FRONTEND = ROOT / "frontend"

if not (ROOT / ".git").exists():
    raise RuntimeError("Execute este arquivo na raiz do RunCore.")

for required in (APP, PROFILE, BACKEND):
    if not required.exists():
        raise RuntimeError(f"Arquivo não encontrado: {required}")

branch = subprocess.check_output(
    ["git", "branch", "--show-current"],
    cwd=ROOT,
    text=True,
).strip()

if branch != "main":
    raise RuntimeError(f"Branch atual: {branch}. Troque para main.")


# ------------------------------------------------------------------
# Backend: estado real de conclusão do cadastro
# ------------------------------------------------------------------
backend = BACKEND.read_text(encoding="utf-8")

old_serialize = '''def serialize(item, athlete=None):
    personal = dict(item.personal) if item else {}
    if athlete:
        personal.setdefault("name", athlete.name)
        personal.setdefault("email", athlete.email)
        personal.setdefault("phone", athlete.phone)
        personal.setdefault("goal", athlete.goal)
    return {"personal": personal, "parq": item.parq if item else {}, "training": item.training if item else {}}
'''

new_serialize = '''REQUIRED_PERSONAL_FIELDS = {
    "name": "Nome completo",
    "birth_date": "Data de nascimento",
    "sex": "Sexo",
    "phone": "Celular",
    "city": "Cidade",
    "state": "Estado",
}

REQUIRED_TRAINING_FIELDS = {
    "days": "Dias disponíveis",
    "modality": "Modalidade principal",
    "goal": "Objetivo atual",
}


def profile_completion(personal, parq, training):
    missing = []

    for field, label in REQUIRED_PERSONAL_FIELDS.items():
        value = personal.get(field)

        if not value or (
            isinstance(value, str)
            and not value.strip()
        ):
            missing.append(label)

    for index in range(1, 8):
        if parq.get(f"q{index}") not in {
            "Sim",
            "Não",
        }:
            missing.append(f"PAR-Q {index}")

    for field, label in REQUIRED_TRAINING_FIELDS.items():
        value = training.get(field)

        if not value or (
            isinstance(value, str)
            and not value.strip()
        ):
            missing.append(label)

    return {
        "complete": len(missing) == 0,
        "missing_fields": missing,
    }


def serialize(item, athlete=None):
    personal = dict(item.personal) if item else {}
    parq = dict(item.parq) if item else {}
    training = dict(item.training) if item else {}

    if athlete:
        personal.setdefault("name", athlete.name)
        personal.setdefault("email", athlete.email)
        personal.setdefault("phone", athlete.phone)
        personal.setdefault("goal", athlete.goal)

    completion = profile_completion(
        personal,
        parq,
        training,
    )

    return {
        "personal": personal,
        "parq": parq,
        "training": training,
        **completion,
    }
'''

if old_serialize in backend:
    backend = backend.replace(
        old_serialize,
        new_serialize,
        1,
    )
elif "def profile_completion(" not in backend:
    raise RuntimeError(
        "Não encontrei serialize em profiles.py no formato esperado."
    )

BACKEND.write_text(
    backend,
    encoding="utf-8",
    newline="\n",
)


# ------------------------------------------------------------------
# ProfilePanel: modo obrigatório e retorno após salvar
# ------------------------------------------------------------------
profile = PROFILE.read_text(encoding="utf-8")

profile = profile.replace(
    '''export default function ProfilePanel({ onClose }) {''',
    '''export default function ProfilePanel({
  onClose,
  onboarding = false,
  onSaved,
}) {''',
    1,
)

old_save = '''  async function save() { setSaving(true); setMessage(""); try { await saveStudentProfile(profile); setMessage("Perfil salvo com sucesso."); } catch (error) { setMessage(error.message); } finally { setSaving(false); } }
'''

new_save = '''  async function save() {
    setSaving(true);
    setMessage("");

    try {
      const savedProfile = await saveStudentProfile(profile);
      setProfile(savedProfile);

      if (savedProfile.complete) {
        setMessage("Cadastro concluído com sucesso.");
      } else {
        setMessage(
          `Complete os campos obrigatórios: ${
            savedProfile.missing_fields.join(", ")
          }.`,
        );
      }

      onSaved?.(savedProfile);
    } catch (error) {
      setMessage(error.message);
    } finally {
      setSaving(false);
    }
  }
'''

if old_save in profile:
    profile = profile.replace(
        old_save,
        new_save,
        1,
    )
elif "const savedProfile = await saveStudentProfile(profile);" not in profile:
    raise RuntimeError(
        "Não encontrei a função save do ProfilePanel."
    )

old_header = '''<div><h1>Meu perfil</h1><p>Complete seus dados para o acompanhamento</p></div></div><button className="btn-ghost" onClick={onClose}>Voltar</button></header>'''

new_header = '''<div><h1>{onboarding ? "Complete seu cadastro" : "Meu perfil"}</h1><p>{onboarding ? "Preencha os dados essenciais para liberar seu acesso ao RunCore" : "Complete seus dados para o acompanhamento"}</p></div></div>{!onboarding && <button className="btn-ghost" onClick={onClose}>Voltar</button>}</header>'''

if old_header in profile:
    profile = profile.replace(
        old_header,
        new_header,
        1,
    )
elif 'onboarding ? "Complete seu cadastro"' not in profile:
    raise RuntimeError(
        "Não encontrei o cabeçalho do ProfilePanel."
    )

PROFILE.write_text(
    profile,
    encoding="utf-8",
    newline="\n",
)


# ------------------------------------------------------------------
# App: consulta antes de liberar as rotas do aluno
# ------------------------------------------------------------------
app = APP.read_text(encoding="utf-8")

old_api_import = '''  approveInvitation,
} from "./api";'''

new_api_import = '''  approveInvitation,
  getStudentProfile,
} from "./api";'''

if old_api_import in app:
    app = app.replace(
        old_api_import,
        new_api_import,
        1,
    )
elif "getStudentProfile," not in app:
    raise RuntimeError(
        "Não encontrei o import da API em App.jsx."
    )

old_component_import = '''import StudentPortal from "./StudentPortal";
'''

new_component_import = '''import StudentPortal from "./StudentPortal";
import ProfilePanel from "./ProfilePanel";
'''

if old_component_import in app and new_component_import not in app:
    app = app.replace(
        old_component_import,
        new_component_import,
        1,
    )

state_anchor = '''  const [quickAction, setQuickAction] = useState(null);
'''

state_block = '''  const [quickAction, setQuickAction] = useState(null);
  const [studentProfileStatus, setStudentProfileStatus] = useState(null);
  const [studentProfileLoading, setStudentProfileLoading] = useState(false);
'''

if state_block not in app:
    if state_anchor not in app:
        raise RuntimeError(
            "Não encontrei o bloco de estados em App.jsx."
        )

    app = app.replace(
        state_anchor,
        state_block,
        1,
    )

effect_anchor = '''  useEffect(() => {
    if (["coach", "master"].includes(currentUser?.role)) { loadAthletes(""); loadInvitations(); }
  }, [currentUser]);
'''

effect_block = '''  useEffect(() => {
    if (["coach", "master"].includes(currentUser?.role)) { loadAthletes(""); loadInvitations(); }
  }, [currentUser]);

  useEffect(() => {
    let active = true;

    if (currentUser?.role !== "student") {
      setStudentProfileStatus(null);
      setStudentProfileLoading(false);
      return undefined;
    }

    setStudentProfileLoading(true);

    getStudentProfile()
      .then((profile) => {
        if (active) {
          setStudentProfileStatus(profile);
        }
      })
      .catch((err) => {
        if (active) {
          setError(err.message);
          setStudentProfileStatus({
            complete: false,
            missing_fields: [],
          });
        }
      })
      .finally(() => {
        if (active) {
          setStudentProfileLoading(false);
        }
      });

    return () => {
      active = false;
    };
  }, [currentUser]);
'''

if effect_block not in app:
    if effect_anchor not in app:
        raise RuntimeError(
            "Não encontrei o efeito de carregamento por usuário."
        )

    app = app.replace(
        effect_anchor,
        effect_block,
        1,
    )

student_anchor = '''  if (currentUser.role === "student") {
    const studentLogout = () => {
      clearSession();
      setCurrentUser(null);
    };

    return (
'''

student_block = '''  if (currentUser.role === "student") {
    const studentLogout = () => {
      clearSession();
      setCurrentUser(null);
      setStudentProfileStatus(null);
    };

    if (studentProfileLoading || studentProfileStatus === null) {
      return (
        <main
          className="app-bootstrap-loading"
          aria-label="Verificando cadastro"
        >
          <section className="app-bootstrap-loading-card">
            <img
              src="/logo-horizontal.png?v=2"
              alt="RunCore"
            />
            <span
              className="app-bootstrap-spinner"
              aria-hidden="true"
            />
            <p>Verificando seu cadastro...</p>
          </section>
        </main>
      );
    }

    if (!studentProfileStatus.complete) {
      return (
        <AppShell
          user={currentUser}
          onLogout={studentLogout}
        >
          <ProfilePanel
            onboarding
            onSaved={(savedProfile) => {
              setStudentProfileStatus(savedProfile);

              if (savedProfile.complete) {
                navigate(
                  studentPaths.dashboard,
                  { replace: true },
                );
              }
            }}
          />
        </AppShell>
      );
    }

    return (
'''

if student_block not in app:
    if student_anchor not in app:
        raise RuntimeError(
            "Não encontrei o bloco de rotas do aluno."
        )

    app = app.replace(
        student_anchor,
        student_block,
        1,
    )

APP.write_text(
    app,
    encoding="utf-8",
    newline="\n",
)


compile_result = subprocess.run(
    [
        "python",
        "-m",
        "py_compile",
        str(BACKEND),
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


print("\nEtapa 66 concluída.")
print(
    "Alunos com cadastro incompleto serão direcionados "
    "obrigatoriamente para Complete seu cadastro."
)
print("\nExecute:")
print(
    "git add frontend/src/App.jsx "
    "frontend/src/ProfilePanel.jsx "
    "src/api/routers/profiles.py"
)
print(
    'git commit -m "feat: exige conclusao do cadastro no primeiro acesso"'
)
print("git push origin main")
