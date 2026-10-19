# 2.0 Functional Description

This section lists the significant functions of CampusCure. Each function has an identifier (F-xxx-nn), a status label from Table 1.3, and a table giving its actor or trigger, inputs, processing, outputs, validations and error conditions, and dependencies. Endpoints are relative to the API base URL. In the endpoint lists, `S` is short for `/api/students`, `F` for `/api/faculty` and `A` for `/api/admin`.

Table 2.1: Function catalogue

| ID | Function | Primary actor | Status |
|---|---|---|---|
| F-AUTH-01 | Register account | Student, Faculty | [M] |
| F-AUTH-02 | Sign in with password and issue session | All roles | [M] |
| F-AUTH-03 | Verify second factor (TOTP, recovery code, face) | All roles | [J] |
| F-AUTH-04 | Sign in with emailed one-time code | All roles | [J\*] |
| F-AUTH-05 | Refresh session and log out | All roles | [J] |
| F-AUTH-06 | Authenticate and authorize each request | System | [M] |
| F-USR-01 | Approve, reject, activate and deactivate accounts | Admin, Super Admin | [M] |
| F-USR-02 | View and edit profile | All roles | [M] |
| F-USR-03 | Manage admin permissions and system settings | Super Admin | [M] |
| F-USR-04 | Browse staff directory | All roles | [J] |
| F-DBT-01 | Post a doubt | Student | [M] |
| F-DBT-02 | Browse, filter and view doubts | Student, Faculty | [M] |
| F-DBT-03 | Answer a doubt | Student, Faculty | [M] |
| F-DBT-04 | Moderate a student answer | Faculty | [M] |
| F-DBT-05 | Accept an answer | Student (doubt author) | [M] |
| F-DBT-06 | Upvote and bookmark | Student, Faculty | [M] / [J] |
| F-DBT-07 | Edit and delete own content with history | Student, Faculty | [M] |
| F-DBT-08 | Attach files, rich text, code and math | Student, Faculty | [J\*] |
| F-AI-01 | Generate and store embeddings | System | [J] |
| F-AI-02 | Suggest similar doubts (hybrid search) | Student | [J] |
| F-AI-03 | Draft an answer from approved answers | System, Faculty | [J] |
| F-AI-04 | Converse with the assistant chatbot | Student | [J] |
| F-AI-05 | Transcribe a photographed doubt | Student | [J\*] |
| F-CMP-01 | Parse a free-text complaint | Student | [J] |
| F-CMP-02 | Detect duplicate complaints | Student, Admin | [J] |
| F-CMP-03 | File a complaint | Student | [M] |
| F-CMP-04 | Assign a complaint with ranked candidates | Admin | [M] / [J] |
| F-CMP-05 | Update complaint status | Faculty, Admin | [M] |
| F-CMP-06 | Confirm or reject a resolution | Student (owner) | [M] |
| F-CMP-07 | Rate a resolved complaint | Student (owner) | [M] |
| F-CMP-08 | Handle escalated complaints | Super Admin | [M] |
| F-CMP-09 | Escalate overdue complaints automatically (SLA) | Scheduler | [J] |
| F-NTF-01 | Create and read in-app notifications | System, all roles | [M] |
| F-NTF-02 | Deliver email, Telegram and push messages | System | [J\*] |
| F-RPT-01 | Role dashboards and analytics | All roles | [M] |
| F-RPT-02 | Reputation points, ranks and leaderboard | Student, Faculty | [J] |
| F-RPT-03 | Faculty performance statistics | Faculty, Admin | [J\*] |
| F-SEC-01 | Record and query the audit log | System, Super Admin | [J] |
| F-SEC-02 | Consent, data export and erasure | All roles | [J] |
| F-SEC-03 | Scheduled maintenance and retention | Scheduler | [J] |
| F-PLT-01 | Installable app and offline reading | All roles | [J\*] |
| F-PLT-02 | Hindi language for the complaint journey | All roles | [P] (partial) |

## 2.1 Authentication and Access Functions

**F-AUTH-01 Register account [M]**

| Attribute | Description |
|---|---|
| Actor / trigger | Visitor submits the registration form (`POST /api/auth/register`) |
| Inputs | `name`, `email`, `password`, `role`, `userID` (enrolment or staff identifier) |
| Processing | Checks all fields are present. Allows only `STUDENT` or `FACULTY` for self-service; `ADMIN` and `SUPER_ADMIN` accounts can be created only by an active Super Admin. Checks that the email and `userID` are unique, hashes the password with bcrypt (cost factor 10), and creates the `User` with `approvalStatus = PENDING` and `isActive = false` |
| Outputs | New user record; the client signs in immediately and shows the pending-approval state |
| Validation / errors | 400 if fields are missing or the role is invalid; 400 for a duplicate email or `userID`; 403 for a privileged role without a Super Admin token; rate limited (5 requests per 15 minutes per client) |
| Dependencies | F-USR-01 (approval) |

