"""Mermaid sources for every SDD figure. render_diagrams.py writes them to
../diagrams/*.mmd and renders PNGs into ../images/.

Notation used across the document:
  FBD   - rectangles are functional blocks, parallelograms are inputs/outputs,
          cylinders are persistent stores, dashed blocks are external services.
  DFD   - rectangles = external entities, rounded boxes numbered n.0 = processes,
          cylinders labelled Dn = data stores, arrow labels = data flows.
  Flow  - stadium = start/end, rectangle = process, diamond = decision,
          parallelogram = input/output.
"""

CLASSES = """
  classDef ext fill:#ffffff,stroke:#555555,stroke-dasharray:5 4,color:#111111
  classDef io fill:#f2f2f2,stroke:#333333,color:#111111
  classDef store fill:#e8eef7,stroke:#1f3a5f,color:#111111
  classDef major fill:#fff6e5,stroke:#9a6200,color:#111111
  classDef entity fill:#e9f3ea,stroke:#2c6e46,color:#111111
  classDef term fill:#1f3a5f,stroke:#1f3a5f,color:#ffffff"""

D = {}

# ---------------------------------------------------------------- 2.0 FBD
D["fbd-system"] = """flowchart TB
  USERS["Users: Student, Faculty / Staff, Admin, Super Admin"]:::entity
  CLIENT["Client Application<br/>React SPA + PWA service worker"]
  CRON["Vercel Cron<br/>daily trigger"]:::ext
  subgraph SERVER["Application Server: Express REST API on Vercel serverless"]
    GW["Request pipeline: request id, helmet, CORS, rate limits,<br/>JWT authentication, role authorization"]
    subgraph CORE["Core functions (Minor Project)"]
      M1["Authentication and<br/>Access Control"]
      M2["User and Profile<br/>Management"]
      M3["Academic Doubt<br/>Community"]
      M8["Complaint<br/>Management"]
      M14["Dashboards and<br/>Analytics"]
    end
    subgraph AI["Intelligence functions (Major Project)"]
      M4["Semantic Search<br/>and Embedding"]:::major
      M5["AI Answer<br/>Drafting"]:::major
      M6["Assistant<br/>Chatbot"]:::major
      M7["Image Doubt<br/>Transcription"]:::major
      M9["Complaint<br/>Intelligence"]:::major
    end
    subgraph PLAT["Platform functions (Major Project)"]
      M10["SLA and<br/>Scheduled Jobs"]:::major
      M11["Notification and<br/>Messaging"]:::major
      M12["File Storage and<br/>Attachments"]:::major
      M13["Reputation and<br/>Faculty Statistics"]:::major
      M15["Audit, Privacy and<br/>Observability"]:::major
    end
  end
  DB[("PostgreSQL (Supabase)<br/>+ pgvector")]:::store
  OBJ[("Supabase Storage<br/>bucket")]:::store
  AIP["AI providers<br/>HuggingFace, Groq, Mistral"]:::ext
  MSG["Messaging providers<br/>Resend, Telegram, Web Push"]:::ext

  M1 ~~~ M2 ~~~ M3 ~~~ M8 ~~~ M14
  M4 ~~~ M5 ~~~ M6 ~~~ M7 ~~~ M9
  M10 ~~~ M11 ~~~ M12 ~~~ M13 ~~~ M15
  USERS -->|"HTTPS"| CLIENT
  CLIENT -->|"REST/JSON + Bearer JWT"| GW
  GW --> M1
  GW --> M4
  GW --> M10
  CRON -->|"/api/internal/cron/daily"| M10
  M14 --> DB
  M9 --> DB
  M15 --> DB
  M9 -->|"embed, generate,<br/>read image"| AIP
  M15 ~~~ MSG
  M11 -.->|"email, chat, push"| MSG
  M12 -.-> OBJ
""" + CLASSES

# ---------------------------------------------------------------- 3.x FBDs
D["fbd-auth"] = """flowchart LR
  I1[/"Registration form<br/>name, email, password, role"/]:::io --> R["Register handler<br/>self-service: STUDENT, FACULTY only"]
  R --> UST[("User<br/>approvalStatus = PENDING")]:::store
  I2[/"Email + password"/]:::io --> L["Login handler<br/>bcrypt compare, generic error"]
  L --> F{"Second factor<br/>enrolled?"}
  F -->|"none"| S["Session issuer<br/>access JWT 15 min,<br/>refresh token 7 days"]
  F -->|"TOTP"| T["TOTP / recovery-code<br/>verifier"]:::major
  F -->|"face"| FV["Face challenge verifier<br/>encrypted template"]:::major
  T --> S
  FV --> S
  I3[/"Email sign-in code"/]:::io --> E["Email OTP verifier"]:::major --> S
  I4[/"Refresh token"/]:::io --> RR["Refresh rotation<br/>and revocation"]:::major --> S
  S --> O1[/"Token pair to client"/]:::io
  I5[/"Bearer token on request"/]:::io --> A1["authenticate()<br/>verify JWT, user active"] --> A2["authorize(roles)"] --> O2[/"req.user to controller<br/>or 401 / 403"/]:::io
""" + CLASSES

