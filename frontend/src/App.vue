<template>
  <div class="app">
    <div class="flex min-h-screen">
      <Sidebar class="sticky-sidebar" />
      <div class="flex-1 p-6 bg-gray-100">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </div>
    </div>
  </div>
</template>

<script>
import Sidebar from './components/Sidebar.vue'

export default {
  name: 'App',
  components: {
    Sidebar
  }
}
</script>

<style scoped>
.app-layout {
  display: flex;
  min-height: 100vh;
}

.sticky-sidebar {
  position: sticky;
  top: 0;
  align-self: flex-start;
  /* 重要：避免被拉伸 */
  height: 100vh;
}

.content-area {
  flex: 1;
}
</style>