**F-AUTH-02 Sign in with password and issue session [M, extended in J]**

| Attribute | Description |
|---|---|
| Actor / trigger | User submits the login form (`POST /api/auth/login`) |
| Inputs | `email`, `password` |
| Processing | Finds the user and compares the password with bcrypt. An erased account is refused. `afterFirstFactor` then decides the next step: if TOTP is enabled it issues an MFA challenge; otherwise, if a face template is enrolled, it issues a face challenge; otherwise it issues a session. `issueSession` sets `isActive = true`, signs an access JWT (payload: `id`, `role`, `userID`, `university`; lifetime 15 minutes by default) and stores a hashed refresh token (7 days by default) |
| Outputs | `{ token, refreshToken, user }`, or a challenge `{ challengeId, method, expiresInSeconds }` |
| Validation / errors | 400 if a field is missing; 401 "Invalid email or password" (the same message for an unknown email or a wrong password, to prevent account enumeration); 403 for an erased account; 503 on a database timeout; rate limited |
| Dependencies | F-AUTH-03, F-AUTH-05 |

**F-AUTH-03 Verify second factor [J]**

| Attribute | Description |
|---|---|
| Actor / trigger | Client answers the challenge (`POST /api/auth/2fa/verify` or `POST /api/auth/face/verify`) |
| Inputs | Challenge id plus a 6-digit TOTP code or a recovery code; or face descriptors (128 numbers each, at least 3 samples) |
| Processing | TOTP: RFC 6238 with 6 digits, a 30-second step and a ±1-step window, and replay protection via `totpLastStep`. Recovery codes are SHA-256 hashed and single-use (10 are issued). Face: the stored template is decrypted with AES-256-GCM; samples must fall within a Euclidean distance of 0.5 and meet a minimum liveness variance of 0.02. Challenges are single-use and expire after 300 s (MFA) or 120 s (face), with a maximum of 5 (MFA) or 3 (face) attempts |
| Outputs | Session as in F-AUTH-02 |
| Validation / errors | 401 with a generic failure message; the challenge is consumed or locked after the attempt limit |
| Dependencies | F-AUTH-02; enrolment endpoints `/2fa/setup`, `/2fa/enable`, `/save-face-descriptor` |

**F-AUTH-04 Sign in with an emailed code [J\*]**

| Attribute | Description |
|---|---|
| Actor / trigger | User chooses "Email me a sign-in code" (`/api/auth/email-login/request`, `/verify`) |
| Inputs | Email address; then the 6-digit code |
| Processing | Stores a hashed code with a 600-second lifetime and a 5-attempt limit, and queues the email through the outbox |
| Outputs | Session as in F-AUTH-02 |
| Validation / errors | Generic "code sent" reply whether or not the account exists; requests limited to 3 per 15 minutes |
| Dependencies | F-NTF-02. **Disabled in production** until a sending domain is verified (`EMAIL_LOGIN_ENABLED`), because without one every code would be redirected to a single inbox |

**F-AUTH-05 Refresh session and log out [J]**

| Attribute | Description |
|---|---|
| Actor / trigger | Axios interceptor on a 401 response (`POST /api/auth/refresh`); user selects Logout (`POST /api/auth/logout`) |
| Inputs | Refresh token |
| Processing | Refresh: verifies the token hash, that it has not expired or been revoked, and that the user is active, then rotates it (revokes the old token and issues a new pair). Logout: revokes the refresh token, sets `isActive = false`, and the client clears stored tokens and the offline cache |
| Outputs | New token pair, or an acknowledgement |
| Validation / errors | 401 "Session expired" sends the client back to the login page |
| Dependencies | `RefreshToken` table; daily purge in F-SEC-03 |

**F-AUTH-06 Authenticate and authorize each request [M]**

| Attribute | Description |
|---|---|
| Actor / trigger | Every request to a protected route |
| Inputs | `Authorization: Bearer <JWT>` header |
| Processing | `authenticate` verifies the JWT signature, loads the user and requires `isActive`, then populates `req.user = { id, role, userID, university }`. `authorize(...roles)` compares `req.user.role` with the roles allowed on the route |
| Outputs | Request continues to the controller |
| Validation / errors | 401 "Authentication required" or "Invalid or expired token"; 403 "Access denied" |
| Dependencies | Used by every module. An automated role matrix (`__tests__/authz/matrix.test.ts`) checks allowed and denied roles per route |

## 2.2 User and Administration Functions

**F-USR-01 Account approval and activation [M]**

