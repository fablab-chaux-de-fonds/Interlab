<template>
    <v-row>
      <v-col cols="6">
        <TimePicker
          v-model="localStartTime"
          :init-time=localStartTime
          :input-name=inputNameStart
          :label=labelStart
        ></TimePicker>
      </v-col>
      <v-col cols="6">
        <TimePicker
          v-model=localEndTime
          :init-time=localEndTime
          :input-name=inputNameEnd
          :label=labelEnd
        ></TimePicker>
      </v-col>
    </v-row>
  </template>

  <script>
  import TimePicker from './TimePicker.vue';

  export default {
    components: {TimePicker},
    props: ['initStartTime', 'initEndTime', 'labelStart', 'labelEnd', 'inputNameStart', 'inputNameEnd', 'min', 'max', 'form'],
    data: function () {
        return {
            localStartTime: this.initStartTime,
            localEndTime: this.initEndTime,
        }
    },
    watch: {
        localStartTime(newStartTime) {
            const [hours, minutes] = newStartTime.split(':').map(Number);
            const newEndTime = new Date();

            newEndTime.setHours(hours, minutes + 90);  // Set hours and add 90 minutes directly

            this.localEndTime = newEndTime.toTimeString().slice(0, 5); // Format as HH:MM
        },
    },
  };
  </script>