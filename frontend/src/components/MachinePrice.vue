<template>
  <v-app>
    <h4>Simulateur</h4>
    <form class="form">
      <div class="form-floating my-2">
        <input type="number" step="50" min="0" max="10000" class="form-control" id="weight" v-model="weight" />
        <label for="weight">Material weight (g):</label>
      </div>
      <div class="form-floating" v-if="weightSupport > 0.0">
        <input type="number" step="50" min="0" max="10000" id="weightSupport" class="form-control"
          v-model="weightSupport" />
        <label for="weightSupport" style="font-size: 0.75rem;">Support material weight (g):</label>
      </div>
      <div class="form-floating">
        <input type="number" step="1" min="1" max="168" class="form-control" id="nbrHours" v-model="nbrHours" />
        <label for="nbrHours">Number of hours:</label>
      </div>
    </form>
    <div class="d-flex justify-center mb-6 bg-surface-variant">
      <v-sheet class="ma-2 pa-2">
        Price: {{ price }} CHF
      </v-sheet>
      <v-sheet class="ma-2 pa-2">
        Half price: {{ priceHalf }} CHF
      </v-sheet>
    </div>
    <h5 class="mt-10">Prix de base horaire (sans matière):</h5>
      <vdsadsadsaable theme="dark" striped="even">
        <thead>
          <tr>
            <th>N°</th>
            <th>Prix</th>
            <th>Prix 1/2</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(priceDetail, index) in priceDetails" :key="index">
            <td>{{ priceDetail.id }}</td>
            <td>{{ priceDetail.price }}</td>
            <td>{{ priceDetail.priceHalf }}</td>
          </tr>
        </tbody>
      </vdsadsadsaable>
  </v-app>
</template>

<script lang="ts">
export default {
  props: ['firstHourPrice', 'hourFactor', 'maxDivider', 'matterFactor', 'supportMatterFactor'],
  data() {
    return {
      nbrHours: 8,
      weight: 0,
      weightSupport: 0
    }
  },
  computed: {
    priceDetails() {
      let index = 2;
      let divider = 1.0;
      let price = this.firstHourPrice;
      let priceHalf = price / 2;
      let total = price;
      let lastTotal = total;
      let totalHalf = priceHalf;
      let priceDetails = [{ id: '1', price: this.priceFormat(price), priceHalf: this.priceFormat(priceHalf) }];
      console.log(divider + ' ' + price)
      while (divider < this.maxDivider && price > 1) {
        divider = index * this.hourFactor;
        if (divider > this.maxDivider) {
          divider = this.maxDivider;
        }
        lastTotal = total;
        let currentPrice = this.firstHourPrice / divider;
        total += Math.floor(currentPrice);
        price = total - Math.ceil(lastTotal);
        if (price < 1) {
          price = 1;
        }
        lastTotal = totalHalf;
        totalHalf += Math.floor(currentPrice / 2);
        priceHalf = totalHalf - Math.ceil(lastTotal);
        if (priceHalf < 1) {
          priceHalf = 1;
        }
        priceDetails.push({ id: index.toFixed(0), price: this.priceFormat(price), priceHalf: this.priceFormat(priceHalf) });
        index++;
      }
      return priceDetails;
    },
    matterPrice() {
      return this.matterFactor.toFixed(3);
    },
    supportMatterPrice() {
      return this.supportMatterFactor.toFixed(2);
    },
    price() {
      return this.computePrice(this.firstHourPrice);
    },
    priceHalf() {
      return this.computePrice(this.firstHourPrice / 2);
    },
    priceQuarter() {
      return this.computePrice(this.firstHourPrice / 4);
    }
  },
  methods: {
    computePrice: function (currentFirstHourPrice) {
      let value = currentFirstHourPrice;
      let currentPrice = value;

      if (this.nbrHours > 1) {
        for (let i = 2; i <= this.nbrHours; i++) {
          let a = i * this.hourFactor;
          if (a > this.maxDivider) {
            a = this.maxDivider;
          }
          currentPrice = Math.floor(currentFirstHourPrice / a);
          if (currentPrice < 1) {
            currentPrice = 1;
          }
          value += currentPrice;
        }
      }

      let lastFullHour = Math.floor(this.nbrHours);
      let lastHourFactor = this.nbrHours % lastFullHour;
      if (lastHourFactor != 0) {
        let a = (lastFullHour + 1) * this.hourFactor;
        if (a > this.maxDivider) {
          a = this.maxDivider;
        }

        currentPrice = Math.floor(currentFirstHourPrice / a) * lastHourFactor;
        if (currentPrice >= 1) {
          value += currentPrice;
        }
      }

      const priceMatter =
        this.weight * this.matterFactor +
        this.weightSupport * this.supportMatterFactor;

      return this.priceFormat(value + priceMatter);
    },
    priceFormat: function (price) {
      return Math.ceil(price).toFixed(2)
    }
  }
}
</script>