| Attribute | Description |
|---|---|
| Actor / trigger | Admin or Super Admin (`PUT A/approve/:userId`, `A/reject/:userId`, `A/users/:userId/approval`, `A/users/:userId/active`) |
| Inputs | Target user id; new approval status or `isActive` flag |
| Processing | Updates the user, records an audit entry, and lists pending students, faculty and (for Super Admin) admins |
| Outputs | Updated user |
| Validation / errors | 400 if the flag is not a boolean; 404 for an unknown user; admins cannot modify Super Admin accounts |
| Dependencies | F-SEC-01. See open items O-1 and O-2 in Appendix A about how approval and deactivation are enforced at sign-in |

**F-USR-02 Profile management [M]**

| Attribute | Description |
|---|---|
| Actor / trigger | Any signed-in user (`GET/PUT S/me`, `F/me`, `A/me`) |
| Inputs | Role-specific profile fields: student department, semester, phone and guardian details; faculty department, subjects, `isTeaching`, `staffRole`, `handlesCategories` and `directoryOptIn` |
| Processing | Validates and updates `StudentProfile`, `FacultyProfile` or `AdminProfile` |
| Outputs | Profile view, also used by routing (F-CMP-04) and the directory (F-USR-04) |
| Validation / errors | 400 for invalid fields; 404 if no profile exists |
| Dependencies | F-CMP-04, F-USR-04 |

**F-USR-03 Admin permissions and system settings [M]**

| Attribute | Description |
|---|---|
| Actor / trigger | Super Admin (`PUT A/permissions/:adminProfileId`, `GET/PUT A/super/settings`) |
| Inputs | Permission flags (`manageUsers`, `manageComplaints`, `manageDoubts`, `viewAnalytics`); allowed complaint categories, doubt subjects and departments |
| Processing | Updates `AdminProfile`. The posting settings (`S/settings/posting`) give clients the current allowed categories and subjects |
| Outputs | Settings used to validate complaint and doubt forms |
| Validation / errors | 403 for non-Super Admin callers |
| Dependencies | F-DBT-01, F-CMP-03 |

**F-USR-04 Staff directory [J]**

| Attribute | Description |
|---|---|
| Actor / trigger | Any signed-in user (`GET /api/staff/directory`) |
| Inputs | Optional filters (department, category) |
| Processing | Lists only staff who opted in (`directoryOptIn`) with professional contact details and the categories they handle |
| Outputs | Directory entries |
| Validation / errors | Personal data of students is never included |
| Dependencies | F-USR-02 |

## 2.3 Academic Doubt Functions

**F-DBT-01 Post a doubt [M, extended in J]**

| Attribute | Description |
|---|---|
| Actor / trigger | Student (`POST S/doubts`) |
| Inputs | `title`, `description` (plain text or sanitised HTML), `subject`, `semester`, `labels` (tags), optional `attachmentIds` |
| Processing | Validates the subject against settings; normalises tags (maximum 5 tags of 30 characters each); sanitises HTML (allow-list in `content/sanitize.ts`); creates the `Doubt` with status `OPEN`; confirms attachments; increments the student's `doubtsAsked`; queues an embedding job |
| Outputs | Created doubt |
| Validation / errors | 400 for missing or invalid fields, a disallowed subject or too many tags |
| Dependencies | F-AI-01, F-AI-02 (suggestions shown while typing), F-DBT-08 |

**F-DBT-02 Browse, filter and view doubts [M]**

| Attribute | Description |
|---|---|
| Actor / trigger | Student or Faculty (`GET S/doubts`, `S/doubts/:id`, `F/doubts`, `F/doubts/:id`, `S/doubts/my`, `S/doubts/tags`, `S/doubts/bookmarked`, `S/doubts/analytics/subjectwise`) |
| Inputs | Filters: search text, subject, semester, tag, status |
| Processing | Queries visible doubts. Students see approved answers plus their own pending ones; faculty also see pending answers. Each user's first view of a doubt adds a `DoubtView` row and increments `views` |
| Outputs | Doubt lists and detail views with answers, tags and attachments |
| Validation / errors | 404 for an unknown doubt |
| Dependencies | F-DBT-06 |

**F-DBT-03 Answer a doubt [M]**

| Attribute | Description |
|---|---|
| Actor / trigger | Student (`POST S/doubts/:doubtId/answers`) or Faculty (`POST F/doubts/:doubtId/answers`) |
| Inputs | Answer content and optional attachments |
| Processing | Student answers are created with `approvalStatus = PENDING`; faculty answers with `APPROVED`. In one transaction: increment `answerCount`, set the doubt status to `ANSWERED`, and notify the doubt author |
| Outputs | Created answer |
| Validation / errors | 400 for empty or too-short content (the faculty form requires at least 10 characters); 404 for an unknown doubt |
| Dependencies | F-DBT-04, F-NTF-01 |

**F-DBT-04 Moderate a student answer [M]**