D["fbd-users"] = """flowchart LR
  I1[/"Pending registrations"/]:::io --> AP["Approval service<br/>approve / reject"]
  I2[/"Activate / deactivate"/]:::io --> AC["Account status service"]
  I3[/"Profile edits"/]:::io --> PR["Profile service<br/>Student, Faculty, Admin profiles"]
  I4[/"Admin permission flags"/]:::io --> PE["Permission manager<br/>Super Admin only"]
  I5[/"Categories, subjects,<br/>departments"/]:::io --> SE["System settings<br/>Super Admin only"]
  I6[/"Directory query"/]:::io --> DIR["Staff directory<br/>opt-in staff only"]:::major
  AP --> US[("User +<br/>profiles")]:::store
  AC --> US
  PR --> US
  PE --> US
  SE --> AS[("AdminProfile<br/>settings arrays")]:::store
  DIR --> US
  AP --> AU["Audit log writer"]:::major
  AC --> AU
  PE --> AU
""" + CLASSES

D["fbd-doubts"] = """flowchart LR
  I1[/"Doubt form<br/>title, description, subject,<br/>semester, tags, attachments"/]:::io --> V["Validator<br/>sanitise HTML, normalise tags<br/>max 5 tags of 30 chars"]
  V --> DS[("Doubt")]:::store
  V --> EQ["Embedding request"]:::major
  I2[/"Answer text"/]:::io --> AN["Answer service<br/>student: PENDING<br/>faculty: APPROVED"]
  AN --> AS[("Answer")]:::store
  I3[/"Moderation decision + note"/]:::io --> MO["Moderation service<br/>faculty only"] --> AS
  I4[/"Accept answer"/]:::io --> AC["Acceptance service<br/>doubt to RESOLVED"] --> DS
  I5[/"Upvote / bookmark"/]:::io --> VB["Vote and bookmark service<br/>one per user"] --> VS[("DoubtUpvote, AnswerUpvote,<br/>DoubtBookmark")]:::store
  AN --> N["Notification request"]
  AC --> N
  MO --> RP["Reputation events"]:::major
  AC --> RP
""" + CLASSES

D["fbd-search"] = """flowchart LR
  I1[/"Doubt or complaint saved"/]:::io --> Q["Enqueue EmbeddingJob<br/>never blocks the user action"]
  Q --> JQ[("EmbeddingJob queue")]:::store
  JQ --> W["Embedding worker<br/>batch of 50, retry on failure"]
  W -->|"text"| HF["HuggingFace Inference<br/>all-MiniLM-L6-v2"]:::ext
  HF -->|"384-d vector"| W
  W --> VEC[("embedding vector(384)<br/>HNSW cosine index")]:::store
  I2[/"Search text from student"/]:::io --> C["Query embedding cache<br/>60 s, 200 entries"]
  C --> K["Keyword retriever<br/>(Minor baseline)"]
  C --> FT["Full-text retriever<br/>tsvector, OR semantics"]
  C --> VR["Vector retriever<br/>cosine nearest neighbours"]
  VR --> VEC
  K --> RRF["Weighted RRF fusion<br/>k = 60, vector 3, keyword 2, FTS 1"]
  FT --> RRF
  VR --> RRF
  RRF --> O[/"Ranked similar doubts"/]:::io
""" + CLASSES

D["fbd-draft"] = """flowchart LR
  I1[/"Daily job or faculty<br/>'generate draft' request"/]:::io --> EL["Eligibility filter<br/>open, unanswered 24 h,<br/>no existing draft"]
  EL --> RT["Grounding retriever<br/>hybrid search over approved answers<br/>similarity at least 0.45, max 3"]
  RT -->|"no grounding"| STOP[/"No draft produced"/]:::io
  RT -->|"sources"| PB["Prompt builder<br/>sources capped at 1200 chars"]
  PB --> LLM["Chat provider chain<br/>Groq, Groq key 2, Mistral"]:::ext
  LLM --> DR[("AnswerDraft<br/>status PENDING, sourceIds")]:::store
  I2[/"Faculty decision<br/>approve, edit, reject"/]:::io --> RV["Review service"]
  DR --> RV
  RV -->|"approve"| ANS[("Answer<br/>aiAssisted = true")]:::store
  RV -->|"reject"| REJ[/"Draft REJECTED,<br/>never shown to students"/]:::io
""" + CLASSES

D["fbd-chat"] = """flowchart LR
  I1[/"Student message<br/>max 1000 chars,<br/>last 6 turns"/]:::io --> RL["Chat rate limiter<br/>10 per minute"]
  RL --> AS["Assistant loop<br/>max 3 tool rounds"]
  AS <-->|"messages + tool schemas"| LLM["Groq chat completion<br/>tool calling"]:::ext
  AS --> TL["Tool executor<br/>userId taken from JWT"]
  TL --> T1["getMyComplaints"]
  TL --> T2["getMyDoubts"]
  TL --> T3["getMyAnswers"]
  TL --> T4["getMyNotifications"]
  TL --> T5["searchDoubts<br/>(hybrid search)"]
  T1 --> DB[("Complaint, Doubt, Answer,<br/>Notification")]:::store
  T2 --> DB
  T3 --> DB
  T4 --> DB
  T5 --> DB
  AS --> O[/"Answer text labelled AI<br/>with records used"/]:::io
""" + CLASSES

