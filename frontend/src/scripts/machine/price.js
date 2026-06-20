import Vue from 'vue';
import vuetify from '~/plugins/vuetify';
import MachinePrice from '~/components/MachinePrice';
import 'font-awesome/css/font-awesome.min.css';

new Vue({
    vuetify,
    el: '#vue',
    delimiters: ['[[', ']]'],
    components: { MachinePrice },
    icons: {
        iconfont: 'fa4',
    },
});