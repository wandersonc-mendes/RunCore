import { NavLink } from "react-router-dom";
import { coachMenu, studentMenu } from "./menuConfig";

export default function Sidebar({ role, mobileOpen, onClose }) {
  const menu = role === "student" ? studentMenu : coachMenu;

  return (
    <>
      {mobileOpen && (
        <button type="button" className="app-shell-backdrop" aria-label="Fechar menu" onClick={onClose} />
      )}
      <aside className={`app-sidebar ${mobileOpen ? "is-open" : ""}`}>
        <div className="app-sidebar-brand">
          <img src="/logo-horizontal.png?v=2" alt="RunCore" />
        </div>
        <nav className="app-sidebar-nav" aria-label="Menu principal">
          {menu.map((item) => (
            <NavLink
              key={`${item.label}-${item.path}`}
              to={item.path}
              onClick={onClose}
              className={({ isActive }) => isActive ? "app-sidebar-link active" : "app-sidebar-link"}
            >
              <span className="app-sidebar-icon" aria-hidden="true">{item.icon}</span>
              <span>{item.label}</span>
            </NavLink>
          ))}
        </nav>
      </aside>
    </>
  );
}
