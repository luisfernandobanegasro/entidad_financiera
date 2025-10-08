import api from '../config/axios';

export async function getMe() {
  const { data } = await api.get('/api/users/me/');
  return data;
}
