# QA — Cat Scheduling Webapp Spec

Answer inline under each **A:**. Each question has a recommended default so you can just write "confirm" if you agree. Once answered, I'll fold these into a refined spec doc.

---

## 1. Purpose & scope

**Q1.1** What is the calendar actually scheduling? (e.g. who is watching Cookie/Snoopy on a given day, feeding/visit sign-ups, drop-in slots.) The whole data model depends on this.
> **A:** feeding visits while parents are out of town

**Q1.2** Is a "spot" a whole day, or are there multiple slots per day (morning/evening)? Recommended default: one claimable day, multiple people can join it.
> **A:** If only 1 name on spot, then whole day, but for scenario where 2 is needed, an additional fam can be added. Lets make it so they can also leave a note

**Q1.3** Is there a max number of people per day, or unlimited? Recommended default: unlimited.
> **A:** unlimited

---

## 2. Users & roles

**Q2.1** Confirm the role list and who is what:
- **Parent** = Wil (7329861906), Max (9734891380) — full admin.
- **Fam** = aunts/uncles ("unc" male / "ant" female — cosmetic label only, same permissions).
- **Baby** = Cookie / Snoopy — is this an actual login, or just a profile/cat with no account? Recommended default: Baby is a non-login profile, not a user who signs in.
> **A:** just a profile no account. fam cannot make parent changes in admin page. They can only put their name down and make a note, or remove their name from a spot.

**Q2.2** What exactly can each role do? Recommended default:
- Parent: manage users, set calendar period, edit help page, claim days.
- Fam: claim/join days, view help page.
- Baby: n/a (no login).
Confirm or adjust.
> **A:**coonfirm

**Q2.3** Can Fam remove themselves from a day after claiming? Can a parent remove anyone? Recommended default: yes to both.
> **A:**yes to both

---

## 3. Login (phone number, no password)

**Q3.1** This is the biggest open item. "No password" needs *something* to prove the person owns the number. Normally that's an SMS one-time code — but you don't have a texting API yet. How should login work in the meantime? Options:
- (a) Phone number only, no verification — anyone who types a known number is in. Simple, insecure. Fine for a tiny family app.
- (b) Phone + a shared/simple PIN per user until SMS is wired up.
- (c) Build the SMS-OTP flow now but stub the send step (log the code instead of texting), so it's real once you add an API key.
Recommended default: **(c)** — real flow, stubbed sender.
> **A:** c, but have it failover to doing no verification since we have no set up

**Q3.2** Should a login session persist ("remember me" so they don't re-enter their number each visit)? Recommended default: yes, long-lived session.
> **A:** yes 

**Q3.3** Phone number format — store/normalize to E.164 (+1XXXXXXXXXX) and accept messy input like "(732) 986-1906"? Recommended default: yes.
> **A:**yes

---

## 4. User management (parents page)

**Q4.1** The parents-only page — what fields when adding a Fam member? Recommended default: name, phone, role label (unc/ant).
> **A:** yes, but lets add additional names for couples invovled. this is completely additional

**Q4.2** Text-to-invite: you want the "bones" only for now. Confirm the stub should: create the invite record, generate an invite link/token, and have a clearly-marked `send_sms()` function that does nothing yet (logs instead). Real send added later when you have an API key.
> **A:**yes

**Q4.3** Which SMS provider are you likely to use later (Twilio, AWS SNS, other)? Affects how the stub is shaped. Recommended default: Twilio.
> **A:**twilio

---

## 5. Calendar

**Q5.1** "Admin sets the time period (day x – day y)" — is there one active period at a time, or many overlapping periods? Recommended default: one active period, editable by parents.
> **A:** one active period, but set them as profiles so we can swap out the schedule for another one if needed, or can have multiple ones that users can flip between if they are on multiple schedules

**Q5.2** View — month grid, week, or simple list of dates in the period? On mobile especially. Recommended default: month grid on desktop, scrollable day-list on mobile.
> **A:** default

**Q5.3** Should people see *who* claimed each day, or just a count? Recommended default: show names/avatars.
> **A:** yes can show names

**Q5.4** Any notifications when someone claims a day (e.g. email/text to parents)? Recommended default: none for v1 (defer with the SMS work).
> **A:** option to send email to parents. 

---

## 6. Help page

**Q6.1** Confirm: parents edit a title + free-text body + a list of links, all stored in the DB and rendered on the page. Anything else on it (photos, contact info)?
> **A:** sure to all 

**Q6.2** Rich text or plain text for the body? Recommended default: simple rich text (bold/links/lists).
> **A:** rich text

---

## 7. Tech & hosting

**Q7.1** Database — recommendation is **PostgreSQL** (best-supported production DB for Django, strong with Docker, handles concurrency for calendar claims cleanly). SQLite would work given the tiny scale but doesn't containerize as cleanly for multi-write. Confirm Postgres.
> **A:** confirm

**Q7.2** "Oracle VCI" — I'm reading this as an **Oracle Cloud Infrastructure (OCI) Compute** VM running Ubuntu. Correct? If you meant Oracle VirtualBox or something else, say so.
> **A:**you are correct. 

**Q7.3** Docker layout — recommendation: `docker-compose` with three services (Django+Gunicorn app, Postgres, Nginx reverse proxy). Confirm, or do you want app + DB only and skip Nginx?
> **A:** confirm

**Q7.4** Domain name + HTTPS — do you have a domain, and should the spec include TLS setup (Let's Encrypt)? Recommended default: yes, include it.
> **A:**yes

**Q7.5** Frontend approach — Django server-rendered templates (simplest, mobile-friendly with responsive CSS) vs. a separate JS framework. Recommended default: Django templates + a light CSS framework, no separate SPA.
> **A:**default

**Q7.6** Timezone for the calendar. Recommended default: America/New_York (US Eastern, matching the phone numbers).
> **A:** default

---

## 8. Nice-to-haves / out of scope

**Q8.1** Anything you explicitly want **excluded** from v1 to keep it small? (e.g. no notifications, no photo uploads, no recurring schedules.)
> **A:**yes keep it small for first release. but keep ease of scale in mind.

**Q8.2** Anything missing above that you already know you want?
> **A:** nope looks good. 
