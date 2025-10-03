// Configuration des URLs API pour le développement local
const API_BASE_URL = 'http://127.0.0.1:5002/api';

export const API_ENDPOINTS = {
  SCAN: `${API_BASE_URL}/scan`,
  HISTORY: `${API_BASE_URL}/history`,
  PROFILE: `${API_BASE_URL}/profile`,
  CART: `${API_BASE_URL}/cart`,
  CHECKOUT: `${API_BASE_URL}/checkout`
};

export default API_BASE_URL;
