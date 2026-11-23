(() => {
  const grid = document.getElementById("calendar-grid");
  const heading = document.getElementById("calendar-month");
  const list = document.getElementById("event-list");
  const initialDate = new Date();
  let year = initialDate.getFullYear();
  let month = initialDate.getMonth();
  let selected = null;
  let focusDate = null;
  const events = [...window.SIGNAL_EVENTS, ...window.SIGNAL_INSTAGRAM_EVENTS];
  const monthFormat = new Intl.DateTimeFormat("en-US", { month: "long", year: "numeric" });
  const dateFormat = new Intl.DateTimeFormat("en-US", { month: "long", day: "numeric", year: "numeric", timeZone: "UTC" });
  const keyFor = (y, m, d) => `${y}-${String(m + 1).padStart(2, "0")}-${String(d).padStart(2, "0")}`;
  const displayDate = value => dateFormat.format(new Date(`${value}T12:00:00Z`));
  const onDate = date => events.filter(event => event.startDate <= date && event.endDate >= date);
  const edgeModules = document.querySelectorAll(".edge-module");
  const desktop = window.matchMedia("(min-width: 901px)");

  function setModuleLayout() {
    edgeModules.forEach(module => { module.open = !desktop.matches; });
  }
  function openTarget(hash) {
    const target = document.getElementById(hash.slice(1));
    const module = target && target.querySelector(".edge-module");
    if (module) module.open = true;
  }
  setModuleLayout();
  document.addEventListener("click", event => {
    const link = event.target.closest('a[href^="#"]');
    if (link) openTarget(link.getAttribute("href"));
  });
  window.addEventListener("hashchange", () => openTarget(window.location.hash));
  openTarget(window.location.hash);

  function element(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text) node.textContent = text;
    return node;
  }

  function renderEvents() {
    list.replaceChildren();
    const monthStart = keyFor(year, month, 1);
    const monthEnd = keyFor(year, month, new Date(year, month + 1, 0).getDate());
    const visible = selected ? onDate(selected) : events.filter(event => event.startDate <= monthEnd && event.endDate >= monthStart);
    const label = selected ? displayDate(selected) : monthFormat.format(new Date(year, month, 1));
    list.append(element("p", "event-date-label mono", label));
    if (!visible.length) {
      list.append(element("h4", "empty-title", "Nothing on the calendar yet."));
      list.append(element("p", "empty-copy", "Have an event to share? Let us know and help us fill in the picture."));
      const link = element("a", "event-link", "Suggest an event ↗");
      link.href = "#contact";
      list.append(link);
      return;
    }
    visible.forEach(event => {
      const article = element("article", "event-item");
      const range = event.startDate === event.endDate ? displayDate(event.startDate) : `${displayDate(event.startDate)} – ${displayDate(event.endDate)}`;
      article.append(element("p", "event-date mono", range), element("h4", "", event.title), element("p", "event-venue", event.venue), element("p", "event-details", event.details), element("p", "event-location", event.location));
      const link = element("a", "event-link", "Event details ↗");
      link.href = event.url;
      link.target = "_blank";
      link.rel = "noopener noreferrer";
      article.append(link);
      if (event.organizerUrl) {
        const organizer = element("a", "event-link organizer-link", "Organizer ↗");
        organizer.href = event.organizerUrl;
        organizer.target = "_blank";
        organizer.rel = "noopener noreferrer";
        article.append(organizer);
      }
      list.append(article);
    });
  }

  function render() {
    const now = new Date();
    heading.textContent = monthFormat.format(new Date(year, month, 1));
    grid.replaceChildren();
    const firstDay = new Date(year, month, 1).getDay();
    const days = new Date(year, month + 1, 0).getDate();
    const monthStart = keyFor(year, month, 1);
    const monthEnd = keyFor(year, month, days);
    if (!focusDate || focusDate < monthStart || focusDate > monthEnd) {
      focusDate = year === now.getFullYear() && month === now.getMonth()
        ? keyFor(year, month, now.getDate())
        : monthStart;
    }
    for (let i = 0; i < firstDay; i++) grid.append(element("span", "calendar-blank"));
    for (let day = 1; day <= days; day++) {
      const date = keyFor(year, month, day);
      const count = onDate(date).length;
      const button = element("button", "calendar-day", String(day));
      button.type = "button";
      button.tabIndex = date === focusDate ? 0 : -1;
      button.setAttribute("aria-label", `${displayDate(date)}${count ? `, ${count} ${count === 1 ? "event" : "events"}` : ", no events"}`);
      button.setAttribute("aria-pressed", String(selected === date));
      if (count) button.classList.add("has-event");
      if (date === keyFor(now.getFullYear(), now.getMonth(), now.getDate())) {
        button.classList.add("is-today");
        button.setAttribute("aria-current", "date");
      }
      if (selected === date) button.classList.add("is-selected");
      button.addEventListener("focus", () => {
        focusDate = date;
        grid.querySelectorAll(".calendar-day").forEach(item => { item.tabIndex = item === button ? 0 : -1; });
      });
      button.addEventListener("keydown", event => {
        const offsets = { ArrowLeft: -1, ArrowRight: 1, ArrowUp: -7, ArrowDown: 7 };
        if (!(event.key in offsets)) return;
        event.preventDefault();
        const next = new Date(year, month, day + offsets[event.key], 12);
        const nextDate = keyFor(next.getFullYear(), next.getMonth(), next.getDate());
        const monthChanged = next.getFullYear() !== year || next.getMonth() !== month;
        focusDate = nextDate;
        if (monthChanged) {
          year = next.getFullYear();
          month = next.getMonth();
          selected = null;
          render();
        } else {
          const nextButton = grid.querySelectorAll(".calendar-day")[next.getDate() - 1];
          nextButton.tabIndex = 0;
          button.tabIndex = -1;
        }
        grid.querySelector('.calendar-day[tabindex="0"]').focus();
      });
      button.addEventListener("click", () => {
        focusDate = date;
        selected = selected === date ? null : date;
        render();
        grid.querySelector('.calendar-day[tabindex="0"]').focus();
      });
      grid.append(button);
    }
    renderEvents();
  }

  function changeMonth(offset) {
    const next = new Date(year, month + offset, 1);
    year = next.getFullYear();
    month = next.getMonth();
    selected = null;
    focusDate = null;
    render();
  }
  document.getElementById("prev-month").addEventListener("click", () => changeMonth(-1));
  document.getElementById("next-month").addEventListener("click", () => changeMonth(1));
  document.getElementById("today").addEventListener("click", () => {
    const current = new Date();
    year = current.getFullYear();
    month = current.getMonth();
    selected = null;
    focusDate = null;
    render();
  });
  document.getElementById("contact-form").addEventListener("submit", event => {
    event.preventDefault();
    const form = event.currentTarget;
    const data = new FormData(form);
    const body = `Name: ${data.get("name")}\nEmail: ${data.get("email")}\n\n${data.get("message")}`;
    window.location.href = `mailto:hello@karinalujan.design?subject=${encodeURIComponent("S/GNAL inquiry")}&body=${encodeURIComponent(body)}`;
  });
  document.getElementById("contact-form").hidden = false;
  document.querySelector(".contact-form-instructions").hidden = false;
  document.getElementById("contact-fallback").hidden = true;
  render();
})();
