<template>
    <div>

        <v-dialog ref="dialog" v-model="dialog" :return-value.sync="date" persistent width="290px">
            <template v-slot:activator="{ on, attrs }">
                <v-text-field :label=label readonly v-bind="attrs" v-on="on" outlined :name=inputName
                    :value="formatDate()"></v-text-field>
            </template>
            <v-date-picker v-model="date" scrollable color="#0b1783" first-day-of-week=1 prev-icon="bi bi-chevron-left"
                next-icon="bi bi-chevron-right">
                <v-spacer></v-spacer>
                <v-btn text color="primary" @click="dialog = false">
                    Cancel
                </v-btn>
                <v-btn text color="primary" @click="$refs.dialog.save(date)">
                    OK
                </v-btn>
            </v-date-picker>
        </v-dialog>

    </div>
</template>

<script>
    var moment = require('moment');
    moment.locale('fr');
    module.exports = {
        props: ['init-date', 'label', 'input-name'],
        data: function () {
            return {
                date: this.initDate,
                dialog: false,
            }
        },
        methods: {
            formatDate() {
                return moment(this.date).format('D MMMM YYYY');
            },
        },
    }
</script>