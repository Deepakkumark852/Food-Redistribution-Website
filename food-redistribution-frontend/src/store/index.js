import { createStore } from 'vuex';

const savedUser = JSON.parse(localStorage.getItem('user')) || {};

const store = createStore({
  state: {
    token: savedUser.token || '',
    roles: savedUser.roles || [],
    username: savedUser.username || '',
  },
  mutations: {
    setUser(state, { token, roles, username }) {
      state.token = token;
      state.roles = Array.isArray(roles) ? roles : (roles ? [roles] : []);
      state.username = username;
      localStorage.setItem('user', JSON.stringify({ token, roles: state.roles, username }));
    },
    logout(state) {
      state.token = '';
      state.roles = [];
      state.username = '';
      localStorage.removeItem('user');
    },
  },
  getters: {
    roles: state => state.roles,
    token: state => state.token,
    username: state => state.username,
    isAuthenticated: state => !!state.token,
  },
});

export default store;
