import { useState, useEffect } from 'react';
import './index.css';

type ServiceStatus = 'loading' | 'up' | 'down';

interface ServiceData {
  id: string;
  name: string;
  endpoint: string;
  status: ServiceStatus;
  version: string;
  message: string;
  lastChecked: Date | null;
}

const initialServices: ServiceData[] = [
  { id: 'user', name: 'User Service', endpoint: '/api/users', status: 'loading', version: '--', message: 'Checking...', lastChecked: null },
  { id: 'order', name: 'Order Service', endpoint: '/api/orders', status: 'loading', version: '--', message: 'Checking...', lastChecked: null },
  { id: 'payment', name: 'Payment Service', endpoint: '/api/payments', status: 'loading', version: '--', message: 'Checking...', lastChecked: null },
  { id: 'notification', name: 'Notification Service', endpoint: '/api/notifications', status: 'loading', version: '--', message: 'Checking...', lastChecked: null },
];

function App() {
  const [services, setServices] = useState<ServiceData[]>(initialServices);

  const checkService = async (serviceId: string, endpoint: string) => {
    setServices(prev => prev.map(s => s.id === serviceId ? { ...s, status: 'loading' } : s));
    
    try {
      // Parallel fetch for both endpoints
      const [pingRes, infoRes] = await Promise.all([
        fetch(`${endpoint}/ping`).catch(() => null),
        fetch(`${endpoint}/info`).catch(() => null)
      ]);

      const pingData = pingRes?.ok ? await pingRes.json() : null;
      const infoData = infoRes?.ok ? await infoRes.json() : null;

      if (pingData?.status === 'UP') {
        setServices(prev => prev.map(s => s.id === serviceId ? {
          ...s,
          status: 'up',
          version: infoData?.version || 'Unknown',
          message: pingData.message || 'Running smoothly',
          lastChecked: new Date()
        } : s));
      } else {
        throw new Error('Service down');
      }
    } catch (err) {
      setServices(prev => prev.map(s => s.id === serviceId ? {
        ...s,
        status: 'down',
        message: 'Connection Failed',
        lastChecked: new Date()
      } : s));
    }
  };

  const checkAllServices = () => {
    services.forEach(s => checkService(s.id, s.endpoint));
  };

  useEffect(() => {
    checkAllServices();
    // Auto refresh every 30 seconds
    const interval = setInterval(checkAllServices, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="dashboard">
      <header>
        <h1>Microservices Nexus</h1>
        <p className="subtitle">Real-time K8s Architecture Monitor</p>
      </header>

      <div className="services-grid">
        {services.map((service) => (
          <div key={service.id} className="service-card">
            <div className="service-header">
              <div className="service-title">
                {service.name}
              </div>
              <div className={`status-indicator ${service.status}`} title={service.status} />
            </div>
            
            <div className="service-details">
              <div className="detail-item">
                <span className="detail-label">Endpoint</span>
                <span className="detail-value">{service.endpoint}</span>
              </div>
              <div className="detail-item">
                <span className="detail-label">Version</span>
                <span className="detail-value">{service.version}</span>
              </div>
              <div className="detail-item">
                <span className="detail-label">Status</span>
                <span className={`detail-value ${service.status === 'down' ? 'error' : ''}`}>
                  {service.message}
                </span>
              </div>
              <div className="detail-item">
                <span className="detail-label">Last Ping</span>
                <span className="detail-value" style={{background: 'transparent', padding: 0}}>
                  {service.lastChecked ? service.lastChecked.toLocaleTimeString() : '--:--:--'}
                </span>
              </div>
            </div>

            <div className="action-bar">
              <button 
                className="btn" 
                onClick={() => checkService(service.id, service.endpoint)}
                disabled={service.status === 'loading'}
              >
                {service.status === 'loading' ? 'Pinging...' : 'Refresh'}
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default App;
