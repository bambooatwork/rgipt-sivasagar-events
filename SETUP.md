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
4. Still in Authentication, open **Settings → Authorized domains** and click
   **Add domain**. Add **`bambooatwork.github.io`**. Without this the admin sign-in on
   the live site fails with `auth/unauthorized-domain`. (`localhost` is already on the
   list, which is why it works when you run the site on your own machine.)

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

## 5. Register yourself as an admin, then publish the rules (important)

### 5a. Register your account as an admin — do this FIRST

The rules deliberately do **not** treat "signed in" as "admin". Email/Password sign-in
is enabled and the web API key is public, so **anyone on the internet can create a
Firebase account** by calling Google's REST API directly. If the rules trusted any
signed-in user, a stranger could read every student registration and rewrite your
events. (This was tested and confirmed — see the Security section of the README.)

So an admin is an account that is **listed in the `admins` collection**:

1. **Authentication → Users** → copy your account's **UID**.
2. **Firestore Database → Start collection** → collection ID **`admins`**.
3. Set the **Document ID** to the **UID** you copied, add a field
   `role` (string) with the value `admin`, and save.

Do this **before** 5b, or you will lock yourself out of your own admin panel.

### 5b. Publish the rules

The rules are kept in **[`firestore.rules`](firestore.rules)** at the root of this
repository, so they are version-controlled next to the code instead of living only in
this document.

**Option A — Firebase CLI (recommended):**

```bash
npm install -g firebase-tools
firebase login
firebase deploy --only firestore:rules
```

`firebase.json` and `.firebaserc` are already configured, so this deploys straight to
the `rgipt-event-management` project.

**Option B — the Firebase console:** open **Firestore Database → Rules**, replace
everything with the contents of `firestore.rules`, and click **Publish**.

In plain terms: the public can **read** published events and announcements and
**create** registrations and contact messages — but only an account listed in `admins`
can read the registration list, read the inbox, or change anything.

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
- **Signed in, but every action says "Missing or insufficient permissions"** — your
  account is not listed in the `admins` collection. See step 5a.
- **Can't sign in** — the user must be created under Authentication → Users (step 3),
  and Email/Password must be enabled.
- **`auth/unauthorized-domain` on the live site** — `bambooatwork.github.io` is not in
  Authentication → Settings → Authorized domains. See step 3.4.
- **Quota** — the free Spark plan is generous (50k reads/day). For a campus event
  site this is plenty.

## Adding more admins

Adding an admin is **two** steps, and that is deliberate: a Firebase Auth account on
its own is *not* an admin, because anyone can create one with the public API key.

1. **Authentication → Users → Add user** — create the account.
2. Copy that account's **UID**, then add a document with that ID to the **`admins`**
   collection: Firestore → `admins` → **Add document** → Document ID = the UID,
   field `role` (string) = `admin`.

To **revoke** access, delete the document from `admins`; to remove the account
entirely, delete the user in Authentication as well.

Keep the list short and use strong passwords.
