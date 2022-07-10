import Vue from 'vue';
import vuetify from '~/plugins/vuetify';
import OpeningForm from '~/components/OpeningForm';
import OpeningCalendar from '~/components/OpeningCalendar';

new Vue({
    vuetify,
    el: '#vue',
    components: {
        OpeningCalendar,
        OpeningForm,
    },
});