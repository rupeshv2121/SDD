# 3.0 Functional Partitions

The system is divided into sixteen functional modules. On the server, a module is a group of route files, controllers and services under `campus_cure_backend/src`; on the client, it is a set of pages, components and API modules under `CampusCure_Frontend/src`. Each subsection gives the module's purpose, status and main source locations, its functional block diagram (FBD), and its input and output dependencies. The FBD notation is the same throughout: rectangles are processing blocks, parallelograms are inputs and outputs, cylinders are persistent stores, dashed boxes are external services, and shaded blocks were added in the Major Project.

## 3.1 Module Name: Authentication and Access Control

**Purpose and status.** Verifies identity, issues and rotates sessions, verifies second factors, and enforces role-based authorization on every protected route. Password login, JWT and role checks are [M]; refresh-token rotation, rate limiting, TOTP, hardened face verification and email OTP are [J] (email OTP is [J\*]). **Sources:** `routes/auth.ts`, `controllers/authController.ts`, `controllers/mfaController.ts`, `services/auth/*`, `middleware/auth.ts`, `middleware/rateLimit.ts`.

### 3.1.1 Functional Block Diagram

![Figure 3.1: FBD of the Authentication and Access Control module](images/fbd-auth.png){w=15.5}

Registration creates a pending account. A password login runs first, then a second-factor check if one is enrolled (TOTP takes precedence over face because it has recovery codes). Every path ends in the single session issuer, so no path can mint a token differently from the others. For each later request, `authenticate()` verifies the token and `authorize()` checks the role.

### 3.1.2 Module Dependencies

#### 3.1.2.1 Input Dependencies

| Source | Input data | Purpose |
|---|---|---|
| Client Application Platform (3.16) | Credentials, codes, face descriptors, bearer and refresh tokens | Sign-in, second factor, session refresh |
| User and Profile Management (3.2) | `approvalStatus`, `isActive`, `role` on `User` | Session content and request authorization |
| Notification and Messaging (3.11) | Delivery of email sign-in codes | Email OTP |
| Environment configuration | `JWT_SECRET`, `ACCESS_TOKEN_TTL`, `REFRESH_TOKEN_TTL_DAYS`, `FACE_ENCRYPTION_KEY`, `MFA_ENCRYPTION_KEY` (names only) | Token signing and encryption |

#### 3.1.2.2 Output Dependencies

| Module | Data | Description |
|---|---|---|
| All server modules | `req.user = { id, role, userID, university }` | Identity used for ownership checks and queries |
| Client Application Platform (3.16) | Access token, refresh token, user summary | Stored by the client and attached to API calls |
| Audit, Privacy and Observability (3.15) | Audit events (2FA reset, face template cleared) and the request user id | Audit trail and log context |
| SLA and Scheduled Jobs (3.10) | Expired tokens and challenges | Purged nightly |

## 3.2 Module Name: User and Profile Management

**Purpose and status.** Account approval, activation, role-specific profiles, admin permissions, system settings and the staff directory. [M], except the staff directory and the routing fields on `FacultyProfile` (`staffRole`, `handlesCategories`, `directoryOptIn`), which are [J]. **Sources:** `routes/admin.ts`, `controllers/admin/users.ts`, `controllers/admin/profile.ts`, `controllers/admin/settings.ts`, `controllers/*/profile.ts`, `services/settings/posting.ts`, `routes/staff.ts`, `services/staff/routing.ts`.

### 3.2.1 Functional Block Diagram

![Figure 3.2: FBD of the User and Profile Management module](images/fbd-users.png){w=15}

Approval and account-status changes are written to the audit log. System settings (allowed complaint categories, doubt subjects and departments) are stored as arrays on `AdminProfile`; the posting-settings endpoint gives clients the current values for form validation.

### 3.2.2 Module Dependencies

#### 3.2.2.1 Input Dependencies

| Source | Input data | Purpose |
|---|---|---|
| Authentication and Access Control (3.1) | Caller identity and role | Restricts approval to Admin/Super Admin and settings to Super Admin |
| Client Application Platform (3.16) | Profile forms, approval decisions, settings forms | User-initiated changes |