D["fbd-vision"] = """flowchart LR
  I1[/"Uploaded image<br/>attachmentId"/]:::io --> V["Validator<br/>JPEG, PNG, WebP only,<br/>max 3 MB, owner check"]
  V --> DL["Fetch bytes from<br/>Supabase Storage"]
  DL --> P["Vision prompt<br/>transcribe only, never solve"]
  P --> VM["Vision provider chain<br/>Groq qwen3.8-27b, Mistral fallback"]:::ext
  VM --> PJ["Response parser<br/>title 100, description 5000,<br/>max 5 labels, known subject"]
  PJ --> O[/"Draft fields for the doubt form<br/>nothing is written"/]:::io
  V -->|"invalid"| E[/"4xx error,<br/>manual entry remains"/]:::io
  VM -->|"timeout / error"| E
""" + CLASSES

D["fbd-complaints"] = """flowchart LR
  I1[/"Complaint form<br/>title, description, category,<br/>block, room, priority 1-5, photos"/]:::io --> FI["Filing service<br/>validate, one transaction,<br/>update student counters"]
  FI --> CS[("Complaint<br/>status RAISED")]:::store
  FI --> EQ["Embedding request<br/>(duplicate detection)"]:::major
  I2[/"Assign: complaint + assignee"/]:::io --> AS["Assignment service<br/>Admin, history entry"] --> CS
  I3[/"Status change + note,<br/>resolution photos"/]:::io --> LC["Lifecycle service<br/>allowed-target rules"] --> CS
  I4[/"Confirm or reject<br/>+ reason"/]:::io --> VD["Verdict service<br/>student owner only"] --> CS
  I5[/"Rating 1-5 + comment"/]:::io --> FB["Feedback service<br/>RESOLVED only"] --> CS
  I6[/"Escalated reassignment<br/>+ note"/]:::io --> SA["Escalation handler<br/>Super Admin"] --> CS
  AS --> N["Notification requests"]
  LC --> N
  VD --> N
  SA --> N
""" + CLASSES

D["fbd-intel"] = """flowchart LR
  I1[/"Free-text description<br/>at least 10 chars"/]:::io --> RU["Rules engine<br/>category regexes, urgency words,<br/>known block and room list"]
  RU -->|"category found"| SUG[/"Suggested category, block,<br/>room, priority, source = rules"/]:::io
  RU -->|"no category"| LM["LLM extraction<br/>validated against known lists"]:::ext
  LM --> SUG
  I2[/"Draft complaint<br/>text + block + room"/]:::io --> DUP["Duplicate finder<br/>same location,<br/>cosine similarity at least 0.52"]
  DUP --> VEC[("Complaint embeddings")]:::store
  DUP --> O2[/"Possible duplicates"/]:::io
  VEC --> CL["Cluster builder<br/>union-find over open complaints"] --> O3[/"Duplicate clusters for Admin"/]:::io
  I3[/"Complaint to assign"/]:::io --> RK["Candidate ranker<br/>handles category 100/80,<br/>non-teaching 40, teaching 10,<br/>open load as tie-break"]
  RK --> O4[/"Ranked assignees,<br/>Admin decides"/]:::io
""" + CLASSES

D["fbd-jobs"] = """flowchart LR
  CR["Vercel Cron<br/>0 2 * * * (02:00 UTC)"]:::ext --> H["Daily handler<br/>INTERNAL secret / CRON secret"]
  H --> S1["1. Embedding drain"]
  S1 --> S2["2. AI draft generation"]
  S2 --> S3["3. Purge expired refresh tokens"]
  S3 --> S4["4. Sweep orphaned attachments"]
  S4 --> S5["5. SLA sweep<br/>escalate overdue, remind<br/>unconfirmed after 72 h"]
  S5 --> S6["6. Outbox drain<br/>email, Telegram, push"]
  S6 --> S7["7. Purge face and MFA challenges"]
  S7 --> S8["8. Retention sweep<br/>notifications 180 d, views 90 d,<br/>sent mail 90 d, failed 365 d"]
  S8 --> O[/"JSON result per step;<br/>a failed step does not stop the rest"/]:::io
""" + CLASSES

D["fbd-notify"] = """flowchart LR
  I1[/"Domain event<br/>assignment, status change,<br/>answer, acceptance, upvote"/]:::io --> CN["createNotification()"]
  CN --> NT[("Notification<br/>in-app")]:::store
  CN --> EP{"Email policy<br/>by type + user opt-in"}
  EP -->|"yes"| OB[("EmailOutbox<br/>channel EMAIL")]:::store
  CN --> PS{"Push subscriptions?"}
  PS -->|"yes"| OB2[("EmailOutbox<br/>channel PUSH")]:::store
  CN --> TG{"Telegram linked?"}
  TG -->|"yes"| OB3[("EmailOutbox<br/>channel TELEGRAM")]:::store
  OB --> DR["Outbox drain<br/>max 5 attempts, dedupe key"]
  OB2 --> DR
  OB3 --> DR
  DR --> RS["Resend API"]:::ext
  DR --> WP["Web Push / VAPID"]:::ext
  DR --> TA["Telegram Bot API"]:::ext
  NT --> UI[/"Client polls unread count<br/>every 30 s"/]:::io
""" + CLASSES

