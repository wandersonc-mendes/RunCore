from pathlib import Path
import re
import subprocess

ROOT = Path.cwd()
PORTAL = ROOT / "frontend/src/StudentPortal.jsx"
CSS = ROOT / "frontend/src/App.css"

if not (ROOT / ".git").exists():
    raise RuntimeError("Execute este arquivo na raiz do RunCore.")
for path in (PORTAL, CSS):
    if not path.exists():
        raise RuntimeError(f"Não encontrei {path}.")

branch = subprocess.check_output(
    ["git", "branch", "--show-current"], cwd=ROOT, text=True
).strip()
if branch != "main":
    raise RuntimeError(f"Branch atual: {branch}. Troque para main.")

portal = PORTAL.read_text(encoding="utf-8")

helper = r'''
function localDateKey(value) {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function dateFromKey(value) {
  if (!value) return null;
  const date = new Date(`${value}T12:00:00`);
  return Number.isNaN(date.getTime()) ? null : date;
}

function StudentTrainingDonut({ completed, proposed, extra }) {
  const total = completed + proposed + extra;
  const completedEnd = total ? completed / total * 100 : 0;
  const proposedEnd = total ? completedEnd + proposed / total * 100 : 0;

  return (
    <div className="student-training-donut-wrap">
      <div
        className="student-training-donut"
        style={{
          background: total
            ? `conic-gradient(#19865f 0 ${completedEnd}%, #1598c8 ${completedEnd}% ${proposedEnd}%, #f29a1f ${proposedEnd}% 100%)`
            : "conic-gradient(#dfe7e3 0 100%)",
        }}
      >
        <div><strong>{total}</strong><span>treinos no mês</span></div>
      </div>
      <div className="student-training-donut-legend">
        <span className="completed"><i />Feitos<strong>{completed}</strong></span>
        <span className="proposed"><i />Propostos<strong>{proposed}</strong></span>
        <span className="extra"><i />Feitos avulsos<strong>{extra}</strong></span>
      </div>
    </div>
  );
}
'''

if "function StudentTrainingDonut(" not in portal:
    marker = "export default function StudentPortal"
    if marker not in portal:
        raise RuntimeError("Não encontrei o componente StudentPortal.")
    portal = portal.replace(marker, helper + "\n\n" + marker, 1)

summary_code = r'''
  const dashboardSummary = (() => {
    const now = new Date();
    const thirtyDaysAgo = new Date(now);
    thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);
    const currentMonth = now.getMonth();
    const currentYear = now.getFullYear();

    const monthRuns = runs.filter((activity) => {
      const date = new Date(activity.start_at);
      return !Number.isNaN(date.getTime())
        && date.getMonth() === currentMonth
        && date.getFullYear() === currentYear;
    });

    const recentDistance = runs.reduce((total, activity) => {
      const date = new Date(activity.start_at);
      return !Number.isNaN(date.getTime()) && date >= thirtyDaysAgo && date <= now
        ? total + Number(activity.distance || 0)
        : total;
    }, 0);

    const monthSessions = (training?.sessions || []).filter((session) => {
      const date = dateFromKey(session.session_date);
      return date && date.getMonth() === currentMonth && date.getFullYear() === currentYear;
    });

    const activityDates = new Set(monthRuns.map((activity) => localDateKey(activity.start_at)));
    const plannedDates = new Set(monthSessions.map((session) => session.session_date).filter(Boolean));
    const completed = monthSessions.filter((session) => activityDates.has(session.session_date)).length;
    const proposed = monthSessions.filter((session) => !activityDates.has(session.session_date)).length;
    const extra = monthRuns.filter((activity) => !plannedDates.has(localDateKey(activity.start_at))).length;

    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const upcomingGoals = [...goals]
      .filter((goal) => {
        const date = dateFromKey(goal.target_date);
        return date && date >= today;
      })
      .sort((a, b) => a.target_date.localeCompare(b.target_date))
      .slice(0, 3);

    return { recentDistance, completed, proposed, extra, upcomingGoals };
  })();
'''

