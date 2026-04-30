<script lang="ts">
  export let genres: string[] = [];
  export let statuses: string[] = [];
  export let selectedGenre = "All";
  export let selectedStatus = "All";
  export let search = "";
</script>

<div class="filter-bar">
  <div class="search-wrap">
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
      <circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" />
    </svg>
    <input
      type="text"
      bind:value={search}
      placeholder="Search by filename or caption..."
    />
  </div>

  <select bind:value={selectedGenre}>
    <option>All</option>
    {#each genres as genre}
      <option>{genre}</option>
    {/each}
  </select>

  <select bind:value={selectedStatus}>
    <option>All</option>
    {#each statuses as status}
      <option>{status}</option>
    {/each}
  </select>
</div>

<style>
  .filter-bar {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    flex-wrap: wrap;
  }

  .search-wrap {
    display: flex;
    align-items: center;
    gap: 0.4rem;
    flex: 1;
    min-width: 180px;
    border: 1px solid var(--pc-border);
    border-radius: var(--pc-radius-md);
    padding: 0.45rem 0.65rem;
    background: var(--pc-surface);
    color: var(--pc-text-muted);
    transition: border-color var(--pc-duration-fast) var(--pc-ease);
  }

  .search-wrap:focus-within {
    border-color: var(--pc-primary);
  }

  input {
    flex: 1;
    border: none;
    background: transparent;
    color: var(--pc-text);
    font-size: 0.85rem;
    outline: none;
  }

  input::placeholder {
    color: var(--pc-text-muted);
  }

  select {
    border: 1px solid var(--pc-border);
    border-radius: var(--pc-radius-md);
    padding: 0.45rem 0.65rem;
    color: var(--pc-text-soft);
    background: var(--pc-surface);
    font-size: 0.85rem;
    cursor: pointer;
    transition: border-color var(--pc-duration-fast) var(--pc-ease);
  }

  select:hover {
    border-color: var(--pc-border-strong);
  }
</style>
