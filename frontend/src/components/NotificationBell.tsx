import React, { useMemo, useState, useEffect } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

interface Notification {
  id: number;
  type: 'info' | 'success' | 'warning' | 'error' | 'critical';
  title: string;
  message: string;
  event_type?: string;
  redirect_url?: string;
  severity?: string;
  is_read: boolean;
  created_at: string;
  action_label?: string;
}

interface NotificationListResponse {
  notifications: Notification[];
  total: number;
  unread_count: number;
  page: number;
  page_size: number;
}

const NotificationBell: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [isOpen, setIsOpen] = useState(false);
  const [selectedEventType, setSelectedEventType] = useState<string>('ALL');
  const [roundFilter, setRoundFilter] = useState('');
  const [hospitalFilter, setHospitalFilter] = useState('');
  const [loading, setLoading] = useState(false);

  const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
  const token = user?.token || localStorage.getItem('access_token');
  const roleParam = user?.role === 'ADMIN' ? 'CENTRAL' : 'HOSPITAL';

  // Fetch notifications
  const fetchNotifications = async () => {
    if (!token) return;

    try {
      setLoading(true);
      const eventQuery = selectedEventType !== 'ALL' ? `&event_type=${encodeURIComponent(selectedEventType)}` : '';
      const response = await axios.get<NotificationListResponse>(`${API_URL}/api/notifications?role=${roleParam}${eventQuery}&page=1&page_size=50`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setNotifications(response.data.notifications || []);
      setUnreadCount(response.data.unread_count || 0);
    } catch (error) {
      console.error('Failed to fetch notifications:', error);
    } finally {
      setLoading(false);
    }
  };

  // Fetch unread count
  const fetchUnreadCount = async () => {
    if (!token) return;

    try {
      const response = await axios.get(`${API_URL}/api/notifications/unread-count?role=${roleParam}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setUnreadCount(response.data.unread_count);
    } catch (error) {
      console.error('Failed to fetch unread count:', error);
    }
  };

  // Mark as read
  const markAsRead = async (id: number) => {
    if (!token) return;

    try {
      await axios.patch(`${API_URL}/api/notifications/${id}/read?role=${roleParam}`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setNotifications(prev => 
        prev.map(n => n.id === id ? { ...n, is_read: true } : n)
      );
      setUnreadCount(prev => Math.max(0, prev - 1));
    } catch (error) {
      console.error('Failed to mark as read:', error);
    }
  };

  // Mark all as read
  const markAllAsRead = async () => {
    if (!token) return;

    try {
      const markAllPath = user?.role === 'ADMIN'
        ? `${API_URL}/api/notifications/central/mark-all-read`
        : `${API_URL}/api/notifications/hospital/mark-all-read`;
      await axios.post(markAllPath, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setNotifications(prev => prev.map(n => ({ ...n, is_read: true })));
      setUnreadCount(0);
    } catch (error) {
      console.error('Failed to mark all as read:', error);
    }
  };

  const filteredNotifications = useMemo(() => {
    return notifications.filter((notification) => {
      const haystack = `${notification.title} ${notification.message}`.toLowerCase();
      const roundOk = !roundFilter || haystack.includes(`round ${roundFilter.toLowerCase()}`);
      const hospitalOk = !hospitalFilter || haystack.includes(hospitalFilter.toLowerCase());
      return roundOk && hospitalOk;
    });
  }, [notifications, roundFilter, hospitalFilter]);

  // Polling fallback (WebSocket-ready architecture)
  useEffect(() => {
    if (!token) return;
    const interval = setInterval(() => {
      fetchUnreadCount();
      if (isOpen) {
        fetchNotifications();
      }
    }, 15000);

    return () => {
      clearInterval(interval);
    };
  }, [token, isOpen, roleParam]);

  // Initial load
  useEffect(() => {
    fetchNotifications();
    fetchUnreadCount();
    
    // Request notification permission
    if ('Notification' in window && Notification.permission === 'default') {
      Notification.requestPermission();
    }
  }, [selectedEventType, roleParam]);

  // Get icon color based on type
  const getTypeColor = (type: string) => {
    switch (type) {
      case 'error': return 'text-red-600';
      case 'warning': return 'text-yellow-600';
      case 'success': return 'text-green-600';
      case 'critical': return 'text-red-700';
      default: return 'text-blue-600';
    }
  };

  const openNotification = async (notification: Notification) => {
    if (!notification.is_read) {
      await markAsRead(notification.id);
    }

    setIsOpen(false);

    if (notification.redirect_url) {
      navigate(notification.redirect_url);
      return;
    }
  };

  return (
    <div className="relative">
      {/* Bell Icon */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="relative p-2 text-gray-600 hover:text-gray-900 focus:outline-none"
      >
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
                d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
        </svg>
        {unreadCount > 0 && (
          <span className="absolute top-0 right-0 flex items-center justify-center w-5 h-5 text-xs font-bold text-white bg-red-600 rounded-full">
            {unreadCount > 99 ? '99+' : unreadCount}
          </span>
        )}
      </button>

      {/* Dropdown */}
      {isOpen && (
        <div className="absolute right-0 z-50 w-[28rem] mt-2 bg-white rounded-lg shadow-xl border border-gray-200">
          {/* Header */}
          <div className="flex items-center justify-between px-4 py-3 border-b">
            <h3 className="text-lg font-semibold text-gray-900">Notifications</h3>
            {unreadCount > 0 && (
              <button
                onClick={markAllAsRead}
                className="text-sm text-blue-600 hover:text-blue-800"
              >
                Mark all read
              </button>
            )}
          </div>

          {/* Filters */}
          <div className="px-4 py-3 border-b bg-slate-50 grid grid-cols-3 gap-2">
            <select
              value={selectedEventType}
              onChange={(e) => setSelectedEventType(e.target.value)}
              className="text-xs border rounded px-2 py-1"
            >
              <option value="ALL">All Events</option>
              <option value="ROUND_CREATED">Round Created</option>
              <option value="ROUND_INVITATION_SENT">Round Invite</option>
              <option value="WEIGHTS_UPLOADED">Weights Uploaded</option>
              <option value="AGGREGATION_COMPLETED">Aggregation Done</option>
              <option value="GLOBAL_MODEL_UPDATED">Global Model</option>
              <option value="DP_APPLIED">DP Applied</option>
              <option value="BLOCKCHAIN_HASH_RECORDED">Blockchain</option>
              <option value="PREDICTION_CREATED">Prediction</option>
            </select>
            <input
              value={roundFilter}
              onChange={(e) => setRoundFilter(e.target.value)}
              className="text-xs border rounded px-2 py-1"
              placeholder="Filter Round"
            />
            <input
              value={hospitalFilter}
              onChange={(e) => setHospitalFilter(e.target.value)}
              className="text-xs border rounded px-2 py-1"
              placeholder={user?.role === 'ADMIN' ? 'Filter Hospital' : 'Search'}
            />
          </div>

          {/* Notification List */}
          <div className="max-h-96 overflow-y-auto">
            {loading ? (
              <div className="px-4 py-8 text-center text-gray-500">Loading...</div>
            ) : filteredNotifications.length === 0 ? (
              <div className="px-4 py-8 text-center text-gray-500">
                No notifications
              </div>
            ) : (
              filteredNotifications.map((notification) => (
                <div
                  key={notification.id}
                  className={`px-4 py-3 border-b hover:bg-gray-50 cursor-pointer ${
                    !notification.is_read ? 'bg-blue-50' : ''
                  }`}
                  onClick={() => openNotification(notification)}
                >
                  <div className="flex items-start">
                    <span className={`mt-1 mr-3 ${getTypeColor(notification.type)}`}>
                      {notification.type === 'error' && '⚠️'}
                      {notification.type === 'warning' && '⚡'}
                      {notification.type === 'success' && '✅'}
                      {notification.type === 'critical' && '🚨'}
                      {notification.type === 'info' && 'ℹ️'}
                    </span>
                    <div className="flex-1">
                      <p className="text-sm font-medium text-gray-900">
                        {notification.title}
                      </p>
                      <p className="mt-1 text-sm text-gray-600">
                        {notification.message}
                      </p>
                      <p className="mt-1 text-xs text-gray-400">
                        {new Date(notification.created_at).toLocaleString()}
                      </p>
                      {(notification.redirect_url || notification.action_label) && (
                        <a
                          href={notification.redirect_url || '#'}
                          className="inline-block mt-2 text-sm font-medium text-blue-600 hover:text-blue-800"
                          onClick={(e) => e.stopPropagation()}
                        >
                          {notification.action_label || 'View'}  →
                        </a>
                      )}
                    </div>
                    {!notification.is_read && (
                      <div className="w-2 h-2 mt-2 ml-2 bg-blue-600 rounded-full"></div>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>

          {/* Footer */}
          {filteredNotifications.length > 0 && (
            <div className="px-4 py-3 text-center border-t">
              <button
                onClick={() => setIsOpen(false)}
                className="text-sm text-gray-600 hover:text-gray-900"
              >
                Close
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default NotificationBell;
