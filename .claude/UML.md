# BabyCal — UML Documentation

Companion to [SYSTEM_DESIGN.md](SYSTEM_DESIGN.md). Derived from [QA.md](QA.md). Diagrams use Mermaid and render in VSCode (with a Mermaid preview extension) and on GitHub.

---

## 1. Domain class diagram

```mermaid
classDiagram
    class User {
        +UUID id
        +string phone_number  %% E.164, unique
        +string display_name
        +Role role  %% PARENT | FAM
        +FamLabel? fam_label  %% UNC | ANT, cosmetic only
        +bool is_active
        +datetime created_at
        +claim_day(day, note) Claim
        +remove_own_claim(claim)
    }

    class AdditionalFamMember {
        +UUID id
        +string name
        %% purely a display name attached to a couple's Fam account
    }

    class Baby {
        +UUID id
        +string name  %% "Cookie" | "Snoopy"
        +string? photo_url
        %% no login, profile only
    }

    class SchedulePeriod {
        +UUID id
        +string name  %% e.g. "August trip"
        +date start_date
        +date end_date
        +bool is_active
        +datetime created_at
    }

    class SchedulePeriodMembership {
        +UUID id
        %% join table: which users can see/use this schedule
    }

    class Claim {
        +UUID id
        +date claim_date
        +string? note
        +datetime created_at
        +remove()  %% self, or by any Parent
    }

    class Invite {
        +UUID id
        +string phone_number
        +UUID token
        +Role assigned_role
        +InviteStatus status  %% PENDING | ACCEPTED | EXPIRED
        +datetime created_at
        +datetime? accepted_at
        +send()  %% calls SmsClient.send_sms(), stubbed
    }

    class LoginOTP {
        +UUID id
        +string phone_number
        +string code
        +datetime expires_at
        +datetime? verified_at
        +bool fallback_used  %% true when sent with no SMS provider configured
        +bool verify(code) bool
    }

    class HelpPage {
        +UUID id
        +string title
        +text body_richtext
        +datetime updated_at
    }

    class HelpLink {
        +UUID id
        +string label
        +string url
        +int order
    }

    class NotificationSetting {
        +bool notify_on_claim
        +string? email
    }

    class SmsClient {
        <<service>>
        +send_sms(phone, message) SendResult
        %% stub today: logs instead of calling Twilio
    }

    class EmailClient {
        <<service>>
        +send_email(to, subject, body) SendResult
    }

    User "1" --> "0..1" NotificationSetting : has
    User "1" --> "0..*" AdditionalFamMember : lists (couples)
    User "1" --> "0..*" Claim : makes
    User "1" --> "0..*" Invite : sends
    User "0..*" --> "0..*" SchedulePeriod : SchedulePeriodMembership
    SchedulePeriod "1" --> "0..*" Claim : contains
    SchedulePeriod "0..1" --> "0..1" Baby : is for
    HelpPage "1" --> "0..*" HelpLink : has
    Invite ..> SmsClient : uses
    NotificationSetting ..> EmailClient : uses
```

**Key decisions encoded above**
- A day is not its own row — a `Claim` carries `claim_date` directly against a `SchedulePeriod`, and multiple `Claim`s can share the same date (unlimited people per day, per QA §1.3). "Whole day belongs to one claimant unless a second family joins" is a UI/business rule, not a schema constraint.
- `AdditionalFamMember` is deliberately a thin, login-less list of extra display names on a Fam `User` — for couples — matching "this is completely additional" (QA §4.1).
- `SchedulePeriodMembership` is a many-to-many join so a user can belong to and switch between multiple active schedule "profiles" (QA §5.1).
- `fam_label` (unc/ant) is cosmetic only, per QA §2.1 — it carries no permission difference.

---

## 2. Entity-relationship diagram (DB schema)

