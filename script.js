const searchInput = document.querySelector("#postSearch");
const filterButtons = document.querySelectorAll("[data-filter]");
const posts = document.querySelectorAll(".post-row");
const visitStatus = document.querySelector("#visitStatus");

let activeFilter = "all";

function updatePosts() {
  if (!posts.length) {
    return;
  }

  const query = searchInput.value.trim().toLowerCase();

  posts.forEach((post) => {
    const title = post.dataset.title.toLowerCase();
    const tags = post.dataset.tags;
    const matchesFilter = activeFilter === "all" || tags.includes(activeFilter);
    const matchesSearch = !query || title.includes(query) || tags.toLowerCase().includes(query);

    post.classList.toggle("is-hidden", !matchesFilter || !matchesSearch);
  });
}

filterButtons.forEach((button) => {
  button.addEventListener("click", () => {
    filterButtons.forEach((item) => item.classList.remove("active"));
    button.classList.add("active");
    activeFilter = button.dataset.filter;
    updatePosts();
  });
});

if (searchInput) {
  searchInput.addEventListener("input", updatePosts);
}

if (visitStatus) {
  visitStatus.textContent = "Visitor analytics ready";
}

async function renderMermaidDiagrams() {
  const diagrams = document.querySelectorAll(".mermaid");

  if (!diagrams.length) {
    return;
  }

  const { default: mermaid } = await import("https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs");

  mermaid.initialize({
    startOnLoad: false,
    securityLevel: "strict",
    theme: "base",
    themeVariables: {
      background: "#fbfaf7",
      primaryColor: "#fbfaf7",
      primaryTextColor: "#161616",
      primaryBorderColor: "#161616",
      lineColor: "#6f6a60",
      secondaryColor: "#ece5d8",
      tertiaryColor: "#f4f1ea",
      fontSize: "14px",
      fontFamily: "ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif",
    },
    flowchart: {
      curve: "basis",
      htmlLabels: true,
    },
  });

  await mermaid.run({ nodes: diagrams });
}

renderMermaidDiagrams();
