<script lang="ts">
  export let genres: string[] = [];
  export let statuses: string[] = [];
  export let selectedGenre = "All";
  export let selectedStatus = "All";
  export let search = "";
  export let maxConfidence = 1;
</script>

<div class="sidebar">
  <label>
    <span>Search</span>
    <input bind:value={search} placeholder="filename, caption" readonly />
  </label>

  <label>
    <span>Genre</span>
    <select bind:value={selectedGenre} disabled>
      <option>All</option>
      {#each genres as genre}
        <option>{genre}</option>
      {/each}
    </select>
  </label>

  <label>
    <span>Status</span>
    <select bind:value={selectedStatus} disabled>
      <option>All</option>
      {#each statuses as status}
        <option>{status}</option>
      {/each}
    </select>
  </label>

  <label>
    <span>Max confidence</span>
    <input type="range" min="0" max="1" step="0.01" bind:value={maxConfidence} disabled />
    <small>{Math.round(maxConfidence * 100)}%</small>
  </label>
</div>

<style>
  .sidebar {
    display: flex;
    flex-direction: column;
    gap: 0.95rem;
  }

  label {
    display: flex;
    flex-direction: column;
    gap: 0.45rem;
  }

  span,
  small {
    color: var(--pc-text-muted);
  }

  input,
  select {
    width: 100%;
    border: 1px solid var(--pc-border);
    border-radius: var(--pc-radius-sm);
    padding: 0.78rem 0.9rem;
    color: var(--pc-text);
    background: rgba(255, 255, 255, 0.04);
  }

  input:focus-visible,
  select:focus-visible {
    outline: 2px solid var(--pc-primary);
    outline-offset: 2px;
  }
</style>
