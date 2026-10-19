import { http } from './http'

/* ==================== 认证 ==================== */
export const authApi = {
  register: (data: { account: string; nickname: string; password: string; confirm_password: string }) =>
    http.post<any, any>('/auth/register', data),
  login: (data: { account: string; password: string }) =>
    http.post<any, any>('/auth/login', data),
  logout: () => {
    // 带上 refresh token，使后端能将其一并加入 Redis 黑名单（原实现未传，导致 refresh token 未被吊销）
    const rt = localStorage.getItem('tyt_refresh_token')
    return http.post<any, any>('/auth/logout', {}, rt ? { headers: { 'X-Refresh-Token': rt } } : {})
  },
  me: () => http.get<any, any>('/auth/me'),
  refresh: (refresh_token: string) => http.post<any, any>('/auth/refresh', { refresh_token }),
  guestInfo: () => http.get<any, any>('/auth/guest-info'),
  changePassword: (data: { old_password: string; new_password: string }) =>
    http.put<any, any>('/auth/password', data),
  updateAvatar: (file: File) => {
    const fd = new FormData()
    fd.append('file', file)
    // 不手动设置 Content-Type：需由浏览器附带 multipart boundary，否则服务端无法解析
    return http.put<any, any>('/auth/avatar', fd, { timeout: 60000 })
  },
}

/* ==================== 会员订阅 ==================== */
export const billingApi = {
  /* 方案 + 权益介绍 + 当前会员状态 */
  plans: () => http.get<any, any>('/billing/plans'),
  /* 创建订阅订单（plan: monthly 包月 / auto_monthly 连续包月） */
  createOrder: (data: { plan: string; pay_channel: string }) =>
    http.post<any, any>('/billing/orders', data),
  /* 模拟支付完成（演示环境） */
  payOrder: (orderId: number) => http.post<any, any>(`/billing/orders/${orderId}/pay`),
  /* 取消连续包月自动续费 */
  cancelAutoRenew: () => http.post<any, any>('/billing/cancel-auto-renew'),
  /* 我的订阅订单 */
  orders: () => http.get<any, any>('/billing/orders'),
}

/* ==================== 生活类 ==================== */
export const lifeApi = {
  searchMerchants: (params: { keyword: string; city?: string; page?: number; page_size?: number }) =>
    http.get<any, any>('/life/merchants/search', { params }),
  merchantDetail: (id: number) => http.get<any, any>(`/life/merchants/${id}`),
  createReview: (id: number, data: { rating: number; content: string }) =>
    http.post<any, any>(`/life/merchants/${id}/reviews`, data),
  searchEstates: (params: { keyword: string; city?: string }) =>
    http.get<any, any>('/life/housing/estates/search', { params }),
  housingRecords: (params: { subject_type: string; keyword: string }) =>
    http.get<any, any>('/life/housing/records', { params }),
  createComplaint: (data: { subject_type: string; subject_id: number; subject_label: string; content: string; category?: string }) =>
    http.post<any, any>('/life/housing/complaints', data),
  jobCompanies: (params: { name: string }) => http.get<any, any>('/life/jobs/companies', { params }),
  personSearch: (data: { name: string }) => http.post<any, any>('/life/person/search', data),
}

/* ==================== 生活圈 ==================== */
export const communityApi = {
  listPosts: (params: { page?: number; page_size?: number; category?: string; topic?: string; keyword?: string }) =>
    http.get<any, any>('/community/posts', { params }),
  getTopics: () => http.get<any, any>('/community/topics'),
  getPost: (id: number) => http.get<any, any>(`/community/posts/${id}`),
  createPost: (data: { category: string; title: string; content: string; is_anonymous: boolean; images?: string[] }) =>
    http.post<any, any>('/community/posts', data),
  uploadImage: (file: File) => {
    const fd = new FormData()
    fd.append('file', file)
    // 不手动设置 Content-Type：需由浏览器附带 multipart boundary，否则服务端无法解析
    return http.post<any, any>('/community/upload-image', fd, { timeout: 60000 })
  },
  likePost: (id: number) => http.post<any, any>(`/community/posts/${id}/like`),
  commentPost: (id: number, data: { content: string; is_anonymous: boolean }) =>
    http.post<any, any>(`/community/posts/${id}/comments`, data),
  report: (data: { target_type: string; target_id: number; reason: string; description?: string }) =>
    http.post<any, any>('/community/reports', data),
}

