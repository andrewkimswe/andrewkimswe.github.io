const GOATCOUNTER_BASE_URL = "https://jiwonkim-blog.goatcounter.com";

function normalize(value = "") {
  return value.normalize("NFKC").toLocaleLowerCase("ko-KR");
}

function setupArticleSearch() {
  const searchInput = document.querySelector("#postSearch");
  const filterButtons = [...document.querySelectorAll("[data-filter]")];
  const posts = [...document.querySelectorAll(".post-row")];
  const resultCount = document.querySelector("#resultCount");
  const emptyState = document.querySelector("#emptyPosts");
  const clearButton = document.querySelector("#clearFilters");

  if (!searchInput || !posts.length) {
    return;
  }

  let activeFilter = "all";

  function updateUrl() {
    const url = new URL(window.location.href);
    if (activeFilter === "all") {
      url.searchParams.delete("topic");
    } else {
      url.searchParams.set("topic", activeFilter);
    }
    window.history.replaceState({}, "", url);
  }

  function updatePosts() {
    const query = normalize(searchInput.value.trim());
    let visibleCount = 0;

    posts.forEach((post) => {
      const title = normalize(post.dataset.title);
      const summary = normalize(post.dataset.summary);
      const tags = (post.dataset.tags || "")
        .split("|")
        .map((tag) => normalize(tag.trim()))
        .filter(Boolean);
      const searchable = `${title} ${summary} ${tags.join(" ")}`;
      const matchesFilter = activeFilter === "all" || tags.includes(normalize(activeFilter));
      const matchesSearch = !query || searchable.includes(query);
      const isVisible = matchesFilter && matchesSearch;

      post.classList.toggle("is-hidden", !isVisible);
      if (isVisible) {
        visibleCount += 1;
      }
    });

    if (resultCount) {
      const context = activeFilter === "all" ? "전체" : activeFilter;
      resultCount.textContent = `${context} · ${visibleCount}개 글`;
    }
    if (emptyState) {
      emptyState.hidden = visibleCount !== 0;
    }
    if (clearButton) {
      clearButton.hidden = activeFilter === "all" && !query;
    }
  }

  function activateFilter(value, shouldUpdateUrl = true) {
    const matchingButton = filterButtons.find((button) => button.dataset.filter === value);
    activeFilter = matchingButton ? value : "all";

    filterButtons.forEach((button) => {
      const isActive = button.dataset.filter === activeFilter;
      button.classList.toggle("active", isActive);
      button.setAttribute("aria-pressed", String(isActive));
    });

    updatePosts();
    if (shouldUpdateUrl) {
      updateUrl();
    }
  }

  filterButtons.forEach((button) => {
    button.addEventListener("click", () => activateFilter(button.dataset.filter || "all"));
  });

  searchInput.addEventListener("input", updatePosts);

  clearButton?.addEventListener("click", () => {
    searchInput.value = "";
    activateFilter("all");
    searchInput.focus();
  });

  const initialTopic = new URLSearchParams(window.location.search).get("topic");
  activateFilter(initialTopic || "all", false);
}

function counterApiUrl() {
  return `${GOATCOUNTER_BASE_URL}/counter/TOTAL.json`;
}

function updateVisitText(text, title) {
  document.querySelectorAll("#visitStatus, [data-visit-status]").forEach((item) => {
    item.textContent = text;
    item.title = title;
  });
}

