import { useEffect, useMemo, useState } from "react";

import {
  getTraining,
  listEvaluations,
} from "../api";

import "./ReportsPage.css";


function percent(value, total) {
  if (!total) return 0;
  return Math.round((value / total) * 100);
}


export default function ReportsPage({
  athletes,
  onOpenPlanning,
  onOpenEvaluations,
}) {
  const [records, setRecords] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;

    async function loadReports() {
      setLoading(true);
      setError("");

      try {
        const results = await Promise.allSettled(
          athletes.map(async (athlete) => {
            const [evaluations, training] = await Promise.all([
              listEvaluations(athlete.id),
              getTraining(athlete.id),
            ]);

            return {
              athlete,
              evaluations: evaluations || [],
              training,
            };
          }),
        );

        if (!active) return;

        setRecords(
          results
            .filter((result) => result.status === "fulfilled")
            .map((result) => result.value),
        );
      } catch (err) {
        if (active) {
          setError(
            err?.message
            || "Não foi possível carregar os relatórios.",
          );
        }
      } finally {
        if (active) setLoading(false);
      }
    }

    loadReports();

    return () => {
      active = false;
    };
  }, [athletes]);

  const report = useMemo(() => {
    const today = new Date().toISOString().slice(0, 10);

    const activeAthletes = records.filter(
      ({ athlete }) => athlete.active,
    ).length;

    const withEvaluations = records.filter(
      ({ evaluations }) => evaluations.length > 0,
    ).length;

    const withTraining = records.filter(
      ({ training }) => Boolean(training),
    ).length;

    const futureSessions = records.reduce(
      (total, { training }) =>
        total
        + (training?.sessions || []).filter(
          (session) =>
            session.session_date
            && session.session_date >= today,
        ).length,
      0,
    );

    const totalEvaluations = records.reduce(
      (total, { evaluations }) =>
        total + evaluations.length,
      0,
    );

    return {
      activeAthletes,
      withEvaluations,
      withTraining,
      futureSessions,
      totalEvaluations,
    };
  }, [records]);

  return (
    <section className="reports-page">
      <header className="reports-heading">
        <div>
          <p className="eyebrow">RELATÓRIOS</p>
          <h2>Visão consolidada</h2>
          <p className="muted">
            Indicadores gerais de acompanhamento,
            avaliações e planejamento dos atletas.
          </p>
        </div>
      </header>

      {error && <div className="alert">{error}</div>}

      {loading ? (
        <p className="muted">Carregando indicadores...</p>
      ) : (
        <>
          <section className="reports-metrics">
            <article>
              <span>Atletas ativos</span>
              <strong>{report.activeAthletes}</strong>
              <small>de {records.length} cadastrados</small>
            </article>

            <article>
              <span>Avaliações registradas</span>
              <strong>{report.totalEvaluations}</strong>
              <small>
                {report.withEvaluations} atleta(s) avaliados
              </small>
            </article>

            <article>
              <span>Planejamentos ativos</span>
              <strong>{report.withTraining}</strong>
              <small>
                {percent(report.withTraining, records.length)}%
                de cobertura
              </small>
            </article>

            <article>
              <span>Sessões futuras</span>
              <strong>{report.futureSessions}</strong>
              <small>na agenda atual</small>
            </article>
          </section>

          <section className="reports-coverage">
            <div>
              <h3>Cobertura de acompanhamento</h3>
              <p>
                Percentual de atletas com dados
                essenciais preenchidos.
              </p>
            </div>

            <div className="coverage-bars">
              <article>
                <header>
                  <span>Com avaliação</span>
                  <strong>
                    {percent(
                      report.withEvaluations,
                      records.length,
                    )}%
                  </strong>
                </header>
                <div>
                  <span
                    style={{
                      width: `${percent(
                        report.withEvaluations,
                        records.length,
                      )}%`,
                    }}
                  />
                </div>
              </article>

              <article>
                <header>
                  <span>Com planejamento</span>
                  <strong>
                    {percent(
                      report.withTraining,
                      records.length,
                    )}%
                  </strong>
                </header>
                <div>
                  <span
                    style={{
                      width: `${percent(
                        report.withTraining,
                        records.length,
                      )}%`,
                    }}
                  />
                </div>
              </article>
            </div>
          </section>

          <section className="reports-athletes">
            <header>
              <div>
                <h3>Situação por atleta</h3>
                <p>
                  Identifique rapidamente lacunas
                  de avaliação ou planejamento.
                </p>
              </div>
            </header>

            <div className="reports-athlete-list">
              {records.map(
                ({ athlete, evaluations, training }) => (
                  <article key={athlete.id}>
                    <div className="report-athlete-main">
                      <span className="report-avatar">
                        {athlete.name
                          .split(" ")
                          .filter(Boolean)
                          .slice(0, 2)
                          .map((part) => part[0])
                          .join("")
                          .toUpperCase()}
                      </span>

                      <div>
                        <h4>{athlete.name}</h4>
                        <p>
                          {athlete.goal
                            || "Sem objetivo informado"}
                        </p>
                      </div>
                    </div>

                    <div className="report-athlete-status">
                      <span
                        className={
                          evaluations.length
                            ? "complete"
                            : "missing"
                        }
                      >
                        {evaluations.length
                          ? `${evaluations.length} avaliação(ões)`
                          : "Sem avaliação"}
                      </span>

                      <span
                        className={
                          training
                            ? "complete"
                            : "missing"
                        }
                      >
                        {training
                          ? "Com planejamento"
                          : "Sem planejamento"}
                      </span>

                      <button
                        type="button"
                        className="btn-ghost"
                        onClick={() =>
                          evaluations.length
                            ? onOpenEvaluations(athlete)
                            : onOpenPlanning(athlete)
                        }
                      >
                        {evaluations.length
                          ? "Ver avaliações"
                          : "Criar planejamento"}
                      </button>
                    </div>
                  </article>
                ),
              )}
            </div>
          </section>
        </>
      )}
    </section>
  );
}
