<script>
import mixins from './mixins.js'
import _ from 'lodash'

export default {
  mounted () {
    this.$store.dispatch('load_index')
  },
  data: function () {
    return {
      filters: {
        state: null
      }
    }
  },
  mixins: [
    mixins.date
  ],
  methods: {
    filter_state: function (state) {
      // Save filter locally
      this.filters.state = state
    }
  },
  computed: {
    tasks () {
      let tasks = this.$store.state.tasks

      // Filter by states
      if (this.filters.state !== null) {
        tasks = _.filter(tasks, t => t.state_full === this.filters.state.key)
      }

      return tasks
    },
    states () {
      return this.$store.state.states
    }
  }
}
</script>

<template>
  <section>

    <div class="states" >
      <div class="state columns" v-for="state in states">
        <div class="column is-one-third">
          <progress class="progress" :class="{'is-danger': state.key.startsWith('error'), 'is-success': state.key == 'done', 'is-info': state.key != 'done' && !state.key.startsWith('error')}" :value="state.percent" max="100">{{ state.percent }}%</progress>
        </div>
        <div class="column is-one-third">
          <strong>{{ state.name }}</strong> - <span class="has-text-grey-light">{{ state.nb }}/{{ tasks.length }} tasks or {{ state.percent }}%</span>
        </div>
      </div>
    </div>

    <table class="table is-fullwidth">
      <thead>
        <tr>
          <td>#</td>
          <td>Revision</td>
          <td>
            <div class="dropdown is-hoverable">
              <div class="dropdown-trigger">
                <button class="button" aria-haspopup="true" aria-controls="dropdown-menu">
                  <span v-if="filters.state === null">All states</span>
                  <span v-else>{{ filters.state.name }}</span>
                </button>
              </div>
              <div class="dropdown-menu" id="dropdown-menu" role="menu">
                <div class="dropdown-content">
                  <a href="#" class="dropdown-item" v-on:click="filter_state(null)">
                    All states
                  </a>
                  <hr class="dropdown-divider">
                  <a href="#" class="dropdown-item" v-for="state in states" v-on:click="filter_state(state)">
                    {{ state.name }}
                  </a>
                </div>
              </div>
            </div>
          </td>
          <td>Nb. Issues</td>
          <td>Indexed</td>
          <td>Actions</td>
        </tr>
      </thead>

      <tbody>
        <tr v-for="task in tasks">
          <td>
            <a class="mono" :href="'https://tools.taskcluster.net/task-inspector/#' + task.taskId" target="_blank">{{ task.taskId }}</a>
          </td>

          <td v-if="task.data.source == 'phabricator'">
            <p v-if="task.data.title">{{ task.data.title }}</p>
            <p class="has-text-danger" v-else>No title</p>
            <small class="mono has-text-grey-light">{{ task.data.diff_phid}}</small>
          </td>
          <td v-else>
            <p class="notification is-danger">Unknown data source: {{ task.data.source }}</p>
          </td>

          <td>
            <span class="tag is-light" v-if="task.data.state == 'started'">Started</span>
            <span class="tag is-info" v-else-if="task.data.state == 'cloned'">Cloned</span>
            <span class="tag is-info" v-else-if="task.data.state == 'analyzing'">Analyzing</span>
            <span class="tag is-primary" v-else-if="task.data.state == 'analyzed'">Analyzed</span>
            <span class="tag is-danger" v-else-if="task.data.state == 'error'" :title="task.data.error_message">
              Error: {{ task.data.error_code || 'unknown' }}
            </span>
            <span class="tag is-success" v-else-if="task.data.state == 'done'">Done</span>
            <span class="tag is-black" v-else>Unknown</span>
          </td>

          <td :class="{'has-text-success': task.data.issues_publishable > 0}">

            <span v-if="task.data.issues_publishable > 0">{{ task.data.issues_publishable }}</span>
            <span v-else-if="task.data.issues_publishable == 0">{{ task.data.issues_publishable }}</span>
            <span v-else>-</span>
            / {{ task.data.issues }}
          </td>

          <td>
            <span :title="task.data.indexed">{{ task.data.indexed|since }} ago</span>
          </td>
          <td>
            <a class="button is-link" :href="task.data.url" target="_blank">Phabricator</a>
            <a v-if="task.data.bugzilla_id" class="button is-dark" :href="'https://bugzil.la/' + task.data.bugzilla_id" target="_blank">Bugzilla</a>
            <router-link v-if="task.data.issues > 0" :to="{ name: 'task', params: { taskId : task.taskId }}" class="button is-primary">Issues</router-link>
          </td>
        </tr>
      </tbody>
    </table>
  </section>
</template>

<style>
.mono{
  font-family: monospace;
}

div.states {
  margin-top: 1rem;
  margin-bottom: 2rem;
}

div.states div.column {
  padding: 0.2rem;
}

div.states div.column progress {
  margin-top: 0.3rem;
}
</style>
