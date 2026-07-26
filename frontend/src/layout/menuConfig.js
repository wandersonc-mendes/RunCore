import { coachPaths, studentPaths } from "../router/paths";

export const coachMenu = [
  { label: "Dashboard", path: coachPaths.dashboard, icon: "⌂" },
  { label: "Atletas", path: coachPaths.athletes, icon: "♙" },
  { label: "Planejamento", path: coachPaths.workouts, icon: "▣" },
  { label: "Treinos", path: coachPaths.workouts, icon: "◇" },
  { label: "Agenda", path: coachPaths.calendar, icon: "□" },
  { label: "Avaliações", path: coachPaths.evaluations, icon: "✓" },
  { label: "Relatórios", path: coachPaths.reports, icon: "▤" },
  { label: "Configurações", path: coachPaths.settings, icon: "⚙" },
];

export const studentMenu = [
  { label: "Dashboard", path: studentPaths.dashboard, icon: "⌂" },
  { label: "Minha planilha", path: studentPaths.trainingPlan, icon: "▣" },
  { label: "Metas e provas", path: studentPaths.goals, icon: "⚑" },
  { label: "Atividades", path: studentPaths.activities, icon: "◇" },
  { label: "Evolução", path: studentPaths.evolution, icon: "↗" },
  { label: "Calculadoras", path: studentPaths.calculators, icon: "⌗" },
  { label: "Agenda", path: studentPaths.calendar, icon: "□" },
  { label: "Meu perfil", path: studentPaths.profile, icon: "○" },
  { label: "Configurações", path: studentPaths.settings, icon: "⚙" },
];
