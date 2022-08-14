<template>
    <div>

        <v-dialog ref="time" v-model="dialog" :return-value.sync="time" persistent width="290px">
            <template v-slot:activator="{ on, attrs }">
                <v-text-field v-model=time :label=label :name=inputName readonly
                    v-bind="attrs" v-on="on" outlined
                    :rules=dateRules>
                </v-text-field>
            </template>
            <v-time-picker v-if="dialog" v-model="time" full-width format="24hr" :min="formatTime_hm(min)" :max="formatTime_hm(max)" color="#0b1783">
                <v-spacer></v-spacer>
                <v-btn text color="primary" @click="dialog = false">
                    Cancel
                </v-btn>
                <v-btn text color="primary" @click="updateTime">
                    OK
                </v-btn>
            </v-time-picker>
        </v-dialog>

    </div> 
</template>

<script>
    var moment = require('moment');
    module.exports = {
        props: ['init-time', 'label', 'input-name', 'min', 'max', 'date-rules'],
        data: function () {
            return {
                dialog: false,
                time: moment(this.initTime).format('HH:mm'),
            }
        },
        methods: {
            updateTime(){
                dialog = false
                this.$refs.time.save(this.time)
                this.$emit('update-time', this.time, this.inputName)
            },
            formatTime_hm(time) {
                if (time === undefined){
                    return ""
                } else {
                return moment(time).format('HH:mm');
                }
            },            
        },
    }
</script>