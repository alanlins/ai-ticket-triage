# ai-ticket-triage

Triagem de tickets de suporte com a API do Claude: FastAPI + SQLAlchemy/Alembic + PostgreSQL 16, tudo em Docker. Detalhes: [README.md](README.md).

## Ambiente

- **Runtime**: Docker (Python 3.12 dentro da imagem). Fora do Docker: Python ≥ 3.12 e `pip install -r requirements.txt`.
- **Variáveis**: `cp .env.example .env` e preencher `ANTHROPIC_API_KEY` (opcional: `ANTHROPIC_MODEL`, `DATABASE_URL`). O `.env` real não vem no clone — **nunca** commite a chave.
- **Subir**: `docker compose up --build` → http://localhost:8000 (as migrações Alembic rodam sozinhas). Parar: `docker compose down`.
- **Testes**: `pytest` (`pytest.ini` na raiz; `test.db` local é artefato de teste).
- Portas: 8000 (API) e 5432 (Postgres) — conflitam com `CRAUD-AI`; suba um de cada vez.

## Regras

- Sem caminhos absolutos de máquina em arquivos versionados; regras comuns em `$PROJECTS_ROOT/CLAUDE.md`.
- Segredos e `.env` **não vêm no `git clone`** — ver `workspace/docs/segredos-e-arquivos-fora-do-git.md`.
- Commit/push só quando o usuário pedir.
