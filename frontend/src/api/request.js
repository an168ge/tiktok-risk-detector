/**
 * API请求封装
 */
import axios from 'axios';

// 创建axios实例
const request = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  }
});

// 请求拦截器
request.interceptors.request.use(
  (config) => {
    // 可以在这里添加token等
    return config;
  },
  (error) => {
    console.error('Request error:', error);
    return Promise.reject(error);
  }
);

// 响应拦截器
request.interceptors.response.use(
  (response) => {
    const res = response.data;
    
    // 如果返回的success字段为false，认为是业务错误
    if (res.success === false) {
      console.error('Business error:', res.error);
      return Promise.reject(new Error(res.error?.message || 'Request failed'));
    }
    
    return res;
  },
  (error) => {
    console.error('Response error:', error);
    
    let message = 'Network error';
    if (error.response) {
      message = error.response.data?.error?.message || error.response.statusText;
    } else if (error.request) {
      message = 'No response from server';
    }
    
    return Promise.reject(new Error(message));
  }
);

export default request;
