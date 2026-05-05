import React, { useState } from 'react';
import { useKeycloak } from '@react-keycloak/web';

// Типы данных для отчета
interface ReportData {
  customerId: string;
  customerName: string;
  customerSegment: string;
  registrationDate: string;
  totalSessions: number;
  totalSessionDurationSeconds: number;
  avgSessionDurationSeconds: number;
  totalPageViews: number;
  totalActions: number;
  avgActionsPerSession: number;
  firstEventDate: string;
  lastEventDate: string;
  daysSinceLastEvent: number;
  engagementScore: number;
  churnRisk: string;
  updatedAt: string;
}

const ReportPage: React.FC = () => {
  const { keycloak, initialized } = useKeycloak();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [reportData, setReportData] = useState<ReportData | null>(null);

  const fetchReport = async () => {
    if (!keycloak?.token) {
      setError('Not authenticated');
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const response = await fetch(`${process.env.REACT_APP_API_URL}/reports`, {
        headers: {
          'Authorization': `Bearer ${keycloak.token}`
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setReportData(data);

    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
      setReportData(null);
    } finally {
      setLoading(false);
    }
  };

  // Форматирование длительности (секунды в HH:MM:SS)
  const formatDuration = (seconds: number): string => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  // Форматирование даты
  const formatDate = (dateString: string): string => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString('ru-RU');
  };

  // Определение цвета для уровня риска оттока
  const getChurnRiskColor = (risk: string): string => {
    switch (risk?.toLowerCase()) {
      case 'high':
        return 'text-red-600 bg-red-100';
      case 'medium':
        return 'text-yellow-600 bg-yellow-100';
      case 'low':
        return 'text-green-600 bg-green-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  // Определение цвета для engagement score
  const getEngagementScoreColor = (score: number): string => {
    if (score >= 80) return 'text-green-600';
    if (score >= 50) return 'text-yellow-600';
    return 'text-red-600';
  };

  if (!initialized) {
    return <div className="flex items-center justify-center min-h-screen">
      <div className="text-lg">Loading...</div>
    </div>;
  }

  if (!keycloak.authenticated) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen bg-gray-100">
        <button
          onClick={() => keycloak.login()}
          className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
        >
          Login
        </button>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <div className="max-w-6xl mx-auto">
        {/* Заголовок и кнопка */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <div className="flex justify-between items-center">
            <h1 className="text-2xl font-bold">Usage Reports</h1>
            <button
              onClick={fetchReport}
              disabled={loading}
              className={`px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 ${
                loading ? 'opacity-50 cursor-not-allowed' : ''
              }`}
            >
              {loading ? 'Loading...' : 'Load Report'}
            </button>
          </div>
        </div>

        {/* Ошибка */}
        {error && (
          <div className="mb-6 p-4 bg-red-100 text-red-700 rounded-lg">
            <strong>Error:</strong> {error}
          </div>
        )}

        {/* Данные отчета */}
        {reportData && (
          <div className="space-y-6">
            {/* Основная информация */}
            <div className="bg-white rounded-lg shadow-md p-6">
              <h2 className="text-xl font-semibold mb-4">Customer Information</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="text-sm text-gray-600">Customer ID</label>
                  <p className="font-mono text-sm">{reportData.customerId}</p>
                </div>
                <div>
                  <label className="text-sm text-gray-600">Customer Name</label>
                  <p className="font-semibold">{reportData.customerName || 'N/A'}</p>
                </div>
                <div>
                  <label className="text-sm text-gray-600">Segment</label>
                  <p>
                    <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-sm">
                      {reportData.customerSegment || 'N/A'}
                    </span>
                  </p>
                </div>
                <div>
                  <label className="text-sm text-gray-600">Registration Date</label>
                  <p>{formatDate(reportData.registrationDate)}</p>
                </div>
              </div>
            </div>

            {/* Метрики активности */}
            <div className="bg-white rounded-lg shadow-md p-6">
              <h2 className="text-xl font-semibold mb-4">Activity Metrics</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                <div className="border rounded-lg p-3">
                  <label className="text-sm text-gray-600">Total Sessions</label>
                  <p className="text-2xl font-bold">{reportData.totalSessions || 0}</p>
                </div>
                <div className="border rounded-lg p-3">
                  <label className="text-sm text-gray-600">Total Duration</label>
                  <p className="text-xl font-semibold">{formatDuration(reportData.totalSessionDurationSeconds || 0)}</p>
                </div>
                <div className="border rounded-lg p-3">
                  <label className="text-sm text-gray-600">Avg Session Duration</label>
                  <p className="text-xl font-semibold">{formatDuration(reportData.avgSessionDurationSeconds || 0)}</p>
                </div>
                <div className="border rounded-lg p-3">
                  <label className="text-sm text-gray-600">Total Page Views</label>
                  <p className="text-2xl font-bold">{reportData.totalPageViews || 0}</p>
                </div>
                <div className="border rounded-lg p-3">
                  <label className="text-sm text-gray-600">Total Actions</label>
                  <p className="text-2xl font-bold">{reportData.totalActions || 0}</p>
                </div>
                <div className="border rounded-lg p-3">
                  <label className="text-sm text-gray-600">Avg Actions/Session</label>
                  <p className="text-xl font-semibold">{reportData.avgActionsPerSession?.toFixed(2) || 0}</p>
                </div>
              </div>
            </div>

            {/* Временные рамки */}
            <div className="bg-white rounded-lg shadow-md p-6">
              <h2 className="text-xl font-semibold mb-4">Timeline</h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="text-sm text-gray-600">First Event</label>
                  <p className="font-semibold">{formatDate(reportData.firstEventDate)}</p>
                </div>
                <div>
                  <label className="text-sm text-gray-600">Last Event</label>
                  <p className="font-semibold">{formatDate(reportData.lastEventDate)}</p>
                </div>
                <div>
                  <label className="text-sm text-gray-600">Days Since Last Event</label>
                  <p className={`font-semibold ${reportData.daysSinceLastEvent > 30 ? 'text-red-600' : 'text-gray-900'}`}>
                    {reportData.daysSinceLastEvent || 0} days
                  </p>
                </div>
              </div>
            </div>

            {/* Engagement & Churn Risk */}
            <div className="bg-white rounded-lg shadow-md p-6">
              <h2 className="text-xl font-semibold mb-4">Engagement & Risk</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="text-center">
                  <label className="text-sm text-gray-600">Engagement Score</label>
                  <div className="mt-2">
                    <div className="relative pt-1">
                      <div className="flex mb-2 items-center justify-between">
                        <div>
                          <span className={`text-xs font-semibold inline-block py-1 px-2 uppercase rounded-full ${getEngagementScoreColor(reportData.engagementScore)}`}>
                            {reportData.engagementScore?.toFixed(1) || 0}%
                          </span>
                        </div>
                      </div>
                      <div className="overflow-hidden h-2 mb-4 text-xs flex rounded bg-gray-200">
                        <div
                          style={{ width: `${reportData.engagementScore || 0}%` }}
                          className="shadow-none flex flex-col text-center whitespace-nowrap text-white justify-center bg-blue-500"
                        ></div>
                      </div>
                    </div>
                  </div>
                </div>
                <div className="text-center">
                  <label className="text-sm text-gray-600">Churn Risk</label>
                  <div className="mt-2">
                    <span className={`px-3 py-1 rounded-full text-sm font-semibold ${getChurnRiskColor(reportData.churnRisk)}`}>
                      {reportData.churnRisk || 'N/A'}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* Последнее обновление */}
            <div className="text-center text-sm text-gray-500">
              Last updated: {formatDate(reportData.updatedAt)}
            </div>
          </div>
        )}

        {/* Сообщение, если данные не загружены */}
        {!reportData && !loading && !error && (
          <div className="bg-white rounded-lg shadow-md p-12 text-center text-gray-500">
            Click "Load Report" to view your usage report
          </div>
        )}
      </div>
    </div>
  );
};

export default ReportPage;