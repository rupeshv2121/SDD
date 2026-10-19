# 1.0 Introduction

## 1.1 Background and Context

CampusCure is a web-based platform that brings two everyday campus activities into one system: resolving academic doubts and managing institutional complaints. Students post academic questions to a moderated community where peers and faculty answer them. Students also report classroom and facility problems (a broken fan, a faulty projector, an unreliable network) and track them until they are fixed.

The system began as the team's Minor Project. That version provided four-role access control, a doubt-and-answer community with faculty moderation, and a complaint workflow with assignment, student confirmation and escalation. The Major Project extends the same codebase. It adds an intelligence layer (semantic search, AI-drafted answers, a chatbot, automated complaint intake and image-based doubt entry), along with the security, notification and platform capabilities a deployable campus system needs. This document describes the design of the system as it exists in the repositories on the date of this document. It records which parts come from the Minor Project and which were added or are still pending in the Major Project.

## 1.2 Problem Statement

Academic doubts are commonly raised in classrooms, messaging groups and email threads, where answers are hard to find again and the same questions are asked repeatedly. Facility complaints are often reported verbally or in registers, with no record of who is responsible, how long resolution takes, or whether the student agrees that the problem was fixed.

The Minor Project addressed the record-keeping problem. Four limitations remained, and the Major Project targets them:

1. Similar-doubt suggestions relied on keyword overlap. They missed questions that ask the same thing in different words.
2. Faculty had to answer every repeated question by hand, even when an approved answer to a similar question already existed.
3. Students had to classify complaints themselves, admins had to choose an assignee from an unranked list, and duplicate reports of the same fault were not detected.
4. Handwritten or printed questions had to be retyped, which is slow and error-prone for formulae and diagrams.

## 1.3 Objectives

**Objectives carried over from the Minor Project**

- Provide a single platform for academic doubts and institutional complaints with role-specific access for Student, Faculty, Admin and Super Admin.
- Maintain a moderated doubt community in which faculty approve or reject student answers.
- Support the complaint lifecycle: raising, assignment, progress, student confirmation of the fix, escalation and resolution.
- Notify users of relevant events and give each role a dashboard.

**Objectives added in the Major Project**

- Find related doubts by meaning, not just by keywords, using hybrid retrieval (keyword, full-text and vector search).
- Draft answers from previously approved answers, with faculty review before anything is published.
- Offer a conversational assistant that answers questions about the user's own records and the doubt base.
- Turn a free-text complaint description into structured fields, detect duplicate reports and rank suitable assignees.
- Let students submit a doubt from a photograph, with a review-and-edit step.
- Add security and compliance measures: rate limiting, refresh-token rotation, two-step verification, encrypted face templates, an audit log, and consent and data-rights handling.
- Add notification channels (email, Telegram, browser push), SLA-based escalation, an installable offline-capable client and Hindi language support for the complaint journey.

## 1.4 Intended Users and Stakeholders

Table 1.1: User roles

| Role | Description | Principal activities |
|---|---|---|
| Student | Enrolled student (`Role.STUDENT`) | Posts and answers doubts, accepts answers, raises and tracks complaints, confirms or rejects resolutions, uses the assistant chatbot |
| Faculty / Staff | Teaching or non-teaching staff (`Role.FACULTY`); `FacultyProfile.isTeaching` distinguishes the two | Answers doubts, moderates student answers, reviews AI drafts, works on assigned complaints |
| Admin | Administrator (`Role.ADMIN`, `AdminLevel.NORMAL`) | Approves registrations, assigns complaints, overrides statuses, views statistics |
| Super Admin | Highest authority (`Role.SUPER_ADMIN`) | Handles escalated complaints, manages admins and system settings, reviews the audit log |

Other stakeholders are the department administration that owns complaint resolution, the project supervisor, and the external service providers listed in Section 1.10.

## 1.5 Scope

**In scope:** academic doubt posting, answering, moderation and search; complaint filing, assignment, tracking, confirmation, feedback and escalation; AI-assisted retrieval, drafting, intake and transcription; notifications; dashboards and statistics; user, profile and settings administration; security, audit and privacy functions.

**Out of scope** (recorded as cut decisions in `docs/ROADMAP.md`): fee collection, payroll, hostel administration and ERP integration; an assignments or grading system; a searchable student directory; WhatsApp notifications (deferred because the WhatsApp Business API requires a verified business entity and paid message templates); a public leaderboard of faculty performance; and full offline write synchronisation.

## 1.6 Evolution from Minor Project to Major Project

The distinction below is based on the repositories. Minor Project features appear in the database migrations dated February to April 2026 (for example `add_doubt_moderation`, `add_complaint_escalation_fields`, `simplify_complaint_statuses`). The roadmap's baseline statement records the Minor Project scope as "4 roles, doubts/answers/upvotes/moderation, complaints w/ escalation + feedback, in-app notifications, face login". Major Project features are specified as feature specifications `CC-00` to `CC-72` under `campus_cure_backend/docs/specs`, and their migrations are dated September to October 2026.

Table 1.2: Evolution by area

