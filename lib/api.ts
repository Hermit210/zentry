// API client for Zentry Cloud frontend
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

// Types
interface User {
  id: number;
  email: string;
  name: string;
  credits: number;
  created_at: string;
}

interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

interface Project {
  id: number;
  name: string;
  description: string;
  created_at: string;
}

interface VM {
  id: number;
  name: string;
  instance_type: string;
  image: string;
  status: string;
  ip_address: string;
  created_at: string;
}

// API Client Class
class ZentryAPI {
  private baseURL: string;
  private token: string | null = null;

  constructor(baseURL: string = API_BASE_URL) {
    this.baseURL = baseURL;
    // Load token from localStorage if available
    if (typeof window !== 'undefined') {
      const storedToken = localStorage.getItem('zentry_token');
      this.token = (storedToken && storedToken !== 'undefined' && storedToken !== 'null') ? storedToken : null;
    }
  }

  // Set authentication token
  setToken(token: string) {
    this.token = token;
    if (typeof window !== 'undefined') {
      localStorage.setItem('zentry_token', token);
    }
  }

  // Clear authentication token
  clearToken() {
    this.token = null;
    if (typeof window !== 'undefined') {
      localStorage.removeItem('zentry_token');
      localStorage.removeItem('zentry_user');
    }
  }

  // Make HTTP request
  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;
    
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(options.headers as Record<string, string>),
    };

    // Add authorization header if token exists
    if (this.token) {
      headers.Authorization = `Bearer ${this.token}`;
    }

    const response = await fetch(url, {
      ...options,
      headers,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
    }

    return response.json();
  }

  // Authentication methods
  async signup(email: string, name: string, password: string): Promise<AuthResponse> {
    const response = await this.request<AuthResponse>('/auth/signup', {
      method: 'POST',
      body: JSON.stringify({ email, name, password }),
    });

    this.setToken(response.access_token);
    
    // Store user info
    if (typeof window !== 'undefined') {
      localStorage.setItem('zentry_user', JSON.stringify(response.user));
    }

    return response;
  }

  async login(email: string, password: string): Promise<AuthResponse> {
    const response = await this.request<AuthResponse>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });

    this.setToken(response.access_token);
    
    // Store user info
    if (typeof window !== 'undefined') {
      localStorage.setItem('zentry_user', JSON.stringify(response.user));
    }

    return response;
  }

  async getCurrentUser(): Promise<User> {
    return this.request<User>('/auth/me');
  }

  logout() {
    this.clearToken();
  }

  // Project methods
  async getProjects(): Promise<Project[]> {
    return this.request<Project[]>('/projects');
  }

  async createProject(name: string, description?: string): Promise<Project> {
    return this.request<Project>('/projects', {
      method: 'POST',
      body: JSON.stringify({ name, description }),
    });
  }

  // VM methods
  async getVMs(): Promise<VM[]> {
    const response = await this.request<{vms: VM[], total_count: number, filters_applied: any}>('/vms');
    return response.vms || [];
  }

  async getVM(vmId: string): Promise<VM> {
    return this.request<VM>(`/vms/${vmId}`);
  }

  async createVM(vmData: {
    name: string;
    instance_type: string;
    image: string;
    project_id: string;
  }): Promise<VM> {
    return this.request<VM>('/vms', {
      method: 'POST',
      body: JSON.stringify(vmData),
    });
  }

  async startVM(vmId: string): Promise<{ success: boolean; message: string }> {
    return this.request<{ success: boolean; message: string }>(`/vms/${vmId}/start`, {
      method: 'POST',
    });
  }

  async stopVM(vmId: string): Promise<{ success: boolean; message: string }> {
    return this.request<{ success: boolean; message: string }>(`/vms/${vmId}/stop`, {
      method: 'POST',
    });
  }

  async restartVM(vmId: string): Promise<{ success: boolean; message: string }> {
    return this.request<{ success: boolean; message: string }>(`/vms/${vmId}/restart`, {
      method: 'POST',
    });
  }

  async deleteVM(vmId: string): Promise<{ success: boolean; message: string }> {
    return this.request<{ success: boolean; message: string }>(`/vms/${vmId}`, {
      method: 'DELETE',
    });
  }

  async getVMPricing(): Promise<{
    pricing: Record<string, number>;
    currency: string;
    specifications: Record<string, any>;
  }> {
    return this.request('/vms/pricing/info');
  }

  // Billing methods
  async getCreditBalance(): Promise<{
    current_credits: number;
    total_spent: number;
    monthly_spending: number;
    projected_monthly_cost: number;
  }> {
    return this.request('/billing/credits');
  }

  async getBillingHistory(params?: {
    page?: number;
    limit?: number;
    action_type?: string;
  }): Promise<{
    items: any[];
    total: number;
    page: number;
    limit: number;
  }> {
    const queryParams = new URLSearchParams();
    if (params?.page) queryParams.append('page', params.page.toString());
    if (params?.limit) queryParams.append('limit', params.limit.toString());
    if (params?.action_type) queryParams.append('action_type', params.action_type);
    
    const query = queryParams.toString();
    return this.request(`/billing/history${query ? `?${query}` : ''}`);
  }

  async addCredits(amount: number, description?: string): Promise<{
    success: boolean;
    message: string;
    data: any;
  }> {
    return this.request('/billing/credits/add', {
      method: 'POST',
      body: JSON.stringify({ amount, description }),
    });
  }

  async getUsageSummary(periodDays: number = 30): Promise<{
    user_id: string;
    current_credits: number;
    total_spent: number;
    active_vms: number;
    total_vms: number;
    hourly_cost: number;
    projected_monthly_cost: number;
  }> {
    return this.request(`/billing/usage-summary?period_days=${periodDays}`);
  }

  // Monitoring methods
  async getVMMetrics(vmId: string): Promise<{
    vm_id: string;
    vm_name: string;
    cpu_usage: number;
    memory_usage: number;
    disk_usage: number;
    network_in: number;
    network_out: number;
    uptime_hours: number;
    cost_per_hour: number;
    total_cost: number;
  }> {
    return this.request(`/monitoring/vms/${vmId}/metrics`);
  }

  async getVMMetricsHistory(vmId: string, hours: number = 24): Promise<{
    vm_id: string;
    metrics: any[];
    averages: any;
    peaks: any;
  }> {
    return this.request(`/monitoring/vms/${vmId}/metrics/history?hours=${hours}`);
  }

  async getMonitoringDashboard(): Promise<{
    overview: any;
    vm_summary: any[];
    alerts: any[];
    resource_utilization: any;
  }> {
    return this.request('/monitoring/dashboard');
  }

  // System health
  async getSystemHealth(): Promise<{
    overall_status: string;
    components: any;
    performance: any;
  }> {
    return this.request('/monitoring/system/health');
  }

  // Check if user is authenticated
  isAuthenticated(): boolean {
    return !!this.token;
  }

  // Get stored user info
  getStoredUser(): User | null {
    if (typeof window !== 'undefined') {
      const userStr = localStorage.getItem('zentry_user');
      if (userStr && userStr !== 'undefined' && userStr !== 'null') {
        try {
          return JSON.parse(userStr);
        } catch (error) {
          console.warn('Failed to parse stored user data:', error);
          localStorage.removeItem('zentry_user');
          return null;
        }
      }
    }
    return null;
  }
}

// Export singleton instance
export const api = new ZentryAPI();

// Export types
export type { User, AuthResponse, Project, VM };