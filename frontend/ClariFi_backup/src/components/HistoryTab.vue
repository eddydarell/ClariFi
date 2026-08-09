<template>
  <div>
    <v-row class="mb-6">
      <v-col>
        <div class="d-flex justify-space-between align-center">
          <h2 class="text-h4 font-weight-bold text-primary">
            <v-icon class="me-2">mdi-history</v-icon>
            Analysis History
          </h2>
          <v-btn
            color="error"
            variant="outlined"
            @click="showClearDialog = true"
            prepend-icon="mdi-delete"
            :disabled="history.length === 0"
          >
            Clear All
          </v-btn>
        </div>
      </v-col>
    </v-row>

    <!-- Filters -->
    <v-row class="mb-4">
      <v-col cols="12" md="4">
        <v-text-field
          v-model="searchQuery"
          label="Search analyses"
          variant="outlined"
          prepend-inner-icon="mdi-magnify"
          clearable
          density="compact"
        ></v-text-field>
      </v-col>
      <v-col cols="12" md="3">
        <v-select
          v-model="filterType"
          label="Filter by type"
          :items="analysisTypes"
          variant="outlined"
          density="compact"
          clearable
        ></v-select>
      </v-col>
      <v-col cols="12" md="3">
        <v-select
          v-model="filterStatus"
          label="Filter by status"
          :items="statusOptions"
          variant="outlined"
          density="compact"
          clearable
        ></v-select>
      </v-col>
      <v-col cols="12" md="2">
        <v-select
          v-model="sortBy"
          label="Sort by"
          :items="sortOptions"
          variant="outlined"
          density="compact"
        ></v-select>
      </v-col>
    </v-row>

    <!-- History List -->
    <v-card elevation="2" v-if="filteredHistory.length > 0">
      <v-list>
        <template v-for="(analysis, index) in paginatedHistory" :key="analysis.id">
          <v-list-item
            :class="{ 'border-b': index < paginatedHistory.length - 1 }"
            class="py-4"
          >
            <template v-slot:prepend>
              <v-avatar :color="getTypeColor(analysis.analysis_type)" size="48">
                <v-icon color="white">{{ getTypeIcon(analysis.analysis_type) }}</v-icon>
              </v-avatar>
            </template>

            <v-list-item-title class="font-weight-medium text-h6">
              {{ analysis.ticker || 'Portfolio Analysis' }}
            </v-list-item-title>

            <v-list-item-subtitle class="mt-1">
              <div class="d-flex align-center flex-wrap ga-2 mb-2">
                <v-chip size="small" :color="getTypeColor(analysis.analysis_type)" variant="flat">
                  {{ analysis.analysis_type || 'Analysis' }}
                </v-chip>
                <v-chip size="small" :color="getStatusColor(analysis.status)" variant="flat">
                  {{ analysis.status || 'Completed' }}
                </v-chip>
                <v-chip size="small" color="grey" variant="outlined">
                  {{ formatDate(analysis.created_at) }}
                </v-chip>
              </div>

              <div v-if="analysis.description" class="text-body-2 text-medium-emphasis">
                {{ analysis.description }}
              </div>

              <div v-if="analysis.parameters" class="text-body-2 text-medium-emphasis mt-1">
                <strong>Parameters:</strong> {{ formatParameters(analysis.parameters) }}
              </div>
            </v-list-item-subtitle>

            <template v-slot:append>
              <div class="d-flex flex-column ga-2">
                <v-btn
                  icon="mdi-eye"
                  size="small"
                  variant="outlined"
                  color="primary"
                  @click="viewAnalysis(analysis)"
                ></v-btn>

                <v-btn
                  icon="mdi-download"
                  size="small"
                  variant="outlined"
                  color="success"
                  @click="downloadAnalysis(analysis)"
                ></v-btn>

                <v-btn
                  icon="mdi-delete"
                  size="small"
                  variant="outlined"
                  color="error"
                  @click="confirmDelete(analysis)"
                ></v-btn>
              </div>
            </template>
          </v-list-item>
        </template>
      </v-list>

      <!-- Pagination -->
      <v-card-actions v-if="totalPages > 1">
        <v-spacer></v-spacer>
        <v-pagination
          v-model="currentPage"
          :length="totalPages"
          total-visible="7"
        ></v-pagination>
        <v-spacer></v-spacer>
      </v-card-actions>
    </v-card>

    <!-- Empty State -->
    <v-empty-state
      v-else
      icon="mdi-history"
      title="No Analysis History"
      text="Your analysis results will appear here once you start using ClariFi."
    >
      <template v-slot:actions>
        <v-btn
          color="primary"
          @click="$emit('navigate-to-analysis')"
          prepend-icon="mdi-chart-bar"
        >
          Run Your First Analysis
        </v-btn>
      </template>
    </v-empty-state>

    <!-- Delete Confirmation Dialog -->
    <v-dialog v-model="showDeleteDialog" max-width="400">
      <v-card>
        <v-card-title class="bg-error text-white">
          <v-icon class="me-2">mdi-delete</v-icon>
          Confirm Delete
        </v-card-title>
        <v-card-text class="pa-6">
          Are you sure you want to delete this analysis? This action cannot be undone.
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn @click="showDeleteDialog = false">Cancel</v-btn>
          <v-btn
            color="error"
            @click="deleteAnalysis"
            :loading="loading"
          >
            Delete
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Clear All Confirmation Dialog -->
    <v-dialog v-model="showClearDialog" max-width="400">
      <v-card>
        <v-card-title class="bg-error text-white">
          <v-icon class="me-2">mdi-delete-sweep</v-icon>
          Clear All History
        </v-card-title>
        <v-card-text class="pa-6">
          Are you sure you want to delete all analysis history? This action cannot be undone.
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn @click="showClearDialog = false">Cancel</v-btn>
          <v-btn
            color="error"
            @click="clearAllHistory"
            :loading="loading"
          >
            Clear All
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script>
import { ref, computed } from 'vue'

