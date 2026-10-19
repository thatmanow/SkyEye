<template>
  <div class="nf">
    <h1>404</h1>
    <p>页面不存在或已被移除</p>
    <router-link to="/">返回首页</router-link>
  </div>
</template>

<style scoped>
.nf { min-height: 100%; display: flex; flex-direction: column; align-items: center;
  justify-content: center; gap: 10px; background: var(--tyt-bg); }
h1 { font-size: 72px; margin: 0;
  background: linear-gradient(135deg,#6366f1,#8b5cf6);
  -webkit-background-clip: text; background-clip: text; color: transparent; }
p { color: var(--tyt-text-dim); }
</style>
