import { createApp } from 'vue';
import { createI18n } from 'vue-i18n';

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
            }, 
            "machines": "Machines"
        }
    },
};

const i18n = createI18n({
    locale: 'fr',
    messages
  });
  
  const app = createApp();
  
  app.use(i18n);
  
  export default i18n;