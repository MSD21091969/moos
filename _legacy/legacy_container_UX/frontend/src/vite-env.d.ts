/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_GEMINI_API_KEY: AIzaSyCMsFK0dhY810FF4_ZjfRgulLFcKctcufk;
  readonly VITE_API_URL?: string;
  readonly VITE_ENVIRONMENT?: string;
  readonly VITE_DEBUG?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
