<template>
  <div>
    <v-row class="mb-6">
      <v-col>
        <h2 class="text-h4 font-weight-bold text-primary">
          <v-icon class="me-2">mdi-view-dashboard</v-icon>
          Dashboard
        </h2>
      </v-col>
    </v-row>

    <!-- Stats Cards -->
    <v-row class="mb-6">
      <v-col cols="12" sm="6" md="3">
        <v-card class="pa-4 text-center" elevation="2">
          <v-icon size="48" color="primary" class="mb-2">mdi-briefcase</v-icon>
          <div class="text-h3 font-weight-bold text-primary">{{ portfolios.length }}</div>
          <div class="text-subtitle-1 text-medium-emphasis">Total Portfolios</div>
        </v-card>
      </v-col>

      <v-col cols="12" sm="6" md="3">
        <v-card class="pa-4 text-center" elevation="2">
          <v-icon size="48" color="success" class="mb-2">mdi-chart-line</v-icon>
          <div class="text-h3 font-weight-bold text-success">{{ recentAnalysisCount }}</div>
          <div class="text-subtitle-1 text-medium-emphasis">Analyses This Week</div>
        </v-card>
      </v-col>

      <v-col cols="12" sm="6" md="3">
        <v-card class="pa-4 text-center" elevation="2">
          <v-icon size="48" color="warning" class="mb-2">mdi-target</v-icon>
          <div class="text-h3 font-weight-bold text-warning">{{ accuracyRate }}%</div>
          <div class="text-subtitle-1 text-medium-emphasis">Prediction Accuracy</div>
        </v-card>
      </v-col>

      <v-col cols="12" sm="6" md="3">
        <v-card class="pa-4 text-center" elevation="2">
          <v-icon size="48" color="info" class="mb-2">mdi-clock</v-icon>
          <div class="text-h3 font-weight-bold text-info">{{ totalTickers }}</div>
          <div class="text-subtitle-1 text-medium-emphasis">Total Tickers</div>
        </v-card>
      </v-col>
    </v-row>

    <!-- Recent Activity -->
    <v-row>
      <v-col cols="12">
        <v-card elevation="2">
          <v-card-title class="bg-primary text-white">
            <v-icon class="me-2">mdi-clock</v-icon>
            Recent Activity
          </v-card-title>

          <v-card-text class="pa-0">
            <v-list v-if="recentActivity.length > 0">
              <v-list-item
                v-for="(activity, index) in recentActivity"
                :key="index"
                :class="{ 'border-b': index < recentActivity.length - 1 }"
              >
                <template v-slot:prepend>
                  <v-avatar color="primary" size="40">
                    <v-icon color="white">mdi-chart-line</v-icon>
                  </v-avatar>
                </template>

                <v-list-item-title class="font-weight-medium">
                  {{ activity.ticker || 'Portfolio Analysis' }}
                </v-list-item-title>

                <v-list-item-subtitle>
                  {{ activity.analysis_type || 'Analysis' }} •
                  {{ formatDate(activity.created_at) }}
                </v-list-item-subtitle>

                <template v-slot:append>
                  <v-chip
                    :color="getStatusColor(activity.status)"
                    size="small"
                    variant="flat"
                  >
                    {{ activity.status || 'Completed' }}
                  </v-chip>
                </template>
              </v-list-item>
            </v-list>

            <v-empty-state
              v-else
              icon="mdi-clock-outline"
              title="No Recent Activity"
              text="Your analysis history will appear here once you start using ClariFi."
            ></v-empty-state>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </div>
</template>

<script>
import { computed } from 'vue'

export default {
  name: 'DashboardTab',
  props: {
    portfolios: {
      type: Array,
      default: () => []
    },
    analysisHistory: {
      type: Array,
      default: () => []
    },
    loading: {
      type: Boolean,
      default: false
    }
  },
  setup(props) {
    const recentAnalysisCount = computed(() => {
      const oneWeekAgo = new Date()
      oneWeekAgo.setDate(oneWeekAgo.getDate() - 7)

      return props.analysisHistory.filter(analysis =>
        new Date(analysis.created_at) > oneWeekAgo
      ).length
    })

    const accuracyRate = computed(() => {
      // Mock accuracy rate - in real app this would come from API
      return 75
    })

    const totalTickers = computed(() => {
      return props.portfolios.reduce((total, portfolio) => {
        return total + (portfolio.tickers?.length || 0)
      }, 0)
    })

    const recentActivity = computed(() => {
      return props.analysisHistory
        .slice(0, 5)
        .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
    })

    const formatDate = (dateString) => {
      const date = new Date(dateString)
      const now = new Date()
      const diffTime = Math.abs(now - date)
      const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))

      if (diffDays === 1) return 'Yesterday'
      if (diffDays < 7) return `${diffDays} days ago`

      return date.toLocaleDateString()
    }

    const getStatusColor = (status) => {
      switch (status?.toLowerCase()) {
        case 'completed': return 'success'
        case 'failed': return 'error'
        case 'running': return 'warning'
        default: return 'success'
      }
    }

    return {
      recentAnalysisCount,
      accuracyRate,
      totalTickers,
      recentActivity,
      formatDate,
      getStatusColor
    }
  }
}
</script>

<style scoped>
.border-b {
  border-bottom: 1px solid rgba(0, 0, 0, 0.12);
}
</style>
