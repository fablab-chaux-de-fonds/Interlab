import Vue from 'vue';
import vuetify from '~/plugins/vuetify';
import OpeningForm from '~/components/OpeningForm';
import DatePicker from '~/components/DatePicker';
import TimePicker from '~/components/TimePicker';
import OpeningCalendar from '~/components/OpeningCalendar';

new Vue({
    vuetify,
    el: '#vue',
    components: {
        OpeningCalendar,
        OpeningForm,
        DatePicker,
        TimePicker
    },
});