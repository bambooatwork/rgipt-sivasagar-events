/* =====================================================================
   Data layer — all reads/writes go through here.

   The Firebase SDK is imported *dynamically* so that a CDN hiccup (or an
   unconfigured project) never blanks the page: the shell still renders and
   the user gets a clear message instead of an empty screen.
   ===================================================================== */
import { firebaseConfig } from "./firebase-config.js";

const SDK = "https://www.gstatic.com/firebasejs/10.12.2";

export const COLLECTIONS = {
  events: "events",
  announcements: "announcements",
  registrations: "registrations",
  messages: "messages"
};

export function isConfigured() {
  return Boolean(firebaseConfig.apiKey && firebaseConfig.projectId);
}

let app = null, db = null, auth = null, sdk = null;

async function loadSdk() {
  if (sdk) return sdk;
  const [appMod, fsMod, authMod] = await Promise.all([
    import(`${SDK}/firebase-app.js`),
    import(`${SDK}/firebase-firestore.js`),
    import(`${SDK}/firebase-auth.js`)
  ]);
  sdk = { appMod, fsMod, authMod };
  return sdk;
}

/** Connects to Firebase. Returns false when no config has been supplied. */
export async function init() {
  if (!isConfigured()) return false;
  if (db) return true;
  const { appMod, fsMod, authMod } = await loadSdk();
  app = appMod.initializeApp(firebaseConfig);
  db = fsMod.getFirestore(app);
  auth = authMod.getAuth(app);
  return true;
}

async function ready() {
  await init();
  if (!db) throw new Error("Firebase is not configured yet.");
  return sdk;
}

const col = (name) => sdk.fsMod.collection(db, name);

const toDate = (v) => {
  if (!v) return null;
  if (typeof v === "string") return v;                    // 'YYYY-MM-DD'
  if (v.toDate) return v.toDate().toISOString().slice(0, 10);
  return String(v);
};

function normaliseEvent(id, d) {
  return {
    id,
    title: d.title || "",
    category: d.category || "Technical",
    shortDescription: d.shortDescription || "",
    description: d.description || "",
    organizer: d.organizer || "RGIPT Sivasagar Campus",
    venue: d.venue || "",
    eventDate: toDate(d.eventDate),
    endDate: toDate(d.endDate),
    startTime: d.startTime || "",
    endTime: d.endTime || "",
    registrationDeadline: toDate(d.registrationDeadline),
    capacity: Number(d.capacity || 0),
    fee: Number(d.fee || 0),
    teamSize: d.teamSize || "Individual",
    contactEmail: d.contactEmail || "",
    accent: d.accent || "teal",
    isFeatured: Boolean(d.isFeatured),
    isPublished: d.isPublished !== false
  };
}

function normaliseAnnouncement(id, d) {
  return {
    id,
    title: d.title || "",
    body: d.body || "",
    category: d.category || "General",
    isPinned: Boolean(d.isPinned),
    isPublished: d.isPublished !== false,
    publishedAt: d.publishedAt || d.createdAt || ""
  };
}

export const today = () => new Date().toISOString().slice(0, 10);
export function isPast(e) { return (e.endDate || e.eventDate || "") < today(); }

/* ------------------------------------------------------------- events */
export async function listEvents({ publishedOnly = true } = {}) {
  await ready();
  // The where-clause is required by the security rule that permits public reads
  // of published documents only.
  const ref = publishedOnly
    ? sdk.fsMod.query(col(COLLECTIONS.events), sdk.fsMod.where("isPublished", "==", true))
    : col(COLLECTIONS.events);
  const snap = await sdk.fsMod.getDocs(ref);
  const rows = snap.docs.map((d) => normaliseEvent(d.id, d.data()));
  rows.sort((a, b) => (a.eventDate || "").localeCompare(b.eventDate || ""));
  return rows;
}

export async function getEvent(id) {
  await ready();
  const s = await sdk.fsMod.getDoc(sdk.fsMod.doc(db, COLLECTIONS.events, id));
  return s.exists() ? normaliseEvent(s.id, s.data()) : null;
}

export async function saveEvent(id, data) {
  await ready();
  if (id) { await sdk.fsMod.updateDoc(sdk.fsMod.doc(db, COLLECTIONS.events, id), data); return id; }
  const ref = await sdk.fsMod.addDoc(col(COLLECTIONS.events), { ...data, createdAt: new Date().toISOString() });
  return ref.id;
}

export async function deleteEvent(id) {
  await ready();
  await sdk.fsMod.deleteDoc(sdk.fsMod.doc(db, COLLECTIONS.events, id));
}

/* ------------------------------------------------------ announcements */
export async function listAnnouncements({ publishedOnly = true } = {}) {
  await ready();
  const ref = publishedOnly
    ? sdk.fsMod.query(col(COLLECTIONS.announcements), sdk.fsMod.where("isPublished", "==", true))
    : col(COLLECTIONS.announcements);
  const snap = await sdk.fsMod.getDocs(ref);
  const rows = snap.docs.map((d) => normaliseAnnouncement(d.id, d.data()));
  rows.sort((a, b) => (b.publishedAt || "").localeCompare(a.publishedAt || ""));
  return rows;
}

