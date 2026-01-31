import React, { useState, useEffect, createContext, useContext } from 'react';
import { createRoot } from 'react-dom/client';

// =============================================================================
// API Configuration
// =============================================================================
const API_BASE_URL = '/api';
const ACCESS_TOKEN_KEY = 'booking_access_token';

// =============================================================================
// Types
// =============================================================================
interface User {
    id: number;
    username: string;
    email: string;
    full_name?: string;
    is_active: boolean;
    is_admin: boolean;
}

interface Classroom {
    id: number;
    name: string;
    code?: string;
    capacity?: number;
    is_active: boolean;
}

interface Booking {
    id: number;
    classroom_id: number;
    user_id: number;
    start_datetime: string;
    end_datetime: string;
    subject?: string;
    description?: string;
    status: string;
    // Frontend computed
    start?: Date;
    end?: Date;
    teacher?: string;
    event?: string;
    createdBy?: string;
}

// =============================================================================
// API Client - All data goes to PostgreSQL backend
// =============================================================================
class ApiClient {
    private getToken(): string | null {
        return localStorage.getItem(ACCESS_TOKEN_KEY);
    }

    private setToken(token: string): void {
        localStorage.setItem(ACCESS_TOKEN_KEY, token);
    }

    private clearToken(): void {
        localStorage.removeItem(ACCESS_TOKEN_KEY);
    }

    private async fetch<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
        const token = this.getToken();
        const headers: Record<string, string> = {
            'Content-Type': 'application/json',
            ...((options.headers as Record<string, string>) || {}),
        };

        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        const response = await fetch(`${API_BASE_URL}${endpoint}`, { ...options, headers });

        if (!response.ok) {
            const error = await response.json().catch(() => ({ detail: 'Network error' }));
            console.error(`API Error [${endpoint}]:`, error);
            throw new Error(error.detail || `Error ${response.status}`);
        }

        if (response.status === 204) return {} as T;
        return response.json();
    }

    // Auth
    async login(username: string, password: string): Promise<{ access_token: string }> {
        const result = await this.fetch<{ access_token: string }>('/auth/login', {
            method: 'POST',
            body: JSON.stringify({ username, password }),
        });
        this.setToken(result.access_token);
        return result;
    }

    async getCurrentUser(): Promise<User> {
        return this.fetch<User>('/auth/me');
    }

    async register(data: { username: string; email: string; password: string; full_name?: string }): Promise<User> {
        return this.fetch<User>('/auth/register', { method: 'POST', body: JSON.stringify(data) });
    }

    logout(): void { this.clearToken(); }
    isAuthenticated(): boolean { return !!this.getToken(); }

    // Classrooms (trailing slashes required by FastAPI)
    async getClassrooms(): Promise<Classroom[]> { return this.fetch<Classroom[]>('/classrooms/'); }
    async createClassroom(data: Partial<Classroom>): Promise<Classroom> {
        return this.fetch<Classroom>('/classrooms/', { method: 'POST', body: JSON.stringify(data) });
    }
    async deleteClassroom(id: number): Promise<void> {
        await this.fetch<void>(`/classrooms/${id}/`, { method: 'DELETE' });
    }

    // Bookings
    async getBookings(): Promise<Booking[]> { return this.fetch<Booking[]>('/bookings/'); }
    async getMyBookings(): Promise<Booking[]> { return this.fetch<Booking[]>('/bookings/'); }
    async createBooking(data: { classroom_id: number; start_datetime: string; end_datetime: string; subject?: string; description?: string }): Promise<Booking> {
        return this.fetch<Booking>('/bookings/', { method: 'POST', body: JSON.stringify(data) });
    }
    async updateBooking(id: number, data: { classroom_id?: number; start_datetime?: string; end_datetime?: string; subject?: string; description?: string }): Promise<Booking> {
        return this.fetch<Booking>(`/bookings/${id}/`, { method: 'PUT', body: JSON.stringify(data) });
    }
    async deleteBooking(id: number): Promise<void> {
        await this.fetch<void>(`/bookings/${id}/`, { method: 'DELETE' });
    }

    // Users (admin)
    async getUsers(): Promise<User[]> { return this.fetch<User[]>('/users/'); }
    async deleteUser(id: number): Promise<void> {
        await this.fetch<void>(`/users/${id}/`, { method: 'DELETE' });
    }
}

const api = new ApiClient();

// =============================================================================
// Auth Context
// =============================================================================
const AuthContext = createContext<any>(null);
const useAuth = () => useContext(AuthContext);

const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const [user, setUser] = useState<User | null>(null);
    const [token, setToken] = useState<string | null>(() => localStorage.getItem(ACCESS_TOKEN_KEY));
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const loadUser = async () => {
            if (!token) { setIsLoading(false); return; }
            try {
                const userData = await api.getCurrentUser();
                setUser(userData);
            } catch {
                api.logout();
                setToken(null);
            } finally {
                setIsLoading(false);
            }
        };
        loadUser();
    }, [token]);

    const login = async (email: string, password: string) => {
        setError(null);
        setIsLoading(true);
        try {
            const result = await api.login(email, password);
            setToken(result.access_token);
            const userData = await api.getCurrentUser();
            setUser(userData);
        } catch (err: any) {
            setError(err.message || 'Login failed');
            throw err;
        } finally {
            setIsLoading(false);
        }
    };

    const logout = () => { api.logout(); setUser(null); setToken(null); };

    return (
        <AuthContext.Provider value={{ user, token, login, logout, isLoading, error }}>
            {children}
        </AuthContext.Provider>
    );
};

