<script lang="ts">
  export let title = "";
  export let content = "";
</script>

<div class="card">
  <p>{title}</p>
  <pre>{content || "No evidence available."}</pre>
</div>

<style>
  .card {
    padding: 0.9rem;
    border: 1px solid var(--pc-border);
    border-radius: var(--pc-radius-md);
    background: rgba(255, 255, 255, 0.03);
  }

  p {
    margin: 0 0 0.55rem;
    color: var(--pc-text-soft);
    font-weight: 700;
  }

  pre {
    margin: 0;
    white-space: pre-wrap;
    font-family: var(--pc-font-body);
    color: var(--pc-text-muted);
    font-size: 0.86rem;
    line-height: 1.45;
  }
</style>
