import { createVuetify } from 'vuetify'; // Import createVuetify from 'vuetify'
import { createApp } from 'vue'; // Import createApp from Vue 3
import i18n from '../locales/i18n';
import { fr } from 'vuetify/locale';

// Create the Vue app instance
const app = createApp();

// Use Vuetify plugin with createVuetify and pass the app instance
const vuetify = createVuetify(app, {
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

export default vuetify;