| Attribute | Description |
|---|---|
| Actor / trigger | Faculty (`PUT F/answers/:answerId/moderate`) |
| Inputs | Decision (`APPROVED` or `REJECTED`) and an optional `moderationNote` |
| Processing | `services/doubts/answerReview.ts` records the decision, moderator and time; awards (or, on later rejection, reverses) 2 reputation points; recomputes the doubt status from its remaining visible answers |
| Outputs | Updated answer; notification to the author |
| Validation / errors | 400 for an invalid decision; 403 for non-faculty |
| Dependencies | F-RPT-02, F-NTF-01 |

**F-DBT-05 Accept an answer [M]**

| Attribute | Description |
|---|---|
| Actor / trigger | Doubt author (`POST S/doubts/:doubtId/answers/:answerId/accept`) |
| Inputs | Doubt id and answer id |
| Processing | Sets `isAccepted` on the answer and `acceptedAnswerId` on the doubt, sets the doubt to `RESOLVED`, awards 15 reputation points to the answerer, and sends a `DOUBT_ACCEPTED` notification |
| Outputs | Updated doubt |
| Validation / errors | 403 if the caller is not the doubt author |
| Dependencies | F-RPT-02, F-NTF-01 |

**F-DBT-06 Upvote and bookmark [M upvotes, J bookmarks]**

| Attribute | Description |
|---|---|
| Actor / trigger | Student or Faculty (`POST S/doubts/:id/upvote`, `S/answers/:id/upvote`, `POST/DELETE S/doubts/:id/bookmark`) |
| Inputs | Target id |
| Processing | Unique constraints (`DoubtUpvote`, `AnswerUpvote`, `DoubtBookmark` on `[targetId, userId]`) allow at most one per user; counters are updated in the same transaction; upvotes award reputation |
| Outputs | Updated counts or bookmark state |
| Validation / errors | A duplicate upvote is rejected |
| Dependencies | F-RPT-02 |

**F-DBT-07 Edit and delete with history [M]**

| Attribute | Description |
|---|---|
| Actor / trigger | Author (`PUT/DELETE S/doubts/:id`, `S/answers/:id`, `F/answers/:id`) |
| Inputs | New content |
| Processing | Appends the previous version to `editHistory` (JSON array) and sets `edited = true`; deletion updates the counters |
| Outputs | Updated record; the UI shows "Edited n times" |
| Validation / errors | 403 if the caller is not the author |
| Dependencies | — |

**F-DBT-08 Attachments, rich text, code and math [J\*]**

| Attribute | Description |
|---|---|
| Actor / trigger | Author while composing; reader while viewing (`POST /api/uploads/sign`, `GET /api/attachments/:id`) |
| Inputs | Files (JPEG, PNG, WebP, HEIC, PDF; at most 5 MB); TipTap HTML |
| Processing | Signed direct upload to Supabase Storage; the attachment is confirmed when the parent record is saved; downloads use short-lived signed URLs after an access check. The client renders code with Shiki and math with KaTeX |
| Outputs | Attachments linked through `Attachment.entityType` and `entityId` |
| Validation / errors | 400 for a disallowed type or size; 403 for a reader without access; uploads limited to 20 per minute |
| Dependencies | Module 3.12. A manual in-browser check is outstanding (CC-23, CC-24) |

## 2.4 Intelligence Functions

**F-AI-01 Generate and store embeddings [J]**

| Attribute | Description |
|---|---|
| Actor / trigger | Creating or editing a doubt or complaint (`requestEmbedding`); the daily job; `/api/internal/embeddings/drain` |
| Inputs | Entity type and id |
| Processing | Adds an `EmbeddingJob` (unique per entity). The worker claims up to 50 pending jobs, embeds their text in one call to HuggingFace (`all-MiniLM-L6-v2`, 384 dimensions), and writes `embedding`, `embeddingModel`, `embeddingVersion` and `embeddedAt`. A failed batch returns to `PENDING` with `attempts + 1` |
| Outputs | Vectors in `Doubt.embedding` and `Complaint.embedding`, indexed with HNSW (cosine) |
| Validation / errors | Refuses to write a vector whose model or dimension differs from the configured canonical model; never throws into the user action |
| Dependencies | F-AI-02, F-AI-03, F-CMP-02 |

**F-AI-02 Suggest similar doubts [J]**

| Attribute | Description |
|---|---|
| Actor / trigger | Student typing a doubt title or searching (`GET S/doubts/suggestions`) |
| Inputs | Query text, optional filters |
| Processing | Runs three retrievers: keyword (the Minor Project baseline), PostgreSQL full-text with OR semantics, and vector nearest neighbours. They are fused with weighted Reciprocal Rank Fusion: score(d) = Σ w / (60 + rank), with weights vector 3, keyword 2, full-text 1. Query embeddings are cached for 60 s (200 entries) |
| Outputs | `{ doubts[], used[], degraded }` with the matched keywords for each doubt |
| Validation / errors | If the embedding provider fails, the vector branch is skipped and `degraded = true`; the endpoint does not fail |
| Dependencies | F-AI-01 |

