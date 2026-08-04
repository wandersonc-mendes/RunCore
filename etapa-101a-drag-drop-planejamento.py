from pathlib import Path
import subprocess

ROOT = Path.cwd()
PAGE = ROOT / "frontend/src/pages/PlanningPage.jsx"
CSS = ROOT / "frontend/src/pages/PlanningPage.css"
ROUTER = ROOT / "src/api/routers/trainings.py"
FRONTEND = ROOT / "frontend"

if not (ROOT / ".git").exists():
    raise RuntimeError("Execute este arquivo na raiz do RunCore.")

for path in (PAGE, CSS, ROUTER):
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

PAGE.write_text(
    'import { useEffect, useMemo, useState } from "react";\n\nimport {\n  getTraining,\n  updateTrainingSession,\n} from "../api";\nimport { formatWorkoutSummary } from "../utils/workoutSummary";\n\nimport "./PlanningPage.css";\n\n\nconst WEEKDAYS = [\n  "Seg",\n  "Ter",\n  "Qua",\n  "Qui",\n  "Sex",\n  "Sáb",\n  "Dom",\n];\n\n\nfunction startOfWeek(date) {\n  const result = new Date(date);\n  const weekday = result.getDay();\n  const offset = weekday === 0 ? -6 : 1 - weekday;\n\n  result.setDate(result.getDate() + offset);\n  result.setHours(0, 0, 0, 0);\n\n  return result;\n}\n\n\nfunction addDays(date, amount) {\n  const result = new Date(date);\n  result.setDate(result.getDate() + amount);\n  return result;\n}\n\n\nfunction dateKey(date) {\n  const year = date.getFullYear();\n  const month = String(date.getMonth() + 1).padStart(2, "0");\n  const day = String(date.getDate()).padStart(2, "0");\n\n  return `${year}-${month}-${day}`;\n}\n\n\nfunction formatDay(date) {\n  return new Intl.DateTimeFormat("pt-BR", {\n    day: "2-digit",\n    month: "2-digit",\n  }).format(date);\n}\n\n\nfunction formatWeekRange(days) {\n  const first = days[0];\n  const last = days[6];\n\n  const start = new Intl.DateTimeFormat("pt-BR", {\n    day: "2-digit",\n    month: "short",\n  }).format(first);\n\n  const end = new Intl.DateTimeFormat("pt-BR", {\n    day: "2-digit",\n    month: "short",\n    year: "numeric",\n  }).format(last);\n\n  return `${start} - ${end}`;\n}\n\n\nfunction initials(name = "") {\n  return name\n    .split(" ")\n    .filter(Boolean)\n    .slice(0, 2)\n    .map((part) => part[0]?.toUpperCase())\n    .join("") || "RC";\n}\n\n\nfunction sessionTone(session) {\n  const value = [\n    session?.workout_name,\n    session?.zone,\n  ]\n    .filter(Boolean)\n    .join(" ")\n    .toLowerCase();\n\n  if (\n    value.includes("long")\n    || value.includes("longo")\n    || value.includes("longão")\n  ) {\n    return "long";\n  }\n\n  if (\n    value.includes("interval")\n    || value.includes("tiro")\n    || value.includes("repetition")\n  ) {\n    return "interval";\n  }\n\n  if (\n    value.includes("tempo")\n    || value.includes("limiar")\n    || value.includes("threshold")\n  ) {\n    return "tempo";\n  }\n\n  if (value.includes("progress")) {\n    return "progressive";\n  }\n\n  if (\n    value.includes("regener")\n    || value.includes("recuper")\n  ) {\n    return "recovery";\n  }\n\n  return "easy";\n}\n\n\nfunction stepPayload(step) {\n  return {\n    type: step.type || "Corrida",\n    prescription_type: step.prescription_type || "distance",\n    intensity_type: step.intensity_type || "pace",\n    distance: Number(step.distance || 0),\n    distance_unit: step.distance_unit || "km",\n    duration: Number(step.duration || 0),\n    repetitions: Number(step.repetitions || 0),\n    recovery: step.recovery || "",\n    pace_min: step.pace_min || "",\n    pace_max: step.pace_max || "",\n    heart_rate_min: step.heart_rate_min || null,\n    heart_rate_max: step.heart_rate_max || null,\n    rpe_min: step.rpe_min || null,\n    rpe_max: step.rpe_max || null,\n    notes: step.notes || "",\n  };\n}\n\n\nfunction sessionPayload(session, sessionDate) {\n  return {\n    session_date: sessionDate,\n    workout_name: session.workout_name,\n    zone: session.zone || "Easy",\n    planned_distance: Number(session.planned_distance || 0),\n    repetitions: Number(session.repetitions || 0),\n    objective: session.objective || "",\n    notes: session.notes || "",\n    steps: (session.steps || []).map(stepPayload),\n  };\n}\n\n\nexport default function PlanningPage({\n  athletes,\n  loading,\n  error,\n  onOpenPlanning,\n}) {\n  const [weekStart, setWeekStart] = useState(\n    () => startOfWeek(new Date()),\n  );\n  const [records, setRecords] = useState([]);\n  const [loadingTrainings, setLoadingTrainings] = useState(true);\n  const [athleteFilter, setAthleteFilter] = useState("all");\n  const [goalFilter, setGoalFilter] = useState("all");\n  const [draggingSessionId, setDraggingSessionId] = useState(null);\n  const [dropTarget, setDropTarget] = useState("");\n  const [movingSessionId, setMovingSessionId] = useState(null);\n  const [moveError, setMoveError] = useState("");\n\n  useEffect(() => {\n    let active = true;\n\n    async function loadTrainings() {\n      setLoadingTrainings(true);\n\n      const results = await Promise.allSettled(\n        athletes.map(async (athlete) => ({\n          athlete,\n          training: await getTraining(athlete.id),\n        })),\n      );\n\n      if (!active) {\n        return;\n      }\n\n      setRecords(\n        results\n          .filter((result) => result.status === "fulfilled")\n          .map((result) => result.value),\n      );\n\n      setLoadingTrainings(false);\n    }\n\n    loadTrainings();\n\n    return () => {\n      active = false;\n    };\n  }, [athletes]);\n\n  const weekDays = useMemo(\n    () => Array.from(\n      { length: 7 },\n      (_, index) => addDays(weekStart, index),\n    ),\n    [weekStart],\n  );\n\n  const goals = useMemo(\n    () => Array.from(\n      new Set(\n        athletes\n          .map((athlete) => athlete.goal?.trim())\n          .filter(Boolean),\n      ),\n    ).sort((first, second) =>\n      first.localeCompare(second, "pt-BR"),\n    ),\n    [athletes],\n  );\n\n  const visibleRecords = useMemo(\n    () => records.filter(({ athlete }) => {\n      const matchesAthlete =\n        athleteFilter === "all"\n        || String(athlete.id) === athleteFilter;\n\n      const matchesGoal =\n        goalFilter === "all"\n        || athlete.goal === goalFilter;\n\n      return athlete.active && matchesAthlete && matchesGoal;\n    }),\n    [\n      athleteFilter,\n      goalFilter,\n      records,\n    ],\n  );\n\n  const sessionsByAthleteAndDate = useMemo(() => {\n    const result = new Map();\n\n    visibleRecords.forEach(({ athlete, training }) => {\n      const byDate = new Map();\n\n      (training?.sessions || []).forEach((session) => {\n        if (!session.session_date) {\n          return;\n        }\n\n        const sessions = byDate.get(session.session_date) || [];\n        sessions.push(session);\n        byDate.set(session.session_date, sessions);\n      });\n\n      result.set(athlete.id, byDate);\n    });\n\n    return result;\n  }, [visibleRecords]);\n\n  function updateSessionDateLocally(\n    athleteId,\n    sessionId,\n    nextDate,\n  ) {\n    setRecords((current) =>\n      current.map((record) => {\n        if (record.athlete.id !== athleteId) {\n          return record;\n        }\n\n        return {\n          ...record,\n          training: {\n            ...record.training,\n            sessions: (record.training?.sessions || []).map(\n              (session) =>\n                session.id === sessionId\n                  ? {\n                      ...session,\n                      session_date: nextDate,\n                      weekday: new Date(\n                        `${nextDate}T12:00:00`,\n                      ).getDay() === 0\n                        ? 6\n                        : new Date(\n                            `${nextDate}T12:00:00`,\n                          ).getDay() - 1,\n                    }\n                  : session,\n            ),\n          },\n        };\n      }),\n    );\n  }\n\n  async function moveSession(\n    athlete,\n    session,\n    nextDate,\n  ) {\n    if (\n      movingSessionId\n      || !session\n      || session.session_date === nextDate\n    ) {\n      return;\n    }\n\n    const previousDate = session.session_date;\n\n    setMoveError("");\n    setMovingSessionId(session.id);\n    updateSessionDateLocally(\n      athlete.id,\n      session.id,\n      nextDate,\n    );\n\n    try {\n      await updateTrainingSession(\n        athlete.id,\n        session.id,\n        sessionPayload(session, nextDate),\n      );\n    } catch (moveFailure) {\n      updateSessionDateLocally(\n        athlete.id,\n        session.id,\n        previousDate,\n      );\n      setMoveError(\n        moveFailure.message\n        || "Não foi possível mover o treino.",\n      );\n    } finally {\n      setMovingSessionId(null);\n      setDraggingSessionId(null);\n      setDropTarget("");\n    }\n  }\n\n  const isLoading = loading || loadingTrainings;\n\n  return (\n    <section className="planning-page planning-week-page">\n      <header className="planning-week-header">\n        <div>\n          <p className="eyebrow">PLANEJAMENTO</p>\n          <h2>Planejamento semanal</h2>\n          <p className="muted">\n            Arraste um treino para outro dia para\n            reorganizar a semana do atleta.\n          </p>\n        </div>\n\n        <div className="planning-week-counter">\n          <strong>{visibleRecords.length}</strong>\n          <span>atletas exibidos</span>\n        </div>\n      </header>\n\n      {(error || moveError) && (\n        <div className="alert">\n          {moveError || error}\n        </div>\n      )}\n\n      <section className="planning-week-toolbar">\n        <div className="week-navigation">\n          <button\n            type="button"\n            aria-label="Semana anterior"\n            onClick={() =>\n              setWeekStart((current) => addDays(current, -7))\n            }\n          >\n            ‹\n          </button>\n\n          <button\n            type="button"\n            className="today-button"\n            onClick={() =>\n              setWeekStart(startOfWeek(new Date()))\n            }\n          >\n            Hoje\n          </button>\n\n          <button\n            type="button"\n            aria-label="Próxima semana"\n            onClick={() =>\n              setWeekStart((current) => addDays(current, 7))\n            }\n          >\n            ›\n          </button>\n\n          <strong>{formatWeekRange(weekDays)}</strong>\n        </div>\n\n        <div className="planning-week-filters">\n          <label>\n            <span>Objetivo</span>\n            <select\n              value={goalFilter}\n              onChange={(event) =>\n                setGoalFilter(event.target.value)\n              }\n            >\n              <option value="all">Todos</option>\n              {goals.map((goal) => (\n                <option value={goal} key={goal}>\n                  {goal}\n                </option>\n              ))}\n            </select>\n          </label>\n\n          <label>\n            <span>Atleta</span>\n            <select\n              value={athleteFilter}\n              onChange={(event) =>\n                setAthleteFilter(event.target.value)\n              }\n            >\n              <option value="all">Todos</option>\n              {athletes\n                .filter((athlete) => athlete.active)\n                .map((athlete) => (\n                  <option\n                    key={athlete.id}\n                    value={athlete.id}\n                  >\n                    {athlete.name}\n                  </option>\n                ))}\n            </select>\n          </label>\n        </div>\n      </section>\n\n      {isLoading ? (\n        <section className="planning-empty">\n          <h3>Carregando semana</h3>\n          <p>Buscando os planejamentos dos atletas.</p>\n        </section>\n      ) : visibleRecords.length === 0 ? (\n        <section className="planning-empty">\n          <h3>Nenhum atleta encontrado</h3>\n          <p>\n            Ajuste os filtros para visualizar\n            outros planejamentos.\n          </p>\n        </section>\n      ) : (\n        <div className="planning-week-scroll">\n          <div className="planning-week-grid">\n            <div className="planning-grid-corner">\n              Atleta\n            </div>\n\n            {weekDays.map((day, index) => (\n              <div\n                className="planning-day-heading"\n                key={dateKey(day)}\n              >\n                <strong>{WEEKDAYS[index]}</strong>\n                <span>{formatDay(day)}</span>\n              </div>\n            ))}\n\n            {visibleRecords.map(({ athlete, training }) => {\n              const athleteSessions =\n                sessionsByAthleteAndDate.get(athlete.id)\n                || new Map();\n\n              return [\n                <button\n                  type="button"\n                  className="planning-athlete-cell"\n                  key={`athlete-${athlete.id}`}\n                  onClick={() => onOpenPlanning(athlete)}\n                >\n                  <span className="planning-avatar">\n                    {initials(athlete.name)}\n                  </span>\n\n                  <span>\n                    <strong>{athlete.name}</strong>\n                    <small>\n                      {training?.objective\n                        || athlete.goal\n                        || "Sem objetivo"}\n                    </small>\n                  </span>\n                </button>,\n\n                ...weekDays.map((day) => {\n                  const key = dateKey(day);\n                  const sessions = athleteSessions.get(key) || [];\n                  const targetKey = `${athlete.id}-${key}`;\n                  const isTarget = dropTarget === targetKey;\n\n                  return (\n                    <div\n                      className={\n                        `planning-session-cell planning-drop-cell ${\n                          sessions.length ? "has-sessions" : "empty"\n                        } ${isTarget ? "drop-target" : ""}`\n                      }\n                      key={targetKey}\n                      onDragOver={(event) => {\n                        event.preventDefault();\n                        event.dataTransfer.dropEffect = "move";\n                        setDropTarget(targetKey);\n                      }}\n                      onDragLeave={(event) => {\n                        if (\n                          !event.currentTarget.contains(\n                            event.relatedTarget,\n                          )\n                        ) {\n                          setDropTarget("");\n                        }\n                      }}\n                      onDrop={(event) => {\n                        event.preventDefault();\n\n                        const sessionId = Number(\n                          event.dataTransfer.getData(\n                            "application/x-runcore-session",\n                          ) || draggingSessionId,\n                        );\n\n                        const session = (\n                          training?.sessions || []\n                        ).find(\n                          (item) => item.id === sessionId,\n                        );\n\n                        moveSession(\n                          athlete,\n                          session,\n                          key,\n                        );\n                      }}\n                    >\n                      {sessions.map((session) => (\n                        <button\n                          type="button"\n                          draggable={!movingSessionId}\n                          className={\n                            `planning-session-card ${sessionTone(session)} ${\n                              draggingSessionId === session.id\n                                ? "is-dragging"\n                                : ""\n                            } ${\n                              movingSessionId === session.id\n                                ? "is-saving"\n                                : ""\n                            }`\n                          }\n                          key={session.id}\n                          onDragStart={(event) => {\n                            setDraggingSessionId(session.id);\n                            event.dataTransfer.effectAllowed = "move";\n                            event.dataTransfer.setData(\n                              "application/x-runcore-session",\n                              String(session.id),\n                            );\n                            event.dataTransfer.setData(\n                              "text/plain",\n                              String(session.id),\n                            );\n                          }}\n                          onDragEnd={() => {\n                            setDraggingSessionId(null);\n                            setDropTarget("");\n                          }}\n                          onClick={() => {\n                            if (!draggingSessionId) {\n                              onOpenPlanning(\n                                athlete,\n                                session,\n                              );\n                            }\n                          }}\n                        >\n                          <strong>{session.workout_name}</strong>\n                          <span>{formatWorkoutSummary(session)}</span>\n                          <small>{session.zone || "Treino"}</small>\n                        </button>\n                      ))}\n\n                      <button\n                        type="button"\n                        className="planning-add-session"\n                        onClick={() =>\n                          onOpenPlanning(athlete, null)\n                        }\n                      >\n                        <span className="empty-plus">＋</span>\n                        <small>Adicionar</small>\n                      </button>\n                    </div>\n                  );\n                }),\n              ];\n            })}\n          </div>\n        </div>\n      )}\n\n      <footer className="planning-week-legend">\n        <span><b className="easy" />Fácil</span>\n        <span><b className="interval" />Intervalado</span>\n        <span><b className="tempo" />Tempo/Limiar</span>\n        <span><b className="long" />Longo</span>\n        <span><b className="recovery" />Regenerativo</span>\n        <span><b className="progressive" />Progressivo</span>\n      </footer>\n    </section>\n  );\n}\n',
    encoding="utf-8",
    newline="\n",
)

