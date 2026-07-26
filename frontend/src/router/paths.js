export const publicPaths = {
  login: "/login",
  forgotPassword: "/recuperar-senha",
  resetPassword: "/redefinir-senha",
};

export const coachPaths = {
  dashboard: "/treinador/dashboard",
  athletes: "/treinador/atletas",
  athleteProfile: (athleteId = ":athleteId") =>
    `/treinador/atletas/${athleteId}`,
  athletePlanning: (athleteId = ":athleteId") =>
    `/treinador/atletas/${athleteId}/planejamento`,
  athleteEvaluations: (athleteId = ":athleteId") =>
    `/treinador/atletas/${athleteId}/avaliacoes`,
  athleteIpt: (athleteId = ":athleteId") =>
    `/treinador/atletas/${athleteId}/ipt`,
  workouts: "/treinador/treinos",
  calendar: "/treinador/agenda",
  evaluations: "/treinador/avaliacoes",
  reports: "/treinador/relatorios",
  settings: "/treinador/configuracoes",
};

export const studentPaths = {
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