#### 3.2.2.2 Output Dependencies

| Module | Data | Description |
|---|---|---|
| Authentication and Access Control (3.1) | `approvalStatus`, `isActive` | Account state |
| Academic Doubt Community (3.3) | Allowed doubt subjects | Validates new doubts |
| Complaint Management (3.8) | Allowed complaint categories | Validates new complaints |
| Complaint Intelligence (3.9) | `handlesCategories`, `isTeaching`, `department` | Assignee ranking |
| Dashboards and Analytics (3.14) | User counts by role and status | Admin dashboards |
| Audit, Privacy and Observability (3.15) | Approval and activation events | Audit trail |

## 3.3 Module Name: Academic Doubt Community

**Purpose and status.** Posting, browsing, answering, moderating, accepting, upvoting, bookmarking and editing doubts and answers. Core behaviour is [M]; tags vocabulary, bookmarks, rich text and attachments are [J]/[J\*]. **Sources:** `routes/students.ts`, `routes/faculty.ts`, `controllers/student/doubts.ts`, `controllers/student/answers.ts`, `controllers/faculty/doubts.ts`, `services/doubts/answerReview.ts`, `services/content/sanitize.ts`, `utils/tags.ts`.

### 3.3.1 Functional Block Diagram

![Figure 3.3: FBD of the Academic Doubt Community module](images/fbd-doubts.png){w=15.5}

The validator sanitises rich content and normalises tags before a doubt is stored, and every new doubt queues an embedding request. Student answers enter moderation as `PENDING`; faculty answers are approved immediately. Moderation and acceptance produce reputation events, and answers and acceptances produce notification requests.

### 3.3.2 Module Dependencies

#### 3.3.2.1 Input Dependencies

| Source | Input data | Purpose |
|---|---|---|
| Authentication and Access Control (3.1) | Caller identity and role | Ownership and moderation rights |
| User and Profile Management (3.2) | Allowed subjects | Doubt validation |
| File Storage and Attachments (3.12) | Confirmed attachment ids | Files and inline images on doubts and answers |
| Image Doubt Transcription (3.7) | Prefilled title, description, subject and labels | Photo-based posting (student-confirmed) |
| AI Answer Drafting (3.5) | Approved draft content | Published as a faculty answer with `aiAssisted = true` |

#### 3.3.2.2 Output Dependencies

| Module | Data | Description |
|---|---|---|
| Semantic Search and Embedding (3.4) | `EmbeddingJob` for each new or edited doubt | Keeps vectors current |
| AI Answer Drafting (3.5) | Approved answers and unanswered doubts | Grounding sources and draft candidates |
| Assistant Chatbot (3.6) | The user's doubts and answers | Tool results |
| Notification and Messaging (3.11) | `DOUBT_ANSWER`, `DOUBT_ACCEPTED`, `ANSWER_UPVOTED` events | User notifications |
| Reputation and Faculty Statistics (3.13) | Accept, upvote and approve events | Points and statistics |
| Dashboards and Analytics (3.14) | Doubt counts by subject | Subject-wise analytics |

## 3.4 Module Name: Semantic Search and Embedding

**Purpose and status.** Maintains vector representations of doubts and complaints and answers similar-doubt queries with hybrid retrieval. [J]. **Sources:** `services/ai/embeddingWorker.ts`, `services/ai/embeddings/*`, `repositories/embeddingRepository.ts`, `repositories/searchRepository.ts`, `services/search/hybridSearch.ts`, `services/search/keywordRetriever.ts`, `services/search/rrf.ts`.

### 3.4.1 Functional Block Diagram

![Figure 3.4: FBD of the Semantic Search and Embedding module](images/fbd-search.png){w=15.5}

The upper path shows asynchronous indexing: user actions only add a job, and the worker embeds jobs in batches. The lower path is the query: three retrievers run independently and are fused with weighted Reciprocal Rank Fusion [17]. The keyword retriever is the Minor Project baseline, kept both as a fallback and as the comparison point for evaluation.

### 3.4.2 Module Dependencies

#### 3.4.2.1 Input Dependencies