export async function getAnnouncement(id) {
  await ready();
  const s = await sdk.fsMod.getDoc(sdk.fsMod.doc(db, COLLECTIONS.announcements, id));
  return s.exists() ? normaliseAnnouncement(s.id, s.data()) : null;
}

export async function saveAnnouncement(id, data) {
  await ready();
  if (id) { await sdk.fsMod.updateDoc(sdk.fsMod.doc(db, COLLECTIONS.announcements, id), data); return id; }
  const ref = await sdk.fsMod.addDoc(col(COLLECTIONS.announcements), {
    ...data, publishedAt: new Date().toISOString(), createdAt: new Date().toISOString()
  });
  return ref.id;
}

export async function deleteAnnouncement(id) {
  await ready();
  await sdk.fsMod.deleteDoc(sdk.fsMod.doc(db, COLLECTIONS.announcements, id));
}

/* ------------------------------------------------------- registrations */
export function ticketCode() {
  return "RGI" + Math.random().toString(36).slice(2, 8).toUpperCase();
}

export async function createRegistration(data) {
  await ready();
  const payload = {
    ...data, status: "confirmed", ticketCode: ticketCode(),
    createdAt: new Date().toISOString()
  };
  const ref = await sdk.fsMod.addDoc(col(COLLECTIONS.registrations), payload);
  return { id: ref.id, ...payload };
}

export async function listRegistrations() {
  await ready();
  const snap = await sdk.fsMod.getDocs(col(COLLECTIONS.registrations));
  const rows = snap.docs.map((d) => ({ id: d.id, ...d.data() }));
  rows.sort((a, b) => (b.createdAt || "").localeCompare(a.createdAt || ""));
  return rows;
}

export async function updateRegistration(id, patch) {
  await ready();
  await sdk.fsMod.updateDoc(sdk.fsMod.doc(db, COLLECTIONS.registrations, id), patch);
}

export async function deleteRegistration(id) {
  await ready();
  await sdk.fsMod.deleteDoc(sdk.fsMod.doc(db, COLLECTIONS.registrations, id));
}

export async function countRegistrationsFor(eventId) {
  await ready();
  const snap = await sdk.fsMod.getDocs(
    sdk.fsMod.query(col(COLLECTIONS.registrations), sdk.fsMod.where("eventId", "==", eventId)));
  return snap.size;
}

/* ------------------------------------------------------------ messages */
export async function createMessage(data) {
  await ready();
  await sdk.fsMod.addDoc(col(COLLECTIONS.messages), { ...data, isRead: false, createdAt: new Date().toISOString() });
}

export async function listMessages() {
  await ready();
  const snap = await sdk.fsMod.getDocs(col(COLLECTIONS.messages));
  const rows = snap.docs.map((d) => ({ id: d.id, ...d.data() }));
  rows.sort((a, b) => (b.createdAt || "").localeCompare(a.createdAt || ""));
  return rows;
}

export async function updateMessage(id, patch) {
  await ready();
  await sdk.fsMod.updateDoc(sdk.fsMod.doc(db, COLLECTIONS.messages, id), patch);
}

export async function deleteMessage(id) {
  await ready();
  await sdk.fsMod.deleteDoc(sdk.fsMod.doc(db, COLLECTIONS.messages, id));
}

/* --------------------------------------------------------------- auth */
export async function watchAuth(cb) {
  await init();
  if (!auth) return;
  sdk.authMod.onAuthStateChanged(auth, (user) => cb(user));
}

export async function login(email, password) {
  await ready();
  return sdk.authMod.signInWithEmailAndPassword(auth, email, password);
}

export async function logout() {
  await ready();
  return sdk.authMod.signOut(auth);
}

export async function changePassword(newPassword) {
  await ready();
  if (!auth.currentUser) throw new Error("Not signed in");
  return sdk.authMod.updatePassword(auth.currentUser, newPassword);
}

/* -------------------------------------------------------- starter data */
export async function loadStarterData() {
  const res = await fetch("starter-data.json", { cache: "no-store" });
  const data = await res.json();
  let n = 0;
  for (const e of data.events) { await saveEvent(null, e); n++; }
  for (const a of data.announcements) { await saveAnnouncement(null, a); n++; }
  return n;
}

/* -------------------------------------------------------------- utils */
export function formatDate(iso, opts) {
  if (!iso) return "";
  const d = new Date(iso + "T00:00:00");
  if (isNaN(d)) return iso;
  return d.toLocaleDateString("en-GB", opts || { day: "2-digit", month: "short", year: "numeric" });
}

export function inr(n) {
  const v = Number(n || 0);
  return v === 0 ? "Free" : "\u20b9" + v.toLocaleString("en-IN");
}

export function escapeHtml(s) {
  return String(s == null ? "" : s).replace(/[&<>"']/g, (c) => (
    { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]
  ));
}
