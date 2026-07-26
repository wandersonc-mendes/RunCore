import { useState } from "react";
import { Outlet, useLocation } from "react-router-dom";
import Sidebar from "./Sidebar";
import Topbar from "./Topbar";
import "./AppShell.css";

const pageTitles = {
  "/treinador/dashboard": "Dashboard",
  "/treinador/meu-perfil": "Meu perfil",
  "/treinador/atletas": "Atletas",
  "/treinador/treinos": "Treinos",
  "/treinador/agenda": "Agenda",
  "/treinador/avaliacoes": "Avaliações",
  "/treinador/relatorios": "Relatórios",
  "/treinador/configuracoes": "Configurações",
  "/atleta/dashboard": "Dashboard",
  "/atleta/minha-planilha": "Minha planilha",
  "/atleta/metas-e-provas": "Metas e provas",
  "/atleta/atividades": "Atividades",
  "/atleta/evolucao": "Evolução",
  "/atleta/calculadoras": "Calculadoras",
  "/atleta/agenda": "Agenda",
  "/atleta/meu-perfil": "Meu perfil",
  "/atleta/configuracoes": "Configurações",
};

function titleFor(pathname) {
  if (pageTitles[pathname]) return pageTitles[pathname];
  if (pathname.includes("/planejamento")) return "Planejamento";
  if (pathname.includes("/avaliacoes")) return "Avaliações";
  if (pathname.includes("/ipt")) return "Índice de perfil de treino";
  if (pathname.startsWith("/treinador/atletas/")) return "Perfil do atleta";
  return "RunCore";
}

export default function AppShell({ user, onLogout, children }) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const location = useLocation();

  return (
    <div className="app-shell">
      <Sidebar role={user?.role} mobileOpen={mobileMenuOpen} onClose={() => setMobileMenuOpen(false)} />
      <div className="app-shell-main">
        <Topbar user={user} title={titleFor(location.pathname)} onMenu={() => setMobileMenuOpen(true)} onLogout={onLogout} />
        <main className="app-shell-content">{children || <Outlet />}</main>
      </div>
    </div>
  );
}
