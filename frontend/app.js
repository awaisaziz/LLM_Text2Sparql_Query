document.addEventListener("DOMContentLoaded", () => {
  const questionInput = document.getElementById("question");
  const providerSelect = document.getElementById("provider");
  const modelInput = document.getElementById("model");
  const techniqueToggle = document.getElementById("technique-toggle");
  const chat = document.getElementById("chat");
  const planBtn = document.getElementById("plan");
  const executeBtn = document.getElementById("execute");
  const planFields = document.getElementById("plan-fields");
  const planEmpty = document.getElementById("plan-empty");
  const planStatus = document.getElementById("plan-status");
  const entitiesInput = document.getElementById("entities");
  const relationsInput = document.getElementById("relations");
  const thoughtInput = document.getElementById("thought");

  let currentTechnique = "zero_shot";
  let lastQuestion = "";

  function appendMessage(text, role = "user") {
    const div = document.createElement("div");
    div.className = `message ${role}`;
    div.textContent = text;
    chat.appendChild(div);
    chat.scrollTop = chat.scrollHeight;
  }

  function setTechnique(technique) {
    currentTechnique = technique;
    techniqueToggle.querySelectorAll("button").forEach((btn) => {
      btn.classList.toggle("active", btn.dataset.technique === technique);
    });

    const cot = technique === "chain_of_thought";
    planFields.classList.toggle("hidden", !cot);
    planEmpty.classList.toggle("hidden", cot);
    planStatus.textContent = cot ? "Chain-of-thought plan" : "Zero-shot mode";
  }

  function renderPlan(plan) {
    if (!plan) return;
    planFields.classList.remove("hidden");
    planEmpty.classList.add("hidden");
    planStatus.textContent = "Plan ready";

    const toLines = (items = []) =>
      items
        .map((item) => {
          const label = item.text || "";
          const uri = item.uri || "";
          return [label, uri].filter(Boolean).join(" | ");
        })
        .filter(Boolean)
        .join("\n");

    entitiesInput.value = toLines(plan.entities);
    relationsInput.value = toLines(plan.relations);
    thoughtInput.value = (plan.chain_of_thought || []).join("\n");
  }

  function parseList(text) {
    return text
      .split("\n")
      .map((line) => line.trim())
      .filter(Boolean);
  }

  function buildPlanPayload() {
    const entityLines = parseList(entitiesInput.value);
    const relationLines = parseList(relationsInput.value);
    const thoughtLines = parseList(thoughtInput.value);

    const toItems = (lines) =>
      lines.map((line) => {
        const [label, uri] = line.split("|").map((part) => part.trim());
        return { text: label, uri: uri || undefined };
      });

    return {
      entities: toItems(entityLines),
      relations: toItems(relationLines),
      chain_of_thought: thoughtLines,
    };
  }

  async function requestPlan() {
    if (currentTechnique !== "chain_of_thought") {
      appendMessage("Switch to chain-of-thought to request a plan.", "system");
      return;
    }

    const question = questionInput.value.trim();
    if (!question) {
      appendMessage("Please enter a question.", "system");
      return;
    }

    lastQuestion = question;
    appendMessage(question, "user");
    appendMessage("Planning chain-of-thought steps...", "system");

    try {
      const response = await fetch("http://127.0.0.1:8000/plan", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question,
          provider: providerSelect.value,
          model: modelInput.value,
        }),
      });

      if (!response.ok) {
        const errText = await response.text();
        appendMessage(`Planning failed: ${errText}`, "system");
        return;
      }

      const data = await response.json();
      if (!data.plan) {
        appendMessage("Planner returned an empty plan.", "system");
        return;
      }

      renderPlan(data.plan);
      appendMessage("Plan ready. Review it on the right.", "assistant");
    } catch (error) {
      appendMessage(`Request failed: ${error}`, "system");
    }
  }

  async function execute() {
    const question = questionInput.value.trim() || lastQuestion;
    if (!question) {
      appendMessage("Please enter a question.", "system");
      return;
    }

    const payload = {
      question,
      provider: providerSelect.value,
      model: modelInput.value,
      technique: currentTechnique,
    };

    if (currentTechnique === "chain_of_thought") {
      payload.plan = buildPlanPayload();
      planStatus.textContent = "Using edited plan";
    } else {
      planStatus.textContent = "Zero-shot mode";
    }

    appendMessage(question, "user");
    appendMessage("Generating SPARQL...", "system");

    try {
      const response = await fetch("http://127.0.0.1:8000/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const errText = await response.text();
        appendMessage(`Error: ${errText}`, "system");
        return;
      }

      const data = await response.json();
      if (data.plan) {
        renderPlan(data.plan);
      }
      appendMessage(data.sparql || "No SPARQL returned", "assistant");
    } catch (error) {
      appendMessage(`Request failed: ${error}`, "system");
    }
  }

  techniqueToggle.addEventListener("click", (event) => {
    const btn = event.target.closest("button[data-technique]");
    if (!btn) return;
    setTechnique(btn.dataset.technique);
  });

  planBtn.addEventListener("click", requestPlan);
  executeBtn.addEventListener("click", execute);

  setTechnique(currentTechnique);
});
