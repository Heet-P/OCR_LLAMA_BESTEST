import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

export const api = axios.create({
    baseURL: API_URL,
});

export const uploadForm = async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await api.post('/forms/upload', formData, {
        headers: {
            'Content-Type': 'multipart/form-data',
        },
    });
    return response.data;
};

export const startChat = async (formId: string) => {
    const response = await api.post('/chat/start', { form_id: formId });
    return response.data;
};

export const sendMessage = async (sessionId: string, message: string) => {
    const response = await api.post('/chat/message', { session_id: sessionId, message });
    return response.data;
};

export const generatePDF = async (formId: string, sessionId: string) => {
    const response = await api.post('/pdf/generate', { form_id: formId, session_id: sessionId });
    return response.data;
};

export const getFormStatus = async (formId: string) => {
    const response = await api.get(`/forms/${formId}`);
    return response.data;
};

export const getForms = async () => {
    const response = await api.get('/forms/');
    return response.data;
};
