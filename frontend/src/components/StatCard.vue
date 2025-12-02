<template>
  <div class="stat-card bg-white rounded-xl p-6 border border-gray-200">
    <div class="flex items-center mb-3">
      <div :class="iconBgClass" class="w-12 h-12 rounded-lg flex items-center justify-center mr-4">
        <i :class="[icon, iconColorClass, 'text-xl']"></i>
      </div>
      <div>
        <h3 class="text-gray-500 text-sm font-medium">{{ title }}</h3>
        <p class="text-3xl font-bold text-gray-800">{{ value }}</p>
      </div>
    </div>
    <div :class="trendColorClass" class="text-sm">
      <i :class="[getTrendIcon(trend.type), 'mr-1']"></i> {{ trend.value }}
    </div>
  </div>
</template>

<script>
export default {
  name: 'StatCard',
  props: {
    title: String,
    value: String,
    icon: String,
    trend: Object,
    color: String  // 这个color现在只控制图标背景和图标颜色
  },
  computed: {
    iconBgClass() {
      const classes = {
        blue: 'bg-blue-100',
        orange: 'bg-orange-100',
        red: 'bg-red-100',
        green: 'bg-green-100'
      }
      return classes[this.color] || 'bg-gray-100'
    },
    iconColorClass() {
      const classes = {
        blue: 'text-blue-500',
        orange: 'text-orange-500',
        red: 'text-red-500',
        green: 'text-green-500'
      }
      return classes[this.color] || 'text-gray-500'
    },
    trendColorClass() {
      const classes = {
        up: 'text-green-500',
        down: 'text-red-500',
        alert: 'text-blue-500'
      }
      return classes[this.trend.type] || 'text-gray-500'
    }
  },
  methods: {
    getTrendIcon(type) {
      const icons = {
        up: 'fas fa-arrow-up',
        down: 'fas fa-arrow-down',
        alert: 'fas fa-bell'
      }
      return icons[type] || 'fas fa-minus'
    }
  }
}
</script>