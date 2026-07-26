import { useMemo, useState } from "react";

import "./WorkoutsPage.css";


export default function WorkoutsPage({
  athletes,
  loading,
  error,
  onOpenTraining,
}) {
  const [search, setSearch] = useState("");

  const filteredAthletes = useMemo(() => {
    const term = search.trim().toLocaleLowerCase("pt-BR");

    if (!term) {
      return athletes;
    }

    return athletes.filter((athlete) => {
      const content = [
        athlete.name,
        athlete.goal,
        athlete.email,
      ]
        .filter(Boolean)
        .join(" ")
        .toLocaleLowerCase("pt-BR");

      return content.includes(term);
    });
  }, [athletes, search]);

  const activeCount = athletes.filter(
    (athlete) => athlete.active,
  ).length;

  return (
    <section className="workouts-page">
      <header className="workouts-heading">
        <div>
          <p className="eyebrow">TREINOS</p>
          <h2>Central de treinos</h2>
          <p className="muted">
            Localize um atleta e acesse suas sessões
            planejadas para consultar ou editar.
          </p>
        </div>

        <div className="workouts-metrics">
          <article>
            <strong>{athletes.length}</strong>
            <span>atletas</span>
          </article>

          <article>
            <strong>{activeCount}</strong>
            <span>ativos</span>
          </article>
        </div>
      </header>

      <section className="workouts-toolbar">
        <label>
          <span>Buscar atleta ou objetivo</span>
          <input
            type="search"
            placeholder="Ex.: Wanderson, maratona..."
            value={search}
            onChange={(event) =>
              setSearch(event.target.value)
            }
          />
        </label>

        <span>
          {filteredAthletes.length} resultado(s)
        </span>
      </section>

      {error && (
        <div className="alert">
          {error}
        </div>
      )}

      {loading ? (
        <p className="muted">
          Carregando treinos...
        </p>
      ) : filteredAthletes.length === 0 ? (
        <section className="workouts-empty">
          <h3>Nenhum atleta encontrado</h3>
          <p>
            Ajuste a busca ou cadastre um novo atleta.
          </p>
        </section>
      ) : (
        <div className="workouts-list">
          {filteredAthletes.map((athlete) => (
            <article
              className="workout-athlete-row"
              key={athlete.id}
            >
              <div className="workout-athlete-identity">
                <span className="workout-athlete-avatar">
                  {athlete.name
                    .split(" ")
                    .filter(Boolean)
                    .slice(0, 2)
                    .map((part) => part[0])
                    .join("")
                    .toUpperCase()}
                </span>

                <div>
                  <h3>{athlete.name}</h3>
                  <p>
                    {athlete.goal
                      || "Sem objetivo informado"}
                  </p>
                </div>
              </div>

              <div className="workout-athlete-meta">
                <span
                  className={
                    athlete.active
                      ? "workout-athlete-status active"
                      : "workout-athlete-status inactive"
                  }
                >
                  {athlete.active
                    ? "Ativo"
                    : "Inativo"}
                </span>

                <button
                  type="button"
                  className="btn-primary"
                  onClick={() =>
                    onOpenTraining(athlete)
                  }
                >
                  Ver sessões
                </button>
              </div>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