| Source | Input data | Purpose |
|---|---|---|
| Academic Doubt Community (3.3) | Doubt ids, titles, descriptions | Indexing and retrieval |
| Complaint Management (3.8) | Complaint ids and text | Indexing for duplicate detection |
| SLA and Scheduled Jobs (3.10) | Daily drain trigger | Processes the queue |
| HuggingFace Inference (external) | 384-dimensional vectors | Embedding model `all-MiniLM-L6-v2` [18] |

#### 3.4.2.2 Output Dependencies

| Module | Data | Description |
|---|---|---|
| Academic Doubt Community (3.3) | Ranked similar doubts with matched keywords | Suggestions while a student types |
| AI Answer Drafting (3.5) | Similar answered doubts with similarity scores | Grounding sources |
| Assistant Chatbot (3.6) | Search results for `searchDoubts` | Tool output |
| Complaint Intelligence (3.9) | `Complaint.embedding` vectors | Duplicate detection and clustering |

## 3.5 Module Name: AI Answer Drafting

**Purpose and status.** Produces retrieval-grounded draft answers for doubts no one has answered, for faculty review. [J]. **Sources:** `services/ai/answerDraft.ts`, `controllers/faculty/drafts.ts`, `services/ai/chat/index.ts` (provider chain).

### 3.5.1 Functional Block Diagram

![Figure 3.5: FBD of the AI Answer Drafting module](images/fbd-draft.png){w=15.5}

Students get the first 24 hours to answer before a draft is considered. If no approved answer is similar enough, no draft is produced, so the model never writes without grounding. Students never see a draft; only an approved draft is published, under the approving faculty member's name and flagged as AI-assisted.

### 3.5.2 Module Dependencies

#### 3.5.2.1 Input Dependencies

| Source | Input data | Purpose |
|---|---|---|
| Academic Doubt Community (3.3) | Unanswered doubts; approved answers | Candidates and sources |
| Semantic Search and Embedding (3.4) | Similar doubts with similarity scores | Grounding retrieval |
| SLA and Scheduled Jobs (3.10) | Daily trigger | Batch generation |
| Groq / Mistral (external) | Completion text | Draft generation |

#### 3.5.2.2 Output Dependencies

| Module | Data | Description |
|---|---|---|
| Academic Doubt Community (3.3) | Approved draft as an `Answer` (`aiAssisted`, `APPROVED`) | Published answer; doubt becomes `ANSWERED` |
| Client Application Platform (3.16) | Draft text, sources, model | Faculty review panel |
| Notification and Messaging (3.11) | Answer notification | Sent to the doubt author after approval |

## 3.6 Module Name: Assistant Chatbot

**Purpose and status.** A conversational assistant for students that answers questions about their own complaints, doubts, answers and notifications, and searches the doubt base. [J]. **Sources:** `routes/chat.ts`, `services/ai/chat/assistant.ts`, `services/ai/chat/tools.ts`, `services/ai/chat/openaiCompatible.ts`, `components/chat/AssistantWidget.tsx`.

### 3.6.1 Functional Block Diagram

![Figure 3.6: FBD of the Assistant Chatbot module](images/fbd-chat.png){w=15.5}

The model never queries the database directly. It requests named tools, and the tool executor runs them using the user id from the verified token. This retrieval-through-tools design grounds replies in the user's real records [19] and prevents a crafted prompt from reading another user's data.

### 3.6.2 Module Dependencies

#### 3.6.2.1 Input Dependencies

| Source | Input data | Purpose |
|---|---|---|
| Authentication and Access Control (3.1) | `req.user.id`, role `STUDENT` | Tool scoping and access |
| Complaint Management (3.8), Academic Doubt Community (3.3), Notification and Messaging (3.11) | The user's rows (at most 10 per tool) | Tool results |
| Semantic Search and Embedding (3.4) | Hybrid search results | `searchDoubts` tool |
| Groq (external) | Tool calls and final text | Language model |

#### 3.6.2.2 Output Dependencies

| Module | Data | Description |
|---|---|---|
| Client Application Platform (3.16) | Reply text labelled as AI | Shown in the assistant widget |

## 3.7 Module Name: Image Doubt Transcription

