<template>
  <div>
    <v-row class="mb-6">
      <v-col>
        <div class="d-flex justify-space-between align-center">
          <h2 class="text-h4 font-weight-bold text-primary">
            <v-icon class="me-2">mdi-briefcase</v-icon>
            Portfolio Management
          </h2>
          <v-btn
            color="primary"
            @click="showCreateDialog = true"
            prepend-icon="mdi-plus"
            size="large"
          >
            Create Portfolio
          </v-btn>
        </div>
      </v-col>
    </v-row>

    <!-- Portfolios Grid -->
    <v-row v-if="portfolios.length > 0">
      <v-col
        v-for="portfolio in portfolios"
        :key="portfolio.id"
        cols="12"
        md="6"
        lg="4"
      >
        <v-card elevation="2" class="h-100">
          <v-card-title class="bg-primary text-white d-flex justify-space-between align-center">
            <span>{{ portfolio.name }}</span>
            <div>
              <v-btn
                icon="mdi-plus"
                size="small"
                variant="text"
                @click="openAddTickerDialog(portfolio.id)"
                class="me-1"
              ></v-btn>
              <v-btn
                icon="mdi-chart-bar"
                size="small"
                variant="text"
                @click="$emit('analyze-portfolio', portfolio.id)"
              ></v-btn>
            </div>
          </v-card-title>

          <v-card-text>
            <p class="text-medium-emphasis mb-3">{{ portfolio.description || 'No description' }}</p>

            <div class="mb-3">
              <v-chip size="small" color="info" class="me-2">
                {{ portfolio.tickers?.length || 0 }} tickers
              </v-chip>
              <v-chip size="small" color="success">
                Created {{ formatDate(portfolio.created_at) }}
              </v-chip>
            </div>

            <!-- Tickers List -->
            <v-list v-if="portfolio.tickers?.length > 0" density="compact">
              <v-list-item
                v-for="ticker in portfolio.tickers"
                :key="ticker.ticker"
                class="px-0"
              >
                <v-list-item-title class="font-weight-medium">
                  {{ ticker.ticker }}
                </v-list-item-title>
                <v-list-item-subtitle>
                  {{ ticker.quantity }} shares
                </v-list-item-subtitle>
                <template v-slot:append>
                  <v-btn
                    icon="mdi-close"
                    size="x-small"
                    variant="text"
                    color="error"
                    @click="$emit('remove-ticker', portfolio.id, ticker.ticker)"
                  ></v-btn>
                </template>
              </v-list-item>
            </v-list>

            <v-alert v-else type="info" density="compact" class="mt-2">
              No tickers added yet
            </v-alert>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Empty State -->
    <v-empty-state
      v-else
      icon="mdi-briefcase-outline"
      title="No Portfolios Created"
      text="Create your first portfolio to start tracking and analyzing your investments."
    >
      <template v-slot:actions>
        <v-btn
          color="primary"
          @click="showCreateDialog = true"
          prepend-icon="mdi-plus"
        >
          Create Portfolio
        </v-btn>
      </template>
    </v-empty-state>

    <!-- Create Portfolio Dialog -->
    <v-dialog v-model="showCreateDialog" max-width="500">
      <v-card>
        <v-card-title class="bg-primary text-white">
          <v-icon class="me-2">mdi-briefcase-plus</v-icon>
          Create New Portfolio
        </v-card-title>

        <v-card-text class="pa-6">
          <v-form ref="createForm" v-model="createFormValid">
            <v-text-field
              v-model="newPortfolio.name"
              label="Portfolio Name"
              :rules="[v => !!v || 'Name is required']"
              required
              variant="outlined"
              class="mb-4"
            ></v-text-field>

            <v-textarea
              v-model="newPortfolio.description"
              label="Description (Optional)"
              variant="outlined"
              rows="3"
            ></v-textarea>
          </v-form>
        </v-card-text>

        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn @click="showCreateDialog = false">Cancel</v-btn>
          <v-btn
            color="primary"
            @click="createPortfolio"
            :disabled="!createFormValid"
            :loading="loading"
          >
            Create
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Add Ticker Dialog -->
    <v-dialog v-model="showAddTickerDialog" max-width="500">
      <v-card>
        <v-card-title class="bg-primary text-white">
          <v-icon class="me-2">mdi-plus</v-icon>
          Add Ticker
        </v-card-title>

        <v-card-text class="pa-6">
          <v-form ref="tickerForm" v-model="tickerFormValid">
            <v-text-field
              v-model="newTicker.ticker"
              label="Stock Ticker"
              :rules="[v => !!v || 'Ticker is required']"
              required
              variant="outlined"
              class="mb-4"
              placeholder="e.g., AAPL, GOOGL"
            ></v-text-field>

            <v-text-field
              v-model.number="newTicker.quantity"
              label="Quantity"
              type="number"
              :rules="[v => v >= 0 || 'Quantity must be 0 or greater']"
              variant="outlined"
              class="mb-4"
            ></v-text-field>

            <v-text-field
              v-model.number="newTicker.avg_cost"
              label="Average Cost per Share"
              type="number"
              step="0.01"
              variant="outlined"
              prefix="$"
            ></v-text-field>
          </v-form>
        </v-card-text>

        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn @click="showAddTickerDialog = false">Cancel</v-btn>
          <v-btn
            color="primary"
            @click="addTicker"
            :disabled="!tickerFormValid"
            :loading="loading"
          >
            Add Ticker
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script>
import { ref, reactive } from 'vue'

export default {
  name: 'PortfoliosTab',
  props: {
    portfolios: {
      type: Array,
      default: () => []
    },
    loading: {
      type: Boolean,
      default: false
    }
  },
  emits: ['create-portfolio', 'add-ticker', 'remove-ticker', 'analyze-portfolio'],
  setup(props, { emit }) {
    const showCreateDialog = ref(false)
    const showAddTickerDialog = ref(false)
    const createFormValid = ref(false)
    const tickerFormValid = ref(false)
    const currentPortfolioId = ref(null)

    const newPortfolio = reactive({
      name: '',
      description: ''
    })

    const newTicker = reactive({
      ticker: '',
      quantity: 0,
      avg_cost: 0
    })

    const formatDate = (dateString) => {
      const date = new Date(dateString)
      return date.toLocaleDateString()
    }

    const createPortfolio = async () => {
      if (!createFormValid.value) return

      emit('create-portfolio', { ...newPortfolio })

      // Reset form
      newPortfolio.name = ''
      newPortfolio.description = ''
      showCreateDialog.value = false
    }

    const openAddTickerDialog = (portfolioId) => {
      currentPortfolioId.value = portfolioId
      showAddTickerDialog.value = true
    }

    const addTicker = async () => {
      if (!tickerFormValid.value || !currentPortfolioId.value) return

      emit('add-ticker', currentPortfolioId.value, { ...newTicker })

      // Reset form
      newTicker.ticker = ''
      newTicker.quantity = 0
      newTicker.avg_cost = 0
      showAddTickerDialog.value = false
      currentPortfolioId.value = null
    }

    return {
      showCreateDialog,
      showAddTickerDialog,
      createFormValid,
      tickerFormValid,
      newPortfolio,
      newTicker,
      formatDate,
      createPortfolio,
      openAddTickerDialog,
      addTicker
    }
  }
}
</script>
