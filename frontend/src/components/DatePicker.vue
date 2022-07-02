<template>
    <div>
    
        <v-dialog ref="date" v-model="dialog" :return-value.sync="date" persistent width="290px">
            <template v-slot:activator="{ on, attrs }">
                <v-text-field :label=label readonly v-bind="attrs" v-on="on" outlined :name=name
                    :value="formatDate()"></v-text-field>
            </template>
            <v-date-picker v-model="date" scrollable color="#0b1783" first-day-of-week=1>
                <v-spacer></v-spacer>
                <v-btn text color="primary" @click="dialog = false">
                    Cancel
                </v-btn>
                <v-btn text color="primary" @click="$refs.date.save(date)">
                    OK
                </v-btn>
            </v-date-picker>
        </v-dialog>

    </div>
</template>

<script>
    var moment = require('moment');
    module.exports = {
        props: ['init-date', 'label', 'name'],
        data: function () {
            return {
                date: moment(this.initDate).format('YYYY-MM-DD'),
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