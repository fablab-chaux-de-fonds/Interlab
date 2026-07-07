<template>
  <v-app>
    <h4 class="mt-10">Simulateur</h4>
    <div class="row text-center">
      <div class="col">
        <div class="card card-tool">
          <i class="bi bi-cash pe-2 display-1"></i>
          <div class="card-body">Prix: {{ price }} CHF</div>
        </div>
      </div>
      <div class="col">
        <div class="card card-tool">
          <i class="bi bi-percent pe-2 display-1"></i>
          <div class="card-body">Réduit: {{ priceHalf }} CHF</div>
        </div>
      </div>
    </div>
    <form class="form">
      <v-text-field type="number" :step="1" :min="1" :max="168"  v-model="nbrHours" label="Durée impression (h)" prepend-icon="fa-hourglass" append-text="g"/>
      <v-text-field type="number" :step="50" :min="0" :max="10000" v-model="weight" label="Poid matière (g)" prepend-icon="fa-balance-scale" />
      <v-text-field type="number" :step="50" :min="0" :max="10000" v-model="weightSupport" label="Poid matière support (g)" prepend-icon="fa-th" v-if="supportMatterFactor > 0.0" />
    </form>
    <h5 class="mt-10">Prix de base horaire dégressif (sans matière):</h5>
      <v-simple-table dense>
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
      </v-simple-table>
  </v-app>
</template>

<script lang="ts">
export default {
  props: ['firstHourPrice', 'hourFactor', 'maxDivider', 'matterFactor', 'supportMatterFactor'],
  data() {
    return {
      nbrHours: null,
      weight: null,
      weightSupport: null
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