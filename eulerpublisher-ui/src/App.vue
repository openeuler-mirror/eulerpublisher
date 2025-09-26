<template>
  <div class="layout">
    <header class="header">
      <h1>EulerPublisher</h1>
    </header>

    <div class="content">
      <div class="sidebar">
        <router-link to="/container">容器</router-link>
        <router-link to="/rpm">软件包</router-link>
      </div>

      <div class="main">
        <router-view />
      </div>
    </div>
  </div>
</template>

<style scoped>
.layout {
  display: flex;
  flex-direction: column;
  height: 100vh;
}

.header {
  height: 60px;
  background: #1976d2;
  color: white;
  display: flex;
  align-items: center;
  padding: 0 20px;
  font-size: 20px;
  font-weight: bold;
}

.content {
  display: flex;
  flex: 1;
}

.sidebar {
  width: 200px;
  background: #f0f0f0;
  padding: 20px;
  display: flex;
  flex-direction: column;
}

.sidebar a {
  margin: 10px 0;
  text-decoration: none;
  color: #333;
}

.sidebar a.router-link-exact-active {
  font-weight: bold;
  color: #1976d2;
}

.main {
  flex: 1;
  padding: 20px;
}
</style>
<script setup lang="ts">
</script>