D["fbd-storage"] = """flowchart LR
  I1[/"File metadata<br/>name, MIME, size"/]:::io --> SG["Upload signer<br/>allow-list JPEG, PNG, WebP,<br/>HEIC, PDF; max 5 MB;<br/>20 per minute"]
  SG --> AT[("Attachment<br/>status PENDING")]:::store
  SG --> O1[/"Signed upload URL"/]:::io
  O1 --> BK[("Supabase Storage<br/>private bucket")]:::store
  I2[/"attachmentIds on doubt,<br/>answer or complaint"/]:::io --> CF["Confirm step<br/>object exists, owner matches"] --> AT2[("Attachment<br/>status ATTACHED")]:::store
  I3[/"GET /api/attachments/:id"/]:::io --> AZ["Access check<br/>owner, complaint parties,<br/>doubt readers"] --> O2[/"Short-lived signed<br/>download URL"/]:::io
  SW["Nightly sweep"] --> BK
  SW --> AT
""" + CLASSES

D["fbd-reputation"] = """flowchart LR
  I1[/"Answer accepted"/]:::io --> RE["Reputation service<br/>accepted 15, upvoted 10,<br/>approved 2, doubt upvoted 2"]
  I2[/"Answer upvoted"/]:::io --> RE
  I3[/"Answer approved"/]:::io --> RE
  I4[/"Doubt upvoted"/]:::io --> RE
  RE --> CAP{"Daily cap 50<br/>and unique event?"}
  CAP -->|"yes"| EV[("ReputationEvent +<br/>User.reputation")]:::store
  EV --> RK[/"Rank: Newcomer, Contributor,<br/>Helper, Mentor, Expert;<br/>leaderboard"/]:::io
  I5[/"Stats request<br/>window 30, 90 or 365 days"/]:::io --> FS["Faculty statistics<br/>min sample 3"]
  FS --> DB[("Answer, Complaint")]:::store
  FS --> O2[/"Own stats (faculty)<br/>all faculty (Admin)"/]:::io
""" + CLASSES

D["fbd-dash"] = """flowchart LR
  I1[/"Dashboard request"/]:::io --> R{"Role"}
  R -->|"Student"| SD["Own complaints, own doubts,<br/>subject-wise analytics"]
  R -->|"Faculty"| FD["Assigned complaints,<br/>doubt queue"]
  R -->|"Admin"| AD["Dashboard stats, analytics,<br/>pending approvals"]
  R -->|"Super Admin"| XD["Super-admin stats,<br/>escalations, admins"]
  SD --> DB[("Users, Doubts,<br/>Complaints")]:::store
  FD --> DB
  AD --> DB
  XD --> DB
  SD --> O[/"Cards and Recharts charts<br/>in the client"/]:::io
  FD --> O
  AD --> O
  XD --> O
""" + CLASSES

D["fbd-audit"] = """flowchart LR
  I1[/"Privileged action<br/>approve, assign, role change,<br/>2FA reset, stats view"/]:::io --> AW["Audit writer<br/>redacts keys like password,<br/>token, secret, hash"]
  AW --> AL[("AuditLog<br/>append-only")]:::store
  AL --> O1[/"Super Admin audit API"/]:::io
  I2[/"Consent grant / withdrawal"/]:::io --> CO["Consent recorder<br/>policy version, purposes"] --> CR[("ConsentRecord")]:::store
  I3[/"Export request"/]:::io --> EX["Data export<br/>user's own records as JSON"]
  I4[/"Erasure request"/]:::io --> ER["Erasure<br/>delete personal rows,<br/>tombstone identifiers"] --> US[("User erasedAt")]:::store
  I5[/"Every HTTP request"/]:::io --> LG["Request logger<br/>x-request-id, user id only"] --> O2[/"Structured logs;<br/>Sentry when DSN set"/]:::io
""" + CLASSES

D["fbd-client"] = """flowchart LR
  U[/"User navigation"/]:::io --> RT["React Router<br/>ProtectedRoute(allowedRoles)"]
  RT --> LY["AppLayout<br/>role sidebar, notifications bell,<br/>assistant widget (students)"]
  LY --> PG["Pages<br/>student, faculty, admin, super admin"]
  PG --> QC["TanStack Query +<br/>API modules"]
  QC --> AX["Axios client<br/>attach Bearer token,<br/>refresh once on 401"]
  AX --> API["REST API"]:::ext
  AX --> LS[("localStorage<br/>access + refresh token")]:::store
  SW["Service worker<br/>NetworkFirst read cache,<br/>push handler"]:::major --> CC[("Cache Storage<br/>doubts, own complaints")]:::store
  I18["i18next<br/>English, Hindi"]:::major --> PG
""" + CLASSES

