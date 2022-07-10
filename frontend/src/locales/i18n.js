import Vue from 'vue';
import VueI18n from 'vue-i18n';

Vue.use(VueI18n);

const messages = {
    fr: {
        $vuetify: {
            "Today": "Aujourd'hui",
            "day": "Jour",
            "week": "Semaine",
            "month": "Mois",
            "4day": "4 jours",
            "opening": 'Ouverture',
            "event": "Évènement",
            "comment": "Commentaire",
            "date": "Date",
            "start": "Début",
            "end": "Fin",
            "opening": "Ouverture"

        }
    },
};

const i18n = new VueI18n({
    locale: 'fr', // set locale
    messages, // set locale messages
});

export default i18n;