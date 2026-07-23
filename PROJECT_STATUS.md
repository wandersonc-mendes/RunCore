RunCore — Status do Projeto

Última atualização: 23/07/2026

Visão geral

O RunCore possui duas interfaces que compartilham parte da mesma base de código:

Aplicativo desktop em PySide6.

Aplicação web com FastAPI e React.

A versão web está funcional para demonstração e atualmente utiliza o banco SQLite localizado em:

D:\RunCore3\src\runcore.db

Branch de desenvolvimento atual:

feature/web-version

Repositório:

wandersonc-mendes/RunCore

Estado funcional atual

Autenticação

Cadastro de treinador.

Login de treinador.

Login de atleta.

Validação de perfil selecionado no login.

Bloqueio de atleta aguardando aprovação.

Consulta do usuário autenticado em /api/auth/me.

Convites e aprovação

Geração de link de convite.

Pré-cadastro do atleta por convite.

Listagem de cadastros aguardando aprovação.

Aprovação pelo treinador.

Ativação do usuário aprovado.

Criação do perfil esportivo do atleta.

Vínculo entre treinador, usuário e atleta.

Atletas

Listagem de atletas.

Cadastro de atleta.

Perfil do atleta.

Vínculo users.id -> athletes.user_id.

Vínculo coach_user_id.

Compatibilidade com registros antigos.

Avaliações

Cadastro de avaliação.

Histórico de avaliações.

Cálculo de VDOT.

Uso da avaliação mais recente no planejamento.

Exibição no perfil do atleta.

Planejamento e planilha

Criação de planejamento.

Regeneração de planejamento.

Atualização de sessões.

Exibição da planilha no painel do aluno.

Exibição da semana atual.

Exibição das fases do ciclo.

Exibição dos passos de cada treino.

Suporte a scheduled_date.

Suporte a distance_unit.

Metas

Listagem de metas.

Cadastro de metas.

Remoção de metas.

Exibição no painel do aluno.

Strava

Status da integração.

OAuth.

Callback.

Persistência da integração.

Sincronização de atividades.

Listagem de atividades.

Detalhes da atividade.

Feedback da atividade.

Carga de treinamento.

Estatísticas resumidas no painel do aluno.

Perfis

Perfil do aluno.

Consulta de perfil pelo treinador.

Dados complementares do atleta.

Rotas principais do backend

Autenticação

POST /api/auth/register
POST /api/auth/login
GET  /api/auth/me

Atletas

GET    /api/athletes
POST   /api/athletes
GET    /api/athletes/{athlete_id}
PUT    /api/athletes/{athlete_id}
DELETE /api/athletes/{athlete_id}

Avaliações

GET    /api/athletes/{athlete_id}/evaluations
POST   /api/athletes/{athlete_id}/evaluations
PUT    /api/evaluations/{evaluation_id}
DELETE /api/evaluations/{evaluation_id}

Convites

GET  /api/coach/invitations
POST /api/coach/invitations
POST /api/coach/invitations/{invitation_id}/approve

Planejamento

GET   /api/athletes/{athlete_id}/training
POST  /api/athletes/{athlete_id}/training
POST  /api/athletes/{athlete_id}/training/regenerate
PATCH /api/athletes/{athlete_id}/training/sessions/{session_id}
GET   /api/student/training

Metas

GET    /api/goals
POST   /api/goals
DELETE /api/goals/{goal_id}

Perfil

GET /api/student/profile
GET /api/student/profile/athletes/{athlete_id}

Strava

GET  /api/integrations/strava/status
GET  /api/integrations/strava/connect
GET  /api/integrations/strava/callback
GET  /api/integrations/strava/activities
GET  /api/integrations/strava/activities/{activity_id}/details
GET  /api/integrations/strava/activities/{activity_id}/feedback
PUT  /api/integrations/strava/activities/{activity_id}/feedback
POST /api/integrations/strava/sync
GET  /api/integrations/athletes/{athlete_id}/training-load

Arquitetura atual

Backend

src/
├── api/
│   ├── routers/
│   ├── dependencies.py
│   ├── main.py
│   ├── schemas.py
│   └── security.py
├── core/
├── database/
├── models/
├── repositories/
└── ui/

Frontend

frontend/
├── public/
└── src/
    ├── api.js
    ├── App.jsx
    ├── LoginScreen.jsx
    ├── StudentPortal.jsx
    ├── AthleteProfileView.jsx
    └── ProfilePanel.jsx

Fonte de autenticação

A autenticação atual deve usar exclusivamente:

