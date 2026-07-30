import fs from "node:fs";
import path from "node:path";
import process from "node:process";


const root = process.cwd();

function read(relativePath) {
  const fullPath = path.join(root, relativePath);

  if (!fs.existsSync(fullPath)) {
    throw new Error(`Arquivo obrigatório ausente: ${relativePath}`);
  }

  return fs.readFileSync(fullPath, "utf8");
}


function requireText(source, expected, label) {
  if (!source.includes(expected)) {
    throw new Error(`Validação falhou: ${label}`);
  }
}


const app = read("src/App.jsx");
const portal = read("src/StudentPortal.jsx");
const paths = read("src/router/paths.js");
const topbar = read("src/layout/Topbar.jsx");
const themeProvider = read("src/theme/ThemeProvider.jsx");
const evolution = read("src/pages/StudentEvolutionPage.jsx");
const agenda = read("src/pages/StudentAgendaPage.jsx");
const settings = read("src/pages/SettingsPage.jsx");
const dateUtility = read("src/utils/activityDate.js");

const routeChecks = [
  ["dashboard", "studentPaths.dashboard"],
  ["training plan", "studentPaths.trainingPlan"],
  ["goals", "studentPaths.goals"],
  ["activities", "studentPaths.activities"],
  ["evolution", "studentPaths.evolution"],
  ["calculators", "studentPaths.calculators"],
  ["calendar", "studentPaths.calendar"],
  ["profile", "studentPaths.profile"],
  ["settings", "studentPaths.settings"],
];

for (const [label, marker] of routeChecks) {
  requireText(app, marker, `rota do atleta: ${label}`);
}

const pathChecks = [
  "/atleta/dashboard",
  "/atleta/minha-planilha",
  "/atleta/metas-e-provas",
  "/atleta/atividades",
  "/atleta/evolucao",
  "/atleta/calculadoras",
  "/atleta/agenda",
  "/atleta/meu-perfil",
  "/atleta/configuracoes",
];

for (const route of pathChecks) {
  requireText(paths, route, `caminho declarado: ${route}`);
}

const portalViews = [
  'view === "dashboard"',
  'view === "training"',
  'view === "goals"',
  'view === "activities"',
  'view === "calculators"',
  'view === "profile"',
];

for (const view of portalViews) {
  requireText(portal, view, `visualização no StudentPortal: ${view}`);
}

requireText(
  evolution,
  "Fitness · CTL",
  "indicador Fitness · CTL",
);
requireText(
  evolution,
  "Fadiga · ATL",
  "indicador Fadiga · ATL",
);
requireText(
  evolution,
  "Forma · TSB",
  "indicador Forma · TSB",
);
requireText(
  agenda,
  "student-agenda",
  "página dedicada de Agenda",
);
requireText(
  settings,
  "runcore.notification-preferences",
  "persistência local de notificações",
);
requireText(
  settings,
  "studentPaths.activities",
  "atalho do Strava para Atividades",
);
requireText(
  topbar,
  "useTheme",
  "consumo do tema global na barra superior",
);
requireText(
  topbar,
  "toggleTheme",
  "ação global de alternância de tema",
);
requireText(
  topbar,
  "resolvedTheme",
  "resolução do tema ativo",
);
requireText(
  topbar,
  "Ativar modo claro",
  "rótulo da ação para modo claro",
);
requireText(
  topbar,
  "Ativar modo escuro",
  "rótulo da ação para modo escuro",
);
requireText(
  themeProvider,
  "document.documentElement",
  "aplicação do tema no documento",
);
requireText(
  dateUtility,
  "start_date_local",
  "prioridade de data local da atividade",
);
requireText(
  dateUtility,
  "start_date",
  "data principal da atividade",
);
requireText(
  dateUtility,
  "start_at",
  "compatibilidade com data legada",
);

console.log("");
console.log("Auditoria do painel do atleta concluída.");
console.log("9 rotas verificadas.");
console.log("6 visualizações do StudentPortal verificadas.");
console.log("Agenda, Evolução e Configurações verificadas.");
console.log("Tema global e normalização de datas verificados.");