# ---------------------------------------------------------------- 4.1 DFD
D["dfd-0"] = """flowchart LR
  S["Student"]:::entity
  F["Faculty / Staff"]:::entity
  A["Admin"]:::entity
  X["Super Admin"]:::entity
  P(["0<br/>CampusCure<br/>System"])
  AIP["AI Providers"]:::entity
  MSG["Messaging<br/>Providers"]:::entity
  CR["Scheduler<br/>(Vercel Cron)"]:::entity

  S -->|"credentials, doubts, answers,<br/>complaints, photos, feedback,<br/>chat questions"| P
  P -->|"tokens, search results, AI replies,<br/>complaint status, notifications"| S
  F -->|"answers, moderation decisions,<br/>draft reviews, status updates"| P
  P -->|"doubt queue, assigned complaints,<br/>AI drafts, statistics"| F
  A -->|"approvals, assignments,<br/>status overrides"| P
  P -->|"dashboards, user lists,<br/>duplicate clusters, candidates"| A
  X -->|"settings, permissions,<br/>escalation decisions"| P
  P -->|"escalated complaints,<br/>audit log, system stats"| X
  P -->|"text to embed, prompts, images"| AIP
  AIP -->|"vectors, completions,<br/>transcriptions"| P
  P -->|"emails, chat messages, pushes"| MSG
  CR -->|"daily trigger"| P
""" + CLASSES

D["dfd-1"] = """flowchart LR
  S["Student"]:::entity
  F["Faculty"]:::entity
  A["Admin /<br/>Super Admin"]:::entity
  AIP["AI Providers"]:::entity
  MSG["Messaging<br/>Providers"]:::entity
  CR["Scheduler"]:::entity

  P1(["1.0<br/>Authenticate and<br/>manage users"])
  P2(["2.0<br/>Manage doubts<br/>and answers"])
  P3(["3.0<br/>Search and<br/>AI assistance"])
  P4(["4.0<br/>Manage<br/>complaints"])
  P5(["5.0<br/>Notify users"])
  P6(["6.0<br/>Run scheduled<br/>jobs"])
  P7(["7.0<br/>Report and<br/>audit"])

  D1[("D1 Users and profiles")]:::store
  D2[("D2 Doubts and answers")]:::store
  D3[("D3 Complaints")]:::store
  D4[("D4 Notifications and outbox")]:::store
  D5[("D5 Embedding jobs")]:::store
  D6[("D6 AI drafts")]:::store
  D7[("D7 Audit and consent")]:::store

  S -->|"credentials"| P1
  A -->|"approvals"| P1
  P1 -->|"tokens"| S
  P1 <-->|"user records"| D1
  S -->|"doubt, answer"| P2
  F -->|"answer, moderation"| P2
  P2 <-->|"doubt, answer rows"| D2
  P2 -->|"embedding request"| D5
  S -->|"query, image, chat"| P3
  P3 -->|"text, prompt"| AIP
  AIP -->|"vector, reply"| P3
  P3 <-->|"vectors, sources"| D2
  P3 <-->|"drafts"| D6
  F -->|"draft decision"| P3
  P3 -->|"suggestions, replies"| S
  S -->|"complaint, verdict"| P4
  A -->|"assignment"| P4
  F -->|"status update"| P4
  P4 <-->|"complaint rows"| D3
  P2 -->|"event"| P5
  P4 -->|"event"| P5
  P5 -->|"notification, outbox"| D4
  D4 -->|"pending messages"| P5
  P5 -->|"messages"| MSG
  CR -->|"trigger"| P6
  P6 -->|"jobs"| D5
  P6 -->|"overdue updates"| D3
  P6 -->|"generate"| P3
  P1 -->|"audit entry"| D7
  P4 -->|"audit entry"| D7
  D7 -->|"audit rows"| P7
  D3 -->|"counts"| P7
  D2 -->|"counts"| P7
  P7 -->|"dashboards, audit log"| A
""" + CLASSES

D["dfd-2-complaints"] = """flowchart LR
  S["Student"]:::entity
  A["Admin"]:::entity
  F["Assigned Staff"]:::entity
  X["Super Admin"]:::entity
  LLM["AI Providers"]:::entity
  P41(["4.1<br/>Parse<br/>description"])
  P42(["4.2<br/>Check<br/>duplicates"])
  P43(["4.3<br/>File<br/>complaint"])
  P44(["4.4<br/>Rank and<br/>assign"])
  P45(["4.5<br/>Update<br/>status"])
  P46(["4.6<br/>Confirm or<br/>reject"])
  P47(["4.7<br/>Escalate and<br/>reassign"])
  D3[("D3 Complaints")]:::store
  D1[("D1 Users and profiles")]:::store
  D6s[("D6 Attachments")]:::store
  D4[("D4 Notifications")]:::store

  S -->|"free text"| P41
  P41 -->|"unmatched text"| LLM
  LLM -->|"fields"| P41
  P41 -->|"suggested fields"| S
  S -->|"block, room, text"| P42
  D3 -->|"open complaint vectors"| P42
  P42 -->|"possible duplicates"| S
  S -->|"confirmed form, photo ids"| P43
  P43 -->|"new complaint"| D3
  P43 -->|"confirm photos"| D6s
  A -->|"complaint, chosen assignee"| P44
  D1 -->|"staff categories, load"| P44
  P44 -->|"assignee, history"| D3
  F -->|"status, note, repair photos"| P45
  P45 -->|"new status"| D3
  S -->|"confirm or reason"| P46
  P46 -->|"RESOLVED or back to ASSIGNED"| D3
  P46 -->|"rejection alert"| X
  X -->|"new assignee, note"| P47
  P47 -->|"reassignment"| D3
  P44 -->|"notification"| D4
  P45 -->|"notification"| D4
  P46 -->|"notification"| D4
""" + CLASSES

