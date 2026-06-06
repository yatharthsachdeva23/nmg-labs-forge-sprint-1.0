/* app.js — SEO Command Center live cockpit. Plain DOM + SSE, no build step. */
const $ = (id) => document.getElementById(id);
let totals = { High: 0, Medium: 0, Low: 0, total: 0 };

function log(msg) {
  const l = $("log"); if (l.querySelector(".empty")) l.innerHTML = "";
  const d = document.createElement("div"); d.textContent = "› " + msg; l.appendChild(d); l.scrollTop = l.scrollHeight;
}

function recalculateTotals() {
  // Reset aggregate count properties
  totals = { High: 0, Medium: 0, Low: 0, total: 0 };
  const rows = document.querySelectorAll("#tbody tr");

  rows.forEach(row => {
    const sevSpan = row.querySelector(".sev");
    if (sevSpan) {
      const severity = sevSpan.textContent.trim(); // "High", "Medium", "Low"
      totals[severity] = (totals[severity] || 0) + 1;
      totals.total++;
    }
  });

  // Update DOM interface elements with sanitized numbers
  $("c-total").textContent = totals.total;
  $("c-high").textContent = totals.High;
  $("c-med").textContent = totals.Medium;
  $("c-low").textContent = totals.Low;
}

function addIssue(i) {
  const tb = $("tbody"); if (tb.querySelector(".empty")) tb.innerHTML = "";

  // UNIQUE IDENTIFIER GUARD: Check if this specific issue type is already on the screen
  let existingRow = null;
  const rows = tb.querySelectorAll("tr");
  rows.forEach(row => {
    if (row.getAttribute("data-type") === i.type) {
      existingRow = row;
    }
  });

  if (existingRow) {
    // If it exists already, update the URL occurrence counter column instead of adding a new row
    existingRow.cells[2].textContent = i.count;
  } else {
    // If it is completely new, create and append a clean row with an explicit data-type marker
    const tr = document.createElement("tr");
    tr.setAttribute("data-type", i.type);
    tr.innerHTML = `<td><span class="sev ${i.severity.toLowerCase()}">${i.severity}</span></td>
                    <td>${i.type}</td><td>${i.count}</td>`;
    tb.appendChild(tr);
  }

  // Always compute explicit counts from the actual visual DOM list to guarantee accuracy
  recalculateTotals();
}

function handle({ event, data }) {
  if (event === "snapshot") {
    if (data.site) { $("meta").textContent = "· " + data.site; $("urls").textContent = (data.urls || 0) + " URLs"; }
    $("tbody").innerHTML = ""; // Hard clear to completely reset visual artifacts on initial hookup
    (data.issues || []).forEach(addIssue);
  } else if (event === "reset") {
    $("tbody").innerHTML = "";
    totals = { High: 0, Medium: 0, Low: 0, total: 0 };
    recalculateTotals();
  } else if (event === "loaded") {
    $("meta").textContent = "· " + data.site; $("urls").textContent = data.urls + " URLs";
    log(`Loaded ${data.urls} URLs from ${data.site}`);
    $("tbody").innerHTML = "";
    totals = { High: 0, Medium: 0, Low: 0, total: 0 };
    recalculateTotals();
  } else if (event === "issue") {
    addIssue(data);
    log(`Found ${data.count} × ${data.type}`);
  } else if (event === "summary") {
    log(`Audit complete: ${data.total_issues} issues identified across paths`);
  } else if (event === "fixes") {
    log(`Fixes ready: ${(data.titles || []).length} titles, ${(data.redirect_map || []).length} redirects`);
  } else if (event === "exported") {
    $("export").innerHTML = "<b>report.html written ✓</b><br><span style='color:#c8c5be;font-size:12px'>Open or email outputs/report.html to the client.</span>";
  } else if (event === "saved") {
    log("report.json saved");
  }
}

const es = new EventSource("/events");
es.onmessage = (m) => { try { handle(JSON.parse(m.data)); } catch (e) { } };