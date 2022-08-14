<template>
    <div>
        <v-app>
            <v-container>
                <v-select 
                    v-model="event" 
                    name="event"
                    :label="$vuetify.lang.t('$vuetify.event')" 
                    :items="backend.event_items" 
                    return-object
                    outlined 
                    append-icon="bi bi-chevron-down" 
                    color="primary"
                    required
                    >
                    <i class="bi bi-caret-down-fill"></i>
                </v-select>

                <v-select v-if="event.is_on_site" class="mt-4" v-model="opening" :label="$vuetify.lang.t('$vuetify.opening')" name="opening"
                    :items="backend.opening_items" outlined append-icon="bi bi-chevron-down" color="primary">
                    <i class="bi bi-caret-down-fill"></i>
                </v-select>

                <v-row>
                    <v-col cols="8">
                        <date-picker v-model="start" :init-date=start input-name="start_date"
                            :label="$vuetify.lang.t('$vuetify.date')" @update-date=updateDate 
                            :date-rules="startDateRules"
                            >
                        </date-picker>
                    </v-col>
                    <v-col cols="4">
                        <time-picker v-model="start" :init-time=start input-name="start_time"
                            :label="$vuetify.lang.t('$vuetify.start')" @update-time=updateTime :date-rules="startTimeRules"></time-picker>
                    </v-col>
                </v-row>

                <v-row>
                    <v-col cols="8">
                        <date-picker v-model="start" :init-date=start input-name="end_date"
                            :label="$vuetify.lang.t('$vuetify.date')" @update-date=updateDate
                            :date-rules="endDateRules"
                            >
                        </date-picker>
                    </v-col>
                    <v-col cols="4">
                        <time-picker v-model="end" :init-time=end input-name="end_time"
                            :label="$vuetify.lang.t('$vuetify.end')" @update-time=updateTime :date-rules="endTimeRules"></time-picker>
                    </v-col>
                </v-row>

                <v-textarea
                    class="mt-2"
                    v-model="price"
                    name="price"
                    :label="$vuetify.lang.t('$vuetify.price')"
                    required
                    outlined
                ></v-textarea>

                <v-text-field 
                    class="mt-2" 
                    v-model="comment"
                    :label="$vuetify.lang.t('$vuetify.comment')" 
                    name="comment"
                    outlined
                ></v-text-field>

                <v-row align="center">
                    <v-col cols=10 class="pl-6">
                        {{ $vuetify.lang.t('$vuetify.has_subcription') }}
                    </v-col>

                    <v-col cols=2>
                        <v-switch
                            class="switch-end" 
                            v-model="has_registration" 
                            name="has_registration"
                            :value="has_registration"
                        >
                        </v-switch>
                    </v-col>
                </v-row>

                <v-row>
                    <v-col>
                    <v-text-field
                        v-if="has_registration"
                        v-model="registration_limit"
                        :label="$vuetify.lang.t('$vuetify.registration_limit')"
                        :hint="$vuetify.lang.t('$vuetify.registration_limit_hint')"
                        persistent-hint
                        name="registration_limit"
                        type="number"
                        min="0"
                        step="1"
                        outlined
                        />
                    </v-col>
                </v-row>
            </v-container>
        </v-app>
    </div>
</template>

<script>
    var moment = require('moment');
    import DatePicker from './DatePicker';
    import TimePicker from './TimePicker'

    export default {
        props: ['backend'],
        data: function () {
            return {
                start: this.backend.start,
                end: this.backend.end,
                event: '',
                opening: this.backend.opening,
                price: this.backend.price,
                comment: this.backend.comment,
                has_registration: this.backend.has_registration,
                registration_limit: this.backend.registration_limit,
                is_on_site: this.backend.is_on_site,
            }
        },
        computed: {
            startDateRules(){
                return[
                   v => moment(v + 'T' + moment(this.start).format('HH:mm'), 'D MMMM YYYYTHH:mm') < moment(this.end) ||
                   this.$vuetify.lang.t('$vuetify.start_date_after_end_date') 
                ]
            },
            startTimeRules(){
              return[
                v => moment(moment(this.start).format('YYYY-MM-DD') + 'T' + v, 'YYYY-MM-DDTHH:mm') < moment(this.end) ||
                this.$vuetify.lang.t('$vuetify.start_time_after_end_time') 
                ]
            },
            endDateRules(){
                return [
                    v => moment(v + 'T' + moment(this.end).format('HH:mm'), 'D MMMM YYYYTHH:mm') > moment(this.start) ||
                    this.$vuetify.lang.t('$vuetify.end_date_before_start_date') 
                ]
            },
            endTimeRules(){
                return [
                    v => moment(moment(this.end).format('YYYY-MM-DD') + 'T' + v, 'YYYY-MM-DDTHH:mm') > moment(this.start) || 
                    this.$vuetify.lang.t('$vuetify.end_time_before_start_time') 
                ]
            }
        },
        components: {
            DatePicker,
            TimePicker,
        },
        methods: {
            updateTime(time, inputName) {
                if (inputName === 'start_time') {
                    this.start = (moment(this.start).format('YYYY-MM-DD') + 'T' + time + ':00')
                }
                if (inputName === 'end_time') {
                    this.end = (moment(this.end).format('YYYY-MM-DD') + 'T' + time + ':00')
                }
            },
            updateDate(date, inputName) {
                if (inputName === 'start_date') {
                    this.start = (date + 'T' + moment(this.start).format('HH:mm'))
                }
                if (inputName === 'end_date') {
                    this.end = (date + 'T' + moment(this.end).format('HH:mm'))
                }
            },
        },
    }
</script>