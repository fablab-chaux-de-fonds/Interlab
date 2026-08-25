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
export default {
    props: {
        initTime: String,
        label: String,
        inputName: String,
        min: String,
        max: String,
    },
    data() {
        return {
            dialog: false,
            time: this.initTime
        }
    },
    methods: {
        allowedStep: (m) => m % 5 === 0,
        updateTime() {
        // When the input changes, update the internal state and emit the change
        this.$emit('time', this.initTime);
        },
    },
    watch: {
        // Watch for changes to the `initTime` prop
        initTime(newInitTime) {
        // When `initTime` changes, update `time` to reflect the new prop value
        this.time = newInitTime;
        },
        time(newTime) {
        // Emit the updated time value to the parent component
        this.$emit('input', newTime);
        },
    },
};
</script>