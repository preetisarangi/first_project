// Ambient declarations to ensure clean IDE resolution before npm install

declare module "tailwindcss" {
  export interface Config {
    content: string[];
    theme?: Record<string, any>;
    plugins?: any[];
    [key: string]: any;
  }
  const config: Config;
  export default config;
}

declare module "next" {
  export interface NextConfig {
    reactStrictMode?: boolean;
    [key: string]: any;
  }
  export interface Metadata {
    title?: string | { default: string; template?: string };
    description?: string;
    [key: string]: any;
  }
  const next: (options?: any) => any;
  export default next;
}

declare module "lucide-react" {
  import * as React from "react";
  export interface LucideProps extends React.SVGProps<SVGSVGElement> {
    size?: string | number;
    color?: string;
    strokeWidth?: string | number;
    className?: string;
  }
  export type Icon = React.ForwardRefExoticComponent<LucideProps>;
  export const Cpu: Icon;
  export const Sparkles: Icon;
  export const Globe: Icon;
  export const FileText: Icon;
  export const RefreshCw: Icon;
  export const Square: Icon;
  export const CheckCircle2: Icon;
  export const CheckCircle: Icon;
  export const FileCode2: Icon;
  export const Database: Icon;
  export const Code: Icon;
  export const Code2: Icon;
  export const PlayCircle: Icon;
  export const Wrench: Icon;
  export const Clock: Icon;
  export const AlertCircle: Icon;
  export const AlertTriangle: Icon;
  export const Loader2: Icon;
  export const Terminal: Icon;
  export const GitCompare: Icon;
  export const Copy: Icon;
  export const Check: Icon;
  export const Download: Icon;
  export const Github: Icon;
  export const ExternalLink: Icon;
  export const Activity: Icon;
}

declare module "clsx" {
  export type ClassValue = any;
  export function clsx(...inputs: ClassValue[]): string;
  export default clsx;
}

declare module "tailwind-merge" {
  export function twMerge(...classLists: string[]): string;
}

