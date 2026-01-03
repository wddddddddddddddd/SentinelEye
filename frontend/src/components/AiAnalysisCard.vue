<template>
    <!-- 卡片主体（唯一根节点） -->
    <div class="relative bg-white rounded-xl shadow-sm border border-gray-200 p-6 hover:shadow-lg hover:border-purple-300 transition-all cursor-pointer select-none"
        @click="showDetail = true">
        <!-- 标题 + 风险等级 -->
        <div class="flex items-start justify-between mb-5">
            <h5 class="text-lg font-semibold text-gray-900 flex-1 mr-4 leading-relaxed">
                {{ analysis.title }}
            </h5>
            <span class="px-4 py-2 text-sm font-bold rounded-full whitespace-nowrap" :class="riskLevelClass">
                {{ analysis.ai_result.risk_level.toUpperCase() }}
            </span>
        </div>

        <!-- 场景描述 -->
        <div class="mb-5">
            <p class="text-sm font-medium text-gray-700 mb-2">问题场景</p>
            <p class="text-sm text-gray-600 leading-relaxed">{{ analysis.ai_result.scene }}</p>
        </div>

        <!-- 关键证据（全部显示） -->
        <div class="mb-5">
            <p class="text-sm font-medium text-gray-700 mb-3">
                关键证据（{{ analysis.ai_result.key_evidence.length }}条）
            </p>
            <ul class="space-y-2">
                <li v-for="(evidence, index) in analysis.ai_result.key_evidence" :key="index"
                    class="flex items-start text-sm text-gray-600">
                    <span class="text-purple-500 font-bold mr-2 mt-0.5">•</span>
                    <span class="leading-relaxed">{{ evidence }}</span>
                </li>
            </ul>
        </div>

        <!-- 处理建议（全部显示） -->
        <div class="mb-5">
            <p class="text-sm font-medium text-gray-700 mb-3">
                处理建议（{{ analysis.ai_result.suggestions.length }}条）
            </p>
            <ol class="space-y-2 list-decimal list-inside">
                <li v-for="(suggestion, index) in analysis.ai_result.suggestions" :key="index"
                    class="text-sm text-gray-600 leading-relaxed pl-1">
                    {{ suggestion }}
                </li>
            </ol>
        </div>

        <!-- 底部信息 -->
        <div class="flex items-center justify-between text-xs text-gray-500 pt-4 border-t border-gray-100">
            <div class="flex items-center">
                <i class="fas fa-robot mr-1.5"></i>
                <span class="font-medium">{{ modelName }}</span>
            </div>
            <div class="flex items-center">
                <i class="fas fa-clock mr-1.5"></i>
                <span>{{ formatDate(analysis.analyzed_at) }}</span>
            </div>
        </div>

        <!-- 有图片提示图标 -->
        <div v-if="analysis.has_image" class="absolute top-4 right-4">
            <i class="fas fa-image text-purple-400 text-xl opacity-80"></i>
        </div>
    </div>

    <!-- Vue 3 专属 Teleport：模态框传送到 body，避免多根节点 -->
    <Teleport to="body">
        <div v-if="showDetail" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black bg-opacity-60"
            @click.self="showDetail = false">
            <div class="bg-white rounded-2xl shadow-2xl max-w-3xl w-full max-h-[90vh] overflow-y-auto p-8 relative"
                @click.stop>
                <!-- 关闭按钮 -->
                <button class="absolute top-4 right-4 text-gray-400 hover:text-gray-600 text-2xl"
                    @click="showDetail = false">
                    <i class="fas fa-times"></i>
                </button>

                <!-- 标题 + 风险 -->
                <div class="mb-6">
                    <h3 class="text-2xl font-bold text-gray-900 mb-3">{{ analysis.title }}</h3>
                    <span class="px-5 py-2 text-lg font-bold rounded-full" :class="riskLevelClass">
                        {{ analysis.ai_result.risk_level.toUpperCase() }} RISK
                    </span>
                </div>

                <!-- 完整内容区域 -->
                <div class="space-y-6 text-gray-700">
                    <section>
                        <h4 class="text-lg font-semibold mb-2">问题场景</h4>
                        <p class="leading-relaxed">{{ analysis.ai_result.scene }}</p>
                    </section>

                    <section>
                        <h4 class="text-lg font-semibold mb-2">详细分析</h4>
                        <p class="leading-loose whitespace-pre-line">{{ analysis.ai_result.analysis }}</p>
                    </section>

                    <section>
                        <h4 class="text-lg font-semibold mb-2">全部关键证据</h4>
                        <ul class="space-y-2">
                            <li v-for="(e, i) in analysis.ai_result.key_evidence" :key="i" class="flex">
                                <span class="font-bold text-purple-600 mr-2">{{ i + 1 }}.</span>
                                <span>{{ e }}</span>
                            </li>
                        </ul>
                    </section>

                    <section>
                        <h4 class="text-lg font-semibold mb-2">完整处理建议</h4>
                        <ol class="space-y-2 list-decimal list-inside">
                            <li v-for="(s, i) in analysis.ai_result.suggestions" :key="i" class="leading-relaxed">
                                {{ s }}
                            </li>
                        </ol>
                    </section>

                    <section class="pt-4 border-t">
                        <div class="flex justify-between text-sm">
                            <span>分析模型：{{ modelName }}</span>
                            <span>分析时间：{{ formatDate(analysis.analyzed_at, true) }}</span>
                        </div>
                        <div v-if="analysis.has_image" class="mt-3 text-sm text-purple-600">
                            <i class="fas fa-image mr-1"></i> 包含 {{ analysis.image_count }} 张用户截图
                        </div>
                    </section>
                </div>
            </div>
        </div>
    </Teleport>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
    analysis: {
        type: Object,
        required: true
    }
})

const showDetail = ref(false)

const riskLevelClass = computed(() => {
    switch (props.analysis.ai_result.risk_level) {
        case 'high': return 'bg-red-100 text-red-800'
        case 'medium': return 'bg-orange-100 text-orange-800'
        case 'low': return 'bg-green-100 text-green-800'
        default: return 'bg-gray-100 text-gray-800'
    }
})

const modelName = computed(() => props.analysis.model_used || '未知模型')

const formatDate = (dateInput, full = false) => {
    if (!dateInput) return '未知时间'
    const date = new Date(typeof dateInput === 'string' ? dateInput : dateInput.$date || dateInput)
    if (isNaN(date.getTime())) return '无效时间'

    if (full) {
        return date.toLocaleString('zh-CN', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
        }).replace(/\//g, '-')
    }
    const month = String(date.getMonth() + 1).padStart(2, '0')
    const day = String(date.getDate()).padStart(2, '0')
    const hours = String(date.getHours()).padStart(2, '0')
    const minutes = String(date.getMinutes()).padStart(2, '0')
    return `${month}-${day} ${hours}:${minutes}`
}
</script>

<style scoped>
.leading-relaxed {
    line-height: 1.6;
}

.leading-loose {
    line-height: 1.8;
}

.whitespace-pre-line {
    white-space: pre-line;
}
</style>