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

function formatStepDuration(seconds = 0) {
  const value = Math.max(0, Number(seconds || 0));
  const hours = Math.floor(value / 3600);
  const minutes = Math.floor((value % 3600) / 60);
  const remainder = value % 60;

  if (hours > 0) {
    return [
      hours,
      String(minutes).padStart(2, "0"),
      String(remainder).padStart(2, "0"),
    ].join(":");
  }

  if (remainder > 0) {
    return `${minutes}min ${remainder}s`;
  }

  return `${minutes} min`;
}


export function stepDurationInSeconds(step) {
  if (
    (step?.prescription_type || "distance")
    !== "duration"
  ) {
    return 0;
  }

  const repetitions = Math.max(
    Number(step?.repetitions || 0),
    1,
  );

  return Number(step?.duration || 0) * repetitions;
}


export function workoutSummaryFromSteps(steps = []) {
  const repeatedStep = steps.find((step) => (
    Number(step?.repetitions || 0) > 1
    && stepRole(step?.type) === "main"
  ));

  if (repeatedStep) {
    const repetitions = Number(
      repeatedStep.repetitions,
    );

    if (
      (repeatedStep.prescription_type || "distance")
      === "duration"
    ) {
      const duration = formatStepDuration(
        repeatedStep.duration,
      );

      return {
        label: `${repetitions} × ${duration}`,
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
    }

    if (
      (repeatedStep.distance_unit || "m")
      === "m"
    ) {
      const distance = Number(
        repeatedStep.distance || 0,
      );
      const unit = repeatedStep.distance_unit || "m";

      return {
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
    }
  }

  const totalDistance = steps.reduce(
    (total, step) =>
      total + stepDistanceInKm(step),
    0,
  );

  const totalDuration = steps.reduce(
    (total, step) =>
      total + stepDurationInSeconds(step),
    0,
  );

  const parts = [];

  if (totalDistance > 0) {
    parts.push(
      `${totalDistance.toLocaleString("pt-BR", {
        minimumFractionDigits: 1,
        maximumFractionDigits: 2,
      })} km`,
    );
  }

  if (totalDuration > 0) {
    parts.push(formatStepDuration(totalDuration));
  }

  return {
    label: parts.join(" + ") || "Treino estruturado",
    plannedDistance: totalDistance,
    plannedDuration: totalDuration,
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