// =============================================================================
// My Bookings Modal - Users can manage their own bookings
// =============================================================================
const MyBookingsModal = ({ isOpen, onClose, bookings, classrooms, currentUser, reloadData }: {
    isOpen: boolean;
    onClose: () => void;
    bookings: Booking[];
    classrooms: Classroom[];
    currentUser: User;
    reloadData: () => void
}) => {
    const [editingBooking, setEditingBooking] = useState<Booking | null>(null);
    const [loading, setLoading] = useState(false);
    const [editForm, setEditForm] = useState({ subject: '', classroom_id: 0, date: '', startTime: '', endTime: '' });

    const myBookings = bookings.filter(b => b.user_id === currentUser.id);

    const handleEdit = (booking: Booking) => {
        const startDate = booking.start_datetime ? new Date(booking.start_datetime) : new Date();
        const endDate = booking.end_datetime ? new Date(booking.end_datetime) : new Date();
        setEditForm({
            subject: booking.subject || '',
            classroom_id: booking.classroom_id,
            date: startDate.toISOString().split('T')[0],
            startTime: startDate.toTimeString().slice(0, 5),
            endTime: endDate.toTimeString().slice(0, 5)
        });
        setEditingBooking(booking);
    };

    const handleSave = async () => {
        if (!editingBooking) return;
        setLoading(true);
        try {
            const startDatetime = `${editForm.date}T${editForm.startTime}:00`;
            const endDatetime = `${editForm.date}T${editForm.endTime}:00`;
            await api.updateBooking(editingBooking.id, {
                subject: editForm.subject,
                classroom_id: editForm.classroom_id,
                start_datetime: startDatetime,
                end_datetime: endDatetime
            });
            await reloadData();
            setEditingBooking(null);
        } catch (err: any) {
            alert(`Error updating booking: ${err.message}`);
        } finally {
            setLoading(false);
        }
    };

    const handleDelete = async (id: number) => {
        if (!confirm('Are you sure you want to delete this booking?')) return;
        setLoading(true);
        try {
            await api.deleteBooking(id);
            await reloadData();
        } catch (err: any) {
            alert(`Error deleting booking: ${err.message}`);
        } finally {
            setLoading(false);
        }
    };

    if (!isOpen) return null;

    return (
        <div className="modal-overlay" onClick={onClose}>
            <div className="modal-content my-bookings-modal" onClick={e => e.stopPropagation()} style={{ maxWidth: '700px', maxHeight: '80vh', overflow: 'auto' }}>
                <h2 style={{ marginTop: 0, color: 'var(--primary-color)' }}>My Bookings</h2>

                {editingBooking ? (
                    <div className="edit-form" style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                        <h3>Edit Booking</h3>
                        <label>
                            Subject:
                            <input type="text" value={editForm.subject} onChange={e => setEditForm({ ...editForm, subject: e.target.value })} style={{ width: '100%', padding: '0.5rem', marginTop: '0.25rem' }} />
                        </label>
                        <label>
                            Classroom:
                            <select value={editForm.classroom_id} onChange={e => setEditForm({ ...editForm, classroom_id: Number(e.target.value) })} style={{ width: '100%', padding: '0.5rem', marginTop: '0.25rem' }}>
                                {classrooms.map(cr => <option key={cr.id} value={cr.id}>{cr.name}</option>)}
                            </select>
                        </label>
                        <label>
                            Date:
                            <input type="date" value={editForm.date} onChange={e => setEditForm({ ...editForm, date: e.target.value })} style={{ width: '100%', padding: '0.5rem', marginTop: '0.25rem' }} />
                        </label>
                        <div style={{ display: 'flex', gap: '1rem' }}>
                            <label style={{ flex: 1 }}>
                                Start Time:
                                <input type="time" value={editForm.startTime} onChange={e => setEditForm({ ...editForm, startTime: e.target.value })} style={{ width: '100%', padding: '0.5rem', marginTop: '0.25rem' }} />
                            </label>
                            <label style={{ flex: 1 }}>
                                End Time:
                                <input type="time" value={editForm.endTime} onChange={e => setEditForm({ ...editForm, endTime: e.target.value })} style={{ width: '100%', padding: '0.5rem', marginTop: '0.25rem' }} />
                            </label>
                        </div>
                        <div style={{ display: 'flex', gap: '0.5rem', marginTop: '1rem' }}>
                            <button onClick={handleSave} disabled={loading} style={{ flex: 1, padding: '0.75rem', background: 'var(--primary-color)', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>
                                {loading ? 'Saving...' : 'Save Changes'}
                            </button>
                            <button onClick={() => setEditingBooking(null)} style={{ flex: 1, padding: '0.75rem', background: '#6c757d', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>
                                Cancel
                            </button>
                        </div>
                    </div>
                ) : (
                    <>
                        {myBookings.length === 0 ? (
                            <p style={{ textAlign: 'center', color: '#666' }}>You don't have any bookings yet.</p>
                        ) : (
                            <div className="bookings-list" style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                                {myBookings.map(booking => {
                                    const classroom = classrooms.find(c => c.id === booking.classroom_id);
                                    const startDate = booking.start_datetime ? new Date(booking.start_datetime) : null;
                                    const endDate = booking.end_datetime ? new Date(booking.end_datetime) : null;
                                    return (
                                        <div key={booking.id} style={{ border: '1px solid #ddd', borderRadius: '8px', padding: '1rem', background: 'var(--card-bg, #fff)' }}>
                                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                                                <div>
                                                    <strong style={{ fontSize: '1.1rem' }}>{booking.subject || 'Untitled'}</strong>
                                                    <p style={{ margin: '0.25rem 0', color: '#666' }}>{classroom?.name || 'Unknown room'}</p>
                                                    {startDate && (
                                                        <p style={{ margin: '0.25rem 0', fontSize: '0.9rem' }}>
                                                            📅 {startDate.toLocaleDateString()} &nbsp; 🕐 {startDate.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} - {endDate?.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                                        </p>
                                                    )}
                                                </div>
                                                <div style={{ display: 'flex', gap: '0.5rem' }}>
                                                    <button onClick={() => handleEdit(booking)} style={{ padding: '0.5rem 1rem', background: 'var(--primary-color)', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>Edit</button>
                                                    <button onClick={() => handleDelete(booking.id)} disabled={loading} style={{ padding: '0.5rem 1rem', background: '#dc3545', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>Delete</button>
                                                </div>
                                            </div>
                                        </div>
                                    );
                                })}
                            </div>
                        )}
                        <button onClick={onClose} style={{ width: '100%', marginTop: '1.5rem', padding: '0.75rem', background: '#6c757d', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>Close</button>
                    </>
                )}
            </div>
        </div>
    );
};

// =============================================================================
// Main App
// =============================================================================
const App = () => {
    const { user, isLoading, logout } = useAuth();
    const [page, setPage] = useState('main');
    const [logo, setLogo] = useState(() => localStorage.getItem('schoolLogo') || '');
    const [classrooms, setClassrooms] = useState<Classroom[]>([]);
    const [bookings, setBookings] = useState<Booking[]>([]);
    const [users, setUsers] = useState<User[]>([]);
    const [dataLoading, setDataLoading] = useState(true);
    const [dataError, setDataError] = useState<string | null>(null);
    const [myBookingsOpen, setMyBookingsOpen] = useState(false);

    useEffect(() => { localStorage.setItem('schoolLogo', logo); }, [logo]);

    // Theme handling (stays in localStorage - browser preference)
    useEffect(() => {
        const themeMode = localStorage.getItem('appThemeMode') || 'light';
        const root = document.documentElement;
        if (themeMode === 'dark') {
            root.setAttribute('data-theme', 'dark');
        } else if (themeMode === 'custom') {
            const customTheme = JSON.parse(localStorage.getItem('appCustomTheme') || '{}');
            Object.entries(customTheme).forEach(([key, value]) => {
                root.style.setProperty(key, String(value));
            });
        } else {
            root.removeAttribute('data-theme');
        }
    }, []);

    // Load data from API
    const loadData = async () => {
        if (!user) return;
        setDataLoading(true);
        setDataError(null);
        try {
            const [classroomsData, bookingsData] = await Promise.all([
                api.getClassrooms().catch(() => []),
                api.getBookings().catch(() => []),
            ]);
            setClassrooms(classroomsData);
            setBookings(bookingsData.map(b => ({
                ...b,
                start: new Date(b.start_datetime),
                end: new Date(b.end_datetime),
                teacher: b.description || 'Teacher',
                event: b.subject || 'Booking',
                createdBy: `User ${b.user_id}`,
            })));
            if (user.is_admin) {
                try { setUsers(await api.getUsers()); } catch { }
            }
        } catch (err: any) {
            setDataError(err.message);
        } finally {
            setDataLoading(false);
        }
    };

    useEffect(() => { loadData(); }, [user]);

    const handleLogout = () => { logout(); setPage('main'); };

    if (isLoading) return <LoadingScreen message="Authenticating..." />;
    if (!user) return <UserLoginPage logo={logo} />;
    if (dataLoading) return <LoadingScreen message="Loading data..." />;

    return (
        <div className="app-container">
            <header>
                <div className="header-branding">
                    {logo ? <img src={logo} alt="School Logo" className="logo-img" /> : <h1>Classroom Booking</h1>}
                </div>
                {page === 'main' && <MainPageHeader />}
                <div className="header-actions">
                    <span className="user-welcome">Hi, {user.full_name || user.username || user.email.split('@')[0]}</span>
                    {page === 'main' && (
                        <>
                            <button className="book-room-btn" onClick={() => document.dispatchEvent(new Event('openBookingModal'))}>Book a Room</button>
                            <button className="my-bookings-btn" onClick={() => setMyBookingsOpen(true)} style={{ background: 'var(--secondary-color, #6c757d)', color: 'white', border: 'none', padding: '0.5rem 1rem', borderRadius: '4px', cursor: 'pointer', marginLeft: '0.5rem' }}>My Bookings</button>
                        </>
                    )}
                    <button className="settings-btn" onClick={() => setPage(page === 'main' ? 'settings' : 'main')} aria-label="Settings">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor"><path d="M19.14,12.94c0.04-0.3,0.06-0.61,0.06-0.94c0-0.32-0.02-0.64-0.07-0.94l2.03-1.58c0.18-0.14,0.23-0.41,0.12-0.61l-1.92-3.32c-0.12-0.22-0.37-0.29-0.59-0.22l-2.39,0.96c-0.5-0.38-1.03-0.7-1.62-0.94L14.4,2.81c-0.04-0.24-0.24-0.41-0.48-0.41h-3.84c-0.24,0-0.44,0.17-0.48,0.41L9.22,5.72C8.63,5.96,8.1,6.29,7.6,6.67L5.21,5.71C5,5.64,4.75,5.7,4.63,5.92L2.71,9.24c-0.11,0.2-0.06,0.47,0.12,0.61l2.03,1.58C4.82,11.69,4.8,12,4.8,12.31c0,0.32,0.02,0.64,0.07,0.94l-2.03,1.58c-0.18,0.14-0.23,0.41-0.12,0.61l1.92,3.32c0.12,0.22,0.37,0.29,0.59,0.22l2.39-0.96c0.5,0.38,1.03,0.7,1.62,0.94l0.38,2.91c0.04,0.24,0.24,0.41,0.48,0.41h3.84c0.24,0,0.44-0.17,0.48-0.41l0.38-2.91c0.59-0.24,1.12-0.56,1.62-0.94l2.39,0.96c0.22,0.08,0.47,0.02,0.59-0.22l1.92-3.32c0.12-0.2,0.07-0.47-0.12-0.61L19.14,12.94z M12,15.6c-1.98,0-3.6-1.62-3.6-3.6s1.62-3.6,3.6-3.6s3.6,1.62,3.6,3.6S13.98,15.6,12,15.6z" /></svg>
                    </button>
                    <button className="logout-btn" onClick={handleLogout} title="Logout" style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--font-color)' }}>
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" /><polyline points="16 17 21 12 16 7" /><line x1="21" y1="12" x2="9" y2="12" /></svg>
                    </button>
                </div>
            </header>
            <main>
                {dataError && <div className="error-banner" style={{ background: '#dc3545', color: 'white', padding: '1rem', marginBottom: '1rem' }}>{dataError}</div>}
                {page === 'main' ? (
                    <MainPage classrooms={classrooms} bookings={bookings} setBookings={setBookings} currentUser={user} reloadData={loadData} />
                ) : (
                    <SettingsPage setPage={setPage} setLogo={setLogo} classrooms={classrooms} setClassrooms={setClassrooms} bookings={bookings} setBookings={setBookings} users={users} setUsers={setUsers} currentUser={user} reloadData={loadData} />
                )}
            </main>
            <MyBookingsModal
                isOpen={myBookingsOpen}
                onClose={() => setMyBookingsOpen(false)}
                bookings={bookings}
                classrooms={classrooms}
                currentUser={user}
                reloadData={loadData}
            />
        </div>
    );
};

// =============================================================================
// Loading Screen
// =============================================================================
const LoadingScreen: React.FC<{ message: string }> = ({ message }) => (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh', backgroundColor: 'var(--background-color, #f8f9fa)' }}>
        <div style={{ textAlign: 'center' }}>
            <div style={{ width: '40px', height: '40px', border: '4px solid #e9ecef', borderTop: '4px solid var(--primary-color, #007bff)', borderRadius: '50%', animation: 'spin 1s linear infinite', margin: '0 auto 1rem' }}></div>
            <p>{message}</p>
        </div>
        <style>{`@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }`}</style>
    </div>
);

// =============================================================================
// Login Page
// =============================================================================
const UserLoginPage: React.FC<{ logo: string }> = ({ logo }) => {
    const { login, error: authError } = useAuth();
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const [forgotMsg, setForgotMsg] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setLoading(true);
        try {
            await login(email, password);
        } catch (err: any) {
            setError(err.message || 'Invalid credentials');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="login-full-page" style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh', backgroundColor: 'var(--background-color)' }}>
            <div className="login-card" style={{ backgroundColor: 'var(--header-background)', padding: '2.5rem', borderRadius: '12px', boxShadow: '0 8px 30px rgba(0,0,0,0.1)', width: '100%', maxWidth: '400px' }}>
                {logo ? <img src={logo} alt="Logo" style={{ maxHeight: '60px', margin: '0 auto 1.5rem', display: 'block' }} /> : <h1 style={{ color: 'var(--primary-color)', textAlign: 'center', marginBottom: '1.5rem' }}>Classroom Booking</h1>}
                <h2 style={{ textAlign: 'center', marginBottom: '1.5rem', fontWeight: '500' }}>Login</h2>
                {(error || authError) && <p style={{ color: 'white', backgroundColor: '#dc3545', padding: '0.75rem', borderRadius: '5px', marginBottom: '1rem' }}>{error || authError}</p>}
                {forgotMsg && <p style={{ color: 'var(--primary-color)', backgroundColor: '#e3f2fd', padding: '0.75rem', borderRadius: '5px', marginBottom: '1rem', fontSize: '0.9rem' }}>Contact administrator to reset password.</p>}
                <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1.2rem' }}>
                    <div className="form-group">
                        <label>Email Address</label>
                        <input type="email" value={email} onChange={e => setEmail(e.target.value)} required placeholder="you@school.com" disabled={loading} />
                    </div>
                    <div className="form-group">
                        <label>Password</label>
                        <input type="password" value={password} onChange={e => setPassword(e.target.value)} required placeholder="••••••••" disabled={loading} />
                    </div>
                    <button type="submit" className="btn-submit" style={{ padding: '0.8rem', borderRadius: '6px' }} disabled={loading}>
                        {loading ? 'Signing in...' : 'Sign In'}
                    </button>
                </form>
                <button onClick={() => setForgotMsg(true)} style={{ background: 'none', border: 'none', color: 'var(--secondary-color)', cursor: 'pointer', marginTop: '1rem', fontSize: '0.9rem', width: '100%', textDecoration: 'underline' }}>Forgot password?</button>
            </div>
        </div>
    );
};

// =============================================================================
// Main Page Header
// =============================================================================
const MainPageHeader = () => {
    const [view, setView] = useState('week');
    const [currentDate, setCurrentDate] = useState(new Date());

    useEffect(() => {
        const changeViewHandler = (e: any) => setView(e.detail);
        const prevHandler = () => {
            const newDate = new Date(currentDate);
            if (view === 'day') newDate.setDate(currentDate.getDate() - 1);
            else if (view === 'week') newDate.setDate(currentDate.getDate() - 7);
            else newDate.setMonth(currentDate.getMonth() - 1);
            setCurrentDate(newDate);
        };
        const nextHandler = () => {
            const newDate = new Date(currentDate);
            if (view === 'day') newDate.setDate(currentDate.getDate() + 1);
            else if (view === 'week') newDate.setDate(currentDate.getDate() + 7);
            else newDate.setMonth(currentDate.getMonth() + 1);
            setCurrentDate(newDate);
        };
        document.addEventListener('changeView', changeViewHandler);
        document.addEventListener('prevDate', prevHandler);
        document.addEventListener('nextDate', nextHandler);
        document.dispatchEvent(new CustomEvent('dateChange', { detail: { view, currentDate } }));
        return () => {
            document.removeEventListener('changeView', changeViewHandler);
            document.removeEventListener('prevDate', prevHandler);
            document.removeEventListener('nextDate', nextHandler);
        };
    }, [view, currentDate]);

    const getHeaderDate = () => {
        if (view === 'day') return currentDate.toLocaleDateString(undefined, { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' });
        if (view === 'month') return currentDate.toLocaleDateString(undefined, { year: 'numeric', month: 'long' });
        const startOfWeek = new Date(currentDate);
        startOfWeek.setDate(currentDate.getDate() - currentDate.getDay());
        const endOfWeek = new Date(startOfWeek);
        endOfWeek.setDate(startOfWeek.getDate() + 6);
        return `${startOfWeek.toLocaleDateString(undefined, { month: 'short', day: 'numeric' })} - ${endOfWeek.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })}`;
    };

    return (
        <>
            <div className="controls">
                <button onClick={() => document.dispatchEvent(new Event('prevDate'))}>&lt;</button>
                <h2>{getHeaderDate()}</h2>
                <button onClick={() => document.dispatchEvent(new Event('nextDate'))}>&gt;</button>
            </div>
            <div className="view-switcher">
                <button className={view === 'day' ? 'active' : ''} onClick={() => document.dispatchEvent(new CustomEvent('changeView', { detail: 'day' }))}>Day</button>
                <button className={view === 'week' ? 'active' : ''} onClick={() => document.dispatchEvent(new CustomEvent('changeView', { detail: 'week' }))}>Week</button>
                <button className={view === 'month' ? 'active' : ''} onClick={() => document.dispatchEvent(new CustomEvent('changeView', { detail: 'month' }))}>Month</button>
            </div>
        </>
    );
};

// =============================================================================
// Main Page
// =============================================================================
const MainPage = ({ classrooms, bookings, setBookings, currentUser, reloadData }: any) => {
    const [view, setView] = useState('week');
    const [currentDate, setCurrentDate] = useState(new Date());
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [submitting, setSubmitting] = useState(false);

    useEffect(() => {
        const dateChangeHandler = (e: any) => { setView(e.detail.view); setCurrentDate(e.detail.currentDate); };
        const openModalHandler = () => setIsModalOpen(true);
        document.addEventListener('dateChange', dateChangeHandler);
        document.addEventListener('openBookingModal', openModalHandler);
        return () => {
            document.removeEventListener('dateChange', dateChangeHandler);
            document.removeEventListener('openBookingModal', openModalHandler);
        };
    }, []);

    const handleBookingSubmit = async (bookingDetails: any) => {
        const { classroomId, date, startHour, endHour, teacher, event } = bookingDetails;
        if (!classroomId || !date || !startHour || !endHour || !teacher || !event) {
            alert('Please fill in all fields.');
            return;
        }
        if (parseInt(startHour) >= parseInt(endHour)) {
            alert('End time must be after start time.');
            return;
        }

        setSubmitting(true);
        try {
            await api.createBooking({
                classroom_id: parseInt(classroomId),
                start_datetime: `${date}T${startHour}:00:00`,
                end_datetime: `${date}T${endHour}:00:00`,
                subject: event,
                description: teacher,
            });
            await reloadData();
            setIsModalOpen(false);
        } catch (err: any) {
            alert(`Error: ${err.message}`);
        } finally {
            setSubmitting(false);
        }
    };

    const renderDayView = () => {
        const timeSlots = Array.from({ length: 10 }, (_, i) => i + 8);
        return (
            <div className="calendar-grid day-view">
                <div className="header-row"><div className="corner-cell">Time</div>{timeSlots.map(h => <div key={h} className="header-cell">{`${h}:00`}</div>)}</div>
                {classrooms.map((cr: any) => (
                    <div key={cr.id} className="body-row">
                        <div className="row-header">{cr.name}</div>
                        {timeSlots.map(hour => {
                            const booking = bookings.find((b: any) => b.classroom_id === cr.id && b.start?.toDateString() === currentDate.toDateString() && b.start?.getHours() <= hour && b.end?.getHours() > hour);
                            return <div key={hour} className="body-cell">{booking && <div className="booking"><strong>{booking.event}</strong><p>{booking.teacher}</p></div>}</div>;
                        })}
                    </div>
                ))}
            </div>
        );
    };

    const renderWeekView = () => {
        const startOfWeek = new Date(currentDate);
        startOfWeek.setDate(currentDate.getDate() - currentDate.getDay());
        const days = Array.from({ length: 7 }).map((_, i) => new Date(startOfWeek.getFullYear(), startOfWeek.getMonth(), startOfWeek.getDate() + i));
        return (
            <div className="calendar-grid week-view">
                <div className="header-row"><div className="corner-cell">Classroom</div>{days.map(d => <div key={d.toISOString()} className="header-cell">{d.toLocaleDateString(undefined, { weekday: 'short', day: 'numeric' })}</div>)}</div>
                {classrooms.map((cr: any) => (
                    <div key={cr.id} className="body-row">
                        <div className="row-header">{cr.name}</div>
                        {days.map(day => {
                            const dayBookings = bookings.filter((b: any) => b.classroom_id === cr.id && b.start?.toDateString() === day.toDateString());
                            return <div key={day.toISOString()} className="body-cell">{dayBookings.map((bk: any) => <div key={bk.id} className="booking"><strong>{bk.event}</strong><span>{bk.start?.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span></div>)}</div>;
                        })}
                    </div>
                ))}
            </div>
        );
    };

    const renderMonthView = () => {
        const year = currentDate.getFullYear();
        const month = currentDate.getMonth();
        const firstDayOfMonth = new Date(year, month, 1);
        const lastDayOfMonth = new Date(year, month + 1, 0);
        const firstDayOfWeek = firstDayOfMonth.getDay();
        const totalDays = lastDayOfMonth.getDate();
        const daysInPrevMonth = new Date(year, month, 0).getDate();
        const calendarDays: any[] = [];
        for (let i = firstDayOfWeek; i > 0; i--) calendarDays.push({ day: daysInPrevMonth - i + 1, isCurrentMonth: false, date: null });
        for (let i = 1; i <= totalDays; i++) calendarDays.push({ day: i, isCurrentMonth: true, date: new Date(year, month, i) });
        const remainingCells = 42 - calendarDays.length;
        for (let i = 1; i <= remainingCells; i++) calendarDays.push({ day: i, isCurrentMonth: false, date: null });
        const weekdays = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
        return (
            <div className="calendar-grid month-view">
                <div className="month-header">{weekdays.map(day => <div key={day} className="header-cell">{day}</div>)}</div>
                <div className="month-body">{calendarDays.map((d, index) => {
                    const dayBookings = d.date ? bookings.filter((b: any) => b.start?.toDateString() === d.date?.toDateString()) : [];
                    return (<div key={index} className={`body-cell ${d.isCurrentMonth ? 'current-month' : 'other-month'}`}>
                        <div className="day-number">{d.day}</div>
                        <div className="bookings-container">{dayBookings.map((bk: any) => <div key={bk.id} className="booking"><strong>{bk.event}</strong></div>)}</div>
                    </div>);
                })}</div>
            </div>
        );
    };

    const renderCalendar = () => {
        switch (view) {
            case 'day': return renderDayView();
            case 'week': return renderWeekView();
            case 'month': return renderMonthView();
            default: return renderWeekView();
        }
    };

    return (
        <>
            <BookingModal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} classrooms={classrooms} onSubmit={handleBookingSubmit} currentUser={currentUser} submitting={submitting} />
            {classrooms.length === 0 ? (
                <div style={{ textAlign: 'center', padding: '3rem' }}><h3>No classrooms available</h3><p>Add classrooms in Settings.</p></div>
            ) : renderCalendar()}
        </>
    );
};

// =============================================================================
// Booking Modal
// =============================================================================
const BookingModal = ({ isOpen, onClose, classrooms, onSubmit, currentUser, submitting }: any) => {
    const [bookingDetails, setBookingDetails] = useState({
        classroomId: '', teacher: currentUser?.full_name || currentUser?.email?.split('@')[0] || '', event: '',
        date: new Date().toISOString().split('T')[0], startHour: '09', endHour: '10'
    });
    if (!isOpen) return null;

    const handleInputChange = (e: any) => {
        const { name, value } = e.target;
        setBookingDetails(prev => {
            const updated = { ...prev, [name]: value };
            // Auto-update end time when start time changes
            if (name === 'startHour') {
                const nextHour = Math.min(parseInt(value) + 1, 17).toString().padStart(2, '0');
                updated.endHour = nextHour;
            }
            return updated;
        });
    };

    const handleSubmit = (e: any) => { e.preventDefault(); onSubmit(bookingDetails); };
    const timeOptions = Array.from({ length: 10 }, (_, i) => (i + 8).toString().padStart(2, '0'));
    return (
        <div className="modal-overlay" onClick={onClose}>
            <div className="modal-content" onClick={e => e.stopPropagation()}>
                <h2>Book a Classroom</h2>
                <form onSubmit={handleSubmit} className="booking-form" autoComplete="off">
                    <div className="form-group"><label>Teacher</label><input type="text" name="teacher" value={bookingDetails.teacher} onChange={handleInputChange} required disabled={submitting} autoComplete="off" /></div>
                    <div className="form-group"><label>Subject/Event</label><input type="text" name="event" value={bookingDetails.event} onChange={handleInputChange} required disabled={submitting} autoComplete="off" /></div>
                    <div className="form-group"><label>Classroom</label><select name="classroomId" value={bookingDetails.classroomId} onChange={handleInputChange} required disabled={submitting}><option value="" disabled>Select...</option>{classrooms.map((cr: any) => <option key={cr.id} value={cr.id}>{cr.name}</option>)}</select></div>
                    <div className="form-group"><label>Date</label><input type="date" name="date" value={bookingDetails.date} onChange={handleInputChange} required disabled={submitting} /></div>
                    <div className="form-group-inline">
                        <div className="form-group"><label>Start</label><select name="startHour" value={bookingDetails.startHour} onChange={handleInputChange} disabled={submitting}>{timeOptions.map(h => <option key={h} value={h}>{h}:00</option>)}</select></div>
                        <div className="form-group"><label>End</label><select name="endHour" value={bookingDetails.endHour} onChange={handleInputChange} disabled={submitting}>{timeOptions.map(h => <option key={h} value={h}>{h}:00</option>)}</select></div>
                    </div>
                    <div className="form-actions">
                        <button type="button" className="btn-cancel" onClick={onClose} disabled={submitting}>Cancel</button>
                        <button type="submit" className="btn-submit" disabled={submitting}>{submitting ? 'Booking...' : 'Book Now'}</button>
                    </div>
                </form>
            </div>
        </div>
    );
};

// =============================================================================
// Settings Page
// =============================================================================
const SettingsPage = ({ setPage, setLogo, classrooms, setClassrooms, bookings, setBookings, users, setUsers, currentUser, reloadData }: any) => {
    const isAdmin = currentUser?.is_admin;
    const [activeTab, setActiveTab] = useState(isAdmin ? 'classrooms' : 'appearance');

    const TabContent = () => {
        const [newItemName, setNewItemName] = useState('');
        const [newUserEmail, setNewUserEmail] = useState('');
        const [newUserPassword, setNewUserPassword] = useState('');
        const [newUserName, setNewUserName] = useState('');
        const [userError, setUserError] = useState('');
        const [loading, setLoading] = useState(false);

        const handleLogoUpload = (e: any) => {
            const file = e.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onloadend = () => { if (typeof reader.result === 'string') setLogo(reader.result); };
                reader.readAsDataURL(file);
            }
        };

        const addClassroom = async () => {
            if (!newItemName.trim()) return;
            setLoading(true);
            try {
                await api.createClassroom({ name: newItemName.trim(), code: newItemName.trim().toLowerCase().replace(/\s+/g, '-'), capacity: 30, is_active: true });
                await reloadData();
                setNewItemName('');
            } catch (err: any) {
                const msg = typeof err.message === 'string' ? err.message : JSON.stringify(err.message);
                alert(`Error: ${msg}`);
            }
            finally { setLoading(false); }
        };

        const deleteClassroom = async (id: number) => {
            if (!confirm('Delete this classroom?')) return;
            try { await api.deleteClassroom(id); await reloadData(); } catch (err: any) { alert(err.message); }
        };

        const deleteBooking = async (id: number) => {
            if (!confirm('Delete this booking?')) return;
            try { await api.deleteBooking(id); await reloadData(); } catch (err: any) { alert(err.message); }
        };

        const addUser = async () => {
            setUserError('');
            if (!newUserEmail.trim() || !newUserPassword.trim()) return;
            if (newUserPassword.length < 6) { setUserError('Password min 6 chars'); return; }
            setLoading(true);
            try {
                await api.register({ username: newUserEmail.split('@')[0], email: newUserEmail.trim(), password: newUserPassword.trim(), full_name: newUserName.trim() || undefined });
                await reloadData();
                setNewUserEmail(''); setNewUserPassword(''); setNewUserName('');
            } catch (err: any) { setUserError(err.message); }
            finally { setLoading(false); }
        };

        const deleteUser = async (id: number) => {
            if (id === currentUser.id) { alert('Cannot delete yourself.'); return; }
            if (!confirm('Delete this user?')) return;
            try { await api.deleteUser(id); await reloadData(); } catch (err: any) { alert(err.message); }
        };

        switch (activeTab) {
            case 'logo': return (<div><h3>Upload Logo</h3><input type="file" accept="image/*" onChange={handleLogoUpload} /></div>);
            case 'classrooms': return (
                <div><h3>Manage Classrooms</h3>
                    <div className="add-form"><input type="text" value={newItemName} onChange={e => setNewItemName(e.target.value)} placeholder="Classroom name" disabled={loading} /><button onClick={addClassroom} disabled={loading}>{loading ? '...' : 'Add'}</button></div>
                    <ul className="management-list">{classrooms.map((c: any) => <li key={c.id}><span>{c.name}</span><button onClick={() => deleteClassroom(c.id)}>Delete</button></li>)}</ul>
                </div>
            );
            case 'bookings': return (
                <div><h3>Manage Bookings</h3>
                    <ul className="management-list">{bookings.map((b: any) => <li key={b.id}><span>{classrooms.find((c: any) => c.id === b.classroom_id)?.name} - {b.event} @ {b.start?.toLocaleString()}</span><button onClick={() => deleteBooking(b.id)}>Delete</button></li>)}</ul>
                </div>
            );
            case 'users': return (
                <div><h3>Manage Users</h3>
                    <p style={{ fontSize: '0.9rem', marginBottom: '1rem' }}>Users can login from any device. Use Adminer at <a href="http://127.0.0.1:8080" target="_blank">localhost:8080</a> to reset passwords.</p>
                    {userError && <p style={{ color: 'red', marginBottom: '1rem' }}>{userError}</p>}
                    <div className="add-form" style={{ flexWrap: 'wrap', gap: '0.5rem' }}>
                        <input type="text" value={newUserName} onChange={e => setNewUserName(e.target.value)} placeholder="Full name" disabled={loading} style={{ flex: '1 1 100%' }} />
                        <input type="email" value={newUserEmail} onChange={e => setNewUserEmail(e.target.value)} placeholder="Email" disabled={loading} />
                        <input type="password" value={newUserPassword} onChange={e => setNewUserPassword(e.target.value)} placeholder="Password (min 6)" disabled={loading} />
                        <button onClick={addUser} disabled={loading}>{loading ? '...' : 'Add'}</button>
                    </div>
                    <ul className="management-list">{users.map((u: any) => <li key={u.id}>
                        <span><strong>{u.email}</strong> {u.is_admin && <small>(Admin)</small>}<br /><small>{u.full_name || u.username}</small></span>
                        <button onClick={() => deleteUser(u.id)} disabled={u.id === currentUser.id}>Delete</button>
                    </li>)}</ul>
                </div>
            );
            case 'appearance': {
                const defaultColors: Record<string, string> = {
                    '--primary-color': '#007bff', '--secondary-color': '#6c757d', '--background-color': '#f8f9fa',
                    '--font-color': '#333', '--border-color': '#dee2e6', '--header-background': '#fff',
                    '--booking-color': '#ffc107', '--hover-color': '#e9ecef', '--danger-color': '#dc3545', '--success-color': '#28a745',
                };
                const [themeMode, setThemeMode] = useState(() => localStorage.getItem('appThemeMode') || 'light');
                const [customColors, setCustomColors] = useState<Record<string, string>>(() => {
                    const saved = localStorage.getItem('appCustomTheme');
                    return saved ? JSON.parse(saved) : defaultColors;
                });

                useEffect(() => {
                    localStorage.setItem('appThemeMode', themeMode);
                    const root = document.documentElement;
                    root.removeAttribute('data-theme');
                    Object.keys(defaultColors).forEach(key => root.style.removeProperty(key));
                    if (themeMode === 'dark') root.setAttribute('data-theme', 'dark');
                    else if (themeMode === 'custom') {
                        localStorage.setItem('appCustomTheme', JSON.stringify(customColors));
                        Object.entries(customColors).forEach(([key, value]) => root.style.setProperty(key, value));
                    }
                }, [themeMode, customColors]);

                const handleColorChange = (key: string, value: string) => setCustomColors(prev => ({ ...prev, [key]: value }));

                return (
                    <div>
                        <h3>Theme</h3>
                        <div className="theme-options">
                            <div><input type="radio" id="light" name="theme" checked={themeMode === 'light'} onChange={() => setThemeMode('light')} /><label htmlFor="light"> Light</label></div>
                            <div><input type="radio" id="dark" name="theme" checked={themeMode === 'dark'} onChange={() => setThemeMode('dark')} /><label htmlFor="dark"> Dark</label></div>
                            <div><input type="radio" id="custom" name="theme" checked={themeMode === 'custom'} onChange={() => setThemeMode('custom')} /><label htmlFor="custom"> Custom</label></div>
                        </div>
                        {themeMode === 'custom' && (
                            <div className="custom-theme-settings"><h4>Colors</h4>
                                <div className="color-pickers">{Object.entries(customColors).map(([key, value]) => (
                                    <div key={key}><label>{key.replace('--', '').replace(/-/g, ' ')}</label><input type="color" value={value} onChange={e => handleColorChange(key, e.target.value)} /></div>
                                ))}</div>
                            </div>
                        )}
                    </div>
                );
            }
            default: return null;
        }
    };

    return (
        <div className="settings-page admin-panel">
            <div className="settings-header">
                <h2>{isAdmin ? 'Admin Panel' : 'Settings'}</h2>
                <button className="btn-back-main" onClick={() => setPage('main')}>Back to Calendar</button>
            </div>
            <div className="tabs">
                {isAdmin && (
                    <>
                        <button className={activeTab === 'classrooms' ? 'active' : ''} onClick={() => setActiveTab('classrooms')}>Classrooms</button>
                        <button className={activeTab === 'bookings' ? 'active' : ''} onClick={() => setActiveTab('bookings')}>Bookings</button>
                        <button className={activeTab === 'users' ? 'active' : ''} onClick={() => setActiveTab('users')}>Users</button>
                        <button className={activeTab === 'logo' ? 'active' : ''} onClick={() => setActiveTab('logo')}>Logo</button>
                    </>
                )}
                <button className={activeTab === 'appearance' ? 'active' : ''} onClick={() => setActiveTab('appearance')}>Appearance</button>
            </div>
            <div className="tab-content"><TabContent /></div>
        </div>
    );
};

// =============================================================================
// Bootstrap
// =============================================================================
const root = createRoot(document.getElementById('root')!);
root.render(<AuthProvider><App /></AuthProvider>);