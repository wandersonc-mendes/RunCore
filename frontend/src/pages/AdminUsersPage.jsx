import { useEffect, useState } from "react";

import {
  createCoach,
  createManagedUser,
  listManagedUsers,
  updateManagedUser,
} from "../api";

import "./AdminUsersPage.css";


const emptyAdmin = {
  name: "",
  email: "",
  password: "",
  role: "admin",
  is_active: true,
};

const emptyCoach = {
  name: "",
  email: "",
  password: "",
  is_active: true,
  birth_date: "",
  sex: "",
  cpf: "",
  rg: "",
  team_role: "Treinador",
  cref: "",
  instagram: "",
  show_public_profile: true,
  photo_url: "",
  zip_code: "",
  address: "",
  address_number: "",
  address_extra: "",
  neighborhood: "",
  city: "",
  state: "",
  phone: "",
  phone_secondary: "",
  curriculum: "",
  notes: "",
};

const coachTabs = [
  ["personal", "Dados pessoais"],
  ["access", "Acesso"],
  ["address", "Endereço"],
  ["curriculum", "Mini currículo"],
  ["notes", "Anotações gerais"],
];


function roleLabel(role) {
  if (role === "master") return "Master";
  if (role === "admin") return "Administrativo";
  if (role === "coach") return "Treinador";
  return "Aluno";
}


function CoachField({
  label,
  name,
  form,
  setForm,
  type = "text",
  required = false,
  ...props
}) {
  return (
    <label>
      {label}
      <input
        {...props}
        type={type}
        required={required}
        value={form[name]}
        onChange={(event) => setForm({
          ...form,
          [name]: event.target.value,
        })}
      />
    </label>
  );
}


