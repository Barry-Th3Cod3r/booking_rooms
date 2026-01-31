/**
 * API Client for Booking Rooms Backend
 * Replaces localStorage mock data with real API calls
 */

// API base URL - set via Vite environment variable
const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

// Token storage keys
const ACCESS_TOKEN_KEY = 'booking_access_token';
const REFRESH_TOKEN_KEY = 'booking_refresh_token';

// Types
export interface Booking {
    id: number;
    classroom_id: number;
    user_id: number;
    start_datetime: string;
    end_datetime: string;
    booking_date: string;
    start_time: string;
    end_time: string;
    subject?: string;
    description?: string;
    is_recurring: boolean;
    recurring_pattern?: string;
    recurring_end_date?: string;
    status: string;
    created_at: string;
    updated_at: string;
}

export interface BookingCreate {
    classroom_id: number;
    start_datetime?: string;
    end_datetime?: string;
    booking_date?: string;
    start_time?: string;
    end_time?: string;
    subject?: string;
    description?: string;
    is_recurring?: boolean;
    recurring_pattern?: string;
    recurring_end_date?: string;
}

export interface Classroom {
    id: number;
    name: string;
    code: string;
    capacity: number;
    description?: string;
    location?: string;
    floor?: number;
    building?: string;
    equipment?: Record<string, boolean>;
    is_active: boolean;
}

export interface User {
    id: number;
    username: string;
    email: string;
    full_name?: string;
    is_active: boolean;
    is_admin: boolean;
}

export interface AuthTokens {
    access_token: string;
    refresh_token?: string;
    token_type: string;
}

// Auth helpers
function getToken(): string | null {
    return localStorage.getItem(ACCESS_TOKEN_KEY);
}

function setTokens(tokens: AuthTokens): void {
    localStorage.setItem(ACCESS_TOKEN_KEY, tokens.access_token);
    if (tokens.refresh_token) {
        localStorage.setItem(REFRESH_TOKEN_KEY, tokens.refresh_token);
    }
}

function clearTokens(): void {
    localStorage.removeItem(ACCESS_TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
}

function getAuthHeaders(): HeadersInit {
    const token = getToken();
    return token ? { 'Authorization': `Bearer ${token}` } : {};
}

// API Error class
export class ApiError extends Error {
    constructor(public status: number, message: string, public details?: unknown) {
        super(message);
        this.name = 'ApiError';
    }
}

// Generic fetch wrapper
async function apiFetch<T>(
    endpoint: string,
    options: RequestInit = {}
): Promise<T> {
    const url = `${API_BASE_URL}${endpoint}`;

    const response = await fetch(url, {
        ...options,
        headers: {
            'Content-Type': 'application/json',
            ...getAuthHeaders(),
            ...options.headers,
        },
    });

    if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new ApiError(
            response.status,
            errorData.detail || `API Error: ${response.statusText}`,
            errorData
        );
    }

    // Handle 204 No Content
    if (response.status === 204) {
        return {} as T;
    }

    return response.json();
}

// ===================
// Auth API
// ===================
export const authApi = {
    async login(username: string, password: string): Promise<AuthTokens> {
        const response = await apiFetch<AuthTokens>('/auth/login', {
            method: 'POST',
            body: JSON.stringify({ username, password }),
        });
        setTokens(response);
        return response;
    },

    async loginWithGoogle(idToken: string): Promise<AuthTokens> {
        const response = await apiFetch<AuthTokens>('/auth/google', {
            method: 'POST',
            body: JSON.stringify({ id_token: idToken }),
        });
        setTokens(response);
        return response;
    },

    async logout(): Promise<void> {
        clearTokens();
    },

    async getCurrentUser(): Promise<User> {
        return apiFetch<User>('/users/me');
    },

    isAuthenticated(): boolean {
        return !!getToken();
    },
};

// ===================
// Bookings API
// ===================
export const bookingsApi = {
    async getAll(params?: {
        classroom_id?: number;
        start_date?: string;
        end_date?: string;
        status?: string;
        limit?: number;
        offset?: number;
    }): Promise<Booking[]> {
        const searchParams = new URLSearchParams();
        if (params) {
            Object.entries(params).forEach(([key, value]) => {
                if (value !== undefined) {
                    searchParams.append(key, String(value));
                }
            });
        }
        const query = searchParams.toString();
        return apiFetch<Booking[]>(`/bookings${query ? `?${query}` : ''}`);
    },

    async getById(id: number): Promise<Booking> {
        return apiFetch<Booking>(`/bookings/${id}`);
    },

    async create(booking: BookingCreate): Promise<Booking> {
        return apiFetch<Booking>('/bookings', {
            method: 'POST',
            body: JSON.stringify(booking),
        });
    },

    async update(id: number, booking: Partial<BookingCreate>): Promise<Booking> {
        return apiFetch<Booking>(`/bookings/${id}`, {
            method: 'PUT',
            body: JSON.stringify(booking),
        });
    },

    async delete(id: number): Promise<void> {
        await apiFetch<void>(`/bookings/${id}`, {
            method: 'DELETE',
        });
    },

    async checkAvailability(params: {
        classroom_id: number;
        start_datetime: string;
        end_datetime: string;
    }): Promise<{ is_available: boolean; conflicts: Booking[] }> {
        return apiFetch('/bookings/check-availability', {
            method: 'POST',
            body: JSON.stringify(params),
        });
    },

    async getByClassroomAndDate(classroomId: number, date: string): Promise<Booking[]> {
        return apiFetch<Booking[]>(`/bookings/classroom/${classroomId}/date/${date}`);
    },
};

// ===================
// Classrooms API
// ===================
export const classroomsApi = {
    async getAll(): Promise<Classroom[]> {
        return apiFetch<Classroom[]>('/classrooms');
    },

    async getById(id: number): Promise<Classroom> {
        return apiFetch<Classroom>(`/classrooms/${id}`);
    },

    async create(classroom: Omit<Classroom, 'id'>): Promise<Classroom> {
        return apiFetch<Classroom>('/classrooms', {
            method: 'POST',
            body: JSON.stringify(classroom),
        });
    },

    async update(id: number, classroom: Partial<Classroom>): Promise<Classroom> {
        return apiFetch<Classroom>(`/classrooms/${id}`, {
            method: 'PUT',
            body: JSON.stringify(classroom),
        });
    },

    async delete(id: number): Promise<void> {
        await apiFetch<void>(`/classrooms/${id}`, {
            method: 'DELETE',
        });
    },
};

// ===================
// Users API
// ===================
export const usersApi = {
    async getAll(): Promise<User[]> {
        return apiFetch<User[]>('/users');
    },

    async getById(id: number): Promise<User> {
        return apiFetch<User>(`/users/${id}`);
    },

    async create(user: {
        username: string;
        email: string;
        password: string;
        full_name?: string;
    }): Promise<User> {
        return apiFetch<User>('/users', {
            method: 'POST',
            body: JSON.stringify(user),
        });
    },

    async update(id: number, user: Partial<User>): Promise<User> {
        return apiFetch<User>(`/users/${id}`, {
            method: 'PUT',
            body: JSON.stringify(user),
        });
    },

    async delete(id: number): Promise<void> {
        await apiFetch<void>(`/users/${id}`, {
            method: 'DELETE',
        });
    },
};

// Default export with all APIs
const apiClient = {
    auth: authApi,
    bookings: bookingsApi,
    classrooms: classroomsApi,
    users: usersApi,
};

export default apiClient;
