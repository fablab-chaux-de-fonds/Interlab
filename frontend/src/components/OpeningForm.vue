<template>
    <div>
        <v-select v-model="select" label="Opening" name="opening" :items="backend.opening_items"
                outlined append-icon="bi bi-chevron-down">
            <i class="bi bi-caret-down-fill"></i>
        </v-select>

        <date-picker v-model="start" :init-date=start name="start_date" label='start'></date-picker>
        <time-picker v-model="start" :init-time=start :max="end" input-name="start_time" label="start" @update-time=updateTime></time-picker>
        <time-picker v-model="end" :init-time=end :min="start" input-name="end_time" label="end" @update-time=updateTime></time-picker>
    </div>
</template>

<script>
var moment = require('moment');
import DatePicker from './DatePicker';
import TimePicker from './TimePicker'

export default {    
    props: ['backend'],
    data: function() {
        return {
            start: this.backend.start,
            end: this.backend.end,
            select: 1
        }
    },
    components: {
        DatePicker,
        TimePicker,
    },
    methods: {
        updateTime(time, inputName){
            console.log(inputName)
            if (inputName === 'start_time'){
                this.start = (moment(this.start).format('YYYY-MM-DD') + 'T' + time + ':00')
            } 
            if (inputName === 'end_time'){
                this.end = (moment(this.end).format('YYYY-MM-DD') + 'T' + time + ':00')
            }
        }
    },
}

</script>