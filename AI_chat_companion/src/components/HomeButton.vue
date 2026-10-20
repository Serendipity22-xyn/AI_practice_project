<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()

function goHome() {
  router.push('/')
}
</script>

<template>
  <button class="home-btn" title="主菜单" @click="goHome">🏠</button>
</template>

<style scoped>
.home-btn {
  position: fixed;
  top: 20px;
  right: 20px;
  width: 48px;
  height: 48px;
  font-size: 24px;
  line-height: 48px;
  text-align: center;
  background: var(--white);
  border-radius: 50%;
  box-shadow: var(--shadow-card);
  z-index: 15;
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}
.home-btn:hover {
  transform: translateY(-2px) scale(1.05);
}
.home-btn:active {
  transform: translateY(1px) scale(0.96);
}
</style>