**Purpose and status.** Reads a photographed question into editable doubt fields. It replaces the optical character recognition (OCR) step proposed in the original plan with a vision-language model, which handles handwriting, formulae and diagrams in one call. [J\*]. **Sources:** `services/vision/extractDoubt.ts`, `services/ai/vision/*`, `pages/student/DoubtCommunity.tsx` (`handleReadFromImage`).

### 3.7.1 Functional Block Diagram

![Figure 3.7: FBD of the Image Doubt Transcription module](images/fbd-vision.png){w=15.5}

The module never writes to the database. Its output is a draft the student reviews in the normal doubt form, and the original image stays attached so readers can compare the transcription with the source.

### 3.7.2 Module Dependencies

#### 3.7.2.1 Input Dependencies

| Source | Input data | Purpose |
|---|---|---|
| File Storage and Attachments (3.12) | Attachment id and stored bytes | Image to read |
| User and Profile Management (3.2) | Allowed subjects | Validates the suggested subject |
| Groq / Mistral vision (external) | JSON transcription | Model output |

#### 3.7.2.2 Output Dependencies

| Module | Data | Description |
|---|---|---|
| Academic Doubt Community (3.3) | `{ title, description, subject, labels, legible, model, provider }` | Prefilled form; on submission the doubt records `transcribedFromImage` and `transcriptionModel` |

## 3.8 Module Name: Complaint Management

**Purpose and status.** Filing, assignment, status lifecycle, student confirmation, feedback and Super Admin escalation handling. [M]; photo evidence and SLA deadlines added in [J]. **Sources:** `routes/students.ts`, `routes/faculty.ts`, `routes/admin.ts`, `controllers/*/complaints.ts`, `services/complaints/filing.ts`, `services/complaints/assignment.ts`, `services/complaints/lifecycle.ts`, `services/storage/resolutionEvidence.ts`, `utils/complaintAssignmentHistory.ts`.

### 3.8.1 Functional Block Diagram

![Figure 3.8: FBD of the Complaint Management module](images/fbd-complaints.png){w=15.5}

Each block enforces its own rules: filing validates and writes in one transaction; assignment appends to the history; the lifecycle service applies the allowed-target table for staff and Admins; the verdict service accepts only the owning student; and the escalation handler accepts only escalated complaints. All state-changing blocks emit notification requests. The full state machine appears in Section 4.4 (Figure 4.12).

### 3.8.2 Module Dependencies

#### 3.8.2.1 Input Dependencies

| Source | Input data | Purpose |
|---|---|---|
| Authentication and Access Control (3.1) | Caller identity and role | Ownership and role rules |
| User and Profile Management (3.2) | Allowed categories; faculty list | Validation and assignee choice |
| Complaint Intelligence (3.9) | Suggested fields, duplicates, ranked candidates | Advisory input to the student and Admin |
| File Storage and Attachments (3.12) | Complaint and resolution photo ids | Evidence |
| SLA and Scheduled Jobs (3.10) | Escalation updates | Automatic escalation |

#### 3.8.2.2 Output Dependencies

| Module | Data | Description |
|---|---|---|
| Notification and Messaging (3.11) | `COMPLAINT_ASSIGNED`, `COMPLAINT_STATUS_UPDATE` events | Notifies students, assignees and Super Admins |
| Semantic Search and Embedding (3.4) | Embedding job per complaint | Duplicate detection |
| SLA and Scheduled Jobs (3.10) | `slaDueAt`, `priority`, `status` | Deadline tracking |
| Assistant Chatbot (3.6) | The student's complaints | Tool results |
| Dashboards and Analytics (3.14), Reputation and Faculty Statistics (3.13) | Status, timing and feedback fields | Statistics |
| Audit, Privacy and Observability (3.15) | Assignment and status events | Audit trail |

## 3.9 Module Name: Complaint Intelligence

**Purpose and status.** Advisory analysis of complaints: free-text intake, duplicate detection and clustering, and assignee ranking. [J]. **Sources:** `services/intake/parseComplaint.ts`, `services/intake/rules.ts`, `data/block_classroom.json`, `services/search/duplicateComplaints.ts`, `services/search/duplicateClusters.ts`, `services/staff/routing.ts`.

