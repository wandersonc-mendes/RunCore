import "./PlanningPage.css";


export default function PlanningPage({
  athletes,
  loading,
  error,
  onOpenPlanning,
}) {
  const activeAthletes = athletes.filter(
    (athlete) => athlete.active,
  );

  return (
    <section className="planning-page">
      <header className="planning-heading">
        <div>
          <p className="eyebrow">PLANEJAMENTO</p>
          <h2>Planejamentos dos atletas</h2>
          <p className="muted">
            Acesse os ciclos de treinamento e acompanhe
            a situação de cada atleta.
          </p>
        </div>

        <div className="planning-summary">
          <strong>{activeAthletes.length}</strong>
          <span>atletas ativos</span>
        </div>
      </header>

      {error && (
        <div className="alert">
          {error}
        </div>
      )}

      {loading ? (
        <p className="muted">
          Carregando atletas...
        </p>
      ) : athletes.length === 0 ? (
        <section className="planning-empty">
          <h3>Nenhum atleta cadastrado</h3>
          <p>
            Cadastre um atleta antes de criar
            um planejamento.
          </p>
        </section>
      ) : (
        <div className="planning-grid">
          {athletes.map((athlete) => (
            <article
              className="planning-athlete-card"
              key={athlete.id}
            >
              <div className="planning-athlete-main">
                <span className="planning-avatar">
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
                      || "Objetivo ainda não informado"}
                  </p>
                </div>
              </div>

              <div className="planning-card-footer">
                <span
                  className={
                    athlete.active
                      ? "planning-status active"
                      : "planning-status inactive"
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
                    onOpenPlanning(athlete)
                  }
                >
                  Abrir planejamento
                </button>
              </div>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
