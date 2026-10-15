const wagonForm = document.querySelector("#wagon-form");
const track = document.querySelector("#wagon-track");
const emptyState = document.querySelector("#empty-state");
const notice = document.querySelector("#notice");
const previousButton = document.querySelector("#previous-button");
const nextButton = document.querySelector("#next-button");
const removeButton = document.querySelector("#remove-button");

let yardSnapshot = null;
let noticeTimer = null;

async function request(path, options = {}) {
  const response = await fetch(path, {
    ...options,
    headers: {
      ...(options.body ? { "Content-Type": "application/json" } : {}),
      ...options.headers,
    },
  });
  const body = await response.json();
  if (!response.ok) {
    throw new Error(body.error || "No se pudo completar la operación.");
  }
  return body;
}

function setNotice(message, isError = false) {
  window.clearTimeout(noticeTimer);
  notice.textContent = message;
  notice.classList.toggle("notice-error", isError);
  notice.classList.add("notice-visible");
  noticeTimer = window.setTimeout(() => {
    notice.classList.remove("notice-visible");
  }, 3200);
}

function addTextElement(parent, tagName, className, text) {
  const element = document.createElement(tagName);
  element.className = className;
  element.textContent = text;
  parent.append(element);
  return element;
}

function renderTrack(wagons, currentWagon) {
  track.replaceChildren();
  emptyState.hidden = wagons.length > 0;
  track.hidden = wagons.length === 0;

  wagons.forEach((wagon, index) => {
    if (index > 0) {
      addTextElement(track, "span", "wagon-link", "↔").setAttribute("aria-hidden", "true");
    }

    const isCurrent = currentWagon && wagon.wagon_id === currentWagon.wagon_id;
    const card = document.createElement("button");
    card.type = "button";
    card.className = `wagon-node${isCurrent ? " wagon-node-current" : ""}`;
    card.setAttribute(
      "aria-label",
      `${wagon.wagon_id}, ${wagon.cargo}, destino ${wagon.destination}${isCurrent ? ", seleccionado" : ""}`,
    );
    card.setAttribute("aria-pressed", String(Boolean(isCurrent)));
    card.addEventListener("click", async () => {
      if (isCurrent) return;
      for (let steps = 0; steps < wagons.length; steps += 1) {
        await request("/api/navigation/next", { method: "POST" });
        const snapshot = await request("/api/wagons");
        if (snapshot.current_wagon?.wagon_id === wagon.wagon_id) {
          await refresh();
          return;
        }
      }
    });

    const top = addTextElement(card, "span", "wagon-node-top", "");
    addTextElement(top, "span", "", isCurrent ? "EN INSPECCIÓN" : "VAGÓN");
    addTextElement(card, "span", "wagon-art", "");
    const art = card.lastElementChild;
    addTextElement(art, "span", "wagon-body", "");
    addTextElement(card, "span", "wagon-node-bottom", wagon.wagon_id);
    track.append(card);
  });
}

function renderSnapshot(snapshot) {
  yardSnapshot = snapshot;
  const wagons = snapshot.wagons;
  const currentWagon = snapshot.current_wagon;
  const currentIndex = wagons.findIndex((wagon) => wagon.wagon_id === currentWagon?.wagon_id);

  document.querySelector("#wagon-count").textContent = snapshot.count;
  document.querySelector("#total-weight").textContent =
    Number(snapshot.total_weight_tonnes).toLocaleString("es-CO", { maximumFractionDigits: 1 });
  document.querySelector("#current-wagon").textContent = currentWagon?.wagon_id || "Sin selección";
  document.querySelector("#current-destination").textContent = currentWagon
    ? `Destino: ${currentWagon.destination}`
    : "Selecciona un vagón para comenzar";
  document.querySelector("#position-label").textContent = currentWagon
    ? `Vagón ${currentIndex + 1} de ${snapshot.count}`
    : "Sin vagones";
  document.querySelector("#detail-id-badge").textContent = currentWagon?.wagon_id || "—";
  document.querySelector("#detail-cargo").textContent = currentWagon?.cargo || "—";
  document.querySelector("#detail-destination").textContent = currentWagon?.destination || "—";
  document.querySelector("#detail-weight").textContent = currentWagon
    ? `${Number(currentWagon.weight_tonnes).toLocaleString("es-CO")} t`
    : "—";
  document.querySelector("#return-label").textContent = wagons.length > 1
    ? `El circuito continúa desde ${wagons.at(-1).wagon_id} hasta ${wagons[0].wagon_id}`
    : wagons.length === 1
      ? `El circuito vuelve al vagón ${wagons[0].wagon_id}`
      : "El circuito continúa desde el último vagón al primero";

  previousButton.disabled = wagons.length === 0;
  nextButton.disabled = wagons.length === 0;
  removeButton.disabled = !currentWagon;
  renderTrack(wagons, currentWagon);
}

async function refresh() {
  renderSnapshot(await request("/api/wagons"));
}

async function navigate(direction) {
  try {
    await request(`/api/navigation/${direction}`, { method: "POST" });
    await refresh();
  } catch (error) {
    setNotice(error.message, true);
  }
}

previousButton.addEventListener("click", () => navigate("previous"));
nextButton.addEventListener("click", () => navigate("next"));

wagonForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const formData = new FormData(wagonForm);
  const wagon = Object.fromEntries(formData.entries());
  wagon.weight_tonnes = Number(wagon.weight_tonnes);
  try {
    await request("/api/wagons", { method: "POST", body: JSON.stringify(wagon) });
    wagonForm.reset();
    await refresh();
    setNotice(`Vagón ${wagon.wagon_id} añadido al circuito.`);
  } catch (error) {
    setNotice(error.message, true);
  }
});

removeButton.addEventListener("click", async () => {
  const currentWagon = yardSnapshot?.current_wagon;
  if (!currentWagon) return;
  try {
    await request(`/api/wagons/${encodeURIComponent(currentWagon.wagon_id)}`, {
      method: "DELETE",
    });
    await refresh();
    setNotice(`Vagón ${currentWagon.wagon_id} retirado del circuito.`);
  } catch (error) {
    setNotice(error.message, true);
  }
});

refresh().catch((error) => {
  setNotice(`No se pudo conectar con el patio: ${error.message}`, true);
});
