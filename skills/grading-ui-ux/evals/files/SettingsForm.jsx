import { useState } from "react";

export default function SettingsForm({ onSave }) {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [tz, setTz] = useState("");
  const [saving, setSaving] = useState(false);

  async function submit() {
    setSaving(true);
    await onSave({ name, email, tz });
    setSaving(false);
  }

  return (
    <div style={{ padding: 7, fontSize: 13 }}>
      <div style={{ fontWeight: "bold", fontSize: 13 }}>Settings</div>
      <input placeholder="Name" value={name} onChange={(e) => setName(e.target.value)} style={{ margin: 3 }} />
      <input placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} style={{ margin: 3 }} />
      <input placeholder="Timezone (e.g. -05:00)" value={tz} onChange={(e) => setTz(e.target.value)} style={{ margin: 3 }} />
      <div onClick={submit} style={{ color: "#9ec5fe", cursor: "pointer", marginTop: 3 }}>
        Submit
      </div>
      <div onClick={() => fetch("/api/account", { method: "DELETE" })} style={{ color: "#9ec5fe", cursor: "pointer" }}>
        Delete account
      </div>
      <span style={{ display: saving ? "inline" : "none" }}>...</span>
    </div>
  );
}
