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
  <span class="cb-label">{label}</span>
  <div class="cb-control">
    <button
      class="cb-trigger"
      type="button"
      role="combobox"
      aria-expanded={open}
      aria-haspopup="listbox"
      aria-activedescendant={activeDescendant}
      on:click={toggleOpen}
      on:keydown={handleKeydown}
    >
      {value} ▾
    </button>
    {#if open}
      <ul class="cb-list" role="listbox" bind:this={listEl}>
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
    gap: 0.45rem;
  }

  .cb-label {
    color: var(--pc-text-muted);
  }

  .cb-control {
    position: relative;
  }

  .cb-trigger {
    width: 100%;
    appearance: none;
    border: 1px solid var(--pc-border);
    border-radius: var(--pc-radius-sm);
    padding: 0.95rem 2.8rem 0.95rem 0.95rem;
    color: var(--pc-text);
    background: linear-gradient(180deg, rgba(34, 20, 42, 0.94), rgba(24, 13, 31, 0.94));
    font-weight: 600;
    box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.02);
    text-align: left;
    cursor: pointer;
    font-size: inherit;
    font-family: inherit;
  }

  .cb-trigger:focus-visible {
    outline: 2px solid var(--pc-primary);
    outline-offset: 2px;
  }

  .cb-list {
    position: absolute;
    top: calc(100% + 4px);
    left: 0;
    right: 0;
    z-index: 50;
    list-style: none;
    margin: 0;
    padding: 0;
    background: rgba(24, 13, 31, 0.98);
    border: 1px solid var(--pc-border);
    border-radius: var(--pc-radius-sm);
    max-height: 14rem;
    overflow-y: auto;
  }

  .cb-option {
    padding: 0.75rem 1rem;
    cursor: pointer;
    color: var(--pc-text);
  }

  .cb-option:hover,
  .cb-option.active {
    background: rgba(93, 42, 122, 0.25);
  }

  .cb-option[aria-selected="true"] {
    color: var(--pc-primary);
  }
</style>