export default {
  name: 'HistoryTab',
  props: {
    history: {
      type: Array,
      default: () => []
    },
    loading: {
      type: Boolean,
      default: false
    }
  },
  emits: ['delete-analysis', 'navigate-to-analysis'],
  setup(props, { emit }) {
    const searchQuery = ref('')
    const filterType = ref(null)
    const filterStatus = ref(null)
    const sortBy = ref('date_desc')
    const currentPage = ref(1)
    const itemsPerPage = 10

    const showDeleteDialog = ref(false)
    const showClearDialog = ref(false)
    const selectedAnalysis = ref(null)

    const analysisTypes = [
      'Pattern Analysis',
      'Event Correlation',
      'Options Analysis',
      'Seasonal Analysis',
      'Portfolio Analysis',
      'Comparison Analysis'
    ]

    const statusOptions = [
      'Completed',
      'Failed',
      'Running',
      'Pending'
    ]

    const sortOptions = [
      { title: 'Date (Newest)', value: 'date_desc' },
      { title: 'Date (Oldest)', value: 'date_asc' },
      { title: 'Ticker A-Z', value: 'ticker_asc' },
      { title: 'Ticker Z-A', value: 'ticker_desc' },
      { title: 'Type', value: 'type' },
      { title: 'Status', value: 'status' }
    ]

    const filteredHistory = computed(() => {
      let filtered = [...props.history]

      // Search filter
      if (searchQuery.value) {
        const query = searchQuery.value.toLowerCase()
        filtered = filtered.filter(analysis =>
          (analysis.ticker?.toLowerCase().includes(query)) ||
          (analysis.analysis_type?.toLowerCase().includes(query)) ||
          (analysis.description?.toLowerCase().includes(query))
        )
      }

      // Type filter
      if (filterType.value) {
        filtered = filtered.filter(analysis =>
          analysis.analysis_type === filterType.value
        )
      }

      // Status filter
      if (filterStatus.value) {
        filtered = filtered.filter(analysis =>
          analysis.status === filterStatus.value
        )
      }

      // Sort
      filtered.sort((a, b) => {
        switch (sortBy.value) {
          case 'date_desc':
            return new Date(b.created_at) - new Date(a.created_at)
          case 'date_asc':
            return new Date(a.created_at) - new Date(b.created_at)
          case 'ticker_asc':
            return (a.ticker || '').localeCompare(b.ticker || '')
          case 'ticker_desc':
            return (b.ticker || '').localeCompare(a.ticker || '')
          case 'type':
            return (a.analysis_type || '').localeCompare(b.analysis_type || '')
          case 'status':
            return (a.status || '').localeCompare(b.status || '')
          default:
            return 0
        }
      })

      return filtered
    })

    const totalPages = computed(() => {
      return Math.ceil(filteredHistory.value.length / itemsPerPage)
    })

    const paginatedHistory = computed(() => {
      const start = (currentPage.value - 1) * itemsPerPage
      const end = start + itemsPerPage
      return filteredHistory.value.slice(start, end)
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

    const formatParameters = (parameters) => {
      if (!parameters) return ''
      if (typeof parameters === 'string') return parameters

      const params = Object.entries(parameters)
        .filter(([key, value]) => value !== null && value !== undefined)
        .map(([key, value]) => `${key}: ${value}`)
        .slice(0, 3)
        .join(', ')

      return params + (Object.keys(parameters).length > 3 ? '...' : '')
    }

    const getTypeColor = (type) => {
      const colors = {
        'Pattern Analysis': 'primary',
        'Event Correlation': 'success',
        'Options Analysis': 'warning',
        'Seasonal Analysis': 'info',
        'Portfolio Analysis': 'purple',
        'Comparison Analysis': 'orange'
      }
      return colors[type] || 'grey'
    }

    const getTypeIcon = (type) => {
      const icons = {
        'Pattern Analysis': 'mdi-chart-line',
        'Event Correlation': 'mdi-calendar-clock',
        'Options Analysis': 'mdi-finance',
        'Seasonal Analysis': 'mdi-weather-partly-cloudy',
        'Portfolio Analysis': 'mdi-briefcase',
        'Comparison Analysis': 'mdi-scale-balance'
      }
      return icons[type] || 'mdi-chart-bar'
    }

    const getStatusColor = (status) => {
      switch (status?.toLowerCase()) {
        case 'completed': return 'success'
        case 'failed': return 'error'
        case 'running': return 'warning'
        case 'pending': return 'info'
        default: return 'success'
      }
    }

    const viewAnalysis = (analysis) => {
      // In a real app, this would navigate to a detailed view
      console.log('View analysis:', analysis)
    }

    const downloadAnalysis = (analysis) => {
      // In a real app, this would download the analysis results
      console.log('Download analysis:', analysis)
    }

    const confirmDelete = (analysis) => {
      selectedAnalysis.value = analysis
      showDeleteDialog.value = true
    }

    const deleteAnalysis = () => {
      if (selectedAnalysis.value) {
        emit('delete-analysis', selectedAnalysis.value.id)
        showDeleteDialog.value = false
        selectedAnalysis.value = null
      }
    }

    const clearAllHistory = () => {
      // In a real app, this would clear all history
      console.log('Clear all history')
      showClearDialog.value = false
    }

    return {
      searchQuery,
      filterType,
      filterStatus,
      sortBy,
      currentPage,
      showDeleteDialog,
      showClearDialog,
      analysisTypes,
      statusOptions,
      sortOptions,
      filteredHistory,
      totalPages,
      paginatedHistory,
      formatDate,
      formatParameters,
      getTypeColor,
      getTypeIcon,
      getStatusColor,
      viewAnalysis,
      downloadAnalysis,
      confirmDelete,
      deleteAnalysis,
      clearAllHistory
    }
  }
}
</script>

<style scoped>
.border-b {
  border-bottom: 1px solid rgba(0, 0, 0, 0.12);
}
</style>
