<template>
  <div class="app">
    <div class="flex min-h-screen">
      <Sidebar />
      <div class="flex-1 p-6 bg-gray-100">
        <router-view />
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