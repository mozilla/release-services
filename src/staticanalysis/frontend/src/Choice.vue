<template>
  <div class="dropdown is-hoverable">
    <div class="dropdown-trigger">
      <button class="button" aria-haspopup="true" aria-controls="dropdown-menu">
        <span v-if="current === null">{{ default_choice_name }}</span>
        <span v-else>{{ current.name }}</span>
      </button>
    </div>
    <div class="dropdown-menu" id="dropdown-menu" role="menu">
      <div class="dropdown-content">
        <a href="#" class="dropdown-item" v-on:click="$emit('new-choice', null)">
          {{ default_choice_name }}
        </a>
        <hr class="dropdown-divider">
        <a href="#" class="dropdown-item" v-for="choice in choices" v-on:click="$emit('new-choice', choice)">
          {{ choice.name }}
        </a>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  props: {
    'current': Object,
    'name': String,
    'choices': Array
  },
  computed: {
    default_choice_name: function () {
      return 'All ' + this.name + 's'
    }
  }
}
</script>