```mermaid
erDiagram
    USER ||--o{ ADDITIONAL_FAM_MEMBER : "lists"
    USER ||--o{ CLAIM : "makes"
    USER ||--o{ INVITE : "sends"
    USER ||--o| NOTIFICATION_SETTING : "configures"
    USER }o--o{ SCHEDULE_PERIOD : "via SCHEDULE_MEMBERSHIP"
    SCHEDULE_PERIOD ||--o{ CLAIM : "contains"
    SCHEDULE_PERIOD }o--o| BABY : "is for"
    HELP_PAGE ||--o{ HELP_LINK : "has"
    USER ||--o{ LOGIN_OTP : "requests"

    USER {
        uuid id PK
        string phone_number UK
        string display_name
        string role "PARENT|FAM"
        string fam_label "UNC|ANT|null"
        bool is_active
        datetime created_at
    }
    ADDITIONAL_FAM_MEMBER {
        uuid id PK
        uuid user_id FK
        string name
    }
    BABY {
        uuid id PK
        string name
        string photo_url
    }
    SCHEDULE_PERIOD {
        uuid id PK
        string name
        date start_date
        date end_date
        bool is_active
        uuid baby_id FK
        uuid created_by FK
        datetime created_at
    }
    SCHEDULE_MEMBERSHIP {
        uuid id PK
        uuid user_id FK
        uuid schedule_period_id FK
    }
    CLAIM {
        uuid id PK
        uuid schedule_period_id FK
        uuid user_id FK
        date claim_date
        text note
        datetime created_at
    }
    INVITE {
        uuid id PK
        string phone_number
        uuid token UK
        string assigned_role
        string status "PENDING|ACCEPTED|EXPIRED"
        uuid invited_by FK
        datetime created_at
        datetime accepted_at
    }
    LOGIN_OTP {
        uuid id PK
        string phone_number
        string code
        datetime expires_at
        datetime verified_at
        bool fallback_used
    }
    HELP_PAGE {
        uuid id PK
        string title
        text body_richtext
        uuid updated_by FK
        datetime updated_at
    }
    HELP_LINK {
        uuid id PK
        uuid help_page_id FK
        string label
        string url
        int order
    }
    NOTIFICATION_SETTING {
        uuid id PK
        uuid user_id FK
        bool notify_on_claim
        string email
    }
```

`CLAIM` has a unique constraint on `(schedule_period_id, claim_date, user_id)` — one claim per user per day, but no limit on distinct users per day (unlimited fam per QA §1.3).

---

## 3. Invite lifecycle (state diagram)

```mermaid
stateDiagram-v2
    [*] --> PENDING : Parent creates invite\n(token generated, send_sms() stub fires)
    PENDING --> ACCEPTED : Fam opens link,\nlogs in successfully
    PENDING --> EXPIRED : token TTL elapses
    ACCEPTED --> [*]
    EXPIRED --> [*]
```

---

## 4. Login sequence (use-case level)

```mermaid
sequenceDiagram
    actor U as User
    participant W as Django views (accounts)
    participant O as LoginOTP
    participant S as SmsClient

    U->>W: submit phone number
    W->>W: normalize to E.164
    W->>O: create OTP record
    W->>S: send_sms(phone, code)
    alt Twilio configured
        S-->>W: sent
        W-->>U: prompt for code
        U->>W: submit code
        W->>O: verify(code)
        O-->>W: valid
    else no provider configured
        S-->>W: fallback_no_verification (logged, not sent)
        W->>O: mark fallback_used=true, auto-verify
    end
    W-->>U: establish long-lived session, redirect to calendar
```

---

## 5. Use-case diagram

```mermaid
flowchart TB
    Parent((Parent))
    Fam((Fam))

    subgraph BabyCal
        UC1([Log in via phone])
        UC2([View schedule / month grid])
        UC3([Claim a day + note])
        UC4([Remove own claim])
        UC5([Remove any claim])
        UC6([Manage users & invites])
        UC7([Create/edit schedule period])
        UC8([Switch active schedule])
        UC9([Edit help page])
        UC10([View help page])
        UC11([Toggle claim email alerts])
    end

    Parent --> UC1
    Parent --> UC2
    Parent --> UC3
    Parent --> UC4
    Parent --> UC5
    Parent --> UC6
    Parent --> UC7
    Parent --> UC8
    Parent --> UC9
    Parent --> UC10
    Parent --> UC11

    Fam --> UC1
    Fam --> UC2
    Fam --> UC3
    Fam --> UC4
    Fam --> UC8
    Fam --> UC10
```
