import Vue from 'vue';
import vuetify from '~/plugins/vuetify';

var moment = require('moment');
const initial = JSON.parse(document.getElementById('initial').textContent);
var start = new Date(initial.start);
var end = new Date(initial.end);

new Vue({
  vuetify,
  delimiters: ["[[", "]]"],

  data: {
    time: null,
    modal: false,
    modal2: false,
    modal3: false,
    date: moment(start).format('YYYY-MM-DD'),
    start: moment(start).format('HH:mm:ss'),
    end: moment(end).format('HH:mm:ss'),
    items: initial.items,
  }
}
).$mount('#timepicker');