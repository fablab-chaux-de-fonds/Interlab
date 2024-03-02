import Vue from 'vue';
import vuetify from '~/plugins/vuetify';
import MachinePrice from '~/components/MachinePrice';

new Vue({
    vuetify,
    el: '#vue',
    delimiters: ['[[', ']]'],
    components: { MachinePrice }
});