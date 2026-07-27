# Cat Feeding Scheduler — Software Spec (v1)

**Product:** A small family webapp for scheduling feeding visits for the cats (Cookie & Snoopy) while the parents are out of town. Family members claim days on a shared calendar and leave notes.

**Status:** v1 spec, derived from the answered QA. Built lean for a first release, but the data model and infrastructure are designed to scale cleanly later.

---

## 1. Goals & scope

The app lets **parents** publish a schedule covering a date range, and lets **fam** (aunts/uncles) sign up for the days they'll come feed the cats. Each day can be claimed by one person, or several can add themselves to the same day, and anyone can attach a short note.

**In scope for v1:** phone-number login, role-based access, the parents admin page, user management with a stubbed text-invite, one or more schedule "profiles," a calendar with claims + notes, an optional email notification to parents on claims, and a parent-editable help page. Dockerized deployment to an Oracle Cloud (OCI) Ubuntu VM with Postgres, Nginx, and HTTPS.

**Deliberately deferred (built to add later, not shipped in v1):** live SMS sending (invites and OTP), photo uploads beyond the help page, recurring/auto-generated schedules, push notifications, and any non-family public access.

---

## 2. Roles & permissions

There are two account roles plus one non-account profile.

| Role | Who | Can do |
|------|-----|--------|
| **Parent** (admin) | Wil (732-986-1906), Max (973-489-1380) | Everything: manage users, create/edit/activate schedules, set the date range, edit the help page, claim/remove any day, receive email notifications. |
| **Fam** | Aunts & uncles | Log in, view active schedule(s), add their name to a day, leave/edit a note on their claim, remove their own name. Cannot access the parents admin page or change anyone else's claim. |
| **Baby** | Cookie & Snoopy | A profile only — **no login**. Represents the cats; shown in the help page / branding. |

The `unc` (male) / `ant` (female) distinction is a **cosmetic label** on a Fam member. It does not change permissions.

---

## 3. Authentication (phone number, no password)

Login is by **phone number**, no password.

**Flow (OTP with automatic failover):**

1. User enters their phone number.
2. The number is normalized to E.164 (`+1XXXXXXXXXX`); messy input like `(732) 986-1906` is accepted and cleaned.
3. The system looks for a matching active user.
4. **If an OTP/SMS provider is configured** (env flag set): generate a one-time code, "send" it via the `send_sms()` service, and prompt the user to enter it. (In v1 the sender is a stub — see §5.) 
5. **If no provider is configured** (the v1 default, since nothing is set up yet): skip verification and log the user straight in. This is the failover behavior and is controlled by a single config flag, so flipping on real OTP later requires no code changes to the login view.

**Sessions persist** ("remember me") — a long-lived session cookie so users don't re-enter their number each visit.

Security note: phone-only login with no verification is acceptable for a tiny private family app, and the design makes turning on real OTP a config switch once Twilio is wired up.

---

## 4. Data model

Core entities (Django models). Field lists are indicative, not exhaustive.

**User**
- `name`
- `phone` (E.164, unique)
- `role` — `parent` | `fam`
- `role_label` — `unc` | `ant` | none (Fam cosmetic label)
- `partner_name` (optional) — a second name for couples, so one Fam entry can represent both people. Purely additional/display.
- `is_active`, `created_at`

**Schedule** (a "profile")
- `name` (e.g. "Thanksgiving trip")
- `start_date`, `end_date`
- `is_active` — one active at a time is the norm, but multiple can exist and be swapped/flipped between
- `notify_parents_email` (bool) — whether claims on this schedule email the parents
- `created_by`, `created_at`

**ScheduleMembership** — links users to the schedule(s) they participate in, so someone on multiple schedules can flip between them.
- `user`, `schedule`

**Claim** — one person signing up for one day.
- `schedule`, `date`, `user`
- `note` (optional short text)
- `created_at`
- (No per-day cap — unlimited people per day. A day with a single claim is effectively "that person has the whole day"; a second person simply adds themselves.)

**Invite** (bones only in v1)
- `name`, `phone`, `role_label`, `partner_name` (optional)
- `token` (unique), `status` (`pending`/`accepted`/`expired`)
- `created_by`, `created_at`, `sent_at` (null until real send exists)

