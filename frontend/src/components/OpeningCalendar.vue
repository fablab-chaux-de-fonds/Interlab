<template>
  <div>
    <v-app>
      <v-sheet tile height="64" class="d-flex">
        <v-toolbar flat>
          <v-btn outlined color="primary" class="mr-4" @click="setToday">
            {{ $vuetify.lang.t("$vuetify.Today") }}
          </v-btn>
          <v-btn icon @click="$refs.calendar.prev()" color="primary">
            <i class="bi bi-chevron-left"></i>
          </v-btn>
          <v-btn icon @click="$refs.calendar.next()" color="primary">
            <i class="bi bi-chevron-right"></i>
          </v-btn>
          <v-toolbar-title v-if="$refs.calendar" class="text-blue">
            {{ $refs.calendar.title }}
          </v-toolbar-title>
          <v-spacer></v-spacer>
          <v-menu bottom right color="primary">
            <template v-slot:activator="{ on, attrs }">
              <v-btn outlined color="primary" v-bind="attrs" v-on="on">
                <span>{{ $vuetify.lang.t("$vuetify." + type) }}</span>
                <i class="bi bi-chevron-down"></i>
              </v-btn>
            </template>
            <v-list>
              <v-list-item @click="type = 'day'">
                <v-list-item-title>{{ $vuetify.lang.t('$vuetify.day') }}</v-list-item-title>
              </v-list-item>
              <v-list-item @click="type = 'week'">
                <v-list-item-title>{{ $vuetify.lang.t('$vuetify.week') }}</v-list-item-title>
              </v-list-item>
              <v-list-item @click="type = 'month'">
                <v-list-item-title>{{ $vuetify.lang.t('$vuetify.month') }}</v-list-item-title>
              </v-list-item>
              <v-list-item @click="type = '4day'">
                <v-list-item-title>{{ $vuetify.lang.t('$vuetify.4day') }}</v-list-item-title>
              </v-list-item>
            </v-list>
          </v-menu>
        </v-toolbar>
      </v-sheet>

      <v-sheet height="80vh">
        <v-calendar ref="calendar" color="primary" locale="fr" class="text-blue" v-model="focus" :weekdays="weekday" :type="type" :events="events"
          :event-overlap-mode="mode" :event-overlap-threshold="30" @change="getEvents" @click:event="showEvent"
          @click:date="type = 'day'" @mousedown:event="showEvent" @mousedown:time="startTime"
          @mousemove:time="mouseMove" @mouseup:time="endDrag" @mouseleave.native="cancelDrag" @click:day="clickDay">
          <template v-slot:event="{ event }">
            <div class="v-event-summary pl-1" :style="{'color':event.text_color}">
              <strong>{{ formatEventTime(event.start) }} - {{ formatEventTime(event.end) }} </strong>
              <span v-if="type!='month'"> <br> </span>
                 {{ event.title }}
              <span v-if="type!='month' & event.type=='opening'"> <br> </span>
              <span v-if="event.type=='opening'"> {{ event.user_firstname }} </span>
              <span v-if="type!='month'"> <br>
                {{ event.comment }}
              </span>
            </div>
          </template>
        </v-calendar>

        <v-dialog v-model="selectSlotCategory" max-width='350px'>
          <v-card>
            <v-toolbar>
              <v-spacer></v-spacer>
              <v-btn icon @click="selectSlotCategory = false" class="text-blue">
                  <i large class="bi bi-x display-5"></i>
              </v-btn>
            </v-toolbar>
            <v-card-text class="pa-4 text-center">
              <v-btn @click="createOpeningSlot" class="my-2 v-btn-primary">
                  <i class="bi bi-door-open pe-2"></i> {{ $vuetify.lang.t('$vuetify.opening') }}
              </v-btn>
              <br>
              <v-btn @click="createTrainingSlot" class="my-2 v-btn-primary-outlined" outlined>
                <i class="bi bi-mortarboard pe-2"></i> {{ $vuetify.lang.t('$vuetify.training') }}
              </v-btn>
              <br>
              <v-btn @click="createEventSlot" class="my-2 v-btn-primary-outlined" outlined>
                <i class="bi bi-calendar-event pe-2"></i> {{ $vuetify.lang.t('$vuetify.event') }}
              </v-btn>
            </v-card-text>
          </v-card>
        </v-dialog>

        <v-dialog v-model="selectedOpen" max-width="350px">
          <v-card>
            <v-toolbar :color="selectedEvent.color" :style="{'color':selectedEvent.text_color}" dark>
              <p class="my-0">{{formatEventTime(selectedEvent.start)}} - {{formatEventTime(selectedEvent.end)}}</p>
              <v-spacer></v-spacer>
              <div v-if="backend.is_superuser">
                <div v-if="backend.username === selectedEvent.username">
                  <v-btn icon>
                    <a :href="'/fabcal/openingslot/update/' + selectedEvent.pk + '/'"
                      :style="{'color':selectedEvent.text_color}">
                      <i class="bi bi-pencil"></i>
                    </a>
                  </v-btn>
                </div>
              </div>

              <v-btn icon :style="{'color':selectedEvent.text_color}" @click="selectedOpen = false">
                <i class="bi bi-x"></i>
              </v-btn>
            </v-toolbar>
            <v-card-text>
              <v-img v-if="selectedEvent.img" :src="selectedEvent.img" class="mb-2 rounded"></v-img>
              <span class="h3 align-middle me-2">
                {{selectedEvent.title}}
              </span>
              <span class='badge align-middle' :style="{'color':selectedEvent.text_color, 'background':selectedEvent.color}">
                {{selectedEvent.user_firstname}}
              </span>

              <p>{{selectedEvent.desc}}</p>
              <div v-if="selectedEvent.type=='opening'">
                <h4> {{ $vuetify.lang.t('$vuetify.machines') }} </h4>
                  <span v-for="machine in selectedEvent.machines">
                  <a :href="'/machines/machines/' + machine.pk + '/show'" class="badge text-bg-info rounded-pill btn-sm m-1">
                    {{machine.category}} - {{ machine.title }}
                  </a>
                </span>
              </div>
              <p v-if="selectedEvent.comment"><i class="bi bi-card-text"></i> {{selectedEvent.comment}}</p>
            </v-card-text>
          </v-card>
        </v-dialog>
      </v-sheet>
    </v-app>
  </div>
