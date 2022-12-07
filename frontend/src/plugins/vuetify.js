import Vue from 'vue';
import Vuetify from 'vuetify';
import i18n from '../locales/i18n';
import fr from 'vuetify/src/locale/fr.ts';

Vue.use(Vuetify);

export default new Vuetify({
  theme: {
    themes: {
      light: {
        primary: '#0b1783',
        secondary: '#e3005c',
      },
    },
  },
  lang: {
    locales: { fr },
    current: 'fr',
    t: (key, ...params) => i18n.t(key, params),
  },
});