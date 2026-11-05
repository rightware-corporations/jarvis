(() => {
  "use strict";
  let token = "";
  let sessionId = "";
  let pending = false;
  let modelConfigured = false;
  const byId = (id) => document.getElementById(id);
  const transcript = byId("transcript");
  const input = byId("messageInput");
  const send = byId("sendBtn");
  const connection = byId("connectionButton");
  const dialog = byId("connectDialog");
  const note = byId("connectionNote");

  function status(text, active = false) {
    byId("statusText").textContent = text;
    byId("statusDot").classList.toggle("online", active);
  }
  function addMessage(role, value) {
    const item = document.createElement("article");
    item.className = "message " + role;
    const title = document.createElement("span");
    title.className = "role";
    title.textContent = role === "user" ? "YOU / REQUEST" : "JARVIS / RESPONSE";
    const p = document.createElement("p");
    p.textContent = value;
    item.append(title, p);
    transcript.append(item);
    transcript.scrollTop = transcript.scrollHeight;
  }
  async function api(path, options = {}) {
    const response = await fetch(path, {
      method: options.method || "GET",
      headers: {
        "Content-Type": "application/json",
        ...(token ? {"X-Jarvis-Lab-Token": token} : {}),
      },
      body: options.body ? JSON.stringify(options.body) : undefined,
      cache: "no-store",
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(data.detail || "NETWORK_ERROR");
    return data;
  }
  function updateControls() {
    input.disabled = !sessionId || pending;
    send.disabled = !sessionId || pending;
    byId("sessionState").textContent = sessionId ? "ACTIVE / MEMORY ONLY" : "NOT CONNECTED";
    connection.textContent = sessionId ? "CONNECTED / END SESSION" : "CONNECT / LAB ACCESS";
  }
  function endSession() {
    token = ""; sessionId = "";
    input.value = "";
    updateControls();
    status("NOT CONNECTED");
    note.textContent = "A ligação foi encerrada nesta página.";
  }
  async function inspect() {
    try {
      const health = await api("/api/v1/health");
      modelConfigured = Boolean(health.inference_configured);
      byId("backendState").textContent = "ONLINE";
      byId("inferenceState").textContent = modelConfigured ? "CONFIGURED / UNTESTED" : "NOT CONFIGURED";
      byId("networkText").textContent = "WEB / ONLINE";
      note.textContent = modelConfigured
        ? "Modelo configurado no servidor. A disponibilidade real será verificada ao conversar."
        : "Não há modelo Ollama configurado. A interface está acessível, mas o chat não está operacional.";
      status(modelConfigured ? "LAB ONLINE" : "MODEL OFFLINE", modelConfigured);
    } catch {
      byId("backendState").textContent = "UNAVAILABLE";
      byId("inferenceState").textContent = "UNKNOWN";
      byId("networkText").textContent = "NO RESPONSE";
      status("BACKEND OFFLINE");
      note.textContent = "A API do laboratório não está disponível.";
    }
    updateControls();
  }
  connection.addEventListener("click", () => {
    if (sessionId) { endSession(); return; }
    byId("connectError").textContent = "";
    dialog.showModal();
  });
  byId("cancelConnect").addEventListener("click", () => dialog.close());
  byId("connectForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    const candidate = byId("labToken").value;
    byId("connectError").textContent = "";
    token = candidate;
    try {
      const response = await api("/api/v1/sessions", {method: "POST"});
      sessionId = response.session_id;
      byId("labToken").value = "";
      dialog.close();
      updateControls();
      status("SESSION ONLINE", true);
      note.textContent = "Sessão iniciada. O laboratório não tem acesso às ferramentas do Windows.";
      input.focus();
    } catch (error) {
      token = "";
      byId("connectError").textContent = "Não foi possível ligar: " + error.message;
    }
  });
  byId("chatForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    const value = input.value.trim();
    if (!value || !sessionId || pending) return;
    pending = true; updateControls(); input.value = "";
    addMessage("user", value);
    status("PROCESSING", true);
    try {
      const answer = await api("/api/v1/chat", {method: "POST", body: {session_id: sessionId, message: value}});
      addMessage("assistant", answer.reply);
      status("SESSION ONLINE", true);
    } catch (error) {
      addMessage("assistant", "[ERRO DE LABORATÓRIO] " + error.message + ". Nenhuma acção foi executada.");
      if (error.message === "SESSION_NOT_FOUND" || error.message === "UNAUTHORIZED") endSession();
      else status("MODEL ERROR");
    } finally { pending = false; updateControls(); input.focus(); }
  });
  input.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      byId("chatForm").requestSubmit();
    }
  });
  document.addEventListener("visibilitychange", () => {
    if (document.visibilityState === "hidden") return;
    if (!sessionId) inspect();
  });
  inspect();
})();
