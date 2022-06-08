import Vue from 'vue';
import vuetify from '~/plugins/vuetify';

new Vue({
    vuetify,
    delimiters: ["[[", "]]"],
    data: {
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
        backend: JSON.parse(document.getElementById('backend').textContent),
    },
    methods: {
      startTime (tms) {
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
      },
      extendBottom (event) {
        this.createEvent = event;
        this.createStart = event.start;
        this.extendOriginal = event.end;
      },
      mouseMove (tms) {
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
      },

      createOpeningSlot (event) {
        location.href="/fabcal/create-opening/"+ this.start + "/" + this.end;
      },

      createEventSlot (event) {
        location.href="/fabcal/create-event/"+ this.start + "/" + this.end;
      },

      cancelDrag () {
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

        this.createEvent = null;
        this.createStart = null;
        this.dragTime = null;
        this.dragEvent = null;
      },
      roundTime (time, down = true) {
        const roundTo = 15; // minutes
        const roundDownTime = roundTo * 60 * 1000;

        return down
          ? time - time % roundDownTime
          : time + (roundDownTime - (time % roundDownTime));
      },
      toTime (tms) {
        return new Date(tms.year, tms.month - 1, tms.day, tms.hour, tms.minute).getTime();
      },

      clickDay (day) {
        this.start= Date.parse(day.date + 'T18:00:00'),
        this.end =Date.parse(day.date + 'T20:00:00'),
        this.selectSlotCategory=true;
      },

      endDrag () {
        this.start= this.createEvent.start;
        this.end = this.createEvent.end;
        this.selectSlotCategory=true;
      },

      setToday () {
          this.focus = '';
        },

      showEvent ({ nativeEvent, event }) {
          const open = () => {
            this.selectedEvent = event;
            this.selectedElement = nativeEvent.target;
            requestAnimationFrame(() => requestAnimationFrame(() => this.selectedOpen = true));
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
          return new Date(date).toLocaleTimeString('en-US', {
            hour: "2-digit", 
            minute: "2-digit", 
            hour12: false
          });
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
                username: event.username,
              });
          }

          this.events = events;
      },
    },
    mounted () {
        this.$refs.calendar.scrollToTime('08:00');
      },
  }).$mount('#app');