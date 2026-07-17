# RunCore Web — como rodar localmente

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
- Endpoints atuais: `GET/POST /api/athletes`, `GET/PUT/DELETE /api/athletes/{id}`

## Frontend (React + Vite)

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

- App disponível em `http://localhost:5173`
- `VITE_API_URL` no `.env` aponta pro backend (padrão: `http://localhost:8000`)

## Status (Sprint 0 — esqueleto)

- [x] API expõe CRUD completo de atletas reaproveitando o `AthleteRepository`
- [x] Tela React lista, busca, cria e remove atletas
- [ ] Editar atleta pela web
- [ ] Demais módulos (avaliações, planejamento, dashboard)

## Estrutura nova

```
src/api/            # FastAPI: main.py, schemas.py, routers/
frontend/           # React (Vite)
```
