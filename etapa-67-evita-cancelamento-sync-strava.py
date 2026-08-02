from pathlib import Path
import subprocess

ROOT = Path.cwd()
API = ROOT / "frontend/src/api.js"
PORTAL = ROOT / "frontend/src/StudentPortal.jsx"
FRONTEND = ROOT / "frontend"

if not (ROOT / ".git").exists():
    raise RuntimeError("Execute este arquivo na raiz do RunCore.")

for required in (API, PORTAL):
    if not required.exists():
        raise RuntimeError(f"Arquivo não encontrado: {required}")

branch = subprocess.check_output(
    ["git", "branch", "--show-current"],
    cwd=ROOT,
    text=True,
).strip()

if branch != "main":
    raise RuntimeError(f"Branch atual: {branch}. Troque para main.")

api = API.read_text(encoding="utf-8")

old_sync = '''export function syncStravaActivities() {
  return request(
    "/api/integrations/strava/sync",
    {
      method: "POST",
    },
  );
}
'''

new_sync = '''export function syncStravaActivities() {
  return request(
    "/api/integrations/strava/sync",
    {
      method: "POST",
      timeout: 60000,
    },
  );
}
'''

if old_sync in api:
    api = api.replace(old_sync, new_sync, 1)
elif "timeout: 60000" not in api:
    raise RuntimeError(
        "Não encontrei syncStravaActivities no formato esperado."
    )

API.write_text(api, encoding="utf-8", newline="\n")

portal = PORTAL.read_text(encoding="utf-8")

old_effect = '''  useEffect(() => {
    function loadStatus() {
      getStravaStatus()
        .then((status) => {
          setStrava(status);
          if (status.connected) listStravaActivities().then(setActivities).catch(() => {});
        })
        .catch((err) => setError(err.message));
      getStudentTraining().then(setTraining).catch(() => {});
      listGoals().then(setGoals).catch(() => {});
    }

    loadStatus();
    const interval = window.setInterval(loadStatus, 10000);
    window.addEventListener("focus", loadStatus);
    return () => {
      window.clearInterval(interval);
      window.removeEventListener("focus", loadStatus);
    };
  }, []);
'''

new_effect = '''  useEffect(() => {
    if (syncing) {
      return undefined;
    }

    function loadStatus() {
      getStravaStatus()
        .then((status) => {
          setStrava(status);

          if (status.connected) {
            listStravaActivities()
              .then(setActivities)
              .catch(() => {});
          }
        })
        .catch((err) => setError(err.message));

      getStudentTraining()
        .then(setTraining)
        .catch(() => {});

      listGoals()
        .then(setGoals)
        .catch(() => {});
    }

    loadStatus();

    const interval = window.setInterval(
      loadStatus,
      10000,
    );

    window.addEventListener(
      "focus",
      loadStatus,
    );

    return () => {
      window.clearInterval(interval);
      window.removeEventListener(
        "focus",
        loadStatus,
      );
    };
  }, [syncing]);
'''

if old_effect in portal:
    portal = portal.replace(old_effect, new_effect, 1)
elif "  }, [syncing]);" not in portal:
    raise RuntimeError(
        "Não encontrei o polling do portal no formato esperado."
    )

old_sync_function = '''  async function sync() {
    setSyncing(true);
    setError("");
    try {
      const result = await syncStravaActivities();
      setActivities(result.activities);
      setActivityDetails({});
    } catch (err) {
      setError(err.message);
    } finally {
      setSyncing(false);
    }
  }
'''

new_sync_function = '''  async function sync() {
    if (syncing) {
      return;
    }

    setSyncing(true);
    setError("");

    try {
      const result = await syncStravaActivities();
      setActivities(result.activities);
      setActivityDetails({});
    } catch (err) {
      setError(err.message);
    } finally {
      setSyncing(false);
    }
  }
'''

if old_sync_function in portal:
    portal = portal.replace(old_sync_function, new_sync_function, 1)
elif "    if (syncing) {" not in portal:
    raise RuntimeError(
        "Não encontrei a função sync no formato esperado."
    )

PORTAL.write_text(portal, encoding="utf-8", newline="\n")

build = subprocess.run(
    ["npm.cmd", "run", "build"],
    cwd=FRONTEND,
)

if build.returncode:
    raise SystemExit(build.returncode)

print("\nEtapa 67 concluída.")
print(
    "A sincronização do Strava agora possui timeout de 60 segundos "
    "e suspende o polling durante o processamento."
)
print("\nExecute:")
print("git add frontend/src/api.js frontend/src/StudentPortal.jsx")
print('git commit -m "fix: evita cancelamento da sincronizacao do strava"')
print("git push origin main")