**F-AI-03 Draft an answer [J]**

| Attribute | Description |
|---|---|
| Actor / trigger | Daily job (`runDraftGeneration`) or faculty request (`POST F/doubts/:id/draft/generate`); review through `F/doubts/:id/draft`, `/approve`, `/reject` |
| Inputs | Doubts that are still unanswered 24 hours after posting and have no draft |
| Processing | Retrieves similar doubts that have approved answers. If no source reaches a similarity of 0.45, no draft is produced. Otherwise up to 3 sources (1,200 characters each) go into a constrained prompt sent through the chat provider chain (Groq, a second Groq key, then Mistral). The result is saved as an `AnswerDraft` with `status = PENDING` and its `sourceIds` |
| Outputs | Draft visible to faculty only. On approval it becomes a faculty answer with `aiAssisted = true`, recording whether it was edited; on rejection it is kept with `status = REJECTED` and never shown to students |
| Validation / errors | Approval requires at least 10 characters; each doubt gets at most one draft, so a rejected draft is not regenerated |
| Dependencies | F-AI-02, F-DBT-03 |

**F-AI-04 Assistant chatbot [J]**

| Attribute | Description |
|---|---|
| Actor / trigger | Student through the assistant widget (`POST /api/chat`; route restricted to `STUDENT`) |
| Inputs | `message` (at most 1,000 characters) and recent `history` (at most 6 turns) |
| Processing | An assistant loop with at most 3 tool rounds. The LLM may call `getMyComplaints`, `getMyDoubts`, `getMyAnswers`, `getMyNotifications` and `searchDoubts`. Tools take the user id from the JWT, never from model arguments, and parameters on the forbidden list are rejected. Each tool returns at most 10 rows |
| Outputs | Reply text, labelled as AI in the widget |
| Validation / errors | 429 above 10 messages per minute; 400 for an over-long message; a provider failure returns a clear error |
| Dependencies | F-AI-02, complaint and doubt data |

**F-AI-05 Transcribe a photographed doubt [J\*]**

| Attribute | Description |
|---|---|
| Actor / trigger | Student selects "Read my question from the image" after uploading a photo (`POST S/doubts/from-image`) |
| Inputs | Id of an uploaded attachment owned by the student |
| Processing | Accepts JPEG, PNG or WebP of at most 3 MB; fetches the bytes from storage; calls the vision provider (Groq `qwen/qwen3.8-27b`, with Mistral as fallback) with an instruction to transcribe, not solve; parses the JSON reply (title up to 100 characters, description up to 5,000, at most 5 labels, subject checked against the allowed list, legibility flag) |
| Outputs | Draft form fields marked as read from the image; **nothing is written** until the student submits through F-DBT-01 |
| Validation / errors | 4xx for an unsupported or oversized image; a clear failure message for illegible input or provider errors, after which manual entry remains available; shares the chat rate limit |
| Dependencies | Module 3.12. A manual photo check is outstanding |

## 2.5 Complaint Functions

**F-CMP-01 Parse a free-text complaint [J]**

| Attribute | Description |
|---|---|
| Actor / trigger | Student selects "Fill the form for me" (`POST S/complaints/parse`) |
| Inputs | Free text of at least 10 characters |
| Processing | Rules first: category regular expressions (SMART_BOARD, NETWORK, FAN, LIGHT, SEATING, FURNITURE), urgency and low-priority phrases, and block and room tokens matched against `data/block_classroom.json`. The LLM is called only when the rules find no category, and its output is validated against the known lists |
| Outputs | `{ category, priority, block, classroomNumber, source: "rules" | "model" | "none" }` used to prefill the form |
| Validation / errors | Never throws: if AI is disabled or fails, the rules result is returned |
| Dependencies | F-CMP-03 |

**F-CMP-02 Detect duplicate complaints [J]**

| Attribute | Description |
|---|---|
| Actor / trigger | Student completing the form (`GET S/complaints/similar`); Admin viewing duplicate groups (`GET A/complaints/duplicates`) |
| Inputs | Text, block and room; or all open complaints |
| Processing | Compares the embedding with open complaints in the same location using cosine similarity, with the threshold `DUPLICATE_SIMILARITY_THRESHOLD` (default 0.52, calibrated by script). The admin view groups complaints into connected clusters with union-find |
| Outputs | Candidate list for the student; clusters for the Admin |
| Validation / errors | Never merges or hides complaints; returns an empty list on failure |
| Dependencies | F-AI-01 |

**F-CMP-03 File a complaint [M]**

