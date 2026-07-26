# RunCore Web — como rodar localmente

> **Atualizado:** o backend canônico agora está em `D:\RunCore2\src`.
> Use o guia em `D:\RunCore2\docs\WEB_SETUP.md`; não execute mais
> `RunCore-web\src` como uma API independente.

Versão web do RunCore, construída em cima da mesma lógica de negócio do app
desktop (`core/`, `models/`, `repositories/`, `database/`). O app desktop
(PySide6) continua funcionando normalmente e não foi alterado.

## Backend (FastAPI)

```bash
pip install -r requirements.txt
cd src
uvicorn api.main:app --reload --port 8000
```

- API disponível em `http://localhost:8000`
- Docs interativas (Swagger) em `http://localhost:8000/docs`
- Endpoints atuais:
  - `GET/POST /api/athletes`, `GET/PUT/DELETE /api/athletes/{id}`
  - `GET/POST /api/athletes/{id}/evaluations`, `PUT/DELETE /api/evaluations/{id}` (calcula VDOT automaticamente)

## Frontend (React + Vite)

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

- App disponível em `http://localhost:5173`
- `VITE_API_URL` no `.env` aponta pro backend (padrão: `http://localhost:8000`)

## Status

- [x] Sprint 0 — API expõe CRUD completo de atletas reaproveitando o `AthleteRepository`
- [x] Sprint 0 — Tela React lista, busca, cria e remove atletas
- [x] Sprint 1 — Perfil do atleta: histórico de avaliações + cálculo automático de VDOT
      (reaproveita `EvaluationRepository` e `VdotService` como estão)
- [ ] Editar atleta / avaliação pela web
- [ ] Demais módulos (planejamento de treino, dashboard)

## Estrutura nova

```
src/api/            # FastAPI: main.py, schemas.py, routers/
frontend/           # React (Vite)
```
