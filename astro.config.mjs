import { defineConfig } from 'astro/config';
import vercel from '@astrojs/vercel';

export default defineConfig({
  site: 'https://shengxia.dev',
  server: { host: true },
  output: 'server',
  adapter: vercel(),
  vite: {
    ssr: {
      external: ['mysql2']
    }
  }
});