function CoachRegistration({ onClose, onCreated }) {
  const [tab, setTab] = useState("personal");
  const [form, setForm] = useState(emptyCoach);
  const [saving, setSaving] = useState(false);
  const [searchingZip, setSearchingZip] = useState(false);
  const [error, setError] = useState("");

  async function completeAddress() {
    const zip = form.zip_code.replace(/\D/g, "");

    if (zip.length !== 8) {
      setError("Informe um CEP com 8 números.");
      return;
    }

    setSearchingZip(true);
    setError("");

    try {
      const response = await fetch(`https://viacep.com.br/ws/${zip}/json/`);
      const address = await response.json();

      if (!response.ok || address.erro) {
        throw new Error("CEP não encontrado.");
      }

      setForm((current) => ({
        ...current,
        address: address.logradouro || current.address,
        neighborhood: address.bairro || current.neighborhood,
        city: address.localidade || current.city,
        state: address.uf || current.state,
      }));
    } catch (err) {
      setError(err.message || "Não foi possível consultar o CEP.");
    } finally {
      setSearchingZip(false);
    }
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");

    if (!form.name.trim()) {
      setTab("personal");
      setError("Informe o nome do treinador.");
      return;
    }

    if (!form.email.trim() || form.password.length < 8) {
      setTab("access");
      setError("Informe um e-mail e uma senha temporária com 8 caracteres.");
      return;
    }

    setSaving(true);

    try {
      await createCoach({
        ...form,
        birth_date: form.birth_date || null,
      });
      await onCreated();
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  }

  return (
    <section className="coach-registration-card">
      <header className="coach-registration-heading">
        <div>
          <p className="eyebrow">NOVO TREINADOR</p>
          <h3>Cadastro de treinador e auxiliares</h3>
          <p>Preencha os dados profissionais e crie o acesso ao RunCore.</p>
        </div>
        <button type="button" className="btn-ghost" onClick={onClose}>
          Fechar
        </button>
      </header>

      <nav className="coach-registration-tabs" aria-label="Etapas do cadastro">
        {coachTabs.map(([value, label]) => (
          <button
            key={value}
            type="button"
            className={tab === value ? "active" : ""}
            onClick={() => setTab(value)}
          >
            {label}
          </button>
        ))}
      </nav>

      <form onSubmit={handleSubmit}>
        {tab === "personal" && (
          <div className="coach-registration-fields">
            <CoachField label="Nome completo" name="name" form={form} setForm={setForm} required />
            <CoachField label="Data de nascimento" name="birth_date" form={form} setForm={setForm} type="date" />
            <label>
              Sexo
              <select
                value={form.sex}
                onChange={(event) => setForm({ ...form, sex: event.target.value })}
              >
                <option value="">Selecione</option>
                <option value="Feminino">Feminino</option>
                <option value="Masculino">Masculino</option>
                <option value="Não informar">Não informar</option>
              </select>
            </label>
            <CoachField label="CPF" name="cpf" form={form} setForm={setForm} />
            <CoachField label="RG" name="rg" form={form} setForm={setForm} />
            <CoachField label="Função na equipe" name="team_role" form={form} setForm={setForm} />
            <CoachField label="CREF" name="cref" form={form} setForm={setForm} />
            <CoachField label="Instagram" name="instagram" form={form} setForm={setForm} placeholder="@usuario" />
            <CoachField label="URL da foto" name="photo_url" form={form} setForm={setForm} type="url" placeholder="https://..." />
            <label className="coach-registration-check wide">
              <input
                type="checkbox"
                checked={form.show_public_profile}
                onChange={(event) => setForm({
                  ...form,
                  show_public_profile: event.target.checked,
                })}
              />
              Exibir este treinador no perfil público da equipe
            </label>
          </div>
        )}

        {tab === "access" && (
          <div className="coach-registration-fields">
            <CoachField label="E-mail de acesso" name="email" form={form} setForm={setForm} type="email" required />
            <CoachField label="Senha temporária" name="password" form={form} setForm={setForm} type="password" minLength="8" required />
            <label>
              Status
              <select
                value={form.is_active ? "active" : "inactive"}
                onChange={(event) => setForm({
                  ...form,
                  is_active: event.target.value === "active",
                })}
              >
                <option value="active">Ativo</option>
                <option value="inactive">Inativo</option>
              </select>
            </label>
            <label>
              Perfil de acesso
              <input value="Treinador" readOnly />
            </label>
            <p className="coach-registration-help wide">
              O treinador poderá substituir a senha temporária pelo fluxo
              seguro de recuperação enviado ao próprio e-mail.
            </p>
          </div>
        )}

        {tab === "address" && (
          <div className="coach-registration-fields">
            <label>
              CEP
              <span className="coach-registration-inline">
                <input
                  value={form.zip_code}
                  onChange={(event) => setForm({
                    ...form,
                    zip_code: event.target.value,
                  })}
                />
                <button type="button" className="btn-ghost" onClick={completeAddress}>
                  {searchingZip ? "Buscando..." : "Completar endereço"}
                </button>
              </span>
            </label>
            <CoachField label="Endereço" name="address" form={form} setForm={setForm} />
            <CoachField label="Número" name="address_number" form={form} setForm={setForm} />
            <CoachField label="Complemento" name="address_extra" form={form} setForm={setForm} />
            <CoachField label="Bairro" name="neighborhood" form={form} setForm={setForm} />
            <CoachField label="Cidade" name="city" form={form} setForm={setForm} />
            <CoachField label="Estado" name="state" form={form} setForm={setForm} maxLength="2" />
            <CoachField label="Telefone" name="phone" form={form} setForm={setForm} />
            <CoachField label="Telefone secundário" name="phone_secondary" form={form} setForm={setForm} />
          </div>
        )}

        {tab === "curriculum" && (
          <label className="coach-registration-textarea">
            Mini currículo
            <span>Este conteúdo poderá ser exibido no perfil do treinador.</span>
            <textarea
              rows="10"
              maxLength="5000"
              value={form.curriculum}
              onChange={(event) => setForm({
                ...form,
                curriculum: event.target.value,
              })}
            />
          </label>
        )}

        {tab === "notes" && (
          <label className="coach-registration-textarea">
            Anotações internas
            <span>Informações visíveis apenas para a administração.</span>
            <textarea
              rows="10"
              maxLength="5000"
              value={form.notes}
              onChange={(event) => setForm({
                ...form,
                notes: event.target.value,
              })}
            />
          </label>
        )}

        {error && <div className="alert">{error}</div>}

        <footer className="coach-registration-actions">
          <button type="button" className="btn-ghost" onClick={onClose}>
            Cancelar
          </button>
          <button className="btn-primary" disabled={saving}>
            {saving ? "Salvando..." : "Cadastrar treinador"}
          </button>
        </footer>
      </form>
    </section>
  );
}


export default function AdminUsersPage({ currentUser }) {
  const [users, setUsers] = useState([]);
  const [adminForm, setAdminForm] = useState(emptyAdmin);
  const [showCoachForm, setShowCoachForm] = useState(false);
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

  async function handleCreateAdmin(event) {
    event.preventDefault();
    setSaving(true);
    setError("");
    setMessage("");

    try {
      await createManagedUser(adminForm);
      setAdminForm(emptyAdmin);
      setMessage("Acesso administrativo criado com sucesso.");
      await loadUsers();
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  }

  async function handleCoachCreated() {
    setShowCoachForm(false);
    setMessage("Treinador cadastrado com sucesso.");
    await loadUsers();
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
          <p>Cadastre treinadores e pessoas responsáveis pela administração.</p>
        </div>
        <div className="admin-users-heading-actions">
          <span>{users.filter((user) => user.is_active).length} ativos</span>
          <button
            type="button"
            className="btn-primary"
            onClick={() => setShowCoachForm(true)}
          >
            + Cadastrar treinador
          </button>
        </div>
      </header>

      {error && <div className="alert">{error}</div>}
      {message && <div className="admin-users-success">{message}</div>}

      {showCoachForm && (
        <CoachRegistration
          onClose={() => setShowCoachForm(false)}
          onCreated={handleCoachCreated}
        />
      )}

      <section className="admin-users-grid">
        <form className="admin-user-form" onSubmit={handleCreateAdmin}>
          <header>
            <h3>Novo administrativo</h3>
            <p>Crie uma pessoa com acesso às funções administrativas.</p>
          </header>

          <CoachField label="Nome" name="name" form={adminForm} setForm={setAdminForm} required />
          <CoachField label="E-mail" name="email" form={adminForm} setForm={setAdminForm} type="email" required />
          <CoachField label="Senha temporária" name="password" form={adminForm} setForm={setAdminForm} type="password" minLength="8" required />

          <button className="btn-primary" disabled={saving}>
            {saving ? "Criando..." : "Criar administrativo"}
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
                          <span className="admin-role-readonly">{roleLabel(user.role)}</span>
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
