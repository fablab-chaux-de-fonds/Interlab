import Vue from 'vue';
import vuetify from '~/plugins/vuetify';
import OpeningForm from '~/components/OpeningForm';
import EventForm from '~/components/EventForm';
import OpeningCalendar from '~/components/OpeningCalendar';

new Vue({
    vuetify,
    el: '#vue',
    components: {
        OpeningCalendar,
        OpeningForm,
        EventForm
    },
});