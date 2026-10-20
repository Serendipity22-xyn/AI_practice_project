<template>
  <p class="watermark">该网站最终解释权由开发者：Serendipity 所有</p>
</template>

<style scoped>
.watermark {
  position: fixed;
  top: 14px;
  left: 50%;
  transform: translateX(-50%);
  margin: 0;
  font-size: 13px;
  font-weight: 700;
  color: var(--blue-deep);
  opacity: 0.9;
  white-space: nowrap;
  pointer-events: none;
  z-index: 4;
}
</style>
