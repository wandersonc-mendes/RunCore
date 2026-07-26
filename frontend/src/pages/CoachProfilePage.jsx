import { useEffect, useMemo, useState } from "react";

import "./CoachProfilePage.css";


function storageKey(user) {
  return `runcore_profile_photo_${user?.id || user?.email || "coach"}`;
}


function initials(name = "") {
  return name
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase())
    .join("") || "RC";
}


export default function CoachProfilePage({ user }) {
  const key = useMemo(() => storageKey(user), [user]);
  const [photo, setPhoto] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    setPhoto(localStorage.getItem(key) || "");
  }, [key]);

  function notify(nextPhoto) {
    window.dispatchEvent(
      new CustomEvent("runcore-profile-photo-changed", {
        detail: {
          key,
          photo: nextPhoto,
        },
      }),
    );
  }

  function handlePhoto(event) {
    const file = event.target.files?.[0];

    setMessage("");
    setError("");

    if (!file) return;

    if (!["image/jpeg", "image/png", "image/webp"].includes(file.type)) {
      setError("Use uma imagem JPG, PNG ou WEBP.");
      event.target.value = "";
      return;
    }

    if (file.size > 1024 * 1024) {
      setError("A imagem deve ter no máximo 1 MB.");
      event.target.value = "";
      return;
    }

    const reader = new FileReader();

    reader.onload = () => {
      const image = new Image();

      image.onload = () => {
        if (image.width < 300 || image.height < 300) {
          setError(
            "A imagem precisa ter pelo menos 300 × 300 px.",
          );
          event.target.value = "";
          return;
        }

        const size = Math.min(image.width, image.height);
        const offsetX = (image.width - size) / 2;
        const offsetY = (image.height - size) / 2;
        const canvas = document.createElement("canvas");

        canvas.width = 400;
        canvas.height = 400;

        const context = canvas.getContext("2d");

        context.drawImage(
          image,
          offsetX,
          offsetY,
          size,
          size,
          0,
          0,
          400,
          400,
        );

        const nextPhoto = canvas.toDataURL("image/jpeg", 0.86);

        localStorage.setItem(key, nextPhoto);
        setPhoto(nextPhoto);
        setMessage("Foto do perfil atualizada.");
        notify(nextPhoto);
        event.target.value = "";
      };

      image.onerror = () => {
        setError("Não foi possível ler essa imagem.");
        event.target.value = "";
      };

      image.src = String(reader.result);
    };

    reader.onerror = () => {
      setError("Não foi possível carregar essa imagem.");
      event.target.value = "";
    };

    reader.readAsDataURL(file);
  }

  function removePhoto() {
    localStorage.removeItem(key);
    setPhoto("");
    setMessage("Foto removida.");
    setError("");
    notify("");
  }

  return (
    <section className="coach-profile-page">
      <header>
        <div>
          <p className="eyebrow">MEU PERFIL</p>
          <h2>Cadastro do treinador</h2>
          <p>
            Consulte seus dados e defina a foto exibida
            no menu superior.
          </p>
        </div>
      </header>

      <section className="coach-profile-card">
        <div className="coach-profile-photo-column">
          <div className="coach-profile-photo-preview">
            {photo ? (
              <img src={photo} alt="Foto do perfil" />
            ) : (
              <span>{initials(user?.name)}</span>
            )}
          </div>

          <label className="coach-profile-photo-button">
            Escolher foto
            <input
              type="file"
              accept="image/jpeg,image/png,image/webp"
              onChange={handlePhoto}
            />
          </label>

          {photo && (
            <button
              type="button"
              className="btn-ghost"
              onClick={removePhoto}
            >
              Remover foto
            </button>
          )}

          <small>
            Recomendado: imagem quadrada de 400 × 400 px.
            Mínimo de 300 × 300 px, formato JPG, PNG ou WEBP,
            com no máximo 1 MB.
          </small>
        </div>

        <div className="coach-profile-fields">
          <label>
            Nome
            <input value={user?.name || ""} readOnly />
          </label>

          <label>
            E-mail
            <input value={user?.email || ""} readOnly />
          </label>

          <label>
            Perfil de acesso
            <input value="Treinador" readOnly />
          </label>

          <p>
            Nesta etapa, os dados cadastrais permanecem protegidos.
            A edição disponível é apenas da foto do perfil.
          </p>

          {message && (
            <div className="coach-profile-success">
              {message}
            </div>
          )}

          {error && (
            <div className="alert">
              {error}
            </div>
          )}
        </div>
      </section>
    </section>
  );
}
