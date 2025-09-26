import Vue from 'vue'
import Router from 'vue-router'
import ContainerConfig from '@/views/ContainerConfig/index.vue'
import ContainerBuildResult from "@/views/ContainerConfig/ContainerBuildResult.vue";
import RpmConfig from '@/views/RpmConfig/index.vue'
import RpmBuildResult from "@/views/RpmConfig/RpmBuildResult.vue"

Vue.use(Router)

const router = new Router({
  mode: 'history',
  routes: [
    { path: '/', redirect: '/container' },
    { path: '/container', component: ContainerConfig },
    { path: '/rpm', component: RpmConfig },
    {
      path: '/rpm/build/:id',
      name: 'RpmBuildResult',
      component: RpmBuildResult,
      props: true,
    },
    {
      path: '/container/build/:id',
      name: 'ContainerBuildResult',
      component: ContainerBuildResult,
      props: true,
    },
  ]
})

export default router
