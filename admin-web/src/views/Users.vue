<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getUsers, deleteUser, type User } from '../api'

const users = ref<User[]>([])
const isLoading = ref(true)
const offset = ref(0)
const limit = 50

async function loadUsers() {
  isLoading.value = true
  try {
    const data = await getUsers({ limit, offset: offset.value })
    users.value = data.users
  } catch (e) {
    console.error('Failed to load users', e)
  }
  isLoading.value = false
}

async function handleDelete(user: User) {
  if (!confirm(`Delete user "${user.username}"?\n\nThis will delete all their games, streaks, and data. This cannot be undone.`)) {
    return
  }
  try {
    await deleteUser(user.id)
    users.value = users.value.filter(u => u.id !== user.id)
  } catch (e) {
    alert('Failed to delete user: ' + (e as Error).message)
  }
}

function formatDate(dateStr: string | null): string {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleDateString()
}

onMounted(loadUsers)
</script>

<template>
  <div class="card">
    <div class="card-header">
      <h3 class="card-title">Users ({{ users.length }})</h3>
    </div>

    <div v-if="isLoading" class="loading">
      <div class="spinner"></div>
    </div>

    <table v-else>
      <thead>
        <tr>
          <th>ID</th>
          <th>Username</th>
          <th>Email</th>
          <th>Games</th>
          <th>Wins</th>
          <th>Streak</th>
          <th>Joined</th>
          <th>Action</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="user in users" :key="user.id">
          <td>{{ user.id }}</td>
          <td>{{ user.username }}</td>
          <td>{{ user.email || '-' }}</td>
          <td>{{ user.total_games }}</td>
          <td>{{ user.total_wins }}</td>
          <td>{{ user.current_streak }}</td>
          <td>{{ formatDate(user.created_at) }}</td>
          <td>
            <button class="btn-delete" @click="handleDelete(user)">Delete</button>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<style scoped>
.btn-delete {
  background: #da3633;
  color: white;
  border: none;
  padding: 4px 8px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
}
.btn-delete:hover {
  background: #f85149;
}
</style>