css = CSS.read_text(encoding="utf-8")

marker = "/* ETAPA 101A: DRAG AND DROP */"

drag_css = r"""
/* ETAPA 101A: DRAG AND DROP */
.planning-drop-cell {
  align-content: start;
  display: grid;
  gap: 7px;
  min-height: 98px;
  padding: 7px;
  transition:
    background-color .16s ease,
    box-shadow .16s ease;
}

.planning-drop-cell.drop-target {
  background:
    color-mix(in srgb, var(--accent) 14%, var(--surface));
  box-shadow:
    inset 0 0 0 2px var(--accent);
}

.planning-session-card,
.planning-add-session {
  width: 100%;
  border: 0;
  text-align: left;
}

.planning-session-card {
  display: grid;
  gap: 4px;
  min-height: 82px;
  padding: 12px 11px;
  border-left: 3px solid currentColor;
  background: transparent;
  color: inherit;
  cursor: grab;
  transition:
    opacity .16s ease,
    transform .16s ease,
    box-shadow .16s ease;
}

.planning-session-card:hover {
  transform: translateY(-1px);
  box-shadow: 0 8px 20px rgb(0 0 0 / .12);
}

.planning-session-card:active {
  cursor: grabbing;
}

.planning-session-card.is-dragging {
  opacity: .38;
}

.planning-session-card.is-saving {
  cursor: progress;
  opacity: .58;
  pointer-events: none;
}

.planning-session-card strong,
.planning-session-card span,
.planning-session-card small {
  pointer-events: none;
}

.planning-session-card.easy {
  background: color-mix(in srgb, #2684ff 10%, var(--surface));
  border-left-color: #2684ff;
}

.planning-session-card.interval {
  background: color-mix(in srgb, #ff5d5d 11%, var(--surface));
  border-left-color: #ff5d5d;
}

.planning-session-card.tempo {
  background: color-mix(in srgb, #f4b400 11%, var(--surface));
  border-left-color: #f4b400;
}

.planning-session-card.long {
  background: color-mix(in srgb, #9566ff 11%, var(--surface));
  border-left-color: #9566ff;
}

.planning-session-card.recovery {
  background: color-mix(in srgb, #22c997 11%, var(--surface));
  border-left-color: #22c997;
}

.planning-session-card.progressive {
  background: color-mix(in srgb, #18b981 11%, var(--surface));
  border-left-color: #18b981;
}

.planning-add-session {
  display: grid;
  place-items: center;
  min-height: 34px;
  padding: 5px;
  background: transparent;
  color: var(--muted);
  cursor: pointer;
}

.planning-drop-cell.has-sessions .planning-add-session {
  min-height: 26px;
  opacity: .55;
}

.planning-drop-cell.has-sessions .planning-add-session:hover {
  opacity: 1;
}
"""