### 3.9.1 Functional Block Diagram

![Figure 3.9: FBD of the Complaint Intelligence module](images/fbd-intel.png){w=15.5}

All three outputs are suggestions. Intake uses the rules first, so the common case costs nothing and is deterministic; the LLM is used only when the rules cannot name a category. Duplicate detection requires the same location, because two faults in different rooms can read alike. Ranking orders staff by how well they match the category and then by workload; it never assigns automatically.

### 3.9.2 Module Dependencies

#### 3.9.2.1 Input Dependencies

| Source | Input data | Purpose |
|---|---|---|
| Client Application Platform (3.16) | Free text; draft complaint location | Intake and duplicate checks |
| Semantic Search and Embedding (3.4) | Complaint vectors | Similarity |
| User and Profile Management (3.2) | Staff `handlesCategories`, `isTeaching`, `department` | Ranking |
| Complaint Management (3.8) | Open complaints and assignee workload | Clusters and tie-breaking |
| Groq (external) | Extracted fields | Intake fallback |

#### 3.9.2.2 Output Dependencies

| Module | Data | Description |
|---|---|---|
| Complaint Management (3.8) | Suggested fields, duplicate candidates, ranked assignees | Shown to the student and Admin for a decision |
| Dashboards and Analytics (3.14) | Duplicate clusters | Admin complaint page |

## 3.10 Module Name: SLA and Scheduled Jobs

**Purpose and status.** Runs the daily maintenance pipeline and the SLA escalation ladder. [J]. **Sources:** `vercel.json` (`crons`), `routes/internal.ts`, `services/sla/policy.ts`, `services/sla/escalation.ts`, `services/privacy/retention.ts`.

### 3.10.1 Functional Block Diagram

![Figure 3.10: FBD of the SLA and Scheduled Jobs module](images/fbd-jobs.png){w=15.5}

Vercel serverless functions cannot keep long-running timers, so all periodic work happens in one daily invocation. The SLA sweep runs before the outbox drain so that escalation notices go out in the same run. Each step is isolated: one failure is recorded and the remaining steps still run. The same steps can be triggered individually through `/api/internal/*`, protected by a shared secret.

### 3.10.2 Module Dependencies

#### 3.10.2.1 Input Dependencies

| Source | Input data | Purpose |
|---|---|---|
| Vercel Cron (external) | HTTP call with a bearer cron secret | Trigger |
| Complaint Management (3.8) | Overdue and unconfirmed complaints | SLA sweep |
| Semantic Search and Embedding (3.4), AI Answer Drafting (3.5), Notification and Messaging (3.11), File Storage (3.12), Authentication (3.1) | Pending jobs, eligible doubts, outbox rows, orphaned uploads, expired tokens | Maintenance steps |

#### 3.10.2.2 Output Dependencies

| Module | Data | Description |
|---|---|---|
| Complaint Management (3.8) | Updated `escalationCount`, `status`, `slaDueAt` | Escalation |
| Notification and Messaging (3.11) | Escalation and reminder notifications | Delivered in the same run |
| Audit, Privacy and Observability (3.15) | Retention deletions | Purpose limitation |

## 3.11 Module Name: Notification and Messaging

**Purpose and status.** Creates in-app notifications [M] and delivers them through email, browser push and Telegram via a database-backed outbox [J\*]. **Sources:** `utils/notifications.ts`, `routes/notifications.ts`, `services/email/*`, `services/notify/push.ts`, `services/notify/telegram.ts`, `routes/telegram.ts`, `CampusCure_Frontend/src/sw.ts`.

### 3.11.1 Functional Block Diagram

![Figure 3.11: FBD of the Notification and Messaging module](images/fbd-notify.png){w=15.5}

The in-app notification is always created; other channels are added only when the user has enabled them. Outbound messages are never sent from inside a request handler, because a serverless function may be frozen after it responds. Instead they are queued and drained, with a dedupe key so a retry cannot send the same message twice.

### 3.11.2 Module Dependencies

#### 3.11.2.1 Input Dependencies

