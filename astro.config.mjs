import { defineConfig } from 'astro/config';
import tailwindcss from '@tailwindcss/vite';

export default defineConfig({
  site: 'https://artempodcast.com',
  output: 'static',
  vite: {
    plugins: [tailwindcss()],
  },
});