async function loadVisitCount() {
  const visitItems = document.querySelectorAll("#visitStatus, [data-visit-status]");
  if (!visitItems.length) {
    return;
  }

  const url = counterApiUrl();
  document.querySelectorAll("[data-visit-api-link]").forEach((link) => {
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
    const rawCount = data?.count_unique ?? data?.count ?? "0";
    const numericCount = Number(String(rawCount).replaceAll(",", ""));
    const count = Number.isFinite(numericCount)
      ? new Intl.NumberFormat("ko-KR").format(numericCount)
      : String(rawCount);
    updateVisitText(`방문 ${count}`, "GoatCounter 공개 API의 고유 방문 집계값입니다.");
  } catch (error) {
    updateVisitText("통계 연결 안 됨", "방문 통계를 불러오지 못했습니다. 글 읽기에는 영향이 없습니다.");
  }
}

function setupCodeBlocks() {
  document.querySelectorAll(".article-body pre").forEach((pre) => {
    const code = pre.querySelector("code");
    if (!code || pre.querySelector(".copy-button")) {
      return;
    }

    const languageClass = [...code.classList].find((name) => name.startsWith("language-"));
    pre.dataset.language = languageClass ? languageClass.replace("language-", "") : "code";

    const button = document.createElement("button");
    button.className = "copy-button";
    button.type = "button";
    button.textContent = "복사";
    button.setAttribute("aria-label", "코드 복사");

    button.addEventListener("click", async () => {
      try {
        await navigator.clipboard.writeText(code.textContent || "");
        button.textContent = "완료";
        button.setAttribute("aria-label", "코드가 복사되었습니다");
        window.setTimeout(() => {
          button.textContent = "복사";
          button.setAttribute("aria-label", "코드 복사");
        }, 1600);
      } catch (error) {
        button.textContent = "실패";
        button.setAttribute("aria-label", "코드를 복사하지 못했습니다");
      }
    });

    pre.append(button);
  });

  document.querySelectorAll(".article-body table").forEach((table) => {
    if (table.parentElement?.classList.contains("table-shell")) {
      return;
    }
    const shell = document.createElement("div");
    shell.className = "table-shell";
    shell.tabIndex = 0;
    shell.setAttribute("role", "region");
    shell.setAttribute("aria-label", "가로로 스크롤할 수 있는 표");
    table.before(shell);
    shell.append(table);
  });
}

function setupHeadingAnchors() {
  const headings = [...document.querySelectorAll(".article-body h2, .article-body h3")];
  headings.forEach((heading, index) => {
    if (!heading.id) {
      heading.id = `heading-${index + 1}`;
    }
    if (heading.querySelector(".heading-anchor")) {
      return;
    }

    const anchor = document.createElement("a");
    anchor.className = "heading-anchor";
    anchor.href = `#${heading.id}`;
    anchor.textContent = "#";
    anchor.setAttribute("aria-label", `${heading.textContent?.trim() || "섹션"} 바로가기`);
    heading.append(anchor);
  });
}

function setupTableOfContents() {
  const toc = document.querySelector(".article-toc");
  const details = toc?.querySelector("details");
  const links = [...(toc?.querySelectorAll("a[href^='#']") || [])];

  if (!toc || !links.length) {
    return;
  }

  if (window.matchMedia("(max-width: 820px)").matches && details) {
    details.open = false;
  }

  const linkById = new Map(
    links.map((link) => [decodeURIComponent(link.getAttribute("href").slice(1)), link]),
  );
  const headings = [...linkById.keys()]
    .map((id) => document.getElementById(id))
    .filter(Boolean);

  if (!("IntersectionObserver" in window) || !headings.length) {
    return;
  }

  let activeId = headings[0].id;
  const setActive = (id) => {
    if (activeId === id) {
      return;
    }
    activeId = id;
    links.forEach((link) => link.classList.toggle("is-active", linkById.get(id) === link));
  };

  linkById.get(activeId)?.classList.add("is-active");
  const observer = new IntersectionObserver(
    (entries) => {
      const visible = entries
        .filter((entry) => entry.isIntersecting)
        .sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top);
      if (visible[0]?.target.id) {
        setActive(visible[0].target.id);
      }
    },
    { rootMargin: "-18% 0px -70% 0px", threshold: 0 },
  );
  headings.forEach((heading) => observer.observe(heading));
}

async function renderMermaidDiagrams() {
  const diagrams = [...document.querySelectorAll(".mermaid")];
  if (!diagrams.length) {
    return;
  }

  try {
    const { default: mermaid } = await import(
      "https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs"
    );
    mermaid.initialize({
      startOnLoad: false,
      securityLevel: "strict",
      theme: "base",
      themeVariables: {
        background: "#ffffff",
        primaryColor: "#e8f1ed",
        primaryTextColor: "#171a18",
        primaryBorderColor: "#0d675c",
        lineColor: "#68716b",
        secondaryColor: "#edf1f5",
        tertiaryColor: "#f3f5f2",
        fontSize: "14px",
        fontFamily: "-apple-system, BlinkMacSystemFont, Apple SD Gothic Neo, Noto Sans KR, Segoe UI, sans-serif",
      },
      flowchart: {
        curve: "linear",
        htmlLabels: true,
      },
    });
    await mermaid.run({ nodes: diagrams });
    diagrams.forEach((diagram, index) => {
      diagram.setAttribute("role", "img");
      diagram.setAttribute("aria-label", `본문 아키텍처 다이어그램 ${index + 1}`);
    });

    const fragment = decodeURIComponent(window.location.hash.slice(1));
    const fragmentTarget = fragment ? document.getElementById(fragment) : null;
    if (fragmentTarget) {
      window.requestAnimationFrame(() => fragmentTarget.scrollIntoView({ block: "start" }));
    }
  } catch (error) {
    diagrams.forEach((diagram) => {
      diagram.classList.add("diagram-error");
      diagram.setAttribute("role", "note");
      diagram.setAttribute("aria-label", "다이어그램을 불러오지 못해 원본 정의를 표시합니다.");
    });
  }
}

setupArticleSearch();
setupCodeBlocks();
setupHeadingAnchors();
setupTableOfContents();
loadVisitCount();
renderMermaidDiagrams();
