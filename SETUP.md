# Setup — connect the site to Firebase (about 10 minutes, free)

GitHub Pages can only serve static files, so the site keeps its files on GitHub and
uses **Firebase** (Google's free app backend) for the database and the admin login.
Everything below happens in your browser — nothing to install, nothing running on
your laptop.

You need a Google account. The free "Spark" plan is more than enough.

---

## 1. Create the Firebase project

1. Go to **https://console.firebase.google.com** and click **Add project**.
2. Name it something like `rgipt-sivasagar-events` and continue.
3. You can turn Google Analytics **off** (not needed). Click **Create project**.

## 2. Create the database (Firestore)

1. In the left sidebar click **Build → Firestore Database**.
2. Click **Create database**.
3. Choose **Start in production mode** (we set proper rules in step 5).
4. Pick a location close to India — `asia-south1 (Mumbai)` is a good choice.
5. Click **Enable**.

## 3. Turn on the admin login

1. Left sidebar → **Build → Authentication** → **Get started**.
2. Under **Sign-in method**, enable **Email/Password**.
3. Go to the **Users** tab → **Add user**. Enter the email and password you want to
   use as the admin login. **This is your admin account** — remember it.
   (You can add more admin accounts the same way later.)

## 4. Paste your config into the site

1. In Firebase, click the **gear icon → Project settings**.
2. Scroll to **Your apps** → click the **`</>`** (web) icon → register an app
   (nickname anything, no hosting needed).
3. Firebase shows a `firebaseConfig` block. Copy those values into
   **`docs/js/firebase-config.js`** in this repo:

```js
export const firebaseConfig = {
  apiKey: "AIza...",
  authDomain: "your-project.firebaseapp.com",
  projectId: "your-project",
  storageBucket: "your-project.appspot.com",
  messagingSenderId: "1234567890",
  appId: "1:1234567890:web:abcdef"
};
```

> **These values are public on purpose.** A Firebase web API key is not a secret —
> your data is protected by the security rules below, not by hiding this key. It is
> safe to commit.

Commit and push. The site will stop showing "backend not configured" and start
reading from your database (it will be empty until step 6).

## 5. Add the security rules (important)

Without this, anyone could read or wipe your data. In Firebase go to
**Firestore Database → Rules**, replace everything with the following, and click
**Publish**:

```
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {

    // Anyone can read PUBLISHED events and announcements.
    // Only a signed-in admin can create, edit or delete them.
    match /events/{doc} {
      allow read:  if resource.data.isPublished == true || request.auth != null;
      allow write: if request.auth != null;
    }
    match /announcements/{doc} {
      allow read:  if resource.data.isPublished == true || request.auth != null;
      allow write: if request.auth != null;
    }

    // Anyone can register for an event (create only), with basic checks.
    // Only a signed-in admin can read, change or delete registrations.
    match /registrations/{doc} {
      allow create: if request.resource.data.name is string
                    && request.resource.data.name.size() > 0
                    && request.resource.data.name.size() < 120
                    && request.resource.data.email is string
                    && request.resource.data.email.matches('.*@.*')
                    && request.resource.data.eventId is string;
      allow read, update, delete: if request.auth != null;
    }

    // Contact form: anyone can send, only admins can read.
    match /messages/{doc} {
      allow create: if request.resource.data.name is string
                    && request.resource.data.message is string
                    && request.resource.data.message.size() < 4000;
      allow read, update, delete: if request.auth != null;
    }
  }
}
```

In plain terms: the public can **read** events and **create** registrations, but only
you (signed in) can read the registration list or change anything.

## 6. Load the starter content

1. Go to your site → **Admin** (top-right) → sign in with the account from step 3.
2. On the dashboard click **Load starter data**.

This writes the 7 real campus events and 4 announcements into your database. Edit
them freely — dates, descriptions, capacity — and add your own.

> **No dummy data:** no registrations are created, and nothing is invented. The
> starter events are the campus's real events; confirm the exact dates for this
> session and edit them in the admin panel.

## 7. Publish on GitHub Pages

Repo → **Settings → Pages → Build and deployment**:
- **Source:** Deploy from a branch
- **Branch:** `main` · **Folder:** `/docs`
- **Save**

Your site appears at `https://<username>.github.io/<repo>/`.

---

## What works where

| Feature | Where it runs |
|---|---|
| Public site (events, announcements, faculty, about, contact) | GitHub Pages |
| Registration (writes to Firestore) | GitHub Pages |
| Admin panel (login, CRUD) | GitHub Pages — at `/admin.html` |
| Database | Firebase Firestore |
| Admin accounts | Firebase Authentication |

There is **no server to run anywhere**. The Flask app in the repo root is optional
and only for local/offline use.

---

## Troubleshooting

- **"Backend not configured yet"** — `docs/js/firebase-config.js` still has empty
  values, or you haven't pushed the change.
- **"Missing or insufficient permissions"** — the rules in step 5 aren't published,
  or your data has no `isPublished` field. Re-run step 6.
- **Nothing shows on the site but the admin works** — you're signed in as admin on a
  public page; the public read rule allows published documents, so make sure events
  are marked **Published**.
- **Can't sign in** — the user must be created under Authentication → Users (step 3),
  and Email/Password must be enabled.
- **Quota** — the free Spark plan is generous (50k reads/day). For a campus event
  site this is plenty.

## Adding more admins

Firebase console → Authentication → Users → **Add user**. Any account you create
there can sign in at `/admin.html`. There is no separate "roles" system — every
account is an admin, so keep the list short and use strong passwords.