</template>


<script>
  export default {
    props: ['backend'],
    data: function () {
      return {
        type: window.innerWidth < 992 ? '4day' : 'month',
        types: ['month', 'week', 'day', '4day'],
        mode: 'stack',
        weekday: [1, 2, 3, 4, 5, 6, 0],
        events: [],
        focus: '',
        selectedEvent: {},
        selectedElement: null,
        selectedOpen: false,
        createEvent: null,
        createStart: null,
        selectSlotCategory: false,
        start: null,
        end: null,
      }
    },
    methods: {
      startTime(tms) {
        if (this.backend.is_superuser) {
          const mouse = this.toTime(tms);

          if (this.dragEvent && this.dragTime === null) {
            const start = this.dragEvent.start;

            this.dragTime = mouse - start;
          } else {
            this.createStart = this.roundTime(mouse);
            this.createEvent = {
              color: '#808080',
              start: this.createStart,
              end: this.createStart,
              timed: true,
            };

            this.events.push(this.createEvent);
          }
        }
      },
      extendBottom(event) {
        this.createEvent = event;
        this.createStart = event.start;
        this.extendOriginal = event.end;
      },
      mouseMove(tms) {
        if (this.backend.is_superuser) {
          const mouse = this.toTime(tms);

          if (this.dragEvent && this.dragTime !== null) {
            const start = this.dragEvent.start;
            const end = this.dragEvent.end;
            const duration = end - start;
            const newStartTime = mouse - this.dragTime;
            const newStart = this.roundTime(newStartTime);
            const newEnd = newStart + duration;

            this.dragEvent.start = newStart;
            this.dragEvent.end = newEnd;
          } else if (this.createEvent && this.createStart !== null) {
            const mouseRounded = this.roundTime(mouse, false);
            const min = Math.min(mouseRounded, this.createStart);
            const max = Math.max(mouseRounded, this.createStart);

            this.createEvent.start = min;
            this.createEvent.end = max;
          }
        }
      },

      createOpeningSlot(event) {
        location.href = "/fabcal/openingslot/create/" + this.start + "/" + this.end;
      },

      createEventSlot(event) {
        location.href = "/fabcal/eventslot/create/" + this.start + "/" + this.end;
      },

      createTrainingSlot(event) {
        location.href = "/fabcal/trainingslot/create/" + this.start + "/" + this.end;
      },

      cancelDrag() {
        if (this.backend.is_superuser) {
          if (this.createEvent) {
            if (this.extendOriginal) {
              this.createEvent.end = this.extendOriginal;
            } else {
              const i = this.events.indexOf(this.createEvent);
              if (i !== -1) {
                this.events.splice(i, 1);
              }
            }
          }
        }

        this.createEvent = null;
        this.createStart = null;
        this.dragTime = null;
        this.dragEvent = null;
      },
      roundTime(time, down = true) {
        const roundTo = 15; // minutes
        const roundDownTime = roundTo * 60 * 1000;

        return down ?
          time - time % roundDownTime :
          time + (roundDownTime - (time % roundDownTime));
      },
      toTime(tms) {
        return new Date(tms.year, tms.month - 1, tms.day, tms.hour, tms.minute).getTime();
      },

      clickDay(day) {
        if (this.backend.is_superuser) {
          this.start = Date.parse(day.date + 'T18:00:00'),
            this.end = Date.parse(day.date + 'T20:00:00'),
            this.selectSlotCategory = true;
        }
      },

      endDrag() {
        if (this.backend.is_superuser) {
          this.start = this.createEvent.start;
          if (this.start === this.createEvent.end){
            console.log(this.createEvent.start)
            this.end = this.createEvent.start + 5400000;
          } else {
            this.end = this.createEvent.end;
          }
          this.selectSlotCategory = true;
        }
      },

      setToday() {
        this.focus = '';
      },

      showEvent({
        nativeEvent,
        event
      }) {
        const open = () => {
          this.selectedEvent = event;
          this.selectedElement = nativeEvent.target;
          if (this.selectedEvent.type === 'opening') {
            requestAnimationFrame(() => requestAnimationFrame(() => this.selectedOpen = true));
          } else if (this.selectedEvent.type === 'event') {
            location.href = "/fabcal/eventslot/" + this.selectedEvent.pk;
          } else if (this.selectedEvent.type === 'training') {
            location.href = "/machines/training/" + this.selectedEvent.training_pk;
          }
        };

        if (this.selectedOpen) {
          this.selectedOpen = false;
          requestAnimationFrame(() => requestAnimationFrame(() => open()));
        } else {
          open();
        }

        nativeEvent.stopPropagation();
      },

      formatEventTime(date) {
        if(typeof date !== "undefined"){
          date = date.replace(' ', 'T') //convert to ISO-8601-like format
          return new Date(date).toLocaleTimeString('en-US', {
            hour: "2-digit",
            minute: "2-digit",
            hour12: false
          });
        }
      },

      getEvents({
        start,
        end
      }) {
        const events = [];

        for (const event of this.backend.events) {
          events.push({
            color: event.background_color,
            comment: event.comment,
            desc: event.desc,
            end: event.end,
            title: event.title,
            user_firstname: event.user_firstname,
            start: event.start,
            text_color: event.color,
            pk: event.pk,
            training_pk: event.training_pk,
            username: event.username,
            type: event.type,
            machines: event.machines
          });
        }

        this.events = events;
      },
    },
    mounted() {
      this.$refs.calendar.scrollToTime('10:00');
    },
  }
</script>