<script lang="ts">
  import { tick } from "svelte";

  export let options: string[] = [];
  export let value: string = "";
  export let label: string = "";

  let open = false;
  let highlighted = -1;
  let listEl: HTMLUListElement;

  function clickOutside(node: HTMLElement) {
    const handle = (e: MouseEvent) => {
      if (!node.contains(e.target as Node)) open = false;
    };
    document.addEventListener("click", handle, true);
    return { destroy() { document.removeEventListener("click", handle, true); } };
  }

  function toggleOpen() {
    open = !open;
    if (open) {
      highlighted = options.indexOf(value);
      if (highlighted < 0) highlighted = 0;
      scrollHighlighted();
    }
  }

  async function scrollHighlighted() {
    await tick();
    if (!listEl) return;
    const item = listEl.querySelector<HTMLElement>(`[data-idx="${highlighted}"]`);
    item?.scrollIntoView({ block: "nearest" });
  }

  function select(opt: string) {
    value = opt;
    open = false;
  }

  async function handleKeydown(e: KeyboardEvent) {
    if (!open) {
      if (e.key === "Enter" || e.key === " " || e.key === "ArrowDown") {
        e.preventDefault();
        open = true;
        highlighted = options.indexOf(value);
        if (highlighted < 0) highlighted = 0;
        await scrollHighlighted();
      }
      return;
    }

    if (e.key === "ArrowDown") {
      e.preventDefault();
      highlighted = Math.min(highlighted + 1, options.length - 1);
      await scrollHighlighted();
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      highlighted = Math.max(highlighted - 1, 0);
      await scrollHighlighted();
    } else if (e.key === "Enter") {
      e.preventDefault();
      if (highlighted >= 0 && highlighted < options.length) {
        select(options[highlighted]);
      }
    } else if (e.key === "Escape") {
      e.preventDefault();
      open = false;
    }
  }

  $: activeDescendant = open && highlighted >= 0 ? `cb-opt-${highlighted}` : undefined;
</script>

<div class="combobox" use:clickOutside>
  {#if label}
    <span class="cb-label">{label}</span>
  {/if}
  <div class="cb-control">
    <button
      class="cb-trigger"
      type="button"
      role="combobox"
      aria-controls="cb-listbox"
      aria-expanded={open}
      aria-haspopup="listbox"
      aria-activedescendant={activeDescendant}
      on:click={toggleOpen}
      on:keydown={handleKeydown}
    >
      <span class="cb-value">{value}</span>
      <svg class="cb-chevron" class:open width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
        <polyline points="6 9 12 15 18 9" />
      </svg>
    </button>
    {#if open}
      <ul class="cb-list" id="cb-listbox" role="listbox" bind:this={listEl}>
        {#each options as opt, i}
          <!-- svelte-ignore a11y-click-events-have-key-events -->
          <li
            id="cb-opt-{i}"
            class="cb-option"
            class:active={i === highlighted}
            role="option"
            aria-selected={opt === value}
            data-idx={i}
            on:click={() => select(opt)}
            on:mouseenter={() => (highlighted = i)}
          >
            {#if opt === value}
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round">
                <polyline points="20 6 9 17 4 12" />
              </svg>
            {:else}
              <span class="check-space"></span>
            {/if}
            {opt}
          </li>
        {/each}
      </ul>
    {/if}
  </div>
</div>

<style>
  .combobox {
    display: flex;
    flex-direction: column;
    gap: 0.3rem;
  }

  .cb-label {
    color: var(--pc-text-muted);
    font-size: 0.78rem;
    font-weight: 500;
  }

  .cb-control {
    position: relative;
  }

  .cb-trigger {
    width: 100%;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 0.5rem;
    appearance: none;
    border: 1px solid var(--pc-border);
    border-radius: var(--pc-radius-md);
    padding: 0.55rem 0.7rem;
    color: var(--pc-text);
    background: var(--pc-surface);
    font-weight: 500;
    font-size: 0.85rem;
    text-align: left;
    cursor: pointer;
    transition: border-color var(--pc-duration-fast) var(--pc-ease);
  }

  .cb-trigger:hover {
    border-color: var(--pc-border-strong);
  }

  .cb-trigger:focus-visible {
    outline: 2px solid var(--pc-primary);
    outline-offset: 2px;
  }

  .cb-value {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .cb-chevron {
    color: var(--pc-text-muted);
    flex-shrink: 0;
    transition: transform var(--pc-duration-fast) var(--pc-ease);
  }

  .cb-chevron.open {
    transform: rotate(180deg);
  }

  .cb-list {
    position: absolute;
    top: calc(100% + 4px);
    left: 0;
    right: 0;
    z-index: 50;
    list-style: none;
    margin: 0;
    padding: 0.25rem;
    background: var(--pc-bg-elevated);
    border: 1px solid var(--pc-border-strong);
    border-radius: var(--pc-radius-md);
    max-height: 14rem;
    overflow-y: auto;
    box-shadow: var(--pc-shadow);
  }

  .cb-option {
    display: flex;
    align-items: center;
    gap: 0.45rem;
    padding: 0.45rem 0.55rem;
    cursor: pointer;
    color: var(--pc-text-soft);
    border-radius: var(--pc-radius-sm);
    font-size: 0.85rem;
    transition: background var(--pc-duration-fast) var(--pc-ease);
  }

  .cb-option:hover,
  .cb-option.active {
    background: var(--pc-surface-soft);
    color: var(--pc-text);
  }

  .cb-option[aria-selected="true"] {
    color: var(--pc-primary);
  }

  .check-space {
    display: inline-block;
    width: 14px;
  }
</style>