# ---------------------------------------------------------------- 4.4 Flowcharts
D["fc-system"] = """flowchart TD
  A(["Start: user opens CampusCure"]):::term --> B{"Valid session<br/>token stored?"}
  B -->|"no"| C[/"Landing page:<br/>Log in or Register"/]:::io
  C --> D{"New user?"}
  D -->|"yes"| E["Register: account created<br/>PENDING, awaits Admin"]
  E --> C
  D -->|"no"| F["Sign in (see Fig. login)"]
  F --> G{"Signed in?"}
  G -->|"no"| C
  G -->|"yes"| H["Redirect to role dashboard"]
  B -->|"yes"| H
  H --> I{"Role"}
  I -->|"Student"| J["Doubts, complaints,<br/>assistant, reputation"]
  I -->|"Faculty"| K["Doubt queue, moderation,<br/>AI drafts, assigned complaints"]
  I -->|"Admin"| L["Users, complaints,<br/>assignment, statistics"]
  I -->|"Super Admin"| M["Escalations, settings,<br/>admins, audit"]
  J --> N["Server validates,<br/>authorises, persists"]
  K --> N
  L --> N
  M --> N
  N --> O["Notifications sent to<br/>affected users"]
  O --> P{"Log out?"}
  P -->|"no"| H
  P -->|"yes"| Q["Revoke refresh token,<br/>clear tokens and offline cache"]
  Q --> R(["End"]):::term
""" + CLASSES

D["fc-login"] = """flowchart TD
  A(["Start"]):::term --> B[/"Enter email and password"/]:::io
  B --> C{"Both present?"}
  C -->|"no"| C1[/"400: fields required"/]:::io --> B
  C -->|"yes"| D["Find user by email"]
  D --> E{"User found and<br/>bcrypt matches?"}
  E -->|"no"| E1[/"401: Invalid email or password"/]:::io --> B
  E -->|"yes"| F{"Account erased?"}
  F -->|"yes"| F1[/"403: account erased"/]:::io --> Z
  F -->|"no"| G{"TOTP enabled?"}
  G -->|"yes"| H["Issue MFA challenge<br/>TTL 300 s, 5 attempts"]
  H --> H1[/"Enter 6-digit code<br/>or recovery code"/]:::io
  H1 --> H2{"Valid and<br/>not replayed?"}
  H2 -->|"no"| H1
  H2 -->|"yes"| S
  G -->|"no"| I{"Face template<br/>enrolled?"}
  I -->|"yes"| J["Issue face challenge<br/>TTL 120 s, 3 attempts"]
  J --> J1[/"Capture 3 face samples"/]:::io
  J1 --> J2{"Distance under 0.5 and<br/>liveness variance met?"}
  J2 -->|"no"| J1
  J2 -->|"yes"| S
  I -->|"no"| S["Issue access JWT (15 min)<br/>and refresh token (7 days)"]
  S --> T["Store tokens in client,<br/>route by role"]
  T --> Z(["End"]):::term
""" + CLASSES

D["fc-doubt"] = """flowchart TD
  A(["Start"]):::term --> B{"Typed or photo?"}
  B -->|"photo"| C[/"Select image"/]:::io
  C --> C1["Strip metadata, request<br/>signed upload, upload"]
  C1 --> C2["POST doubts/from-image"]
  C2 --> C3{"Fields returned?"}
  C3 -->|"no"| D
  C3 -->|"yes"| C4[/"Review and edit<br/>prefilled fields"/]:::io --> E
  B -->|"typed"| D[/"Enter title, description,<br/>subject, semester, tags"/]:::io
  D --> E["While typing: GET suggestions<br/>(hybrid search)"]
  E --> F{"Existing doubt<br/>answers it?"}
  F -->|"yes"| G["Open existing thread"] --> Z
  F -->|"no"| H["POST /api/students/doubts"]
  H --> I{"Valid? subject allowed,<br/>tags within limits,<br/>HTML sanitised"}
  I -->|"no"| I1[/"400 with message"/]:::io --> D
  I -->|"yes"| J["Insert Doubt (OPEN),<br/>confirm attachments,<br/>increment doubtsAsked"]
  J --> K["Enqueue embedding job"]
  K --> L[/"Doubt visible in community"/]:::io
  L --> Z(["End"]):::term
""" + CLASSES

D["fc-answer"] = """flowchart TD
  A(["Start"]):::term --> B{"Who answers?"}
  B -->|"Student"| C["Create Answer<br/>approvalStatus PENDING"]
  B -->|"Faculty"| D["Create Answer<br/>approvalStatus APPROVED"]
  C --> I0["answerCount + 1,<br/>doubt status ANSWERED"]
  D --> I0
  I0 --> E{"Student answer?"}
  E -->|"yes"| F{"Faculty decision"}
  F -->|"approve"| G["APPROVED, reputation +2,<br/>visible to students"]
  F -->|"reject"| H["REJECTED with note; doubt status<br/>recomputed (ANSWERED or OPEN)"]
  E -->|"no"| I["Notify doubt author"]
  G --> I
  I --> J{"Author accepts<br/>an answer?"}
  J -->|"yes"| K["isAccepted = true,<br/>doubt RESOLVED,<br/>reputation +15, notify"]
  J -->|"not yet"| L["Remains ANSWERED;<br/>others may upvote"]
  H --> Z(["End"]):::term
  K --> Z
  L --> Z
""" + CLASSES