| Area | Minor Project (inherited) | Major Project (added or changed) |
|---|---|---|
| Architecture | React SPA, Express REST API with four controllers, PostgreSQL through Prisma, deployed on Vercel | Service layer extracted from controllers (CC-72); background jobs on Vercel Cron; provider interfaces for AI services |
| Authentication | Email/password login with JWT; face login by searching all users (1:N) for a matching descriptor | Refresh-token rotation (CC-01b); rate limiting and security headers (CC-01); face login made a second factor with encrypted templates (CC-60); TOTP and recovery codes (CC-62); email OTP (CC-63) |
| Doubt community | Doubts, answers, upvotes, views, faculty moderation, accepted answers, edit history, keyword similar-doubt suggestions | Hybrid semantic search (CC-11); AI answer drafts (CC-12); tags vocabulary (CC-20); bookmarks (CC-21); code highlighting (CC-22); rich text and math (CC-23); attachments (CC-24); reputation (CC-25); image-based doubts (CC-50) |
| Complaints | Categories, assignment with history, six-state lifecycle, student confirmation and rejection, Super Admin reassignment, feedback | Free-text intake (CC-14); duplicate detection (CC-13); staff-directory routing (CC-27); photo evidence (CC-30); SLA timers and automatic escalation (CC-31) |
| Notifications | In-app notifications, polled by the client | Email outbox (CC-03, CC-40); web push (CC-41); Telegram (CC-42) |
| Platform | Role dashboards with charts | Assistant chatbot (CC-15); faculty statistics (CC-26); audit log (CC-61); DPDP consent and data rights (CC-64); PWA and offline reading (CC-70); Hindi (CC-71); automated test suite (CC-04) |

The Minor Project code was refactored during the Major Project (CC-72), so inherited behaviour is described here as it is implemented today.

## 1.7 Implementation Status Legend

Every function, module and page in this document carries one of the following status labels.

Table 1.3: Status labels

| Label | Meaning |
|---|---|
| **[M]** Minor Project | Implemented in the Minor Project and retained (possibly refactored) |
| **[J]** Major — implemented | Implemented during the Major Project; the specification is marked shipped or implemented, and automated tests exist |
| **[J\*]** Major — implemented, pending check | Code complete, but the specification or `docs/MANUAL-CHECKLIST.md` lists an outstanding manual check, a missing production setting, or an external dependency (such as an email domain) |
| **[P]** Planned or partial | Not yet implemented, or implemented only in part |

## 1.8 Practical Applications

- **Departmental doubt clearing:** a searchable record of questions and faculty-verified answers that can be reused across semesters.
- **Facility management:** complaints carry a location and priority, go to the staff member who handles that category, and are escalated if they stay unresolved.
- **Accountability:** assignment history, rejection history, SLA deadlines and an audit log show who did what and when.
- **Accessibility:** photo-based doubt entry, Hindi for non-teaching staff filing complaints, and an installable app that keeps working on poor connectivity.

## 1.9 Expected Outcomes

- Fewer repeated questions, because semantically similar doubts are suggested before a new doubt is posted.
- Less faculty effort, because grounded drafts can be approved or edited instead of written from scratch.
- Faster complaint routing, through structured intake, duplicate warnings and ranked assignees.
- Measurable AI behaviour, using the evaluation scripts in the repository (`evalRetrieval.ts`, `evalIntake.ts`, `calibrateDuplicateThreshold.ts`). Their results belong in the project report, not in this design document.

## 1.10 Technology Stack

Table 1.4: Technologies by layer

| Layer | Technology | Status |
|---|---|---|
| Client | React 18, TypeScript, Vite 7, React Router 6, TanStack Query 5, Axios, Tailwind CSS 4, shadcn/ui (Radix UI), Ant Design 6, Recharts, React Hook Form with Zod, face-api.js | [M] |
| Client additions | TipTap editor, Shiki code highlighting, KaTeX, Workbox service worker (vite-plugin-pwa), i18next | [J] |
| Server | Node.js 24, Express 5, TypeScript, jsonwebtoken, bcrypt | [M] |
| Server additions | helmet, express-rate-limit, sanitize-html, web-push | [J] |
| Data | PostgreSQL on Supabase, accessed through Prisma ORM 7 with versioned migrations | [M] |
| Retrieval and storage | pgvector (`vector(384)`, HNSW index), PostgreSQL full-text search, Supabase Storage | [J] |
| AI services | HuggingFace Inference (`sentence-transformers/all-MiniLM-L6-v2`), Groq (`openai/gpt-oss-120b` for chat, `qwen/qwen3.8-27b` for vision), Mistral (fallback); model ids are configurable | [J] |
| Messaging | Resend (email), Telegram Bot API, Web Push with VAPID | [J\*] |
| Hosting | Vercel: static client, serverless API (`api/index.ts`) and a daily cron job | [M] / [J] |
| Testing | Vitest, Supertest, Testing Library | [J] |

## 1.11 Design Principles

The source code and specifications consistently apply five principles. Later sections refer back to them.

1. **The server enforces authorization.** Every protected route passes `authenticate` and `authorize(...roles)` middleware. The client's route guards only affect the user interface.
2. **AI is assistive and never the last step.** Drafts, intake suggestions, transcriptions, duplicate warnings and assignee rankings are proposals that a person accepts, edits or rejects.
3. **Graceful degradation.** No retriever or provider is load-bearing. If embedding fails, search falls back to keyword and full-text results. If the LLM fails, intake returns the rules result. Users can always enter information manually.
4. **Asynchronous AI work.** Embedding, draft generation and message delivery run through database-backed queues (`EmbeddingJob`, `EmailOutbox`) that are drained in the background, so a slow provider never delays a user action.
5. **Provider abstraction.** Embedding, chat and vision providers sit behind the interfaces in `src/services/ai/types.ts`. Model ids come from environment variables, and every stored vector records the model that produced it.

## 1.12 Basis of this Document

The design was established by inspecting both repositories: `campus_cure_backend` (routes, controllers, services, middleware, `prisma/schema.prisma`, migrations and `docs/`) and `CampusCure_Frontend` (routes in `App.tsx`, pages, layouts, API modules, service worker). On 17 October 2026 the automated test suites passed in full: 1,014 backend tests in 56 files and 69 frontend tests in 7 files. Both suites run with a mocked database, so they verify logic, not the production deployment. Secrets and environment values are not reproduced here; configuration is identified only by variable name.