if "const dashboardSummary = (() =>" not in portal:
    start = portal.find("  const predictedTime =")
    insert_at = portal.find("  useEffect(() => {", start)
    if start == -1 or insert_at == -1:
        raise RuntimeError("Não encontrei o ponto dos cálculos da dashboard.")
    portal = portal[:insert_at] + summary_code + "\n" + portal[insert_at:]

markup = r'''
        {view === "dashboard" && (
          <>
            <section className="student-dashboard-hero">
              <div>
                <p className="eyebrow">VISÃO GERAL</p>
                <h2>Olá, {user.name}.</h2>
                <p>Acompanhe sua semana de treino, suas atividades e sua evolução em um único lugar.</p>
              </div>
              <div className="student-dashboard-hero-brand">
                <span>RUNCORE</span>
                <strong>Seu treinamento em movimento</strong>
              </div>
            </section>

            <section className="student-dashboard-overview">
              <div className="student-dashboard-overview-main">
                <article className="student-month-distance-card">
                  <div className="student-dashboard-icon">KM</div>
                  <div>
                    <span>Quilometragem recente</span>
                    <strong>{dashboardSummary.recentDistance.toLocaleString("pt-BR", { minimumFractionDigits: 1, maximumFractionDigits: 1 })} km</strong>
                    <small>percorridos nos últimos 30 dias</small>
                  </div>
                </article>

                <article className="student-race-calendar-card">
                  <header>
                    <div><span>Calendário pessoal</span><h3>Próximas provas</h3></div>
                    <button type="button" className="btn-ghost" onClick={() => document.getElementById("metas")?.scrollIntoView({ behavior: "smooth", block: "start" })}>Gerenciar</button>
                  </header>
                  {dashboardSummary.upcomingGoals.length ? (
                    <div className="student-race-calendar-list">
                      {dashboardSummary.upcomingGoals.map((goal) => {
                        const raceDate = dateFromKey(goal.target_date);
                        return (
                          <article key={goal.id}>
                            <time><strong>{String(raceDate.getDate()).padStart(2, "0")}</strong><span>{new Intl.DateTimeFormat("pt-BR", { month: "short" }).format(raceDate)}</span></time>
                            <div><strong>{goal.name}</strong><span>{Number(goal.distance).toLocaleString("pt-BR", { maximumFractionDigits: 2 })} km · {goal.priority}</span></div>
                          </article>
                        );
                      })}
                    </div>
                  ) : <p className="muted">Nenhuma prova futura cadastrada.</p>}
                </article>
              </div>

              <article className="student-training-status-card">
                <header><div><span>Situação dos treinos</span><h3>Mês atual</h3></div></header>
                <StudentTrainingDonut completed={dashboardSummary.completed} proposed={dashboardSummary.proposed} extra={dashboardSummary.extra} />
              </article>
            </section>
          </>
        )}
'''

if "student-dashboard-overview" not in portal:
    start_marker = '{view === "dashboard" && ('
    start = portal.find(start_marker)
    if start == -1:
        raise RuntimeError("Não encontrei o painel inicial do aluno.")
    end = portal.find("        )}", start)
    if end == -1:
        raise RuntimeError("Não encontrei o final do painel inicial do aluno.")
    end += len("        )}")
    portal = portal[:start] + markup.strip("\n") + portal[end:]

PORTAL.write_text(portal, encoding="utf-8", newline="\n")

css = CSS.read_text(encoding="utf-8")
marker = "/* RUNCORE STUDENT DASHBOARD OVERVIEW */"
if marker in css:
    css = css.split(marker)[0].rstrip()