/* ==================== 商业类 ==================== */
export const bizApi = {
  searchCompanies: (params: { keyword: string; page?: number; page_size?: number }) =>
    http.get<any, any>('/biz/companies/search', { params }),
  companyDetail: (id: number) => http.get<any, any>(`/biz/companies/${id}`),
  shareholders: (id: number) => http.get<any, any>(`/biz/companies/${id}/shareholders`),
  personnel: (id: number) => http.get<any, any>(`/biz/companies/${id}/personnel`),
  investments: (id: number) => http.get<any, any>(`/biz/companies/${id}/investments`),
  branches: (id: number) => http.get<any, any>(`/biz/companies/${id}/branches`),
  changes: (id: number) => http.get<any, any>(`/biz/companies/${id}/changes`),
  risks: (id: number, params?: { risk_type?: string }) =>
    http.get<any, any>(`/biz/companies/${id}/risks`, { params }),
}

/* ==================== 图谱 ==================== */
export const graphApi = {
  status: () => http.get<any, any>('/biz/graph/status'),
  expand: (tytId: number, limit = 30) =>
    http.get<any, any>(`/biz/graph/nodes/${tytId}/expand`, { params: { limit } }),
  companyGraph: (companyId: number) => http.get<any, any>(`/biz/graph/companies/${companyId}`),
  path: (fromId: number, toId: number) =>
    http.get<any, any>('/biz/graph/path', { params: { from_id: fromId, to_id: toId } }),
  controller: (companyId: number) => http.get<any, any>(`/biz/graph/companies/${companyId}/controller`),
}

/* ==================== 监控 ==================== */
export const monitorApi = {
  watches: () => http.get<any, any>('/biz/monitor/watches'),
  addWatch: (data: { company_id: number }) => http.post<any, any>('/biz/monitor/watches', data),
  removeWatch: (id: number) => http.delete<any, any>(`/biz/monitor/watches/${id}`),
  events: (params?: { page?: number; page_size?: number }) =>
    http.get<any, any>('/biz/monitor/events', { params }),
  scan: () => http.post<any, any>('/biz/monitor/scan'),
  notifications: () => http.get<any, any>('/biz/monitor/notifications'),
  markRead: (id: number) => http.post<any, any>(`/biz/monitor/notifications/${id}/read`),
  schedule: () => http.get<any, any>('/biz/monitor/schedule'),
  updateSchedule: (data: { enabled: boolean; freq: string }) =>
    http.put<any, any>('/biz/monitor/schedule', data),
  digest: () => http.get<any, any>('/biz/monitor/digest'),
}

/* ==================== 站内消息中心（右上角铃铛） ==================== */
export const notificationApi = {
  list: (params?: { unread_only?: boolean; page?: number; page_size?: number }) =>
    http.get<any, any>('/notifications', { params }),
  unreadCount: () => http.get<any, any>('/notifications/unread-count'),
  markRead: (id: number) => http.post<any, any>(`/notifications/${id}/read`),
  markAllRead: () => http.post<any, any>('/notifications/read-all'),
  remove: (id: number) => http.delete<any, any>(`/notifications/${id}`),
}

/* ==================== 报告 ==================== */
export const reportApi = {
  create: (data: { company_id: number; template: string }) =>
    http.post<any, any>('/biz/reports', data),
  list: () => http.get<any, any>('/biz/reports'),
  get: (taskId: number) => http.get<any, any>(`/biz/reports/${taskId}`),
}

export function reportDownloadUrl(taskId: number, format: 'pdf' | 'xlsx') {
  return `/api/v1/biz/reports/${taskId}/download?format=${format}`
}

/* ==================== 线索 ==================== */
export const leadApi = {
  list: (params?: { [k: string]: any }) => http.get<any, any>('/biz/leads', { params }),
  options: () => http.get<any, any>('/biz/leads/options'),
  favorites: () => http.get<any, any>('/biz/leads/favorites'),
  favorite: (id: number) => http.post<any, any>(`/biz/leads/${id}/favorite`),
  follow: (id: number, data: { status: string; note?: string; next_action?: string }) =>
    http.put<any, any>(`/biz/leads/${id}/follow`, data),
}

