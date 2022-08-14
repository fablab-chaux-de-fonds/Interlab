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
            "opening": "Ouverture",
            "has_subcription": "Sur inscription",
            "price": "Tarifs",
            "more_information": "Plus d'info",
            "register": "S'inscrire",
            "registration_limit": "Limite d'inscription",
            "registration_limit_hint": "laisser vide si pas de limite, mais inscription obligatoire",
            "start_date_after_end_date": "La date du début est après la date de fin",
            "start_time_after_end_time": "L'heure du début est après l'heure de fin",
            "end_date_before_start_date": "La date du fin est avant la date de début",
            "end_time_before_start_time": "L'heure du fin est avant l'heure de début",
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