# Deliverables checklist (requirements Section 19)

Use this list when packaging the capstone submission.

- [ ] **Source code** — this repository (`apps/web`, `apps/api`, `data/samples`, `docs/`).  
- [ ] **Architecture diagram** — see [architecture.md](architecture.md) (Mermaid); export to PNG/SVG for slides if required.  
- [ ] **README / setup guide** — [README.md](../README.md) (local + Docker paths).  
- [ ] **Demo video** — record separately; script aligned with requirements Section 22 sample flow.  
- [ ] **Test dataset** — [data/samples](../data/samples) plus optional extra PDFs/runbooks.  
- [ ] **Final presentation** — outside repo.  
- [ ] **Transition metrics dashboard** — `GET /api/v1/dashboard/summary` + forthcoming Next.js dashboard views.  
- [ ] **AI feature demonstration** — show stub mode (no key) vs live OpenAI mode (with key).

## Evaluation alignment (requirements Section 20)

| Criterion | Where demonstrated |
|-----------|-------------------|
| Functional implementation | Sessions, documents, chat, dashboard routes |
| AI / GenAI usage | `services/llm.py`, `services/rag.py`, OpenAPI `/process-ai` and `/chat` |
| UI/UX | `apps/web` (extend beyond landing page in later weeks) |
| Documentation | `README.md`, `docs/architecture.md`, this checklist |
