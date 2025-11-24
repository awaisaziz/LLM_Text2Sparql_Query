document.addEventListener("DOMContentLoaded", () => {
  const questionInput = document.getElementById("question");
  const providerSelect = document.getElementById("provider");
  const modelInput = document.getElementById("model");
  const techniqueSelect = document.getElementById("technique");
  const chat = document.getElementById("chat");
  const generateBtn = document.getElementById("generate");

  function appendMessage(text, role = "user") {
    const div = document.createElement("div");
    div.className = `message ${role}`;
    div.textContent = text;
    chat.appendChild(div);
    chat.scrollTop = chat.scrollHeight;
  }

  async function generate() {
    const question = questionInput.value.trim();
    if (!question) {
      appendMessage("Please enter a question.", "system");
      return;
    }
    appendMessage(question, "user");

    const payload = {
      question,
      provider: providerSelect.value,
      model: modelInput.value,
      technique: techniqueSelect.value,
    };

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
      appendMessage(data.sparql || "No SPARQL returned", "assistant");
    } catch (error) {
      appendMessage(`Request failed: ${error}`, "system");
    }
  }

  generateBtn.addEventListener("click", generate);
});