| Source | Input data | Purpose |
|---|---|---|
| Complaint Management (3.8), Academic Doubt Community (3.3), SLA and Scheduled Jobs (3.10) | Event type, recipient, title, message, route data | Notification content |
| User and Profile Management (3.2) | `emailNotifications`, `telegramChatId`, push subscriptions | Channel selection |
| Resend, Web Push, Telegram (external) | Delivery result or error | Status update |

#### 3.11.2.2 Output Dependencies

| Module | Data | Description |
|---|---|---|
| Client Application Platform (3.16) | Notification list, unread count, push payloads | Bell, notification page, system notifications |
| Authentication and Access Control (3.1) | Email sign-in codes | Email OTP |
| Assistant Chatbot (3.6) | The user's notifications | Tool results |

## 3.12 Module Name: File Storage and Attachments

**Purpose and status.** Handles uploads and access-controlled downloads for doubts, answers, complaints and resolution evidence. [J\*]. **Sources:** `routes/uploads.ts`, `services/storage/attachments.ts`, `services/storage/supabaseStorage.ts`, `services/storage/resolutionEvidence.ts`, `components/attachments/*`, `lib/stripImageMetadata.ts`.

### 3.12.1 Functional Block Diagram

![Figure 3.12: FBD of the File Storage and Attachments module](images/fbd-storage.png){w=15.5}

Files go directly from the browser to the private bucket using a signed URL, so the serverless API never handles the file bytes on upload. An attachment row starts as `PENDING` and becomes `ATTACHED` only when the parent record is saved and the object is confirmed to exist. Before upload, the client strips image metadata such as GPS location.

### 3.12.2 Module Dependencies

#### 3.12.2.1 Input Dependencies

| Source | Input data | Purpose |
|---|---|---|
| Client Application Platform (3.16) | File name, MIME type, size; uploaded bytes | Signing and upload |
| Academic Doubt Community (3.3), Complaint Management (3.8) | Parent entity id when saving | Confirmation |
| Supabase Storage (external) | Object existence and signed URLs | Storage |

#### 3.12.2.2 Output Dependencies

| Module | Data | Description |
|---|---|---|
| Academic Doubt Community (3.3), Complaint Management (3.8) | Attachment metadata | Display and evidence |
| Image Doubt Transcription (3.7) | Image bytes | Vision input |
| SLA and Scheduled Jobs (3.10) | Orphaned `PENDING` rows | Nightly sweep |

## 3.13 Module Name: Reputation and Faculty Statistics

**Purpose and status.** Rewards helpful contributions and gives faculty and Admins private performance statistics. [J]. **Sources:** `services/reputation/reputation.ts`, `routes/reputation.ts`, `services/faculty/stats.ts`, `controllers/facultyStatsController.ts`, `pages/student/ReputationPage.tsx`, `pages/faculty/MyPerformance.tsx`, `pages/admin/FacultyPerformance.tsx`.

### 3.13.1 Functional Block Diagram

![Figure 3.13: FBD of the Reputation and Faculty Statistics module](images/fbd-reputation.png){w=15.5}

Reputation is event-sourced: `User.reputation` is a running total of `ReputationEvent` rows, and a unique key on (user, reason, source, actor) prevents the same event from being counted twice. Ranks are computed from the total, not stored. Faculty statistics are visible only to the faculty member and to Admins, by design.

### 3.13.2 Module Dependencies

#### 3.13.2.1 Input Dependencies

| Source | Input data | Purpose |
|---|---|---|
| Academic Doubt Community (3.3) | Accept, upvote and approve events | Points |
| Complaint Management (3.8) | Assignment, resolution and feedback timing | Faculty statistics |

#### 3.13.2.2 Output Dependencies

| Module | Data | Description |
|---|---|---|
| Client Application Platform (3.16) | Points, rank, history, leaderboard, statistics | Reputation and performance pages; author badges |
| Audit, Privacy and Observability (3.15) | `faculty.stats_view` events | Audit of who viewed whose statistics |

## 3.14 Module Name: Dashboards and Analytics

