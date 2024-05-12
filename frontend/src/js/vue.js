import { createApp } from 'vue';
import vuetify from '~/plugins/vuetify';
import DatePicker from '~/components/DatePicker';
import TimePicker from '~/components/TimePicker';
import OpeningCalendar from '~/components/OpeningCalendar';

const app = createApp({
    components: {
        OpeningCalendar,
        DatePicker,
        TimePicker
    }
});

app.use(vuetify);

app.mount('#vue');