| Attribute | Description |
|---|---|
| Actor / trigger | Student (`POST S/complaints/new`) |
| Inputs | `title`, `description`, `category`, `block`, `classroomNumber`, `priority`, optional `attachmentIds` |
| Processing | `validateComplaint` checks that all fields are present, that the priority is an integer from 1 to 5 and that the category is allowed. One transaction creates the complaint (`RAISED`, with the initial SLA deadline), attaches photos and updates the student's counters. An embedding job is queued afterwards |
| Outputs | Complaint with a unique id |
| Validation / errors | 400 "All fields are required", "Priority must be a whole number from 1 to 5", "Selected complaint category is not allowed" |
| Dependencies | F-CMP-01, F-CMP-02, F-AI-01 |

**F-CMP-04 Assign with ranked candidates [M, ranking J]**

| Attribute | Description |
|---|---|
| Actor / trigger | Admin (`GET A/complaints/:id/candidates`, `POST A/complaints/assign`) |
| Inputs | Complaint id and chosen assignee id |
| Processing | Candidates are scored: 100 for staff who handle the category in the same department, 80 for staff who handle the category, 40 for non-teaching general staff, 10 for teaching staff as a fallback; open workload breaks ties. Assignment sets `ASSIGNED`, `assignedAt` and a new SLA deadline, appends an `assignmentHistory` entry, notifies the assignee and writes an audit entry |
| Outputs | Assigned complaint |
| Validation / errors | 400 for an invalid assignee; 404 for an unknown complaint |
| Dependencies | F-USR-02, F-NTF-01, F-SEC-01 |

**F-CMP-05 Update complaint status [M]**

| Attribute | Description |
|---|---|
| Actor / trigger | Assigned faculty (`PUT F/complaints/:id/status`); Admin (`PUT A/complaints/status`) |
| Inputs | Target status, resolution note, optional resolution photos |
| Processing | Allowed targets: faculty may set only `IN_PROGRESS` or `PENDING_CONFIRMATION`; an Admin may set `RAISED`, `ASSIGNED`, `IN_PROGRESS`, `PENDING_CONFIRMATION` or `RESOLVED`. `PENDING_CONFIRMATION` stamps `resolutionDate` and `pendingConfirmationAt`. The SLA deadline is recomputed for the new state |
| Outputs | Updated complaint; notification to the student |
| Validation / errors | 403 or 400 for a target the actor may not set, or for a complaint not assigned to the caller |
| Dependencies | F-CMP-06, F-CMP-09 |

**F-CMP-06 Confirm or reject a resolution [M]**

| Attribute | Description |
|---|---|
| Actor / trigger | Complaint owner (`POST S/complaints/:id/confirm-resolution`, `/reject-resolution`) |
| Inputs | Rejection reason (required when rejecting) |
| Processing | Allowed only while the complaint is `PENDING_CONFIRMATION`. Confirming sets `RESOLVED`, `studentConfirmed` and `studentConfirmationDate`. Rejecting returns the complaint to `ASSIGNED` (or `RAISED` if unassigned), increments `escalationCount`, appends to `rejectionHistory` and notifies the assignee and every Super Admin |
| Outputs | Updated complaint |
| Validation / errors | 403 if the caller is not the owner; 400 if not pending or the reason is missing |
| Dependencies | F-CMP-08 |

**F-CMP-07 Rate a resolved complaint [M]**

| Attribute | Description |
|---|---|
| Actor / trigger | Complaint owner (`POST S/complaints/:id/feedback`) |
| Inputs | `feedbackRating` (1 to 5) and an optional `feedbackComment` |
| Processing | Stored on the complaint; allowed only once it is `RESOLVED` |
| Outputs | Rating shown to staff and used in statistics |
| Validation / errors | 400 if the complaint is not resolved or the rating is out of range |
| Dependencies | F-RPT-03 |

**F-CMP-08 Handle escalated complaints [M]**

| Attribute | Description |
|---|---|
| Actor / trigger | Super Admin (`GET A/complaints/escalated`, `POST A/complaints/escalated/reassign`, `/mark-handled`) |
| Inputs | Complaint id, new assignee, optional note |
| Processing | Lists complaints with `escalationCount > 0`, most escalated first. Reassignment requires an escalated complaint in `RAISED` or `ASSIGNED`, a different assignee, and records `handledBySuperAdmin`, `superAdminId` and a history entry with mode `SUPER_ADMIN` |
| Outputs | Reassigned complaint; notifications |
| Validation / errors | 400 if not escalated, if the state is not eligible, or if the assignee is unchanged. See Appendix A, item O-3, for complaints in `ESCALATED_TO_SUPERADMIN` |
| Dependencies | F-CMP-06, F-CMP-09 |

**F-CMP-09 SLA timers and automatic escalation [J]**