**Purpose and status.** Role-specific summaries and charts. [M]. **Sources:** `controllers/admin/stats.ts`, `controllers/student/doubts.ts` (subject-wise analytics), `pages/*/…Dashboard.tsx`.

### 3.14.1 Functional Block Diagram

![Figure 3.14: FBD of the Dashboards and Analytics module](images/fbd-dash.png){w=14}

The server aggregates; the client draws the charts with Recharts. Each role receives only the aggregates its routes allow.

### 3.14.2 Module Dependencies

#### 3.14.2.1 Input Dependencies

| Source | Input data | Purpose |
|---|---|---|
| Complaint Management (3.8), Academic Doubt Community (3.3), User and Profile Management (3.2) | Counts by status, category, department, month and role | Aggregates |
| Complaint Intelligence (3.9) | Duplicate clusters | Admin complaint view |

#### 3.14.2.2 Output Dependencies

| Module | Data | Description |
|---|---|---|
| Client Application Platform (3.16) | `DashboardStats`, `AnalyticsData`, `SuperAdminStats` | Dashboard pages |

## 3.15 Module Name: Audit, Privacy and Observability

**Purpose and status.** An append-only audit trail, consent records, data export and erasure under the Digital Personal Data Protection Act 2023 [20], retention, and structured request logging. [J]; error reporting to Sentry is implemented but dormant (no DSN configured). **Sources:** `services/audit/auditLog.ts`, `routes/privacy.ts`, `services/privacy/*`, `middleware/observability.ts`, `services/observability/*`.

### 3.15.1 Functional Block Diagram

![Figure 3.15: FBD of the Audit, Privacy and Observability module](images/fbd-audit.png){w=15.5}

Audit metadata is redacted before it is written, and database triggers reject any `UPDATE` or `DELETE` on `AuditLog`. Logs carry a request id and the user id only, never names or emails, so personal data does not leave the database through logs.

### 3.15.2 Module Dependencies

#### 3.15.2.1 Input Dependencies

| Source | Input data | Purpose |
|---|---|---|
| Authentication (3.1), User Management (3.2), Complaint Management (3.8), Faculty Statistics (3.13) | Privileged action events | Audit |
| Client Application Platform (3.16) | Consent, export and erasure requests | Data rights |
| SLA and Scheduled Jobs (3.10) | Daily retention trigger | Retention |

#### 3.15.2.2 Output Dependencies

| Module | Data | Description |
|---|---|---|
| Authentication and Access Control (3.1) | `erasedAt` | Blocks sign-in for erased accounts |
| Super Admin (via API) | Audit log pages | Oversight |
| Operations | Structured logs, optional Sentry events | Diagnosis |

## 3.16 Module Name: Client Application Platform

**Purpose and status.** The React single-page application: routing and role guards, the application shell, the API client, the offline cache and localisation. Routing, layout and API client are [M]; the service worker, offline cache and i18n are [J\*]/[P]. **Sources:** `src/App.tsx`, `components/ProtectedRoute.tsx`, `layouts/AppLayout.tsx`, `api/*.ts`, `context/AuthContext.tsx`, `sw.ts`, `lib/offlineCache.ts`, `i18n/*`.

### 3.16.1 Functional Block Diagram

![Figure 3.16: FBD of the Client Application Platform module](images/fbd-client.png){w=15.5}

Pages are lazy-loaded behind `ProtectedRoute`, which checks the stored user's role. The Axios client attaches the bearer token and, on a 401 response, tries one refresh before signing the user out. The service worker serves navigation from the app shell and keeps a narrow read-only cache for offline use.

### 3.16.2 Module Dependencies

#### 3.16.2.1 Input Dependencies

| Source | Input data | Purpose |
|---|---|---|
| All server modules | JSON responses | Page data |
| Authentication and Access Control (3.1) | Token pair and user summary | Session |
| Notification and Messaging (3.11) | Push payloads; unread count | Alerts |

#### 3.16.2.2 Output Dependencies

| Module | Data | Description |
|---|---|---|
| All server modules | REST requests with a bearer token | User actions |
| File Storage and Attachments (3.12) | Direct uploads to signed URLs (metadata stripped) | File transfer |