css += r'''

/* RUNCORE STUDENT DASHBOARD OVERVIEW */
.student-dashboard-overview { display:grid; grid-template-columns:minmax(0,1.35fr) minmax(300px,.65fr); gap:18px; }
.student-dashboard-overview-main { display:grid; grid-template-columns:minmax(220px,.75fr) minmax(0,1.25fr); gap:18px; }
.student-month-distance-card,.student-race-calendar-card,.student-training-status-card { border:1px solid var(--line); border-radius:18px; background:var(--surface); box-shadow:0 10px 28px rgb(18 57 49 / .06); }
.student-month-distance-card { display:grid; align-content:center; justify-items:start; gap:20px; min-height:250px; padding:24px; background:radial-gradient(circle at 85% 15%,rgb(24 134 95 / .13),transparent 38%),var(--surface); }
.student-dashboard-icon { display:grid; place-items:center; width:48px; height:48px; border-radius:15px; background:#e2f3ee; color:var(--accent); font-size:14px; font-weight:800; }
.student-month-distance-card>div:last-child { display:grid; gap:6px; }
.student-month-distance-card span,.student-race-calendar-card header span,.student-training-status-card header span { color:var(--muted); font-size:12px; font-weight:700; }
.student-month-distance-card strong { color:var(--ink); font-size:clamp(30px,4vw,44px); line-height:1; }
.student-month-distance-card small { color:var(--muted); line-height:1.45; }
.student-race-calendar-card,.student-training-status-card { padding:22px; }
.student-race-calendar-card>header,.student-training-status-card>header { display:flex; align-items:flex-start; justify-content:space-between; gap:14px; margin-bottom:18px; }
.student-race-calendar-card h3,.student-training-status-card h3 { margin:4px 0 0; font-size:20px; }
.student-race-calendar-list { display:grid; }
.student-race-calendar-list>article { display:grid; grid-template-columns:52px minmax(0,1fr); align-items:center; gap:13px; padding:12px 0; border-top:1px solid var(--line); }
.student-race-calendar-list time { display:grid; place-items:center; min-height:52px; border-radius:12px; background:#eef8f5; color:var(--accent-dark); text-transform:uppercase; }
.student-race-calendar-list time strong { font-size:19px; line-height:1; }
.student-race-calendar-list time span { margin-top:3px; font-size:10px; font-weight:800; }
.student-race-calendar-list article>div { display:grid; gap:4px; }
.student-race-calendar-list article>div>strong { font-size:13px; }
.student-race-calendar-list article>div>span { color:var(--muted); font-size:11px; }
.student-training-donut-wrap { display:grid; justify-items:center; gap:22px; }
.student-training-donut { display:grid; place-items:center; width:min(210px,70vw); aspect-ratio:1; border-radius:50%; }
.student-training-donut>div { display:grid; place-items:center; width:61%; aspect-ratio:1; border-radius:50%; background:var(--surface); box-shadow:0 4px 18px rgb(18 57 49 / .08); text-align:center; }
.student-training-donut strong { font-size:30px; line-height:1; }
.student-training-donut span { width:80px; margin-top:5px; color:var(--muted); font-size:10px; line-height:1.3; }
.student-training-donut-legend { display:grid; width:100%; gap:9px; }
.student-training-donut-legend>span { display:grid; grid-template-columns:10px minmax(0,1fr) auto; align-items:center; gap:8px; color:var(--muted); font-size:12px; }
.student-training-donut-legend i { width:10px; height:10px; border-radius:50%; }
.student-training-donut-legend .completed i { background:#19865f; }
.student-training-donut-legend .proposed i { background:#1598c8; }
.student-training-donut-legend .extra i { background:#f29a1f; }
.student-training-donut-legend strong { color:var(--ink); }
@media (max-width:940px) { .student-dashboard-overview { grid-template-columns:1fr; } .student-training-donut-wrap { grid-template-columns:auto minmax(180px,1fr); align-items:center; } }
@media (max-width:680px) { .student-dashboard-overview-main { grid-template-columns:1fr; } .student-month-distance-card { min-height:190px; } .student-training-donut-wrap { grid-template-columns:1fr; } }
'''

CSS.write_text(css, encoding="utf-8", newline="\n")

result = subprocess.run(["npm.cmd", "run", "build"], cwd=ROOT / "frontend")
if result.returncode:
    raise SystemExit(result.returncode)

print("\nEtapa 37B concluída.")
print("Dashboard inicial do aluno ampliada.")
print("\nExecute:")
print("git add frontend/src/StudentPortal.jsx frontend/src/App.css")
print('git commit -m "feat: amplia dashboard inicial do aluno"')
print("git push origin main")