| Attribute | Description |
|---|---|
| Actor / trigger | Daily job (`runSlaSweep`) or `/api/internal/sla/sweep` |
| Inputs | Open complaints whose `slaDueAt` has passed |
| Processing | Budgets by priority (hours to assignment / to resolution): 5 → 4/24, 4 → 8/48, 3 → 24/96, 2 → 48/168, 1 → 72/240, scaled by `SLA_MULTIPLIER`. Each breach increments `escalationCount` and pushes the deadline back by a 24-hour cooldown; at `SLA_MAX_ESCALATIONS` (2) the complaint moves to `ESCALATED_TO_SUPERADMIN` and its clock stops. Students who have not confirmed within 72 hours are reminded |
| Outputs | Escalated complaints and notifications |
| Validation / errors | Processes at most 50 complaints per run; can be turned off with `SLA_ENABLED` |
| Dependencies | F-NTF-01, F-CMP-08 |

## 2.6 Notification, Reporting, Security and Platform Functions

**F-NTF-01 In-app notifications [M]**

| Attribute | Description |
|---|---|
| Actor / trigger | Domain events (assignment, status change, answer, acceptance, upvote) through `utils/notifications.ts`; users via `/api/notifications` |
| Inputs | `userId`, `type` (`NotificationType`), `title`, `message`, `data` (JSON route hints) |
| Processing | Inserts a `Notification` row. The client polls `/unread-count` every 30 seconds, lists notifications, marks them read, and opens the related page through `/notifications/:id` |
| Outputs | Notification bell and list |
| Validation / errors | A notification failure never fails the action that caused it |
| Dependencies | F-NTF-02 |

**F-NTF-02 Email, Telegram and push delivery [J\*]**

| Attribute | Description |
|---|---|
| Actor / trigger | `createNotification`; the outbox drain (opportunistic and daily) |
| Inputs | Notification plus the user's channels: email preference, push subscriptions, linked Telegram chat |
| Processing | Queues one `EmailOutbox` row per channel (`EMAIL`, `PUSH`, `TELEGRAM`) with a dedupe key. The drain sends through Resend, Web Push (VAPID) or the Telegram Bot API, with at most 5 attempts per message. Email recipients can unsubscribe through a tokenised link |
| Outputs | Delivered message, or `FAILED` with `lastError` |
| Validation / errors | Channels stay off until configured. Without a verified domain, email goes only to `EMAIL_REDIRECT_TO`; Telegram needs its production variables |
| Dependencies | F-NTF-01 |

**F-RPT-01 Dashboards and analytics [M]**

| Attribute | Description |
|---|---|
| Actor / trigger | Any role opening its dashboard (`A/dashboard`, `A/analytics`, `A/super/stats`, `S/doubts/analytics/subjectwise`) |
| Inputs | — |
| Processing | Aggregates complaint counts by status, category, department and month; user counts; and doubt activity |
| Outputs | Statistic cards and Recharts charts (Monthly Trends, By Category, By Department) |
| Validation / errors | Empty states when there is no data |
| Dependencies | Complaint and doubt data |

**F-RPT-02 Reputation [J]**

| Attribute | Description |
|---|---|
| Actor / trigger | Answer accepted (+15), answer upvoted (+10), answer approved (+2), doubt upvoted (+2); `/api/reputation/me`, `/me/history`, `/leaderboard` |
| Inputs | Source event |
| Processing | Inserts a `ReputationEvent` (a unique key prevents double awards), applies a daily cap of 50 points, updates `User.reputation`, and derives the rank (Newcomer 0, Contributor 50, Helper 150, Mentor 400, Expert 1000) |
| Outputs | Points, rank, history and leaderboard |
| Validation / errors | Reversed when an approval is withdrawn |
| Dependencies | F-DBT-04 to F-DBT-06 |

**F-RPT-03 Faculty statistics [J\*]**

| Attribute | Description |
|---|---|
| Actor / trigger | Faculty (`F/me/stats`); Admin (`A/faculty/stats`, `A/faculty/:id/stats`) |
| Inputs | Window of 30, 90 or 365 days (default 90) |
| Processing | Computes answer and complaint-resolution metrics; suppresses a metric when its sample is below 3 and a department aggregate when the department has fewer than 3 members; viewing another faculty member's statistics writes an audit entry |
| Outputs | Private statistics; not a public leaderboard |
| Validation / errors | — |
| Dependencies | F-SEC-01 |

**F-SEC-01 Audit log [J]**

| Attribute | Description |
|---|---|
| Actor / trigger | Privileged actions; Super Admin queries (`GET A/audit-log`, page size at most 100) |
| Inputs | Actor, action, target and summary; metadata is redacted for keys matching password, token, secret, key, descriptor, nonce or hash |
| Processing | Appends to `AuditLog`; a database trigger enforces append-only behaviour |
| Outputs | Filterable audit trail (no viewer page exists yet; available through the API) |
| Validation / errors | 403 for non-Super Admin callers |
| Dependencies | Used by Modules 3.1, 3.2, 3.8 and 3.13 |

