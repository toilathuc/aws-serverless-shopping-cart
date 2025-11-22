<template>
  <v-container fluid class="mt-6">
    <v-row justify="center">
      <v-col cols="12" md="10" lg="8">
        <v-card>
          <v-card-title class="d-flex align-center">
            <div>
              <div class="headline font-weight-bold">Cart Insights</div>
              <div class="subtitle-2 grey--text">
                Live view of how many times each product appears in carts.
              </div>
            </div>
            <v-spacer></v-spacer>
            <v-btn
              color="primary"
              outlined
              @click="loadStats"
              :loading="loading"
              :disabled="loading"
            >
              Refresh
            </v-btn>
          </v-card-title>
          <v-divider></v-divider>
          <v-card-text>
            <v-alert v-if="error" type="error" dense outlined class="mb-4">
              {{ error }}
            </v-alert>

            <div v-if="loading" class="text-center pa-8">
              <v-progress-circular indeterminate size="48" color="primary" />
            </div>

            <div v-else>
              <div v-if="!stats">
                <p class="subtitle-1 mb-0">
                  No aggregated stats are available yet. Try refreshing in a few
                  minutes once shoppers interact with the store.
                </p>
              </div>

              <div v-else>
                <v-row v-if="summaryMetrics.length">
                  <v-col
                    cols="12"
                    sm="6"
                    v-for="metric in summaryMetrics"
                    :key="metric.name"
                  >
                    <v-sheet class="pa-4 rounded-lg elevation-1">
                      <div class="caption text-uppercase grey--text">
                        {{ metric.label }}
                      </div>
                      <div class="headline font-weight-bold">
                        {{ metric.value }}
                      </div>
                    </v-sheet>
                  </v-col>
                </v-row>

                <h3 class="subtitle-1 font-weight-bold mt-6 mb-2">
                  Products in carts
                </h3>

                <v-data-table
                  v-if="productRows.length"
                  :headers="tableHeaders"
                  :items="productRows"
                  :items-per-page="5"
                  class="elevation-1"
                  dense
                  disable-sort
                >
                  <template #item.product="{ item }">
                    <div>
                      <div class="font-weight-medium">{{ item.name }}</div>
                      <div class="caption grey--text">{{ item.productId }}</div>
                    </div>
                  </template>
                  <template #item.quantity="{ item }">
                    <span class="font-weight-bold">{{ item.quantity }}</span>
                  </template>
                </v-data-table>
                <div v-else class="body-2 grey--text">
                  We have not recorded product-level totals yet.
                </div>
              </div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
import { mapState } from "vuex";
import { getAdminStats } from "@/backend/api";

const TABLE_HEADERS = [
  { text: "Product", value: "product", align: "start" },
  { text: "Quantity in carts", value: "quantity", align: "end" }
];

export default {
  name: "AdminStats",
  data() {
    return {
      stats: null,
      loading: false,
      error: null,
      tableHeaders: TABLE_HEADERS
    };
  },
  computed: {
    ...mapState(["products"]),
    productIndex() {
      if (!this.products) {
        return {};
      }
      return this.products.reduce((acc, product) => {
        acc[product.productId] = product;
        return acc;
      }, {});
    },
    summaryMetrics() {
      if (!this.stats) {
        return [];
      }

      const ignoredKeys = [
        "pk",
        "products",
        "productTotals",
        "totals",
        "popularProducts"
      ];
      return Object.keys(this.stats)
        .filter(
          (key) =>
            ignoredKeys.indexOf(key) === -1 &&
            (typeof this.stats[key] === "number" ||
              typeof this.stats[key] === "string")
        )
        .map((key) => ({
          name: key,
          label: this.humanizeKey(key),
          value: this.stats[key]
        }));
    },
    productRows() {
      if (!this.stats) {
        return [];
      }

      const totals = this.extractProductTotals(this.stats);

      return totals
        .map((entry) => {
          const cleanId = this.cleanProductId(entry.productId);
          const product = this.productIndex[cleanId];
          return {
            productId: cleanId,
            name: product ? product.name : cleanId,
            quantity: entry.quantity
          };
        })
        .sort((a, b) => b.quantity - a.quantity);
    }
  },
  created() {
    if (!this.products) {
      this.$store.dispatch("fetchProducts");
    }
    this.loadStats();
  },
  methods: {
    async loadStats() {
      this.loading = true;
      this.error = null;
      try {
        this.stats = await getAdminStats();
      } catch (err) {
        let message = "Failed to load admin stats.";
        if (err && err.response && err.response.data) {
          message = err.response.data.message || message;
        } else if (err && err.message) {
          message = err.message;
        }
        this.error = message;
        this.stats = null;
      } finally {
        this.loading = false;
      }
    },
    extractProductTotals(stats) {
      const source =
        stats.products ||
        stats.productTotals ||
        stats.totals ||
        stats.popularProducts;

      if (!source) {
        return [];
      }

      if (Array.isArray(source)) {
        return source
          .map((item, index) => ({
            productId:
              item.productId ||
              item.product ||
              item.pk ||
              item.id ||
              `item-${index}`,
            quantity: Number(item.quantity || item.count || item.total || 0)
          }))
          .filter((item) => item.productId);
      }

      if (typeof source === "object") {
        return Object.keys(source).map((key) => ({
          productId: key,
          quantity: Number(source[key] || 0)
        }));
      }

      return [];
    },
    cleanProductId(value) {
      if (!value) {
        return value;
      }
      if (value.indexOf("product#") === 0) {
        return value.replace("product#", "");
      }
      return value;
    },
    humanizeKey(key) {
      return key
        .replace(/_/g, " ")
        .replace(/([a-z0-9])([A-Z])/g, "$1 $2")
        .replace(/\b\w/g, (char) => char.toUpperCase());
    }
  }
};
</script>