**HelpPage** (single editable page)
- `title`, `body` (rich text / HTML)
- `contact_info`
- related **HelpLink** rows: `label`, `url`
- related **HelpPhoto** rows: uploaded image, `caption`

---

## 5. User management (parents page)

A **parents-only** page (hidden and access-denied for Fam) to manage the family.

**Add / edit a Fam member:** name, phone, role label (unc/ant), and optional partner name for couples.

**Text-to-invite (stub in v1):** selecting "invite" creates an `Invite` record, generates an invite link/token, and calls a clearly-marked `send_sms()` service that currently **logs instead of sending**. The provider target is **Twilio**, so the stub is shaped to Twilio's API; wiring it up later means adding credentials and un-stubbing one function. `sent_at` stays null until then.

Parents can also deactivate/remove members and see who is on which schedule.

---

## 6. Calendar & scheduling

**Schedules as profiles.** Parents set a date range (`start_date`–`end_date`) per schedule. Normally one is active, but schedules are stored as named profiles so parents can swap the active one, and users on multiple schedules can flip between them.

**Claiming a day.** On the calendar, a Fam member taps a date to add their name. Additional Fam can add themselves to the same day (unlimited). Each claim can carry an optional **note**. Users remove their own claim; parents can remove anyone's.

**Views (responsive).** Month grid on desktop; a scrollable day-list on mobile. Each day shows the **names** of who has claimed it (not just a count).

**Notifications (optional email).** Per-schedule setting `notify_parents_email`. When on, a claim (and optionally a removal) sends an email to the parents. Email uses Django's SMTP backend — this is separate from and lighter than the deferred SMS work, so it's feasible in v1.

**Timezone:** America/New_York.

---

## 7. Help page

A single page, editable by parents, storing all values in the DB:

- Title and a **rich-text** body (bold, links, lists).
- A managed list of **links** (label + URL).
- **Photos** with captions.
- **Contact info** block.

Fam and parents can view it; only parents can edit.

---

## 8. Tech stack & architecture

| Layer | Choice |
|-------|--------|
| Framework | **Django** (server-rendered templates + a light responsive CSS framework; no separate SPA) |
| Database | **PostgreSQL** — best-supported production DB for Django, containerizes cleanly, handles concurrent claims safely |
| App server | Gunicorn |
| Reverse proxy | Nginx (TLS termination, static files) |
| Containerization | **docker-compose**, three services: `web` (Django+Gunicorn), `db` (Postgres), `nginx` |
| Host | **Oracle Cloud Infrastructure (OCI) Compute** VM, Ubuntu |
| TLS | HTTPS via Let's Encrypt on the mapped domain |
| SMS (later) | Twilio (stubbed in v1) |
| Email | Django SMTP backend (for parent claim notifications) |

**Responsive design** is a hard requirement: the app must work well on both mobile and desktop.

**Config via environment variables:** DB credentials, `SECRET_KEY`, allowed hosts, `OTP_PROVIDER_ENABLED` flag (drives the login failover in §3), Twilio creds (later), and SMTP creds.

---

## 9. Pages / routes (indicative)

- `/login` — phone entry → (OTP or failover) → session
- `/` — active schedule calendar (month grid / mobile day-list)
- `/schedule/<id>` — a specific schedule; flip between schedules a user belongs to
- `/day/<schedule>/<date>` — claim / add note / remove name
- `/help` — view help page
- `/admin-parents` — parents-only: user management, invites, schedule create/edit/activate, help-page editing, notification settings
- `/logout`

(Django's built-in `/admin` may be enabled for the parents as a superuser backstop.)

---

## 10. Phasing

**v1 (this spec):** everything above, kept intentionally small — phone login with failover, roles, parents admin, schedules as profiles, calendar with claims + notes, optional email-to-parents, editable help page, Dockerized OCI deployment with Postgres/Nginx/HTTPS. Invite and OTP senders are stubbed.

**Later (design accommodates, not built now):** turn on Twilio for real invites + OTP, recurring/auto-generated schedules, richer notifications, and any additional scaling. Because auth failover is a config flag, schedules are already multi-instance, and the DB/infra are production-grade, these are additive rather than rewrites.
