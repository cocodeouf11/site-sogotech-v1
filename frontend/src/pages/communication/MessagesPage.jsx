import { useEffect, useRef, useState } from "react";
import { Layout } from "../../components/layout/Layout";
import { api } from "../../lib/api";
import { useAuth } from "../../context/AuthContext";
import { Input } from "../../components/ui/input";
import { Button } from "../../components/ui/button";
import { Paperclip, Send } from "lucide-react";

export default function MessagesPage() {
  const { user } = useAuth();
  const [users, setUsers] = useState([]);
  const [active, setActive] = useState(null);
  const [messages, setMessages] = useState([]);
  const [text, setText] = useState("");
  const fileRef = useRef(null);
  const bottomRef = useRef(null);

  useEffect(() => {
    api.get("/users").then((r) => setUsers(r.data.filter((u) => u.id !== user.id)));
  }, []);

  const loadMessages = async (uid) => {
    setActive(uid);
    const { data } = await api.get(`/communication/messages?with_user=${uid}`);
    setMessages(data);
  };

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages]);

  const send = async () => {
    if (!text.trim() || !active) return;
    await api.post("/communication/messages", { to_user_id: active, content: text });
    setText("");
    loadMessages(active);
  };

  const sendFile = async (e) => {
    const file = e.target.files[0];
    if (!file || !active) return;
    const fd = new FormData();
    fd.append("to_user_id", active);
    fd.append("file", file);
    await api.post("/communication/messages/attachment", fd, { headers: { "Content-Type": "multipart/form-data" } });
    loadMessages(active);
  };

  return (
    <Layout title="Messagerie interne">
      <div className="grid grid-cols-4 gap-4 h-[calc(100vh-160px)]">
        <div className="rounded-xl border border-border bg-card overflow-y-auto" data-testid="messages-user-list">
          {users.map((u) => (
            <button
              key={u.id}
              data-testid={`messages-user-${u.id}`}
              onClick={() => loadMessages(u.id)}
              className={`w-full text-left px-4 py-3 border-b border-border text-sm hover:bg-accent transition-colors duration-200 ${active === u.id ? "bg-accent" : ""}`}
            >
              <p className="font-medium">{u.prenom} {u.nom}</p>
              <p className="text-xs text-muted-foreground">{u.poste}</p>
            </button>
          ))}
        </div>
        <div className="col-span-3 rounded-xl border border-border bg-card flex flex-col">
          <div className="flex-1 overflow-y-auto p-4 space-y-3" data-testid="messages-thread">
            {messages.map((m) => (
              <div key={m.id} className={`flex ${m.from_user_id === user.id ? "justify-end" : "justify-start"}`}>
                <div className={`max-w-sm px-3 py-2 rounded-xl text-sm ${m.from_user_id === user.id ? "bg-primary text-primary-foreground" : "bg-secondary"}`}>
                  {m.content && <p>{m.content}</p>}
                  {m.attachment_url && (
                    <a href={`${process.env.REACT_APP_BACKEND_URL}${m.attachment_url}`} target="_blank" rel="noreferrer" className="underline text-xs flex items-center gap-1">
                      <Paperclip size={12} /> {m.attachment_name}
                    </a>
                  )}
                </div>
              </div>
            ))}
            <div ref={bottomRef} />
          </div>
          {active && (
            <div className="p-3 border-t border-border flex gap-2">
              <input type="file" ref={fileRef} className="hidden" onChange={sendFile} data-testid="messages-file-input" />
              <Button variant="outline" size="icon" onClick={() => fileRef.current.click()} data-testid="messages-attach-button"><Paperclip size={16} /></Button>
              <Input data-testid="messages-text-input" value={text} onChange={(e) => setText(e.target.value)} onKeyDown={(e) => e.key === "Enter" && send()} placeholder="Votre message..." />
              <Button onClick={send} data-testid="messages-send-button"><Send size={16} /></Button>
            </div>
          )}
        </div>
      </div>
    </Layout>
  );
}
