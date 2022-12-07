<template>
    <div>

        <v-dialog ref="dialog" v-model="dialog" :return-value.sync="time" persistent width="290px">
            <template v-slot:activator="{ on, attrs }">
                <v-text-field v-model=time :label=label :name=inputName readonly v-bind="attrs" v-on="on" outlined>
                </v-text-field>
            </template>
            <v-time-picker v-if="dialog" v-model="time" full-width format="24hr" color="#0b1783" :allowed-minutes="allowedStep">
                <v-spacer></v-spacer>
                <v-btn text color="primary" @click="dialog = false">
                    Cancel
                </v-btn>
                <v-btn text color="primary" @click="$refs.dialog.save(time)">
                    OK
                </v-btn>
            </v-time-picker>
        </v-dialog>

    </div>
</template>

<script>
    module.exports = {
        props: ['init-time', 'label', 'input-name', 'min', 'max'],
        data: function () {
            return {
                dialog: false,
                time: this.initTime,
            }
        },
        methods: {
            allowedStep: m => m % 5 === 0,
        }
    }
</script>