import { useEffect, useState } from "react";
import { listAthletes, createAthlete, deleteAthlete } from "./api";
import AthleteProfile from "./AthleteProfile";
import "./App.css";

const emptyForm = { name: "", phone: "", email: "", goal: "", notes: "" };

export default function App() {
  const [athletes, setAthletes] = useState([]);
  const [search, setSearch] = useState("");
  const [form, setForm] = useState(emptyForm);
  const [showForm, setShowForm] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedAthleteId, setSelectedAthleteId] = useState(null);

  async function load(currentSearch = search) {
    setLoading(true);
    setError(null);
    try {
      const data = await listAthletes(currentSearch);
      setAthletes(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load("");
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function handleSearchSubmit(e) {
    e.preventDefault();
    load(search);
  }

  async function handleCreate(e) {
    e.preventDefault();
    if (!form.name.trim()) return;
    try {
      await createAthlete({ ...form, active: true });
      setForm(emptyForm);
      setShowForm(false);
      load(search);
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleDelete(id) {
    if (!window.confirm("Remover este atleta?")) return;
    try {
      await deleteAthlete(id);
      load(search);
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div className="page">
      <header className="topbar">
        <div className="brand">
          <span className="brand-mark">RC</span>
          <div>
            <h1>RunCore</h1>
            <p>Atletas</p>
          </div>
        </div>
        <button className="btn-primary" onClick={() => setShowForm((v) => !v)}>
          {showForm ? "Cancelar" : "+ Novo atleta"}
        </button>
      </header>

      <main className="content">
        {selectedAthleteId ? (
          <AthleteProfile
            athleteId={selectedAthleteId}
            onBack={() => setSelectedAthleteId(null)}
          />
        ) : (
          <>
        <form className="search-row" onSubmit={handleSearchSubmit}>
          <input
            type="text"
            placeholder="Buscar por nome..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
          <button type="submit" className="btn-ghost">Buscar</button>
        </form>

        {showForm && (
          <form className="card new-athlete-form" onSubmit={handleCreate}>
            <div className="form-grid">
              <label>
                Nome
                <input
                  required
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                />
              </label>
              <label>
                Telefone
                <input
                  value={form.phone}
                  onChange={(e) => setForm({ ...form, phone: e.target.value })}
                />
              </label>
              <label>
                E-mail
                <input
                  type="email"
                  value={form.email}
                  onChange={(e) => setForm({ ...form, email: e.target.value })}
                />
              </label>
              <label>
                Objetivo
                <input
                  placeholder="Ex: Maratona, 10K..."
                  value={form.goal}
                  onChange={(e) => setForm({ ...form, goal: e.target.value })}
                />
              </label>
            </div>
            <label className="notes-label">
              Observações
              <textarea
                rows={2}
                value={form.notes}
                onChange={(e) => setForm({ ...form, notes: e.target.value })}
              />
            </label>
            <button type="submit" className="btn-primary">Salvar atleta</button>
          </form>
        )}

        {error && <div className="alert">{error}</div>}

        {loading ? (
          <p className="muted">Carregando...</p>
        ) : athletes.length === 0 ? (
          <div className="empty-state">
            <p>Nenhum atleta cadastrado ainda.</p>
            <p className="muted">Use "+ Novo atleta" para começar.</p>
          </div>
        ) : (
          <table className="athletes-table">
            <thead>
              <tr>
                <th>Nome</th>
                <th>Contato</th>
                <th>Objetivo</th>
                <th>Status</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {athletes.map((a) => (
                <tr key={a.id}>
                  <td className="name-cell">
                    <button
                      className="link-button"
                      onClick={() => setSelectedAthleteId(a.id)}
                    >
                      {a.name}
                    </button>
                  </td>
                  <td className="muted">
                    {a.phone}
                    {a.phone && a.email ? " · " : ""}
                    {a.email}
                  </td>
                  <td>{a.goal || "—"}</td>
                  <td>
                    <span className={`badge ${a.active ? "badge-active" : "badge-inactive"}`}>
                      {a.active ? "Ativo" : "Inativo"}
                    </span>
                  </td>
                  <td>
                    <button className="btn-link-danger" onClick={() => handleDelete(a.id)}>
                      Remover
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
          </>
        )}
      </main>
    </div>
  );
}