if marker not in css:
    CSS.write_text(
        css.rstrip() + "\n\n" + drag_css.strip() + "\n",
        encoding="utf-8",
        newline="\n",
    )

router = ROUTER.read_text(encoding="utf-8")

old = """    if payload.session_date:
        session.scheduled_date = payload.session_date
        session.weekday = payload.session_date.weekday()
"""

new = """    if payload.session_date:
        session.scheduled_date = payload.session_date
        session.weekday = payload.session_date.weekday()

        if training.start_date:
            day_offset = (
                payload.session_date
                - training.start_date
            ).days
            session.week = max(
                1,
                (day_offset // 7) + 1,
            )
"""

if old in router:
    router = router.replace(old, new, 1)
elif "day_offset = (" not in router[router.find("def update_session"):]:
    raise RuntimeError(
        "Não encontrei o bloco de data no endpoint de atualização."
    )

ROUTER.write_text(
    router,
    encoding="utf-8",
    newline="\n",
)

compile_result = subprocess.run(
    ["python", "-m", "py_compile", str(ROUTER)],
    cwd=ROOT,
)

if compile_result.returncode:
    raise SystemExit(compile_result.returncode)

build_result = subprocess.run(
    ["npm.cmd", "run", "build"],
    cwd=FRONTEND,
)

if build_result.returncode:
    raise SystemExit(build_result.returncode)

print("Etapa 101A concluída.")
print(
    "A grade agora permite mover treinos por "
    "arrastar e soltar."
)
print("\nExecute:")
print(
    "git add frontend/src/pages/PlanningPage.jsx "
    "frontend/src/pages/PlanningPage.css "
    "src/api/routers/trainings.py"
)
print(
    'git commit -m '
    '"feat: permite mover treinos no planejamento"'
)
print("git push origin main")
