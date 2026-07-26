export default function PlaceholderPage({ eyebrow = "RUNCORE", title, description }) {
  return (
    <section className="placeholder-page">
      <p className="eyebrow">{eyebrow}</p>
      <h2>{title}</h2>
      <p className="muted">{description}</p>
    </section>
  );
}