D["fc-search"] = """flowchart TD
  A(["Start: query q"]):::term --> B{"q long enough?"}
  B -->|"no"| B1[/"Empty list"/]:::io --> Z
  B -->|"yes"| C["Run keyword retriever"]
  C --> D["Run full-text retriever<br/>(OR semantics)"]
  D --> E{"AI enabled and<br/>vector cached or<br/>embedding succeeds?"}
  E -->|"yes"| F["Vector retriever:<br/>HNSW cosine top-k"]
  E -->|"no"| G["Skip vector branch"]
  F --> H["Weighted RRF:<br/>score = sum of w / (60 + rank)"]
  G --> H
  H --> I["Fetch rows for top ids,<br/>attach matched keywords"]
  I --> J[/"Return ranked suggestions"/]:::io
  J --> Z(["End"]):::term
""" + CLASSES

D["fc-draft"] = """flowchart TD
  A(["Start: daily job or<br/>faculty request"]):::term --> B["Select OPEN doubts older than<br/>24 h with no answer and no draft"]
  B --> C{"Any left?"}
  C -->|"no"| Z(["End"]):::term
  C -->|"yes"| D["Hybrid search for similar doubts<br/>with APPROVED answers"]
  D --> E{"Sources with similarity<br/>at least 0.45?"}
  E -->|"no"| F["Skip: no grounding,<br/>no draft"] --> C
  E -->|"yes"| G["Build prompt with up to 3<br/>sources of 1200 chars"]
  G --> H["Call Groq; on failure<br/>Groq key 2, then Mistral"]
  H --> I{"Completion<br/>returned?"}
  I -->|"no"| J["Log, retry next run"] --> C
  I -->|"yes"| K["Save AnswerDraft PENDING<br/>with sourceIds and model"]
  K --> C
""" + CLASSES

D["fc-chat"] = """flowchart TD
  A(["Start"]):::term --> B[/"Student sends message"/]:::io
  B --> C{"Within rate limit and<br/>at most 1000 chars?"}
  C -->|"no"| C1[/"429 or 400"/]:::io --> Z
  C -->|"yes"| D["Build conversation:<br/>system prompt + last 6 turns"]
  D --> E["Call LLM with tool schemas"]
  E --> F{"Tool call<br/>requested?"}
  F -->|"yes"| G{"Round count<br/>at most 3?"}
  G -->|"yes"| H["Run tool with userId from JWT;<br/>reject forbidden params"]
  H --> E
  G -->|"no"| I["Stop tool use"]
  F -->|"no"| J[/"Return answer,<br/>labelled AI"/]:::io
  I --> J
  J --> Z(["End"]):::term
""" + CLASSES

D["fc-complaint"] = """flowchart TD
  A(["Start"]):::term --> B[/"Describe problem in own words"/]:::io
  B --> C["POST complaints/parse"]
  C --> D{"Rules match<br/>a category?"}
  D -->|"yes"| E["Use rules result"]
  D -->|"no"| F{"AI available?"}
  F -->|"yes"| G["LLM extracts fields"]
  F -->|"no"| E
  G --> H[/"Prefilled form: student edits<br/>category, block, room, priority"/]:::io
  E --> H
  H --> I["GET complaints/similar"]
  I --> J{"Duplicates found?"}
  J -->|"yes"| K[/"Show 'already reported' list"/]:::io --> L
  J -->|"no"| L{"Submit anyway?"}
  L -->|"no"| Z
  L -->|"yes"| M{"All fields valid,<br/>priority 1-5,<br/>category allowed?"}
  M -->|"no"| M1[/"400 with message"/]:::io --> H
  M -->|"yes"| N["Transaction: create RAISED complaint,<br/>attach photos, update counters"]
  N --> O["Compute SLA deadline,<br/>enqueue embedding"]
  O --> P[/"Complaint id and status shown"/]:::io
  P --> Z(["End"]):::term
""" + CLASSES

D["fc-lifecycle"] = """flowchart TD
  A(["Start: status change request"]):::term --> B{"Actor"}
  B -->|"Assigned staff"| C{"Target is IN_PROGRESS or<br/>PENDING_CONFIRMATION?"}
  C -->|"no"| X1[/"403 / 400"/]:::io --> Z
  B -->|"Admin"| D{"Target among RAISED, ASSIGNED,<br/>IN_PROGRESS, PENDING_CONFIRMATION,<br/>RESOLVED?"}
  D -->|"no"| X1
  C -->|"yes"| E["Write status, note,<br/>SLA due date"]
  D -->|"yes"| E
  E --> F{"Now PENDING_<br/>CONFIRMATION?"}
  F -->|"no"| N["Notify student"] --> Z
  F -->|"yes"| G["Stamp resolutionDate,<br/>pendingConfirmationAt; notify"]
  G --> H{"Student verdict"}
  H -->|"confirm"| I["RESOLVED, studentConfirmed;<br/>optional rating and comment"]
  H -->|"reject + reason"| J["Back to ASSIGNED or RAISED;<br/>escalationCount + 1;<br/>rejectionHistory; notify Super Admins"]
  J --> K["Super Admin reassigns<br/>with note"]
  K --> Z(["End"]):::term
  I --> Z
""" + CLASSES