api.security
api.routers.auth.get_current_user

O arquivo api.dependencies.py existe como camada de compatibilidade para os módulos antigos, mas deve delegar a autenticação para get_current_user.

Não criar um segundo mecanismo de JWT ou autenticação paralela.

Fonte de integração Strava

A integração funcional está concentrada em:

src/api/routers/integrations.py
src/models/external_integration.py
src/models/imported_activity.py
src/models/activity_feedback.py
src/repositories/integration_repository.py
src/repositories/activity_repository.py
src/repositories/activity_feedback_repository.py

Não recriar os arquivos removidos:

src/api/routers/strava.py
src/services/strava_service.py
src/models/strava_connection.py
src/repositories/strava_connection_repository.py

Arquivos removidos durante a limpeza

Routers

src/api/routers/strava.py

Models

src/models/coach_invitation.py
src/models/strava_connection.py

Repositories

src/repositories/strava_connection_repository.py

Services

src/services/strava_service.py
src/services/physiology/imc_service.py

A implementação de IMC utilizada pelo sistema permanece em:

src/core/physiology/imc_service.py

Models ativos

activity_feedback.py
athlete.py
athlete_details.py
athlete_profile.py
coach_athlete.py
evaluation.py
external_integration.py
goal.py
imported_activity.py
invitation.py
training.py
training_session.py
training_step.py
user.py

Os models athlete_details.py, athlete_profile.py e coach_athlete.py permanecem por compatibilidade com repositories e dados antigos.

Repositories ativos

access_repository.py
activity_feedback_repository.py
activity_repository.py
athlete_details_repository.py
athlete_repository.py
evaluation_repository.py
goal_repository.py
integration_repository.py
invitation_repository.py
training_repository.py
training_session_repository.py
training_step_repository.py
user_repository.py

Todos possuem referência ativa no backend, no core ou no aplicativo desktop.

Regras de desenvolvimento

O GitHub é a fonte de verdade.

Antes de iniciar uma alteração, o repositório deve estar limpo.

Alterar apenas um módulo por sprint.

Entregar arquivos completos, nunca ajustes fragmentados.

Testar login, treinador e aluno após mudanças estruturais.

Testar Strava após mudanças em autenticação ou banco.

Testar planilha após mudanças em models de treinamento.

Fazer commit apenas quando o módulo estiver funcional.

Não misturar autenticação antiga e nova.

Não duplicar models, repositories, routers ou services.

Checklist mínimo antes de cada commit

[ ] python -c "import sys; sys.path.insert(0,'src'); import api.main"
[ ] Backend inicializa sem traceback.
[ ] /health retorna 200.
[ ] Login treinador funciona.
[ ] Login atleta funciona.
[ ] Painel do treinador carrega.
[ ] Painel do aluno carrega.
[ ] /api/student/training retorna 200.
[ ] /api/goals retorna 200.
[ ] /api/integrations/strava/status retorna 200.
[ ] Sincronização do Strava continua funcionando.
[ ] git status foi revisado.

Pendências técnicas

Alta prioridade

Criar migrations formais para todas as alterações de schema.

Parar de depender de ajustes manuais no SQLite.

Definir estratégia para tabelas antigas e não utilizadas.

Consolidar o caminho oficial do banco.

Adicionar testes automatizados básicos para autenticação e rotas críticas.

Média prioridade

Revisar campos e relacionamentos dos models legados.

Auditar arquivos de core/ com cuidado por serem compartilhados com o desktop.

Organizar scripts administrativos.

Atualizar documentação de instalação.

Padronizar codificação UTF-8 dos arquivos antigos.

Corrigir textos com caracteres corrompidos.

Baixa prioridade

Remover tabelas obsoletas somente por migration.

Revisar código do aplicativo desktop não usado na versão web.

Criar cobertura de testes para geração de planejamento.

Criar relatório automático de aderência treino planejado x executado.

Próximos passos recomendados

Commitar este documento.

Auditar scripts da pasta scripts/.

Auditar arquivos temporários e backups fora do repositório.

Revisar migrations.

Criar teste automatizado de smoke test para as rotas principais.

Retomar novas funcionalidades somente após a estabilização.

Ponto estável atual

O estado atual é adequado para demonstração, contendo:

painel do treinador;

painel do aluno;

convites e aprovação;

avaliações;

planejamento;

metas;

integração completa com Strava;

sincronização e exibição de atividades.

Este documento deve ser atualizado sempre que uma funcionalidade for adicionada, removida, quebrada ou restaurada.