/* ==================== 管理端 ==================== */
export const adminApi = {
  pendingOverview: () => http.get<any, any>('/admin/audit/pending'),
  pendingList: (contentType: string, params?: { page?: number; page_size?: number }) =>
    http.get<any, any>(`/admin/audit/${contentType}`, { params }),
  audit: (contentType: string, itemId: number, data: { action: string; reason?: string }) =>
    http.post<any, any>(`/admin/audit/${contentType}/${itemId}`, data),
  violationWords: () => http.get<any, any>('/admin/audit/violation-words'),
  updateViolationWords: (items: { word: string; category?: string }[]) =>
    http.put<any, any>('/admin/audit/violation-words', { items }),
  violationScan: () => http.post<any, any>('/admin/audit/violation-scan'),
  users: (params?: { keyword?: string; role?: string; status?: string; page?: number; page_size?: number }) =>
    http.get<any, any>('/admin/users', { params }),
  updateRole: (userId: number, role: string) =>
    http.put<any, any>(`/admin/users/${userId}/role`, { role }),
  updateStatus: (userId: number, status: string) =>
    http.put<any, any>(`/admin/users/${userId}/status`, { status }),
  dataSources: () => http.get<any, any>('/admin/data/sources'),
  importData: (data: { source_code: string; entity: string; csv_content: string }) =>
    http.post<any, any>('/admin/data/import', data),
  collectLogs: (params?: { page?: number; page_size?: number }) =>
    http.get<any, any>('/admin/data/collect-logs', { params }),
  auditLogs: (params?: { page?: number; page_size?: number }) =>
    http.get<any, any>('/admin/audit-logs', { params }),
  dashboard: () => http.get<any, any>('/admin/dashboard'),
  kbDocuments: (params?: { kind?: string; keyword?: string; page?: number; page_size?: number }) =>
    http.get<any, any>('/admin/kb/documents', { params }),
  kbAddDocument: (data: { title: string; content: string; url?: string }) =>
    http.post<any, any>('/admin/kb/documents', data),
  kbDeleteDocument: (docId: string) => http.delete<any, any>(`/admin/kb/documents/${docId}`),
  kbResync: () => http.post<any, any>('/admin/kb/resync'),
  kbImportDocument: (file: File, title?: string) => {
    const form = new FormData()
    form.append('file', file)
    if (title) form.append('title', title)
    // 不手动设 Content-Type：axios 会自动为 FormData 添加 multipart/form-data 及 boundary
    return http.post<any, any>('/admin/kb/documents/import', form)
  },
  /* 模型管理：百炼问答/识图开关 + 各模型讲解 */
  modelConfig: () => http.get<any, any>('/admin/ai/model-config'),
  updateModelConfig: (payload: { bailian_enabled?: boolean; bailian_vision_enabled?: boolean }) =>
    http.put<any, any>('/admin/ai/model-config', payload),
}

/* ==================== AI ==================== */
export const aiApi = {
  status: () => http.get<any, any>('/ai/status'),
  /* 异步问答：提交问题立即返回 task_id，回答在后台生成 */
  chat: (question: string) => http.post<any, any>('/ai/chat', { question }),
  /* 轮询问答任务状态：queued/running/done/failed，done 时含完整回答 */
  task: (taskId: number) => http.get<any, any>(`/ai/chat/tasks/${taskId}`),
  history: (limit = 50) => http.get<any, any>('/ai/history', { params: { limit } }),
  removeHistory: (id: number) => http.delete<any, any>(`/ai/history/${id}`),
  clearHistory: () => http.delete<any, any>('/ai/history'),
}

/* ==================== AI 识图 ==================== */
export const visionApi = {
  recognize: (data: { image_base64: string }) => http.post<any, any>('/vision/recognize', data),
  records: () => http.get<any, any>('/vision/records'),
  recordDetail: (id: number) => http.get<any, any>(`/vision/records/${id}`),
  deleteRecord: (id: number) => http.delete<any, any>(`/vision/records/${id}`),
}

/* ==================== 定位天气 ==================== */
export const weatherApi = {
  now: (params?: { lat?: number; lon?: number }) => http.get<any, any>('/weather/now', { params }),
  /* 逆地理编码：GCJ-02（高德）坐标 -> {city, district} */
  position: (lat: number, lon: number) => http.get<any, any>('/weather/position', { params: { lat, lon } }),
  /* 网络定位辅助：auto（融合）/ wifi / cellular -> {city, district, accuracy_m, nearby, ...} */
  locate: (data: { method: string; lat?: number; lon?: number }) =>
    http.post<any, any>('/weather/locate', data),
}

/* ==================== 多智能体股票 ==================== */
export const stockApi = {
  search: (params?: { keyword?: string }) => http.get<any, any>('/biz/stock/search', { params }),
  agents: () => http.get<any, any>('/biz/stock/agents'),
  indices: () => http.get<any, any>('/biz/stock/indices'),
  quote: (code: string) => http.get<any, any>(`/biz/stock/quote/${code}`),
}
