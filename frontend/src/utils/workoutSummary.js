function stepRole(type = "") {
  const label = String(type).toLowerCase();

  if (
    label.includes("aquecimento")
    || label.includes("desaqueci")
    || label.includes("descanso")
    || label.includes("recupera")
  ) {
    return "support";
  }

  return "main";
}

export function stepDistanceInKm(step) {
  const distance = Number(step?.distance || 0);
  const repetitions = Math.max(Number(step?.repetitions || 0), 1);
  const unit = step?.distance_unit
    || (Number(step?.repetitions || 0) > 0 ? "m" : "km");

  return distance * repetitions * (unit === "m" ? 0.001 : 1);
}

export function workoutSummaryFromSteps(steps = []) {
  const repeatedStep = steps.find((step) => (
    Number(step?.repetitions || 0) > 1
    && stepRole(step?.type) === "main"
    && (step?.distance_unit || "m") === "m"
  ));

  if (repeatedStep) {
    const repetitions = Number(repeatedStep.repetitions);
    const distance = Number(repeatedStep.distance || 0);
    const unit = repeatedStep.distance_unit || "m";

    return {
      label: `${repetitions} × ${distance.toLocaleString("pt-BR")} ${unit}`,
      plannedDistance: distance,
      repetitions,
    };
  }

  const totalDistance = steps.reduce(
    (total, step) => total + stepDistanceInKm(step),
    0,
  );

  return {
    label: `${totalDistance.toLocaleString("pt-BR", {
      minimumFractionDigits: 1,
      maximumFractionDigits: 2,
    })} km`,
    plannedDistance: totalDistance,
    repetitions: 0,
  };
}

export function formatWorkoutSummary(session) {
  if (session?.steps?.length) {
    return workoutSummaryFromSteps(session.steps).label;
  }

  return session?.repetitions
    ? `${session.repetitions} × ${session.planned_distance} m`
    : `${Number(session?.planned_distance || 0).toFixed(1)} km`;
}
