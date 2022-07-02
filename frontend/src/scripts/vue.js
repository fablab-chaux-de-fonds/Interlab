import Vue from 'vue';
import vuetify from '~/plugins/vuetify';
import OpeningForm from '~/components/OpeningForm';

new Vue({
    el: '#create-opening',
    components: {
        OpeningForm
    },
    vuetify,
});