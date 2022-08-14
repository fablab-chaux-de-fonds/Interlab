<template>
    <div>
    
        <v-dialog ref="date" v-model="dialog" :return-value.sync="date" persistent width="290px">
            <template v-slot:activator="{ on, attrs }">
                <v-text-field :label=label readonly v-bind="attrs" v-on="on" outlined :name=inputName
                    :value="formatDate()"
                    :rules=dateRules
                    ></v-text-field>
            </template>
            <v-date-picker 
            v-model="date" 
            scrollable 
            color="#0b1783" 
            first-day-of-week=1 
            prev-icon="bi bi-chevron-left"
            next-icon="bi bi-chevron-right">
                <v-spacer></v-spacer>
                <v-btn text color="primary" @click="dialog = false">
                    Cancel
                </v-btn>
                <v-btn text color="primary" @click="updateDate">
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
        props: ['init-date', 'label', 'input-name', 'date-rules'],
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
            updateDate(){
                dialog = false
                this.$refs.date.save(this.date)
                this.$emit('update-date', this.date, this.inputName)
            },
            formatDate_yyyymmdd(time) {
                if (time === undefined){
                    return ""
                } else {
                return moment(time).format('YYYY-MM-DD');
                }
            },
            
        },
    }
</script>