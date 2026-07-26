import { useEffect, useMemo, useState } from "react";

import { listEvaluations } from "../api";
import "./EvaluationsPage.css";


function formatDate(value) {
  if (!value) return "Sem data";

  return new Intl.DateTimeFormat("pt-BR").format(
    new Date(`${value}T12:00:00`),
  );
}


export default function EvaluationsPage({
  athletes,
  onOpenEvaluations,
}) {
  const [records, setRecords] = useState([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;

    async function loadAllEvaluations() {
      setLoading(true);
      setError("");

      try {
        const results = await Promise.allSettled(
          athletes.map(async (athlete) => ({
            athlete,
            evaluations: await listEvaluations(athlete.id),
          })),
        );

        if (!active) return;

        setRecords(
          results
            .filter((result) => result.status === "fulfilled")
            .map((result) => {
              const evaluations = result.value.evaluations || [];
              const latest = [...evaluations].sort(
                (first, second) =>
                  String(second.test_date || "").localeCompare(
                    String(first.test_date || ""),
                  ),
              )[0] || null;

              return {
                athlete: result.value.athlete,
                count: evaluations.length,
                latest,
              };
            }),
        );
      } catch (err) {
        if (active) {
          setError(
            err?.message
            || "Não foi possível carregar as avaliações.",
          );
        }
      } finally {
        if (active) setLoading(false);
      }
    }

    loadAllEvaluations();

    return () => {
      active = false;
    };
  }, [athletes]);

  const filteredRecords = useMemo(() => {
    const term = search.trim().toLocaleLowerCase("pt-BR");

    if (!term) return records;

    return records.filter(({ athlete }) =>
      [athlete.name, athlete.goal, athlete.email]
        .filter(Boolean)
        .join(" ")
        .toLocaleLowerCase("pt-BR")
        .includes(term),
    );
  }, [records, search]);

  const totalEvaluations = records.reduce(
    (total, record) => total + record.count,
    0,
  );

  return (
    <section className="evaluations-page">
      <header className="evaluations-heading">
        <div>
          <p className="eyebrow">AVALIAÇÕES</p>
          <h2>Central de avaliações</h2>
          <p className="muted">
            Consulte o histórico, o último VDOT e registre
            novas avaliações por atleta.
          </p>
        </div>

        <div className="evaluations-summary">
          <article>
            <strong>{records.length}</strong>
            <span>atletas</span>
          </article>
          <article>
            <strong>{totalEvaluations}</strong>
            <span>avaliações</span>
          </article>
        </div>
      </header>

      <section className="evaluations-toolbar">
        <label>
          <span>Buscar atleta</span>
          <input
            type="search"
            placeholder="Nome, e-mail ou objetivo"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
          />
        </label>
        <span>{filteredRecords.length} resultado(s)</span>
      </section>

      {error && <div className="alert">{error}</div>}

      {loading ? (
        <p className="muted">Carregando avaliações...</p>
      ) : filteredRecords.length === 0 ? (
        <section className="evaluations-empty">
          <h3>Nenhum atleta encontrado</h3>
          <p>Ajuste a busca ou cadastre um novo atleta.</p>
        </section>
      ) : (
        <div className="evaluations-list">
          {filteredRecords.map(({ athlete, count, latest }) => (
            <article
              className="evaluation-athlete-row"
              key={athlete.id}
            >
              <div className="evaluation-athlete-main">
                <span className="evaluation-avatar">
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
                    {athlete.goal || "Sem objetivo informado"}
                  </p>
                </div>
              </div>

              <div className="evaluation-data">
                <div>
                  <span>Total</span>
                  <strong>{count}</strong>
                </div>

                <div>
                  <span>Último VDOT</span>
                  <strong>
                    {latest?.vdot != null
                      ? Number(latest.vdot).toFixed(1)
                      : "—"}
                  </strong>
                </div>

                <div>
                  <span>Último teste</span>
                  <strong>
                    {latest
                      ? formatDate(latest.test_date)
                      : "—"}
                  </strong>
                </div>

                <button
                  type="button"
                  className="btn-primary"
                  onClick={() => onOpenEvaluations(athlete)}
                >
                  Abrir avaliações
                </button>
              </div>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
