import Vue from 'vue';
import VueI18n from 'vue-i18n';

Vue.use(VueI18n);

const messages = {
    fr: {
        // TODO clean translation
        $vuetify: {
            "Today": "Aujourd'hui",
            "day": "Jour",
            "week": "Semaine",
            "month": "Mois",
            "4day": "4 jours",
            "opening": 'Ouverture',
            "event": "Évènement",
            "training": "Formation",
            "comment": "Commentaire",
            "date": "Date",
            "start": "Début",
            "end": "Fin",
            "opening": "Ouverture",
            "has_subcription": "Sur inscription",
            "price": "Tarifs",
            "more_information": "Plus d'info",
            "Register": "S'inscrire",
            "registration_limit": "Limite d'inscription",
            "registration_limit_hint": "laisser vide si pas de limite, mais inscription obligatoire",
            "calendar": {
                "moreEvents": "Plus d'évènements" //TODO fix translations with month view
            }
        }
    },
};

const i18n = new VueI18n({
    locale: 'fr', // set locale
    messages, // set locale messages
});

export default i18n;