import Vue from 'vue'
import Vuex from 'vuex'

Vue.use(Vuex)

export default new Vuex.Store({
  state: {
    rpmBuildResult: null,
    containerBuildResult: null
  },
  getters: {
    getRpmBuildResult: state => state.rpmBuildResult,
    getContainerBuildResult: state => state.containerBuildResult
  },
  mutations: {
    SET_RpmBuildResult(state, rpmBuildResult) {
      state.rpmBuildResult = rpmBuildResult
    },
    CLEAR_RpmBuildResult(state) {
      state.rpmBuildResult = null
    },
    SET_ContainerBuildResult(state, containerBuildResult) {
      state.containerBuildResult = containerBuildResult
    },
    CLEAR_ContainerBuildResult(state) {
      state.containerBuildResult = null
    }
  },
  actions: {
    setRpmBuildResult({commit}, data) {
      commit('SET_RpmBuildResult', data)
    },
    clearRpmBuildResult({commit}) {
      commit('CLEAR_RpmBuildResult')
    },
    setContainerBuildResult({commit}, data) {
      commit('SET_ContainerBuildResult', data)
    },
    clearContainerBuildResult({commit}) {
      commit('CLEAR_ContainerBuildResult')
    }
  },
  modules: {
  }
})
