const searchInput = document.querySelector("#postSearch");
const filterButtons = document.querySelectorAll("[data-filter]");
const posts = document.querySelectorAll(".post-card");

let activeFilter = "all";

function updatePosts() {
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

searchInput.addEventListener("input", updatePosts);
