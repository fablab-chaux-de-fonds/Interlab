import Vue from 'vue';
import Vuetify from 'vuetify';
import fr from 'vuetify/src/locale/fr.ts';

Vue.use(Vuetify);

export default new Vuetify({
    vuetify: new Vuetify(),
    theme: {
        themes: {
          options: {
            customProperties: true,
          },
          light: {
            primary: '#0b1783',
            secondary: '#e3005c',
          },
        },
      },
      lang: {
          locales: { fr },
          current: 'fr',
        },
});

