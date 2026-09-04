const searchInput = document.querySelector("#postSearch");
const filterButtons = document.querySelectorAll("[data-filter]");
const posts = document.querySelectorAll(".post-row");
const visitStatusItems = document.querySelectorAll("#visitStatus, [data-visit-status]");
const postCountItems = document.querySelectorAll("[data-post-count]");
const visitApiLinks = document.querySelectorAll("[data-visit-api-link]");
const GOATCOUNTER_BASE_URL = "https://jiwonkim-blog.goatcounter.com";

let activeFilter = "all";

function updatePosts() {
  if (!posts.length) {
    return;
  }

  const query = searchInput.value.trim().toLowerCase();

  posts.forEach((post) => {
    const title = post.dataset.title.toLowerCase();
    const tags = post.dataset.tags;
    const normalizedTags = ` ${tags.toLowerCase()} `;
    const normalizedFilter = ` ${activeFilter.toLowerCase()} `;
    const matchesFilter = activeFilter === "all" || normalizedTags.includes(normalizedFilter);
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

visitStatusItems.forEach((visitStatus) => {
  visitStatus.textContent = "집계 중";
  visitStatus.title = "GoatCounter page view events. AI crawler traffic can be included when it loads JavaScript or the tracking pixel.";
});

postCountItems.forEach((postCount) => {
  postCount.textContent = posts.length.toString();
});

function counterPath() {
  return "TOTAL";
}

function counterApiUrl(path) {
  return `${GOATCOUNTER_BASE_URL}/counter/${encodeURIComponent(path)}.json`;
}

function updateVisitText(text, title) {
  visitStatusItems.forEach((visitStatus) => {
    visitStatus.textContent = text;
    visitStatus.title = title;
  });
}

async function loadVisitCount() {
  if (!visitStatusItems.length) {
    return;
  }

  const path = counterPath();
  const url = counterApiUrl(path);

  visitApiLinks.forEach((link) => {
    link.href = url;
  });

  try {
    const response = await fetch(url, {
      cache: "no-store",
      headers: { accept: "application/json" },
    });

    if (!response.ok) {
      throw new Error(`Counter API returned ${response.status}`);
    }

    const data = await response.json();
    const count = data && data.count ? data.count : "0";
    updateVisitText(`방문 ${count}`, "GoatCounter public counter API에서 가져온 전체 site visit count입니다.");
  } catch (error) {
    updateVisitText("설정 필요", "GoatCounter site code가 없거나 public visitor counter 설정이 꺼져 있어 숫자를 가져오지 못했습니다.");
  }
}

loadVisitCount();

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