**F-SEC-02 Consent, export and erasure [J]**

| Attribute | Description |
|---|---|
| Actor / trigger | Any user (`GET/POST /api/me/consent`, `GET /api/me/data-export`, `POST /api/me/erase`) |
| Inputs | Consent decision and purposes (`account-and-authentication`, `complaint-handling`, `doubt-community`, `service-notifications`) |
| Processing | Consent changes are appended to `ConsentRecord` with the policy version. Export returns the user's own records as JSON. Erasure deletes purely personal rows (notifications, bookmarks, views, tokens, challenges), replaces identifiers with a `deleted-…` tombstone, and sets `erasedAt`; repeat requests have no further effect |
| Outputs | Consent history, export file, erasure result |
| Validation / errors | An erased account cannot sign in |
| Dependencies | API only; no dedicated page exists yet (see Section 5.3) |

**F-SEC-03 Scheduled maintenance and retention [J]**

| Attribute | Description |
|---|---|
| Actor / trigger | Vercel Cron `0 2 * * *` calling `/api/internal/cron/daily` (protected by a shared secret) |
| Inputs | — |
| Processing | Runs eight steps in order: embedding drain, draft generation, refresh-token purge, attachment sweep, SLA sweep, outbox drain, face and MFA challenge purge, and the retention sweep (notifications 180 days, doubt views 90 days, sent messages 90 days, failed messages 365 days) |
| Outputs | JSON result per step; a failing step does not stop the others |
| Validation / errors | Rejected unless the request carries the internal secret (`x-internal-secret`) or Vercel's `Authorization: Bearer` cron secret, compared in constant time |
| Dependencies | Modules 3.4, 3.5, 3.10, 3.11, 3.12 |

**F-PLT-01 Installable app and offline reading [J\*]**

| Attribute | Description |
|---|---|
| Actor / trigger | Browser installs the app; service worker intercepts navigation and selected reads |
| Inputs | — |
| Processing | Workbox `injectManifest` service worker with a NetworkFirst cache that holds only shared doubt content, the student's own complaints and the faculty doubt queue; the cache is cleared on logout; an offline banner is shown when the connection drops |
| Outputs | Offline read access |
| Validation / errors | No credentials, profiles or attachment URLs are cached. A real-device check is outstanding |
| Dependencies | F-NTF-02 (push handler in the same service worker) |

**F-PLT-02 Hindi language [P, partial]**

| Attribute | Description |
|---|---|
| Actor / trigger | User selects English or हिंदी |
| Inputs | Language choice |
| Processing | i18next resources in `src/i18n/en.ts` and `hi.ts` |
| Outputs | Translated login, sidebar, Raise Complaint, My Complaints and staff complaint queue |
| Validation / errors | The rest of the application is still English |
| Dependencies | — |

## 2.7 Functional Block Diagram

Figure 2.1 shows the complete system. Users reach the client application over HTTPS. The client calls the REST API with a bearer token. Every request passes the request pipeline (request identifier, security headers, CORS, rate limits, authentication and authorization) before reaching a functional block. Blocks are grouped into the core functions inherited from the Minor Project and the intelligence and platform functions added in the Major Project (shaded). All blocks persist to PostgreSQL. AI blocks call external AI providers, the messaging block calls external messaging providers, and Vercel Cron triggers the scheduled-jobs block once a day.

![Figure 2.1: Functional block diagram of the complete CampusCure system](images/fbd-system.png){w=15.5}

Table 2.2: Functions grouped by functional block

| Functional block (Section 3) | Functions |
|---|---|
| 3.1 Authentication and Access Control | F-AUTH-01 to F-AUTH-06 |
| 3.2 User and Profile Management | F-USR-01 to F-USR-04 |
| 3.3 Academic Doubt Community | F-DBT-01 to F-DBT-07 |
| 3.4 Semantic Search and Embedding | F-AI-01, F-AI-02 |
| 3.5 AI Answer Drafting | F-AI-03 |
| 3.6 Assistant Chatbot | F-AI-04 |
| 3.7 Image Doubt Transcription | F-AI-05 |
| 3.8 Complaint Management | F-CMP-03 to F-CMP-08 |
| 3.9 Complaint Intelligence | F-CMP-01, F-CMP-02, ranking in F-CMP-04 |
| 3.10 SLA and Scheduled Jobs | F-CMP-09, F-SEC-03 |
| 3.11 Notification and Messaging | F-NTF-01, F-NTF-02 |
| 3.12 File Storage and Attachments | F-DBT-08 |
| 3.13 Reputation and Faculty Statistics | F-RPT-02, F-RPT-03 |
| 3.14 Dashboards and Analytics | F-RPT-01 |
| 3.15 Audit, Privacy and Observability | F-SEC-01, F-SEC-02 |
| 3.16 Client Application Platform | F-PLT-01, F-PLT-02 |