D["fc-sla"] = """flowchart TD
  A(["Start: SLA sweep"]):::term --> B{"SLA enabled?"}
  B -->|"no"| Z(["End"]):::term
  B -->|"yes"| C["Load up to 50 open complaints<br/>with slaDueAt in the past"]
  C --> D{"Next complaint?"}
  D -->|"no"| R
  D -->|"yes"| E["escalationCount + 1,<br/>lastEscalationAt = now"]
  E --> F{"Count reached<br/>SLA_MAX_ESCALATIONS (2)?"}
  F -->|"yes"| G["Status ESCALATED_TO_SUPERADMIN,<br/>stop the clock, notify Super Admins"]
  F -->|"no"| H["Push deadline by 24 h cooldown,<br/>notify assignee or Admins"]
  G --> D
  H --> D
  R["Find PENDING_CONFIRMATION<br/>older than 72 h"] --> S["Remind the student"]
  S --> Z
""" + CLASSES

D["fc-notify"] = """flowchart TD
  A(["Start: domain event"]):::term --> B["Insert Notification row"]
  B --> C{"Email allowed for type<br/>and user opted in?"}
  C -->|"yes"| D["Queue EMAIL in outbox"]
  C -->|"no"| E
  D --> E{"User has push<br/>subscriptions?"}
  E -->|"yes"| F["Queue PUSH per subscription"]
  E -->|"no"| G
  F --> G{"Telegram linked?"}
  G -->|"yes"| H["Queue TELEGRAM"]
  G -->|"no"| I
  H --> I["Trigger outbox drain"]
  I --> J{"Next PENDING row<br/>with attempts under 5?"}
  J -->|"no"| Z(["End"]):::term
  J -->|"yes"| K["Send via provider"]
  K --> L{"Sent?"}
  L -->|"yes"| M["Mark SENT, store providerId"] --> J
  L -->|"no"| N["attempts + 1, lastError;<br/>FAILED at the limit"] --> J
""" + CLASSES

# ---------------------------------------------------------------- 4.5 ER
D["er-academic"] = """erDiagram
  USER ||--o| STUDENT_PROFILE : "has"
  USER ||--o| FACULTY_PROFILE : "has"
  USER ||--o| ADMIN_PROFILE : "has"
  USER ||--o{ DOUBT : "posts"
  USER ||--o{ ANSWER : "writes"
  USER |o--o{ ANSWER : "moderates"
  DOUBT ||--o{ ANSWER : "receives"
  DOUBT ||--o{ DOUBT_VIEW : "viewed in"
  DOUBT ||--o{ DOUBT_UPVOTE : "upvoted in"
  ANSWER ||--o{ ANSWER_UPVOTE : "upvoted in"
  DOUBT ||--o{ DOUBT_BOOKMARK : "saved in"
  USER ||--o{ DOUBT_VIEW : "views"
  USER ||--o{ DOUBT_UPVOTE : "casts"
  USER ||--o{ ANSWER_UPVOTE : "casts"
  USER ||--o{ DOUBT_BOOKMARK : "saves"
  USER ||--o{ REPUTATION_EVENT : "earns"
  DOUBT ||--o| ANSWER_DRAFT : "doubtId (logical)"
  USER { uuid id PK }
  DOUBT { uuid id PK
    uuid postedById FK }
  ANSWER { uuid id PK
    uuid doubtId FK
    uuid answeredById FK
    uuid moderatedById FK }
  ANSWER_DRAFT { uuid id PK
    string doubtId UK }
"""

D["er-complaints"] = """erDiagram
  USER ||--o{ COMPLAINT : "raises"
  USER |o--o{ COMPLAINT : "is assigned"
  USER ||--o{ ATTACHMENT : "uploads"
  USER ||--o{ NOTIFICATION : "receives"
  USER ||--o{ REFRESH_TOKEN : "holds"
  USER ||--o{ FACE_CHALLENGE : "gets"
  USER ||--o{ MFA_CHALLENGE : "gets"
  USER ||--o{ RECOVERY_CODE : "owns"
  USER ||--o{ EMAIL_LOGIN_CODE : "gets"
  USER ||--o{ PUSH_SUBSCRIPTION : "registers"
  USER ||--o{ CONSENT_RECORD : "gives"
  COMPLAINT ||--o{ ATTACHMENT : "entityType, entityId (logical)"
  COMPLAINT { uuid id PK
    uuid raisedById FK
    uuid assignedToId FK }
  ATTACHMENT { uuid id PK
    uuid uploadedById FK
    string entityId "polymorphic" }
  EMAIL_OUTBOX { uuid id PK
    string dedupeKey UK }
  EMBEDDING_JOB { uuid id PK
    string entityId "polymorphic" }
  AUDIT_LOG { uuid id PK
    string actorId "no FK" }
"""
