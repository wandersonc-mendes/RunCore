import { useEffect, useState } from "react";

import {
  createManagedUser,
  listManagedUsers,
  updateManagedUser,
} from "../api";

import "./AdminUsersPage.css";


const initialForm = {
  name: "",
  email: "",
  password: "",
  role: "coach",
  is_active: true,
};


function roleLabel(role) {
  if (role === "master") return "Master";
  if (role === "admin") return "Administrativo";
  if (role === "coach") return "Treinador";
  return "Aluno";
}


export default function AdminUsersPage({ currentUser }) {
  const [users, setUsers] = useState([]);
  const [form, setForm] = useState(initialForm);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  async function loadUsers() {
    setLoading(true);
    setError("");

    try {
      setUsers(await listManagedUsers());
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadUsers();
  }, []);

  async function handleCreate(event) {
    event.preventDefault();
    setSaving(true);
    setError("");
    setMessage("");

    try {
      await createManagedUser(form);
      setForm(initialForm);
      setMessage("Usuário criado com sucesso.");
      await loadUsers();
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  }

  async function handleAccessChange(user, changes) {
    setError("");
    setMessage("");

    try {
      await updateManagedUser(user.id, {
        name: user.name,
        role: user.role,
        is_active: user.is_active,
        ...changes,
      });
      setMessage("Acesso atualizado com sucesso.");
      await loadUsers();
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <section className="admin-users-page">
      <header className="admin-users-heading">
        <div>
          <p className="eyebrow">ADMINISTRAÇÃO</p>
          <h2>Usuários e perfis de acesso</h2>
          <p>
            Cadastre treinadores e pessoas responsáveis apenas pela
            administração do RunCore.
          </p>
        </div>
        <span>{users.filter((user) => user.is_active).length} ativos</span>
      </header>

      {error && <div className="alert">{error}</div>}
      {message && <div className="admin-users-success">{message}</div>}

      <section className="admin-users-grid">
        <form className="admin-user-form" onSubmit={handleCreate}>
          <header>
            <h3>Novo acesso</h3>
            <p>O usuário poderá trocar a senha pelo fluxo de recuperação.</p>
          </header>

          <label>
            Nome
            <input
              required
              minLength="2"
              value={form.name}
              onChange={(event) => setForm({ ...form, name: event.target.value })}
            />
          </label>

          <label>
            E-mail
            <input
              required
              type="email"
              value={form.email}
              onChange={(event) => setForm({ ...form, email: event.target.value })}
            />
          </label>

          <label>
            Senha temporária
            <input
              required
              type="password"
              minLength="8"
              value={form.password}
              onChange={(event) => setForm({ ...form, password: event.target.value })}
            />
          </label>

          <label>
            Perfil
            <select
              value={form.role}
              onChange={(event) => setForm({ ...form, role: event.target.value })}
            >
              <option value="coach">Treinador</option>
              <option value="admin">Administrativo</option>
            </select>
          </label>

          <button className="btn-primary" disabled={saving}>
            {saving ? "Criando..." : "Criar usuário"}
          </button>
        </form>

        <section className="admin-user-list">
          <header>
            <h3>Acessos cadastrados</h3>
            <p>Alunos continuam sendo cadastrados por convite do treinador.</p>
          </header>

          {loading ? (
            <p className="muted">Carregando usuários...</p>
          ) : (
            <div className="admin-user-table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Usuário</th>
                    <th>Perfil</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {users.map((user) => (
                    <tr key={user.id}>
                      <td>
                        <strong>{user.name}</strong>
                        <small>{user.email}</small>
                      </td>
                      <td>
                        {["student", "master"].includes(user.role) ? (
                          <span className="admin-role-readonly">
                            {roleLabel(user.role)}
                          </span>
                        ) : (
                          <select
                            aria-label={`Perfil de ${user.name}`}
                            value={user.role}
                            disabled={user.id === currentUser.id}
                            onChange={(event) => handleAccessChange(user, {
                              role: event.target.value,
                            })}
                          >
                            <option value="coach">Treinador</option>
                            <option value="admin">Administrativo</option>
                          </select>
                        )}
                      </td>
                      <td>
                        <button
                          type="button"
                          className={user.is_active ? "admin-status active" : "admin-status"}
                          disabled={user.id === currentUser.id}
                          onClick={() => handleAccessChange(user, {
                            is_active: !user.is_active,
                          })}
                        >
                          {user.is_active ? "Ativo" : "Inativo"}
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      </section>
    </section>
  );
}
