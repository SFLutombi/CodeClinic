// Type definitions for CodeClinic scan functionality

export type ScanType = 'full_site' | 'selective_pages';

export type SeverityLevel = 'high' | 'medium' | 'low' | 'informational';

export type VulnerabilityType = 
  | 'xss'
  | 'sql_injection'
  | 'csrf'
  | 'insecure_headers'
  | 'ssl_tls'
  | 'authentication'
  | 'authorization'
  | 'data_exposure'
  | 'other';

export interface Vulnerability {
  id: string;
  type: VulnerabilityType;
  severity: SeverityLevel;
  title: string;
  description: string;
  url: string;
  parameter?: string;
  evidence?: string;
  solution?: string;
  cwe_id?: string;
  confidence?: string;
}

export interface ScanRequest {
  url: string;
  scan_type: ScanType;
}

export interface ScanResponse {
  scan_id: string;
  status: string;
  message: string;
}

export interface ScanStatus {
  id: string;
  url: string;
  scan_type: ScanType;
  status: string;
  progress: number;
  vulnerabilities: Vulnerability[];
  pages: string[];
  selected_pages?: string[];
  error?: string;
  created_at: string;
  completed_at?: string;
}

export interface PageInfo {
  url: string;
  title?: string;
  status_code: number;
  content_type?: string;
  size?: number;
}
