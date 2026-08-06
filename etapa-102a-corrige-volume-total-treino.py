from pathlib import Path
import subprocess

ROOT = Path.cwd()
APP = ROOT / "frontend/src/App.jsx"
SUMMARY = ROOT / "frontend/src/utils/workoutSummary.js"
FRONTEND = ROOT / "frontend"

if not (ROOT / ".git").exists():
    raise RuntimeError("Execute este arquivo na raiz do RunCore.")

for path in (APP, SUMMARY):
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

summary = SUMMARY.read_text(encoding="utf-8")

old_step_distance = """export function stepDistanceInKm(step) {
  if (
    (step?.prescription_type || "distance")
    !== "distance"
  ) {
    return 0;
  }

  const distance = Number(step?.distance || 0);
  const repetitions = Math.max(Number(step?.repetitions || 0), 1);
  const unit = step?.distance_unit
    || (Number(step?.repetitions || 0) > 0 ? "m" : "km");

  return distance * repetitions * (unit === "m" ? 0.001 : 1);
}
"""

new_step_distance = """export function stepDistanceInKm(step) {
  if (
    (step?.prescription_type || "distance")
    !== "distance"
  ) {
    return 0;
  }

  const distance = Number(step?.distance || 0);

  if (!Number.isFinite(distance) || distance <= 0) {
    return 0;
  }

  const repetitionsValue = Number(
    step?.repetitions || 0,
  );
  const repetitions = repetitionsValue > 0
    ? repetitionsValue
    : 1;

  const unit = String(
    step?.distance_unit
    || (repetitionsValue > 0 ? "m" : "km"),
  ).trim().toLowerCase();

  const distanceInKm = unit === "m"
    ? distance / 1000
    : distance;

  return distanceInKm * repetitions;
}
"""

if old_step_distance in summary:
    summary = summary.replace(
        old_step_distance,
        new_step_distance,
        1,
    )
elif 'const distanceInKm = unit === "m"' not in summary:
    raise RuntimeError(
        "Não encontrei stepDistanceInKm no formato esperado."
    )

old_repeated_distance = """      return {
        label: `${repetitions} × ${
          distance.toLocaleString("pt-BR")
        } ${unit}`,
        plannedDistance: distance,
        plannedDuration: steps.reduce(
          (total, step) =>
            total + stepDurationInSeconds(step),
          0,
        ),
        repetitions,
      };
"""

new_repeated_distance = """      return {
        label: `${repetitions} × ${
          distance.toLocaleString("pt-BR")
        } ${unit}`,
        plannedDistance: steps.reduce(
          (total, step) =>
            total + stepDistanceInKm(step),
          0,
        ),
        plannedDuration: steps.reduce(
          (total, step) =>
            total + stepDurationInSeconds(step),
          0,
        ),
        repetitions,
      };
"""

if old_repeated_distance in summary:
    summary = summary.replace(
        old_repeated_distance,
        new_repeated_distance,
        1,
    )
elif "plannedDistance: distance," in summary:
    raise RuntimeError(
        "A referência incorreta plannedDistance: distance ainda existe."
    )

SUMMARY.write_text(
    summary,
    encoding="utf-8",
    newline="\n",
)

app = APP.read_text(encoding="utf-8")

old_import = """import {
  formatWorkoutSummary,
  workoutSummaryFromSteps,
} from "./utils/workoutSummary";
"""

new_import = """import {
  formatWorkoutSummary,
  stepDistanceInKm,
  workoutSummaryFromSteps,
} from "./utils/workoutSummary";
"""

if old_import in app:
    app = app.replace(old_import, new_import, 1)
elif "stepDistanceInKm," not in app:
    raise RuntimeError(
        "Não encontrei a importação de workoutSummary."
    )

old_local_function = """  function stepDistanceKm(step) {
    if (
      (step.prescription_type || "distance")
      !== "distance"
    ) {
      return 0;
    }

    const distance = Number(step.distance || 0);
    const repetitions = Math.max(
      Number(step.repetitions || 0),
      1,
    );
    const unit = step.distance_unit || (
      Number(step.repetitions || 0) > 0
        ? "m"
        : "km"
    );

    const total = distance * repetitions;

    return unit === "m"
      ? total / 1000
      : total;
  }
"""

new_local_function = """  function stepDistanceKm(step) {
    return stepDistanceInKm(step);
  }
"""

if old_local_function in app:
    app = app.replace(
        old_local_function,
        new_local_function,
        1,
    )
elif "return stepDistanceInKm(step);" not in app:
    raise RuntimeError(
        "Não encontrei o cálculo local de distância."
    )

old_total_label = """                {totalDistance.toLocaleString(
                  "pt-BR",
                  {
                    minimumFractionDigits: 1,
                    maximumFractionDigits: 2,
                  },
                )} km
              </strong>
            </div>
"""

new_total_label = """                {totalDistance.toLocaleString(
                  "pt-BR",
                  {
                    minimumFractionDigits: 1,
                    maximumFractionDigits: 2,
                  },
                )} km
              </strong>
              <small>
                Inclui aquecimento, blocos repetidos,
                recuperações e desaquecimento.
              </small>
            </div>
"""

if old_total_label in app:
    app = app.replace(
        old_total_label,
        new_total_label,
        1,
    )
elif "Inclui aquecimento, blocos repetidos" not in app:
    raise RuntimeError(
        "Não encontrei a exibição da distância total."
    )

APP.write_text(
    app,
    encoding="utf-8",
    newline="\n",
)

build = subprocess.run(
    ["npm.cmd", "run", "build"],
    cwd=FRONTEND,
)

if build.returncode:
    raise SystemExit(build.returncode)

print("Etapa 102A concluída.")
print(
    "O volume total agora usa um único cálculo e "
    "inclui todos os blocos por distância."
)
print()
print("Execute:")
print(
    "git add frontend/src/App.jsx "
    "frontend/src/utils/workoutSummary.js"
)
print(
    'git commit -m '
    '"fix: corrige volume total do treino estruturado"'
)
print("git push origin main")
