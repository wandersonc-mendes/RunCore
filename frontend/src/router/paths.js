export const publicPaths = {
  login: "/login",
  forgotPassword: "/recuperar-senha",
  resetPassword: "/redefinir-senha",
};

export const coachPaths = {
  dashboard: "/",
  profile: "/treinador/meu-perfil",
  athletes: "/treinador/atletas",
  planning: "/treinador/planejamento",
  athleteProfile: (athleteId = ":athleteId") =>
    `/treinador/atletas/${athleteId}`,
  athletePlanning: (athleteId = ":athleteId") =>
    `/treinador/atletas/${athleteId}/planejamento`,
  athleteEvaluations: (athleteId = ":athleteId") =>
    `/treinador/atletas/${athleteId}/ipt`,
  athleteIpt: (athleteId = ":athleteId") =>
    `/treinador/atletas/${athleteId}/ipt`,
  workouts: "/treinador/treinos",
  calendar: "/treinador/agenda",
  evaluations: "/treinador/ipt-avaliacao",
  reports: "/treinador/relatorios",
  settings: "/treinador/configuracoes",
};

export const studentPaths = {
  completeProfile: "/atleta/completar-cadastro",
  dashboard: "/atleta/dashboard",
  trainingPlan: "/atleta/minha-planilha",
  goals: "/atleta/metas-e-provas",
  activities: "/atleta/atividades",
  evolution: "/atleta/evolucao",
  calculators: "/atleta/calculadoras",
  calendar: "/atleta/agenda",
  profile: "/atleta/meu-perfil",
  settings: "/atleta/configuracoes",
};

export const adminPaths = {
  users: "/administrativo/usuarios",
  settings: "/administrativo/configuracoes",
};
